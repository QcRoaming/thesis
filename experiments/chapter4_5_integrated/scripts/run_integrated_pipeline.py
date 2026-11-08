#!/usr/bin/env python3
"""Connect Chapter 4 schedule selection to the Chapter 5 BLIS evaluator."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import random
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import torch


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
REPO = EXPERIMENTS.parents[2]
CHAPTER4 = EXPERIMENTS / "chapter4_space"
CHAPTER5 = EXPERIMENTS / "chapter5_blis_adapter"
sys.path.insert(0, str(CHAPTER4 / "scripts"))
sys.path.insert(0, str(CHAPTER5 / "scripts"))

from chapter4lib import (  # noqa: E402
    Candidate,
    generate_spaces_for_task,
    load_inputs,
    raw_candidates,
)
import run_chapter5 as chapter5  # noqa: E402


CONFIG = json.loads(
    (PROJECT / "data" / "integration_config.json").read_text(encoding="utf-8")
)
BUILD = PROJECT / "build"
RAW = PROJECT / "raw"
PROCESSED = PROJECT / "processed"
REPORTS = PROJECT / "reports"
TUNER = PROJECT / "tuner"
DYNAMIC_DRIVER = CHAPTER5 / "runtime" / "dynamic_matmul_bench.cpp"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dynamic_payload(symbol: str, nested: bool) -> str:
    function = f"""func.func @{symbol}(
    %A: tensor<?x?xf32>,
    %B: tensor<?x?xf32>,
    %C: tensor<?x?xf32>) -> tensor<?x?xf32>
    attributes {{llvm.emit_c_interface}} {{
  %0 = linalg.matmul
    ins(%A, %B : tensor<?x?xf32>, tensor<?x?xf32>)
    outs(%C : tensor<?x?xf32>) -> tensor<?x?xf32>
  return %0 : tensor<?x?xf32>
}}
"""
    if not nested:
        return function
    indented = "\n".join("  " + line if line else line for line in function.splitlines())
    return f"module @integrated_payload attributes {{buddy.payload}} {{\n{indented}\n}}\n"


def blis_schedule(candidate: Candidate, mr: int, nr: int) -> str:
    options = " ".join(
        f"{name}={value}"
        for name, value in (
            ("tile-m", candidate.tile_m),
            ("tile-n", candidate.tile_n),
            ("tile-k", candidate.tile_k),
            ("mr", mr),
            ("nr", nr),
        )
    )
    return f"""
module attributes {{transform.with_named_sequence}} {{
  transform.named_sequence @__transform_main(%root: !transform.any_op) {{
    %payload = transform.structured.match ops{{["builtin.module"]}}
      attributes{{buddy.payload}} in %root
      : (!transform.any_op) -> !transform.any_op
    %bufferized = transform.bufferization.one_shot_bufferize
      layout{{IdentityLayoutMap}} %payload
      {{bufferize_function_boundaries = true}}
      : (!transform.any_op) -> !transform.any_op
    %prepared = transform.apply_registered_pass
      "buddy-materialize-blis-packed-matmul" to %bufferized
      {{options = "{options}"}}
      : (!transform.any_op) -> !transform.any_op
    %direct = transform.structured.match ops{{["func.call"]}}
      attributes{{callee = @buddy_microkernel_placeholder}} in %prepared
      : (!transform.any_op) -> !transform.any_op
    transform.buddy.call_microkernel
      %direct, "buddy_blis_sgemm_6x16" : !transform.any_op
    %fringe = transform.structured.match ops{{["func.call"]}}
      attributes{{callee = @buddy_microkernel_fringe_placeholder}} in %prepared
      : (!transform.any_op) -> !transform.any_op
    transform.buddy.call_microkernel
      %fringe, "buddy_blis_sgemm_6x16_fringe" : !transform.any_op
    transform.yield
  }}
}}
"""


def fallback_schedule(candidate: Candidate) -> str:
    vector_step = """
    %func = transform.get_parent_op %tiled {isolated_from_above}
      : (!transform.any_op) -> !transform.any_op
    transform.structured.vectorize_children_and_apply_patterns %func
      : (!transform.any_op) -> !transform.any_op
