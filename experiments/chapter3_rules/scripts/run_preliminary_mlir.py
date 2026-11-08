#!/usr/bin/env python3
"""Run the chapter 3 real MLIR Transform/AOT preliminary experiment."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import random
import re
import resource
import subprocess
import time
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
EXPERIMENTS_DIR = PROJECT_DIR.parent


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "llvm" / "build" / "bin" / "mlir-opt").exists():
            return candidate
    raise RuntimeError(f"could not find the workspace MLIR toolchain above {start}")


REPO_ROOT = find_repo_root(PROJECT_DIR)
MLIR_OPT = REPO_ROOT / "llvm" / "build" / "bin" / "mlir-opt"
MLIR_TRANSLATE = REPO_ROOT / "llvm" / "build" / "bin" / "mlir-translate"
CXX = REPO_ROOT / "llvm" / "build" / "bin" / "clang++"
DRIVER = EXPERIMENTS_DIR / "scripts" / "mlir_aot_matmul_bench.cpp"

RAW_FIELDS = [
    "case_id",
    "shape_id",
    "role",
    "m",
    "k",
    "n",
    "dtype",
    "candidate_kind",
    "sample_index",
    "seed",
    "tile_m",
    "tile_n",
    "tile_k",
    "vectorize",
    "raw_space_size",
    "legal_space_size",
    "policy_legal",
    "policy_reason",
    "compile_status",
    "correctness_status",
    "microkernel_replaced",
    "execution_path",
    "status",
    "failure_stage",
    "failure_reason",
    "median_ms",
    "min_ms",
    "max_ms",
    "mean_ms",
    "stddev_ms",
    "p90_ms",
    "gflops",
    "normalized_to_shape_best",
    "speedup_vs_default",
    "max_abs_diff",
    "max_rel_diff",
    "checksum",
    "output_aliases_c",
    "transform_ms",
    "lowering_ms",
    "native_compile_ms",
    "llvm_ir_bytes",
    "executable_bytes",
    "warmups",
    "repeats",
    "inner_iters",
    "stack_limit_kb",
    "cpu_affinity",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT_DIR)
    parser.add_argument("--shape-filter", default=".*")
    parser.add_argument("--samples", type=int)
    parser.add_argument("--rejects", type=int)
    parser.add_argument("--force", action="store_true", help="ignore per-case cached measurements")
    return parser.parse_args()


def payload(symbol: str, m: int, k: int, n: int) -> str:
    return f"""func.func @{symbol}(
    %A: tensor<{m}x{k}xf32>,
    %B: tensor<{k}x{n}xf32>,
    %C: tensor<{m}x{n}xf32>) -> tensor<{m}x{n}xf32>
    attributes {{llvm.emit_c_interface}} {{
  %0 = linalg.matmul
    ins(%A, %B : tensor<{m}x{k}xf32>, tensor<{k}x{n}xf32>)
    outs(%C : tensor<{m}x{n}xf32>) -> tensor<{m}x{n}xf32>
  return %0 : tensor<{m}x{n}xf32>
}}
"""


def transform_schedule(tile_m: int, tile_n: int, tile_k: int, vectorize: bool) -> str:
    vector_step = """
    %func = transform.get_parent_op %tiled {isolated_from_above}
      : (!transform.any_op) -> !transform.any_op
    transform.structured.vectorize_children_and_apply_patterns %func
      : (!transform.any_op) -> !transform.any_op
""" if vectorize else ""
    return f"""
module attributes {{transform.with_named_sequence}} {{
  transform.named_sequence @__transform_main(
      %module_op: !transform.any_op {{transform.consumed}}) {{
    %matmul = transform.structured.match ops{{["linalg.matmul"]}} in %module_op
      : (!transform.any_op) -> !transform.any_op
    %tiled, %loops:3 = transform.structured.tile_using_for %matmul
      tile_sizes [{tile_m}, {tile_n}, {tile_k}]
      : (!transform.any_op) -> (!transform.any_op, !transform.any_op,
          !transform.any_op, !transform.any_op)
{vector_step}    %bufferized = transform.bufferization.one_shot_bufferize
      layout{{IdentityLayoutMap}} %module_op
      {{bufferize_function_boundaries = true}}
      : (!transform.any_op) -> !transform.any_op
    transform.yield
  }}
}}
"""


def generic_candidates(rules: dict) -> list[dict[str, Any]]:
    baseline = rules["generic_baseline"]
    return [
        {"tile_m": tm, "tile_n": tn, "tile_k": tk, "vectorize": vectorize}
        for tm, tn, tk, vectorize in product(
            baseline["tile_m"],
            baseline["tile_n"],
            baseline["tile_k"],
            baseline["vectorize"],
        )
    ]


def policy_check(candidate: dict, shape: dict, vector_lanes: int = 8) -> tuple[bool, str]:
    if candidate["tile_m"] > shape["m"] or candidate["tile_n"] > shape["n"] or candidate["tile_k"] > shape["k"]:
        return False, "tile_exceeds_static_extent"
    if candidate["vectorize"] and candidate["tile_n"] % vector_lanes:
        return False, "vector_tile_not_lane_multiple"
    return True, "policy_legal"


def select_cases(shape: dict, all_candidates: list[dict], config: dict, rules: dict) -> list[dict]:
    legal = []
    rejected = []
    for candidate in all_candidates:
        accepted, reason = policy_check(candidate, shape)
        item = {**candidate, "policy_legal": accepted, "policy_reason": reason}
        (legal if accepted else rejected).append(item)
    sample_count = int(config["samples_per_shape"])
    reject_count = int(config["policy_rejects_per_shape"])
    rng = random.Random(f"{config['seed']}:{shape['id']}")
    selected_legal = []
    anchor = config.get("anchor_candidate", {})
    if shape["id"] == anchor.get("shape_id"):
        anchor_item = {
            "tile_m": anchor["tile_m"],
            "tile_n": anchor["tile_n"],
            "tile_k": anchor["tile_k"],
            "vectorize": bool(anchor["vectorize"]),
            "policy_legal": True,
            "policy_reason": "policy_legal_anchor",
            "anchor": True,
        }
        selected_legal.append(anchor_item)
        legal = [item for item in legal if any(item[key] != anchor_item[key] for key in ("tile_m", "tile_n", "tile_k", "vectorize"))]
    selected_legal.extend(rng.sample(legal, min(sample_count - len(selected_legal), len(legal))))
    selected_rejected = rng.sample(rejected, min(reject_count, len(rejected)))
    cases = [
        {
            "candidate_kind": "baseline",
            "tile_m": 0,
            "tile_n": 0,
            "tile_k": 0,
            "vectorize": False,
            "policy_legal": True,
            "policy_reason": "untiled_reference_baseline",
            "sample_index": 0,
            "case_id": f"{shape['id']}_baseline",
        }
    ]
    for index, item in enumerate(selected_legal, 1):
        suffix = (
            "anchor"
            if item.get("anchor")
            else f"sample{index:02d}_{item['tile_m']}x{item['tile_n']}x{item['tile_k']}_v{int(item['vectorize'])}"
        )
        cases.append({**item, "candidate_kind": "sample", "sample_index": index, "case_id": f"{shape['id']}_{suffix}"})
    for index, item in enumerate(selected_rejected, 1):
        suffix = f"reject{index:02d}_{item['tile_m']}x{item['tile_n']}x{item['tile_k']}_v{int(item['vectorize'])}"
        cases.append({**item, "candidate_kind": "policy_reject", "sample_index": sample_count + index, "case_id": f"{shape['id']}_{suffix}"})
    for item in cases:
        item["raw_space_size"] = len(all_candidates)
        item["legal_space_size"] = sum(policy_check(candidate, shape)[0] for candidate in all_candidates)
    return cases


def run_command(command: list[str], log: Path) -> tuple[int, float, str]:
    start = time.perf_counter()
    completed = subprocess.run(command, text=True, capture_output=True)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    text = "$ " + " ".join(command) + "\n\nSTDOUT\n" + completed.stdout + "\nSTDERR\n" + completed.stderr
    log.write_text(text, encoding="utf-8")
    return completed.returncode, elapsed_ms, completed.stderr.strip()


def empty_measurement() -> dict[str, Any]:
    return {
        field: ""
        for field in (
            "median_ms", "min_ms", "max_ms", "mean_ms", "stddev_ms", "p90_ms",
            "gflops", "max_abs_diff", "max_rel_diff", "checksum", "output_aliases_c",
            "transform_ms", "lowering_ms", "native_compile_ms", "llvm_ir_bytes", "executable_bytes",
        )
    }


def base_row(shape: dict, case: dict, config: dict) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "shape_id": shape["id"],
        "role": shape["role"],
        "m": shape["m"],
        "k": shape["k"],
        "n": shape["n"],
        "dtype": config["dtype"],
        "candidate_kind": case["candidate_kind"],
        "sample_index": case["sample_index"],
        "seed": config["seed"],
        "tile_m": case["tile_m"],
        "tile_n": case["tile_n"],
        "tile_k": case["tile_k"],
        "vectorize": str(case["vectorize"]).lower(),
        "raw_space_size": case["raw_space_size"],
        "legal_space_size": case["legal_space_size"],
        "policy_legal": str(case["policy_legal"]).lower(),
        "policy_reason": case["policy_reason"],
        "warmups": config["warmups"],
        "repeats": config["repeats"],
        "inner_iters": config["inner_iters"],
        "stack_limit_kb": config["stack_limit_kb"],
        "cpu_affinity": config["cpu_affinity"],
        "normalized_to_shape_best": "",
        "speedup_vs_default": "",
        **empty_measurement(),
    }


def cached_case(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def measure_case(project: Path, shape: dict, case: dict, config: dict, force: bool) -> dict:
    row = base_row(shape, case, config)
    if not case["policy_legal"]:
        row.update(
            {
                "compile_status": "not_attempted",
                "correctness_status": "not_attempted",
                "microkernel_replaced": "false",
                "execution_path": "reject",
                "status": "STATIC_REJECT",
                "failure_stage": "policy_check",
                "failure_reason": case["policy_reason"],
            }
        )
        return row

    case_dir = project / "build" / "preliminary_mlir" / case["case_id"]
    case_dir.mkdir(parents=True, exist_ok=True)
    result_cache = case_dir / "measurement.json"
    if not force:
        cached = cached_case(result_cache)
        if cached:
            return {**row, **cached}

    symbol = "chapter3_" + re.sub(r"[^A-Za-z0-9_]", "_", case["case_id"])
    input_mlir = case_dir / "input.mlir"
    transformed_mlir = case_dir / "transformed.mlir"
    llvm_mlir = case_dir / "llvm.mlir"
    llvm_ir = case_dir / "kernel.ll"
    executable = case_dir / "benchmark"
    source = payload(symbol, shape["m"], shape["k"], shape["n"])
    if case["candidate_kind"] != "baseline":
        source += transform_schedule(case["tile_m"], case["tile_n"], case["tile_k"], case["vectorize"])
    input_mlir.write_text(source, encoding="utf-8")

    if case["candidate_kind"] == "baseline":
        transform_cmd = [
            str(MLIR_OPT), str(input_mlir),
            "--one-shot-bufferize=bufferize-function-boundaries",
            "--convert-linalg-to-loops", "--canonicalize", "--cse", "-o", str(transformed_mlir),
        ]
    else:
        transform_cmd = [
            str(MLIR_OPT), str(input_mlir), "--transform-interpreter",
            "-test-transform-dialect-erase-schedule", "--canonicalize", "--cse", "-o", str(transformed_mlir),
        ]
    rc, transform_ms, error = run_command(transform_cmd, case_dir / "01_transform.log")
    if rc:
        measured = {
            "compile_status": "fail", "correctness_status": "not_attempted",
            "microkernel_replaced": "false", "execution_path": "reject", "status": "COMPILE_FAIL",
            "failure_stage": "transform", "failure_reason": error[-800:], "transform_ms": f"{transform_ms:.3f}",
        }
        result_cache.write_text(json.dumps(measured, indent=2) + "\n", encoding="utf-8")
        return {**row, **measured}

    lower_cmd = [
        str(MLIR_OPT), str(transformed_mlir), "--convert-linalg-to-loops",
        "--test-lower-to-llvm", "-o", str(llvm_mlir),
    ]
    rc, lower_dialect_ms, error = run_command(lower_cmd, case_dir / "02_lower_dialect.log")
    if not rc:
        rc, translate_ms, error = run_command(
            [str(MLIR_TRANSLATE), "--mlir-to-llvmir", str(llvm_mlir), "-o", str(llvm_ir)],
            case_dir / "03_translate.log",
        )
    else:
        translate_ms = 0.0
    lowering_ms = lower_dialect_ms + translate_ms
    if rc:
        measured = {
            "compile_status": "fail", "correctness_status": "not_attempted",
            "microkernel_replaced": "false", "execution_path": "reject", "status": "COMPILE_FAIL",
            "failure_stage": "lowering", "failure_reason": error[-800:],
            "transform_ms": f"{transform_ms:.3f}", "lowering_ms": f"{lowering_ms:.3f}",
        }
        result_cache.write_text(json.dumps(measured, indent=2) + "\n", encoding="utf-8")
        return {**row, **measured}

    ir_text = llvm_ir.read_text(encoding="utf-8", errors="replace")
    replaced = bool(re.search(r"\b(?:bli_[sd]gemm|cblas_[sd]gemm)\b", ir_text))
    compile_cmd = [
        str(CXX), "-O3", "-march=native", "-std=c++17",
        f"-DKERNEL_SYMBOL={symbol}", f"-DMATMUL_M={shape['m']}",
        f"-DMATMUL_K={shape['k']}", f"-DMATMUL_N={shape['n']}",
        str(DRIVER), str(llvm_ir), "-o", str(executable),
    ]
    rc, native_compile_ms, error = run_command(compile_cmd, case_dir / "04_native_compile.log")
    if rc:
        measured = {
            "compile_status": "fail", "correctness_status": "not_attempted",
            "microkernel_replaced": str(replaced).lower(), "execution_path": "reject", "status": "COMPILE_FAIL",
            "failure_stage": "native_compile", "failure_reason": error[-800:],
            "transform_ms": f"{transform_ms:.3f}", "lowering_ms": f"{lowering_ms:.3f}",
            "native_compile_ms": f"{native_compile_ms:.3f}", "llvm_ir_bytes": llvm_ir.stat().st_size,
        }
        result_cache.write_text(json.dumps(measured, indent=2) + "\n", encoding="utf-8")
        return {**row, **measured}

    env = os.environ.copy()
    env.update({"OMP_NUM_THREADS": "1", "BLIS_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})

    def set_stack_limit() -> None:
        limit = int(config["stack_limit_kb"]) * 1024
        resource.setrlimit(resource.RLIMIT_STACK, (limit, limit))

    benchmark = subprocess.run(
        [
            "taskset", "-c", str(config["cpu_affinity"]), str(executable),
            str(config["warmups"]), str(config["repeats"]), str(config["inner_iters"]),
        ],
        text=True,
        capture_output=True,
        env=env,
        preexec_fn=set_stack_limit,
    )
    (case_dir / "05_benchmark.log").write_text(
        "STDOUT\n" + benchmark.stdout + "\nSTDERR\n" + benchmark.stderr,
        encoding="utf-8",
    )
    parsed = list(csv.DictReader(io.StringIO(benchmark.stdout)))
    benchmark_values = parsed[-1] if parsed else {}
    correctness = benchmark_values.get("status", "RUNTIME_ERROR")
    passed = benchmark.returncode == 0 and correctness == "PASS"
    measured = {
        "compile_status": "pass",
        "correctness_status": "pass" if passed else "fail",
        "microkernel_replaced": str(replaced).lower(),
        "execution_path": "direct" if replaced else "fallback",
        "status": "REPLACED_PASS" if passed and replaced else ("FALLBACK_PASS" if passed else "CORRECTNESS_FAIL"),
        "failure_stage": "" if passed else "runtime_or_correctness",
        "failure_reason": "" if passed else (benchmark.stderr.strip()[-800:] or correctness),
        "transform_ms": f"{transform_ms:.3f}",
        "lowering_ms": f"{lowering_ms:.3f}",
        "native_compile_ms": f"{native_compile_ms:.3f}",
        "llvm_ir_bytes": llvm_ir.stat().st_size,
        "executable_bytes": executable.stat().st_size,
        **{field: benchmark_values.get(field, "") for field in (
            "median_ms", "min_ms", "max_ms", "mean_ms", "stddev_ms", "p90_ms", "gflops",
            "max_abs_diff", "max_rel_diff", "checksum", "output_aliases_c",
        )},
    }
    result_cache.write_text(json.dumps(measured, indent=2) + "\n", encoding="utf-8")
    return {**row, **measured}


def normalize(rows: list[dict]) -> None:
    by_shape = defaultdict(list)
    for row in rows:
        if row["status"] in {"FALLBACK_PASS", "REPLACED_PASS"} and row["gflops"] != "":
            by_shape[row["shape_id"]].append(row)
    for shape_rows in by_shape.values():
        best = max(float(row["gflops"]) for row in shape_rows if row["candidate_kind"] == "sample")
        baseline = next(float(row["gflops"]) for row in shape_rows if row["candidate_kind"] == "baseline")
        for row in shape_rows:
            row["normalized_to_shape_best"] = f"{float(row['gflops']) / best:.8f}"
            row["speedup_vs_default"] = f"{float(row['gflops']) / baseline:.8f}"


def write_results(project: Path, rows: list[dict], config: dict) -> None:
    raw_dir = project / "raw"
    processed_dir = project / "processed"
    reports_dir = project / "reports"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    raw_csv = raw_dir / "preliminary_aot.csv"
    with raw_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in RAW_FIELDS} for row in rows)

    space_rows = []
    seen = set()
    for row in rows:
        if row["shape_id"] in seen:
            continue
        seen.add(row["shape_id"])
        space_rows.append(
            {
                "shape_id": row["shape_id"], "m": row["m"], "k": row["k"], "n": row["n"],
                "raw_space_size": row["raw_space_size"], "legal_space_size": row["legal_space_size"],
                "reduction_ratio": f"{1 - int(row['legal_space_size']) / int(row['raw_space_size']):.8f}",
            }
        )
    with (processed_dir / "preliminary_space_sizes.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(space_rows[0]))
        writer.writeheader()
        writer.writerows(space_rows)

    convergence = []
    for shape_id in sorted(seen):
        samples = sorted(
            [row for row in rows if row["shape_id"] == shape_id and row["candidate_kind"] == "sample" and row["status"] in {"FALLBACK_PASS", "REPLACED_PASS"}],
            key=lambda item: int(item["sample_index"]),
        )
        best = -math.inf
        for iteration, row in enumerate(samples, 1):
            best = max(best, float(row["normalized_to_shape_best"]))
            convergence.append(
                {
                    "shape_id": shape_id, "iteration": iteration, "case_id": row["case_id"],
                    "normalized_score": row["normalized_to_shape_best"], "best_so_far": f"{best:.8f}",
                }
            )
    with (processed_dir / "preliminary_best_so_far.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(convergence[0]))
        writer.writeheader()
        writer.writerows(convergence)

    status_counts = Counter(row["status"] for row in rows if row["candidate_kind"] != "baseline")
    sampled = sum(status_counts.values())
    summary = {
        "shape_count": len(seen),
        "sampled_candidates": sampled,
        "status_counts": dict(status_counts),
        "status_ratios": {key: value / sampled for key, value in status_counts.items()},
        "compile_pass_ratio_among_attempted": sum(row["compile_status"] == "pass" for row in rows if row["candidate_kind"] == "sample") / sum(row["candidate_kind"] == "sample" for row in rows),
        "correctness_pass_ratio_among_compiled": sum(row["correctness_status"] == "pass" for row in rows if row["candidate_kind"] == "sample") / max(1, sum(row["compile_status"] == "pass" for row in rows if row["candidate_kind"] == "sample")),
        "microkernel_replacement_ratio_among_passed": sum(row["microkernel_replaced"] == "true" for row in rows if row["candidate_kind"] == "sample" and row["correctness_status"] == "pass") / max(1, sum(row["correctness_status"] == "pass" for row in rows if row["candidate_kind"] == "sample")),
        "fallback_ratio_among_passed": sum(row["execution_path"] == "fallback" for row in rows if row["candidate_kind"] == "sample" and row["correctness_status"] == "pass") / max(1, sum(row["correctness_status"] == "pass" for row in rows if row["candidate_kind"] == "sample")),
        "seed": config["seed"],
    }
    (processed_dir / "preliminary_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Chapter 3 Preliminary MLIR Experiment",
        "",
        "This is a small-scale motivation experiment, not the Chapter 6 formal evaluation.",
        "",
        f"- Shapes: **{summary['shape_count']}**",
        f"- Non-baseline sampled rows: **{sampled}**",
        f"- Compile pass ratio among attempted samples: **{summary['compile_pass_ratio_among_attempted']:.1%}**",
        f"- Correctness pass ratio among compiled samples: **{summary['correctness_pass_ratio_among_compiled']:.1%}**",
        f"- Observed microkernel replacement ratio: **{summary['microkernel_replacement_ratio_among_passed']:.1%}**",
        f"- Observed fallback ratio: **{summary['fallback_ratio_among_passed']:.1%}**",
        "",
        "The current Transform template implements tiling and optional vectorization but no BLIS",
        "packing/replacement adapter. Therefore successful candidates are expected to be observed",
        "as fallback. This is a measured system boundary, not a simulated replacement failure.",
        "",
        "Raw rows: `raw/preliminary_aot.csv`.",
        "",
    ]
    (reports_dir / "preliminary_experiment.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main() -> None:
    args = parse_args()
    project = args.project.resolve()
    config = yaml.safe_load((project / "data" / "preliminary_shapes.yaml").read_text())
    if args.samples is not None:
        config["samples_per_shape"] = args.samples
    if args.rejects is not None:
        config["policy_rejects_per_shape"] = args.rejects
    rules = yaml.safe_load((project / "data" / "expert_rules.yaml").read_text())
    candidates = generic_candidates(rules)
    configured_raw = int(rules["generic_baseline"]["raw_space_size"])
    if len(candidates) != configured_raw:
        raise ValueError(f"raw space mismatch: generated {len(candidates)}, configured {configured_raw}")
    for tool in (MLIR_OPT, MLIR_TRANSLATE, CXX, DRIVER):
        if not tool.exists():
            raise FileNotFoundError(tool)
    pattern = re.compile(args.shape_filter)
    shapes = [shape for shape in config["shapes"] if pattern.search(shape["id"])]
    if not shapes:
        raise SystemExit("shape filter selected no workloads")
    rows = []
    for shape in shapes:
        cases = select_cases(shape, candidates, config, rules)
        for case in cases:
            print(f"[{shape['id']}] {case['case_id']}", flush=True)
            rows.append(measure_case(project, shape, case, config, args.force))
    normalize(rows)
    write_results(project, rows, config)


if __name__ == "__main__":
    main()