""" if candidate.vectorize else ""
    return f"""
module attributes {{transform.with_named_sequence}} {{
  transform.named_sequence @__transform_main(
      %root: !transform.any_op {{transform.consumed}}) {{
    %matmul = transform.structured.match ops{{["linalg.matmul"]}} in %root
      : (!transform.any_op) -> !transform.any_op
    %tiled, %loops:3 = transform.structured.tile_using_for %matmul
      tile_sizes [{candidate.tile_m}, {candidate.tile_n}, {candidate.tile_k}]
      : (!transform.any_op) -> (!transform.any_op, !transform.any_op,
          !transform.any_op, !transform.any_op)
{vector_step}    %bufferized = transform.bufferization.one_shot_bufferize
      layout{{IdentityLayoutMap}} %root
      {{bufferize_function_boundaries = true}}
      : (!transform.any_op) -> !transform.any_op
    transform.yield
  }}
}}
"""


def timed_run(command: list[str], log: Path) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.perf_counter()
    completed = chapter5.run(command, log)
    return completed, (time.perf_counter() - started) * 1000.0


def expected_fringe_calls(
    task: dict[str, Any], candidate: Candidate, mr: int, nr: int,
    measurement: dict[str, int],
) -> int:
    shape = task["shape"]
    m_panels = math.ceil(shape["m"] / mr)
    n_panels = math.ceil(shape["n"] / nr)
    full_panels = (shape["m"] // mr) * (shape["n"] // nr)
    fringe_per_k_panel = m_panels * n_panels - full_panels
    k_panels = math.ceil(shape["k"] / candidate.tile_k)
    invocations = (measurement["warmups"] + measurement["repeats"]) * measurement["inner_iters"]
    return fringe_per_k_panel * k_panels * invocations


def evaluate_candidate(
    task: dict[str, Any], row: dict[str, Any], contract: dict[str, Any] | None,
    measurement: dict[str, int], force: bool,
) -> dict[str, Any]:
    candidate = Candidate(
        int(row["tile_m"]), int(row["tile_n"]), int(row["tile_k"]),
        str(row["pack_mode"]), bool(row["vectorize"]),
    )
    predicted_path = str(row["predicted_path"])
    use_blis = predicted_path in {"direct", "adapt"}
    case = BUILD / "evaluations" / task["id"] / candidate.id
    measurement_path = case / "measurement.json"
    if measurement_path.exists() and not force:
        cached = json.loads(measurement_path.read_text(encoding="utf-8"))
        if cached.get("measurement_protocol") == measurement:
            return cached

    case.mkdir(parents=True, exist_ok=True)
    symbol = "integrated_" + re.sub(r"[^A-Za-z0-9_]", "_", f"{task['id']}_{candidate.id}")
    input_mlir = case / "input.mlir"
    transformed = case / "transformed.mlir"
    llvm_mlir = case / "llvm.mlir"
    llvm_ir = case / "kernel.ll"
    executable = case / "benchmark"
    if use_blis:
        if contract is None:
            raise RuntimeError(f"{task['id']} predicts {predicted_path} without a contract")
        schedule = blis_schedule(candidate, int(contract["mr"]), int(contract["nr"]))
    else:
        schedule = fallback_schedule(candidate)
    input_mlir.write_text(dynamic_payload(symbol, use_blis) + schedule, encoding="utf-8")

    timings: dict[str, float] = {}
    if use_blis:
        transform_command = [
            str(chapter5.BUDDY_OPT), str(input_mlir), "--transform-interpreter",
            "--buddy-finalize-transform-payload", "--canonicalize", "--cse",
            "-o", str(transformed),
        ]
    else:
        transform_command = [
            str(chapter5.MLIR_OPT), str(input_mlir), "--transform-interpreter",
            "-test-transform-dialect-erase-schedule", "--canonicalize", "--cse",
            "-o", str(transformed),
        ]
    _, timings["transform_ms"] = timed_run(transform_command, case / "01_transform.log")
    _, timings["lower_dialect_ms"] = timed_run(
        [str(chapter5.MLIR_OPT), str(transformed), "--convert-linalg-to-loops",
         "--test-lower-to-llvm", "-o", str(llvm_mlir)],
        case / "02_lower.log",
    )
    _, timings["translate_ms"] = timed_run(
        [str(chapter5.MLIR_TRANSLATE), "--mlir-to-llvmir", str(llvm_mlir),
         "-o", str(llvm_ir)],
        case / "03_translate.log",
    )

    compile_command = [
        str(chapter5.CXX), "-O3", "-march=native", "-std=c++17",
        f"-DKERNEL_SYMBOL={symbol}", str(DYNAMIC_DRIVER), str(llvm_ir),
    ]
    if use_blis:
        compile_command.extend([
            "-DBLIS_ADAPTER_ENABLED=1", "-I" + str(chapter5.BLIS_INCLUDE),
            str(chapter5.ADAPTER), str(chapter5.BLIS_LIBRARY), "-lpthread", "-lm",
        ])
    compile_command.extend(["-o", str(executable)])
    _, timings["native_compile_ms"] = timed_run(
        compile_command, case / "04_native_compile.log"
    )
    symbols, timings["symbol_check_ms"] = timed_run(
        ["nm", "-C", str(executable)], case / "05_symbols.log"
    )

    shape = task["shape"]
    benchmark, timings["benchmark_wall_ms"] = timed_run(
        [
            "taskset", "-c", str(measurement["cpu_affinity"]), str(executable),
            str(shape["m"]), str(shape["k"]), str(shape["n"]),
            str(measurement["warmups"]), str(measurement["repeats"]),
            str(measurement["inner_iters"]),
        ],
        case / "06_benchmark.log",
    )
    parsed = list(csv.DictReader(io.StringIO(benchmark.stdout)))
    if not parsed or parsed[-1].get("status") != "PASS":
        raise RuntimeError(f"candidate failed correctness: {task['id']} {candidate.id}")
    values = parsed[-1]
    llvm_text = llvm_ir.read_text(encoding="utf-8")
    transformed_text = transformed.read_text(encoding="utf-8")
    has_direct_call = "call void @buddy_blis_sgemm_6x16(" in llvm_text
    has_fringe_call = "call void @buddy_blis_sgemm_6x16_fringe(" in llvm_text
    has_kernel_symbol = " T bli_sgemm_haswell_asm_6x16" in symbols.stdout
    replaced = has_direct_call and has_kernel_symbol
    fringe_calls = int(values["fringe_calls"])
    mr = int(contract["mr"]) if contract else 0
    nr = int(contract["nr"]) if contract else 0
    expected_fringe = (
        expected_fringe_calls(task, candidate, mr, nr, measurement) if use_blis else 0
    )
    if fringe_calls != expected_fringe:
        raise RuntimeError(
            f"fringe count mismatch for {task['id']} {candidate.id}: "
            f"expected {expected_fringe}, observed {fringe_calls}"
        )
    has_k_remainder = use_blis and shape["k"] % candidate.tile_k != 0
    observed_path = (
        "adapt" if replaced and (fringe_calls > 0 or has_k_remainder)
        else "direct" if replaced
        else "fallback"
    )
    result = {
        "task_id": task["id"],
        "candidate_id": candidate.id,
        "tile_m": candidate.tile_m,
        "tile_n": candidate.tile_n,
        "tile_k": candidate.tile_k,
        "pack_mode": candidate.pack_mode,
        "vectorize": candidate.vectorize,
        "contract_id": row.get("contract_id"),
        "predicted_path": predicted_path,
        "observed_path": observed_path,
        "prediction_matches_observation": predicted_path == observed_path,
        "reason_codes": row.get("reason_codes", []),
        "actions": row.get("actions", []),
        "score": float(row["score"]),
        "is_core": bool(row.get("is_core")),
        "is_shell": bool(row.get("is_shell")),
        "status": values["status"],
        "compile_status": "pass",
        "correctness_status": "pass",
        "microkernel_replaced": replaced,
        "has_direct_call": has_direct_call,
        "has_fringe_call": has_fringe_call,
        "has_blis_kernel_symbol": has_kernel_symbol,
        "has_dynamic_dims": "memref.dim" in transformed_text,
        "fringe_calls": fringe_calls,
        "expected_fringe_calls": expected_fringe,
        "median_ms": float(values["median_ms"]),
        "gflops": float(values["gflops"]),
        "max_abs_diff": float(values["max_abs_diff"]),
        "output_aliases_c": int(values["output_aliases_c"]),
        "llvm_ir_bytes": llvm_ir.stat().st_size,
        "executable_bytes": executable.stat().st_size,
        "executable_sha256": sha256(executable),
        "measurement_protocol": measurement,
        **{key: round(value, 6) for key, value in timings.items()},
    }
    measurement_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def load_space_state() -> tuple[dict[str, Any], dict[str, Any]]:
    inputs = load_inputs(CHAPTER4)
    candidates = raw_candidates(inputs["space_config"]["raw_domain"])
    state: dict[str, Any] = {}
    for task in inputs["tasks"]:
        spaces, rows, selection_log = generate_spaces_for_task(
            task, candidates, inputs["contracts"], inputs["space_config"]
        )
        selected = next((item for item in selection_log if item.get("selected")), None)
        contract = next(
            (item for item in inputs["contracts"] if selected and item["id"] == selected["contract_id"]),
            None,
        )
        state[task["id"]] = {
            "task": task,
            "spaces": spaces,
            "rows": {row["candidate_id"]: row for row in rows},
            "contract": contract,
        }
    return inputs, state


def path_matrix(state: dict[str, Any], force: bool) -> list[dict[str, Any]]:
    measurement = dict(CONFIG["baco"])
    measurement = {
        key: int(measurement[key])
        for key in ("warmups", "repeats", "inner_iters", "cpu_affinity")
    }
    results = []
    for case in CONFIG["path_cases"]:
        task_state = state[case["task_id"]]
        row = task_state["rows"][case["candidate_id"]]
        measured = evaluate_candidate(
            task_state["task"], row, task_state["contract"], measurement, force
        )
        results.append({"case_id": case["case_id"], **measured})
    return results


def build_scenario(run_dir: Path, budget: int, indices: list[int]) -> dict[str, Any]:
    doe = min(4, budget)
    return {
        "application_name": "chapter4_5_integrated_blis",
        "optimization_objectives": ["runtime_ms"],
        "optimization_method": "bayesian_optimization",
        "optimization_iterations": max(0, budget - doe),
        "design_of_experiment": {
            "doe_type": "random sampling",
            "number_of_samples": doe,
            "allow_repetitions": False,
        },
        "models": {"model": "gaussian_process"},
        "GP_model": "gpy",
        "hyperparameter_optimization_iterations": 1,
        "acquisition_function": "EI",
        "normalize_inputs": True,
        "predict_noiseless": False,
        "allow_duplicate_samples": False,
        "local_search_random_points": 500,
        "local_search_starting_points": 5,
        "input_parameters": {
            "schedule_index": {
                "parameter_type": "ordinal",
                "values": indices,
                "parameter_default": indices[0],
                "transform": "none",
            }
        },
        "feasible_output": {
            "enable_feasible_predictor": True,
            "name": "Valid",
            "true_value": "True",
            "false_value": "False",
        },
        "run_directory": str(run_dir),
        "log_file": "baco.log",
        "output_data_file": "baco_samples.csv",
    }


def run_baco(state: dict[str, Any], force: bool) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config = CONFIG["baco"]
    task_state = state[config["task_id"]]
    selected_space = task_state["spaces"][CONFIG["space_id"]]
    full_lookup = {row["candidate_id"]: row for row in selected_space}
    missing = [item for item in config["candidate_ids"] if item not in full_lookup]
    if missing:
        raise RuntimeError(f"configured BaCO candidates are outside Expert+Shell: {missing}")
    lookup = []
    for index, candidate_id in enumerate(config["candidate_ids"]):
        row = full_lookup[candidate_id]
        lookup.append({
            "schedule_index": index,
            "candidate_id": candidate_id,
            "tile_m": row["tile_m"],
            "tile_n": row["tile_n"],
            "tile_k": row["tile_k"],
            "pack_mode": row["pack_mode"],
            "vectorize": row["vectorize"],
            "predicted_path": row["predicted_path"],
            "score": row["score"],
            "member_role": "shell" if row.get("is_shell") else "core",
        })
    TUNER.mkdir(parents=True, exist_ok=True)
    run_dir = TUNER / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (TUNER / "integrated_lookup.json").write_text(
        json.dumps({
            "source_space": CONFIG["space_id"],
            "full_space_size": len(selected_space),
            "pool": lookup,
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    scenario = build_scenario(
        run_dir, int(config["budget"]), [item["schedule_index"] for item in lookup]
    )
    scenario_path = TUNER / "baco_scenario.json"
    scenario_path.write_text(json.dumps(scenario, indent=2) + "\n", encoding="utf-8")
    for generated in (run_dir / "baco_samples.csv", run_dir / "baco.log"):
        if generated.exists():
            generated.unlink()
    callback_path = RAW / "baco_callback_log.jsonl"
    if callback_path.exists():
        callback_path.unlink()
    measurement = {
        key: int(config[key])
        for key in ("warmups", "repeats", "inner_iters", "cpu_affinity")
    }
    callbacks: list[dict[str, Any]] = []

    def objective(configuration: dict[str, Any]) -> dict[str, Any]:
        index = int(round(float(configuration["schedule_index"])))
        item = lookup[index]
        row = full_lookup[item["candidate_id"]]
        started = time.perf_counter()
        measured = evaluate_candidate(
            task_state["task"], row, task_state["contract"], measurement, force
        )
        valid = measured["status"] == "PASS" and measured["prediction_matches_observation"]
        record = {
            "invocation": len(callbacks) + 1,
            **item,
            "Valid": valid,
            "runtime_ms": measured["median_ms"] if valid else 1.0e9,
            "observed_path": measured["observed_path"],
            "microkernel_replaced": measured["microkernel_replaced"],
            "correctness_status": measured["correctness_status"],
            "fringe_calls": measured["fringe_calls"],
            "callback_wall_ms": round((time.perf_counter() - started) * 1000.0, 6),
        }
        callbacks.append(record)
        with callback_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
        return {"runtime_ms": record["runtime_ms"], "Valid": valid}

    seed = int(CONFIG["seed"])
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    from baco import run
    from baco.util.file import read_settings_file

    run.optimize(read_settings_file(str(scenario_path)), objective)
    samples = list(csv.DictReader((run_dir / "baco_samples.csv").open(encoding="utf-8")))
    enriched = []
    best = float("inf")
    for iteration, sample in enumerate(samples, 1):
        item = lookup[int(float(sample["schedule_index"]))]
        callback = callbacks[iteration - 1]
        runtime = float(sample["runtime_ms"])
        valid = sample.get("Valid", "False").lower() == "true"
        if valid:
            best = min(best, runtime)
        enriched.append({
            "iteration": iteration,
            **item,
            "runtime_ms": runtime,
            "Valid": valid,
            "best_so_far_ms": best if best < float("inf") else None,
            "observed_path": callback["observed_path"],
            "microkernel_replaced": callback["microkernel_replaced"],
            "correctness_status": callback["correctness_status"],
            "callback_wall_ms": callback["callback_wall_ms"],
        })
    valid_rows = [row for row in enriched if row["Valid"]]
    if not valid_rows:
        raise RuntimeError("BaCO produced no valid integrated evaluations")
    best_row = min(valid_rows, key=lambda row: row["runtime_ms"])
    baco_repo = EXPERIMENTS.parent / "third_party" / "baco"
    commit = subprocess.run(
        ["git", f"--git-dir={baco_repo / '.git'}", "rev-parse", "HEAD"],
        text=True, capture_output=True, check=True,
    ).stdout.strip()
    summary = {
        "baco_commit": commit,
        "task_id": task_state["task"]["id"],
        "source_space": CONFIG["space_id"],
        "full_space_size": len(selected_space),
        "pool_size": len(lookup),
        "pool_role_counts": dict(Counter(item["member_role"] for item in lookup)),
        "budget": int(config["budget"]),
        "evaluated": len(enriched),
        "unique_schedules": len({row["schedule_index"] for row in enriched}),
        "valid_count": len(valid_rows),
        "observed_path_counts": dict(Counter(row["observed_path"] for row in enriched)),
        "real_microkernel_evaluations": sum(bool(row["microkernel_replaced"]) for row in enriched),
        "all_predictions_match_observations": all(
            row["predicted_path"] == row["observed_path"] for row in enriched
        ),
        "best": best_row,
        "seed": seed,
    }
    return enriched, summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value
                for key, value in row.items()
            })


def write_outputs(
    inputs: dict[str, Any], path_rows: list[dict[str, Any]],
    tuning_rows: list[dict[str, Any]], tuning_summary: dict[str, Any],
) -> None:
    for directory in (RAW, PROCESSED, REPORTS):
        directory.mkdir(parents=True, exist_ok=True)
    write_csv(RAW / "path_matrix.csv", path_rows)
    write_csv(PROCESSED / "baco_tuning_trace.csv", tuning_rows)
    summary = {
        "experiment_id": CONFIG["experiment_id"],
        "source_artifacts": {
            "chapter4_space_config": {
                "path": str(CHAPTER4 / "data" / "space_configs.json"),
                "sha256": sha256(CHAPTER4 / "data" / "space_configs.json"),
            },
            "chapter4_contracts": inputs["source_files"]["contracts"],
            "chapter4_rules": inputs["source_files"]["rules"],
            "chapter5_packing_pass": {
                "path": str(REPO / "midend/lib/Conversion/MatMulOptimization/MatMulBlisMicrokernel.cpp"),
                "sha256": sha256(REPO / "midend/lib/Conversion/MatMulOptimization/MatMulBlisMicrokernel.cpp"),
            },
        },
        "path_matrix": {
            "case_count": len(path_rows),
            "predicted_path_counts": dict(Counter(row["predicted_path"] for row in path_rows)),
            "observed_path_counts": dict(Counter(row["observed_path"] for row in path_rows)),
            "all_correct": all(row["status"] == "PASS" for row in path_rows),
            "all_predictions_match_observations": all(
                row["prediction_matches_observation"] for row in path_rows
            ),
            "real_replacement_cases": sum(bool(row["microkernel_replaced"]) for row in path_rows),
            "rows": path_rows,
        },
        "baco": tuning_summary,
        "claim_boundary": CONFIG["claim_boundary"],
    }
    (PROCESSED / "integrated_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    best = tuning_summary["best"]
    lines = [
        "# Chapter 4 to Chapter 5 Integrated Pipeline", "",
        "## Path Matrix", "",
        "| Case | Candidate | Predicted | Observed | Correct | BLIS replacement | Fringe calls | Median ms |",
        "|---|---|---|---|---|---|---:|---:|",
    ]
    for row in path_rows:
        lines.append(
            f"| {row['case_id']} | `{row['candidate_id']}` | {row['predicted_path']} | "
            f"{row['observed_path']} | {row['status']} | {str(row['microkernel_replaced']).lower()} | "
            f"{row['fringe_calls']} | {row['median_ms']:.6f} |"
        )
    lines.extend([
        "", "The direct and adapt cases contain the BLIS wrapper call and linked "
        "`bli_sgemm_haswell_asm_6x16` symbol. The adapt case also records the "
        "expected runtime fringe-call count. The feature-mismatch case remains "
        "on the generated MLIR fallback path.",
        "", "## BaCO Smoke", "",
        f"- Source space: `{tuning_summary['source_space']}` ({tuning_summary['full_space_size']} candidates).",
        f"- Declared pool/budget/evaluated: {tuning_summary['pool_size']}/{tuning_summary['budget']}/{tuning_summary['evaluated']}.",
        f"- Pool roles: {tuning_summary['pool_role_counts']}.",
        f"- Observed paths: {tuning_summary['observed_path_counts']}.",
        f"- Real microkernel evaluations: {tuning_summary['real_microkernel_evaluations']}.",
        f"- Best observed candidate: `{best['candidate_id']}` at {best['runtime_ms']:.6f} ms.",
        "", "## Claim Boundary", "", CONFIG["claim_boundary"], "",
    ])
    (REPORTS / "integrated_results.md").write_text("\n".join(lines), encoding="utf-8")
    artifact_index = """# Chapter 4 to Chapter 5 Integrated Artifact Index

- Configuration: `data/integration_config.json`
- Reproduction entry: `scripts/run_integrated_pipeline.py`
- Chapter 4 source space: `../chapter4_space/processed/spaces/`
- Chapter 5 evaluator implementation: `../chapter5_blis_adapter/`
- Path matrix: `raw/path_matrix.csv`
- BaCO callback log: `raw/baco_callback_log.jsonl`
- BaCO trace: `processed/baco_tuning_trace.csv`
- Machine-readable summary: `processed/integrated_summary.json`
- Human-readable result: `reports/integrated_results.md`
- Tests: `tests/test_integrated_pipeline.py`

This package does not rewrite the frozen Chapter 4 evidence. It imports the
Chapter 4 candidate generator and Compatibility Checker, then evaluates their
decisions through the Chapter 5 packing pass and real BLIS microkernel adapter.
"""
    (PROJECT / "chapter4_5_artifact_index.md").write_text(artifact_index, encoding="utf-8")


def refresh_registry() -> None:
    root = Path(os.environ.get("PERSONAL_OS_ROOT", "/root/personal-os/PersonalOS"))
    script = root / "scripts" / "experiment_registry.py"
    if not script.exists():
        print(f"PersonalOS registry not installed; skipped refresh: {script}")
        return
    chapter5.run(
        [sys.executable, str(script), "refresh", "--workspace-root", str(REPO),
         "--completed-id", CONFIG["experiment_id"]],
        REPORTS / "registry_refresh.log", root,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-registry", action="store_true")
    args = parser.parse_args()
    for directory in (BUILD, RAW, PROCESSED, REPORTS, TUNER):
        directory.mkdir(parents=True, exist_ok=True)
    if not args.skip_build:
        chapter5.ensure_tools()
    chapter5.ensure_blis()
    inputs, state = load_space_state()
    paths = path_matrix(state, args.force)
    tuning_rows, tuning_summary = run_baco(state, args.force)
    write_outputs(inputs, paths, tuning_rows, tuning_summary)
    chapter5.run(
        [sys.executable, str(EXPERIMENTS / "scripts" / "build_paper_evidence_catalog.py")],
        REPORTS / "paper_catalog.log", REPO,
    )
    chapter5.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(PROJECT / "tests"), "-v"],
        REPORTS / "tests.log", REPO,
    )
    if not args.skip_registry:
        refresh_registry()
    print(json.dumps({
        "status": "PASS",
        "summary": str(PROCESSED / "integrated_summary.json"),
        "paper_catalog": str(EXPERIMENTS / "PAPER_EVIDENCE_CATALOG.md"),
    }, indent=2))


if __name__ == "__main__":
    main()
