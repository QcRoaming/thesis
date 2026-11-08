#!/usr/bin/env python3
"""Build and measure Chapter 6 baselines and the frozen candidate corpus."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from chapter6lib import (  # noqa: E402
    CHAPTER4,
    CHAPTER5,
    EXPERIMENTS,
    INTEGRATED,
    METHOD_TO_SPACE,
    PROJECT,
    REPO,
    build_space_state,
    candidate_from_row,
    load_config,
    pool_diagnostics,
    select_pool,
    shell_ratio_pools,
    space_summary,
)

sys.path.insert(0, str(INTEGRATED / "scripts"))
sys.path.insert(0, str(CHAPTER5 / "scripts"))
import run_integrated_pipeline as integrated  # noqa: E402
import run_chapter5 as chapter5  # noqa: E402


BUILD = PROJECT / "build"
RAW = PROJECT / "raw"
PROCESSED = PROJECT / "processed"
REPORTS = PROJECT / "reports"
TUNER = PROJECT / "tuner"
DRIVER = CHAPTER5 / "runtime" / "dynamic_matmul_bench.cpp"
BLIS_DRIVER = PROJECT / "runtime" / "blis_frontend_bench.cpp"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value
                for key, value in row.items()
            })


def logged_run(command: list[str], log: Path, cwd: Path = REPO) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    elapsed = (time.perf_counter() - started) * 1000.0
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        "$ " + " ".join(command) + f"\nELAPSED_MS={elapsed:.6f}\n\nSTDOUT\n"
        + completed.stdout + "\nSTDERR\n" + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stderr[-2000:]}"
        )
    return completed, elapsed


def scalar_schedule() -> str:
    return """
module attributes {transform.with_named_sequence} {
  transform.named_sequence @__transform_main(
      %root: !transform.any_op {transform.consumed}) {
    %bufferized = transform.bufferization.one_shot_bufferize
      layout{IdentityLayoutMap} %root
      {bufferize_function_boundaries = true}
      : (!transform.any_op) -> !transform.any_op
    transform.yield
  }
}
"""


def vectorized_dynamic_payload(symbol: str) -> str:
    """Dynamic tiled/vector MLIR with scalar N-tail cleanup."""
    return f"""
func.func @{symbol}(
    %A: memref<?x?xf32>, %B: memref<?x?xf32>, %C: memref<?x?xf32>)
    -> memref<?x?xf32> attributes {{llvm.emit_c_interface}} {{
  %c0 = arith.constant 0 : index
  %c1 = arith.constant 1 : index
  %c8 = arith.constant 8 : index
  %c24 = arith.constant 24 : index
  %c32 = arith.constant 32 : index
  %c64 = arith.constant 64 : index
  %m = memref.dim %A, %c0 : memref<?x?xf32>
  %k = memref.dim %A, %c1 : memref<?x?xf32>
  %n = memref.dim %B, %c1 : memref<?x?xf32>
  %rem = arith.remui %n, %c8 : index
  %nvec = arith.subi %n, %rem : index
  scf.for %mb = %c0 to %m step %c24 {{
    %mnext = arith.addi %mb, %c24 : index
    %mend = arith.minsi %mnext, %m : index
    scf.for %i = %mb to %mend step %c1 {{
      scf.for %nb = %c0 to %nvec step %c32 {{
        %nnext = arith.addi %nb, %c32 : index
        %nend = arith.minsi %nnext, %nvec : index
        scf.for %j = %nb to %nend step %c8 {{
          scf.for %kb = %c0 to %k step %c64 {{
            %knext = arith.addi %kb, %c64 : index
            %kend = arith.minsi %knext, %k : index
            %initial = vector.load %C[%i, %j] : memref<?x?xf32>, vector<8xf32>
            %updated = scf.for %p = %kb to %kend step %c1
                iter_args(%acc = %initial) -> vector<8xf32> {{
              %avalue = memref.load %A[%i, %p] : memref<?x?xf32>
              %avec = vector.broadcast %avalue : f32 to vector<8xf32>
              %bvec = vector.load %B[%p, %j] : memref<?x?xf32>, vector<8xf32>
              %next = vector.fma %avec, %bvec, %acc : vector<8xf32>
              scf.yield %next : vector<8xf32>
            }}
            vector.store %updated, %C[%i, %j] : memref<?x?xf32>, vector<8xf32>
          }}
        }}
      }}
      scf.for %j = %nvec to %n step %c1 {{
        %initial = memref.load %C[%i, %j] : memref<?x?xf32>
        %updated = scf.for %p = %c0 to %k step %c1
            iter_args(%acc = %initial) -> f32 {{
          %avalue = memref.load %A[%i, %p] : memref<?x?xf32>
          %bvalue = memref.load %B[%p, %j] : memref<?x?xf32>
          %product = arith.mulf %avalue, %bvalue : f32
          %next = arith.addf %acc, %product : f32
          scf.yield %next : f32
        }}
        memref.store %updated, %C[%i, %j] : memref<?x?xf32>
      }}
    }}
  }}
  return %C : memref<?x?xf32>
}}
"""


def compile_dynamic(
    key: str, row: dict[str, Any] | None, config: dict[str, Any], force: bool,
) -> dict[str, Any]:
    case = BUILD / "binaries" / key
    manifest_path = case / "manifest.json"
    executable = case / "benchmark"
    if manifest_path.exists() and executable.exists() and not force:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    case.mkdir(parents=True, exist_ok=True)
    safe_key = re.sub(r"[^A-Za-z0-9_]", "_", key)
    symbol = "chapter6_" + safe_key
    input_mlir = case / "input.mlir"
    transformed = case / "transformed.mlir"
    llvm_mlir = case / "llvm.mlir"
    llvm_ir = case / "kernel.ll"
    use_blis = False
    if key == "B0_scalar":
        schedule = scalar_schedule()
    elif key == "B0_optimized":
        schedule = ""
    else:
        if row is None:
            raise ValueError(f"candidate row required for {key}")
        candidate = candidate_from_row(row)
        use_blis = row["predicted_path"] in {"direct", "adapt"}
        schedule = (
            integrated.blis_schedule(candidate, 6, 16)
            if use_blis else integrated.fallback_schedule(candidate)
        )
    input_mlir.write_text(
        vectorized_dynamic_payload(symbol)
        if key == "B0_optimized"
        else integrated.dynamic_payload(symbol, use_blis) + schedule,
        encoding="utf-8",
    )

    timings: dict[str, float] = {}
    transform_command = (
        [str(chapter5.MLIR_OPT), str(input_mlir), "--canonicalize", "--cse", "-o", str(transformed)]
        if key == "B0_optimized" else
        [str(chapter5.BUDDY_OPT), str(input_mlir), "--transform-interpreter",
         "--buddy-finalize-transform-payload", "--canonicalize", "--cse", "-o", str(transformed)]
        if use_blis else
        [str(chapter5.MLIR_OPT), str(input_mlir), "--transform-interpreter",
         "-test-transform-dialect-erase-schedule", "--canonicalize", "--cse", "-o", str(transformed)]
    )
    _, timings["transform_ms"] = logged_run(transform_command, case / "01_transform.log")
    _, timings["lower_ms"] = logged_run(
        [str(chapter5.MLIR_OPT), str(transformed), "--convert-linalg-to-loops",
         "--test-lower-to-llvm", "-o", str(llvm_mlir)],
        case / "02_lower.log",
    )
    _, timings["translate_ms"] = logged_run(
        [str(chapter5.MLIR_TRANSLATE), "--mlir-to-llvmir", str(llvm_mlir), "-o", str(llvm_ir)],
        case / "03_translate.log",
    )
    command = [
        str(chapter5.CXX), "-O3", "-march=native", "-std=c++17",
        f"-DKERNEL_SYMBOL={symbol}", str(DRIVER), str(llvm_ir),
    ]
    if use_blis:
        command.extend([
            "-DBLIS_ADAPTER_ENABLED=1", "-I" + str(chapter5.BLIS_INCLUDE),
            str(chapter5.ADAPTER), str(chapter5.BLIS_LIBRARY), "-lpthread", "-lm",
        ])
    command.extend(["-o", str(executable)])
    _, timings["native_compile_ms"] = logged_run(command, case / "04_native_compile.log")
    symbols, timings["symbol_check_ms"] = logged_run(
        ["nm", "-C", str(executable)], case / "05_symbols.log"
    )
    packed_vector_fma = False
    if key == "B0_optimized":
        disassembly, timings["disassembly_check_ms"] = logged_run(
            ["objdump", "-d", str(executable)], case / "06_disassembly.log"
        )
        packed_vector_fma = bool(re.search(r"vfmadd\w*ps\b", disassembly.stdout))
    manifest = {
        "key": key,
        "candidate_id": row.get("candidate_id") if row else None,
        "symbol": symbol,
        "use_blis": use_blis,
        "executable": str(executable),
        "executable_sha256": sha256(executable),
        "llvm_ir_bytes": llvm_ir.stat().st_size,
        "executable_bytes": executable.stat().st_size,
        "blis_kernel_symbol": " T bli_sgemm_haswell_asm_6x16" in symbols.stdout,
        "packed_vector_fma_present": packed_vector_fma,
        "pipeline_ms": round(sum(timings.values()), 6),
        **{name: round(value, 6) for name, value in timings.items()},
    }
    write_json(manifest_path, manifest)
    return manifest


def compile_blis_frontend(force: bool) -> dict[str, Any]:
    case = BUILD / "binaries" / "B5_blis"
    manifest_path = case / "manifest.json"
    executable = case / "benchmark"
    if manifest_path.exists() and executable.exists() and not force:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    case.mkdir(parents=True, exist_ok=True)
    _, elapsed = logged_run(
        [str(chapter5.CXX), "-O3", "-march=native", "-std=c++17",
         "-I" + str(chapter5.BLIS_INCLUDE), str(BLIS_DRIVER),
         str(chapter5.BLIS_LIBRARY), "-lpthread", "-lm", "-o", str(executable)],
        case / "compile.log",
    )
    symbols, symbol_ms = logged_run(["nm", "-C", str(executable)], case / "symbols.log")
    manifest = {
        "key": "B5_blis",
        "candidate_id": None,
        "executable": str(executable),
        "executable_sha256": sha256(executable),
        "executable_bytes": executable.stat().st_size,
        "blis_frontend_symbol": " T bli_sgemm" in symbols.stdout,
        "blis_kernel_symbol": " T bli_sgemm_haswell_asm_6x16" in symbols.stdout,
        "pipeline_ms": round(elapsed + symbol_ms, 6),
        "native_compile_ms": round(elapsed, 6),
        "symbol_check_ms": round(symbol_ms, 6),
    }
    write_json(manifest_path, manifest)
    return manifest


def parse_benchmark(stdout: str) -> dict[str, Any]:
    rows = list(csv.DictReader(io.StringIO(stdout)))
    if not rows or rows[-1].get("status") != "PASS":
        raise RuntimeError("benchmark did not produce a passing CSV row")
    result: dict[str, Any] = {}
    for key, value in rows[-1].items():
        if key == "status":
            result[key] = value
        else:
            try:
                result[key] = float(value)
            except (TypeError, ValueError):
                result[key] = value
    return result


def measure_executable(
    manifest: dict[str, Any], workload: dict[str, Any], measurement: dict[str, Any],
    variant: str, trial: int, candidate_row: dict[str, Any] | None,
) -> dict[str, Any]:
    log = BUILD / "measurements" / workload["id"] / variant / f"trial_{trial:02d}.log"
    completed, wall_ms = logged_run(
        ["taskset", "-c", str(measurement["cpu_affinity"]), manifest["executable"],
         str(workload["m"]), str(workload["k"]), str(workload["n"]),
         str(measurement["warmups"]), str(measurement["repeats"]),
         str(measurement["inner_iters"])],
        log,
    )
    values = parse_benchmark(completed.stdout)
    observed_path = "baseline"
    predicted_path = "baseline"
    expected_fringe = 0
    if candidate_row is not None:
        predicted_path = str(candidate_row["predicted_path"])
        if manifest["use_blis"]:
            m_panels = math.ceil(workload["m"] / 6)
            n_panels = math.ceil(workload["n"] / 16)
            full_panels = (workload["m"] // 6) * (workload["n"] // 16)
            k_panels = math.ceil(workload["k"] / int(candidate_row["tile_k"]))
            invocations = (
                int(measurement["warmups"]) + int(measurement["repeats"])
            ) * int(measurement["inner_iters"])
            expected_fringe = (m_panels * n_panels - full_panels) * k_panels * invocations
            # A short final schedule tile is an ordinary loop boundary. It is a
            # contract adaptation only when K violates the Haswell f32 kernel's
            # extracted main-loop step, not merely when K % tile_k is nonzero.
            has_contract_k_remainder = workload["k"] % 4 != 0
            observed_path = "adapt" if (
                expected_fringe > 0 or has_contract_k_remainder
            ) else "direct"
            if int(values.get("fringe_calls", 0)) != expected_fringe:
                raise RuntimeError(
                    f"fringe mismatch {workload['id']} {candidate_row['candidate_id']}: "
                    f"expected {expected_fringe}, observed {values.get('fringe_calls')}"
                )
        else:
            observed_path = "fallback"
    return {
        "workload_id": workload["id"],
        "family": workload["family"],
        "split": workload["split"],
        "tune": workload["tune"],
        "m": workload["m"], "k": workload["k"], "n": workload["n"],
        "variant": variant,
        "trial": trial,
        "candidate_id": candidate_row.get("candidate_id") if candidate_row else None,
        "predicted_path": predicted_path,
        "observed_path": observed_path,
        "prediction_matches_observation": (
            predicted_path == observed_path if candidate_row is not None else True
        ),
        "expected_fringe_calls": expected_fringe,
        "benchmark_wall_ms": round(wall_ms, 6),
        "compile_pipeline_ms": manifest["pipeline_ms"],
        **values,
    }


def aggregate_trials(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault((row["workload_id"], row["variant"]), []).append(row)
    result = []
    for (_, _), values in sorted(groups.items()):
        first = values[0]
        medians = [float(row["median_ms"]) for row in values]
        gflops = [float(row["gflops"]) for row in values]
        result.append({
            **{key: first[key] for key in (
                "workload_id", "family", "split", "tune", "m", "k", "n", "variant",
                "candidate_id", "predicted_path", "observed_path",
            )},
            "trial_count": len(values),
            "all_pass": all(row["status"] == "PASS" for row in values),
            "all_predictions_match": all(row["prediction_matches_observation"] for row in values),
            "median_ms": statistics.median(medians),
            "min_trial_ms": min(medians),
            "max_trial_ms": max(medians),
            "median_gflops": statistics.median(gflops),
            "median_benchmark_wall_ms": statistics.median(float(row["benchmark_wall_ms"]) for row in values),
            "compile_pipeline_ms": first["compile_pipeline_ms"],
            "max_abs_diff": max(float(row["max_abs_diff"]) for row in values),
        })
    return result


def ablation_pools(state: dict[str, Any], config: dict[str, Any]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    result: dict[str, dict[str, list[dict[str, Any]]]] = {}
    size = int(config["pool_size"])
    for workload_id, item in state.items():
        if not item["workload"]["tune"]:
            continue
        generic = item["guarded_spaces"]["generic"]
        contract = item["guarded_spaces"]["contract_only"]
        b4 = item["pools"]["B4"]
        result[workload_id] = {
            "full": b4,
            "no_checker": item["pools"]["B1"],
            "no_cache_prior": item["pools"]["B2"],
            "no_packing_rule": select_pool(
                [row for row in generic if row["pack_mode"] == "none"],
                workload_id, "ABL_no_packing", size,
            ),
            "no_mr_nr": sorted(
                contract,
                key=lambda row: (
                    int(row["tile_m"]) % 6 == 0 and int(row["tile_n"]) % 16 == 0,
                    hashlib.sha256(("no_mr_nr:" + row["candidate_id"]).encode()).hexdigest(),
                ),
            )[:size],
            "no_soft_prior": sorted(
                b4, key=lambda row: hashlib.sha256(row["candidate_id"].encode()).hexdigest()
            ),
            "no_shell": item["pools"]["B3"],
            "misleading_prior": list(reversed(b4)),
        }
    return result


def collect_measurement_rows(
    state: dict[str, Any], ratio_pools: dict[str, dict[str, list[dict[str, Any]]]],
    ablations: dict[str, dict[str, list[dict[str, Any]]]],
) -> dict[str, dict[str, dict[str, Any]]]:
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for workload_id, item in state.items():
        rows: dict[str, dict[str, Any]] = {}
        for method in METHOD_TO_SPACE:
            members = item["pools"][method]
            selected = members if item["workload"]["tune"] else members[:1]
            for row in selected:
                rows[row["candidate_id"]] = row
        if item["workload"]["tune"]:
            for members in ablations[workload_id].values():
                for row in members:
                    rows[row["candidate_id"]] = row
            for pools_by_workload in ratio_pools.values():
                for row in pools_by_workload[workload_id]:
                    rows[row["candidate_id"]] = row
        result[workload_id] = rows
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="measure two shapes and the first four candidates")
    parser.add_argument("--prepare-only", action="store_true", help="refresh spaces and tuner pools without compiling")
    args = parser.parse_args()
    for directory in (BUILD, RAW, PROCESSED, REPORTS, TUNER):
        directory.mkdir(parents=True, exist_ok=True)

    config, workloads = load_config()
    if not args.skip_build:
        chapter5.ensure_tools()
    chapter5.ensure_blis()
    generation_started = time.perf_counter()
    inputs, state = build_space_state(workloads, config)
    space_generation_wall_ms = (time.perf_counter() - generation_started) * 1000.0
    write_csv(PROCESSED / "space_summary.csv", space_summary(state))
    write_json(PROCESSED / "pool_diagnostics.json", pool_diagnostics(state))

    tune_workloads = [row for row in workloads if row["tune"]]
    ratio_pools = {
        f"{ratio:.2f}": shell_ratio_pools(tune_workloads, config, ratio)
        for ratio in config["shell_ratios"]
    }
    ablations = ablation_pools(state, config)
    write_json(TUNER / "base_pools.json", {
        workload_id: {method: members for method, members in item["pools"].items()}
        for workload_id, item in state.items() if item["workload"]["tune"]
    })
    write_json(TUNER / "ablation_pools.json", ablations)
    write_json(TUNER / "shell_ratio_pools.json", ratio_pools)
    measurement_rows = collect_measurement_rows(state, ratio_pools, ablations)
    if args.prepare_only:
        print(json.dumps({
            "status": "PASS",
            "mode": "prepare_only",
            "workloads": len(workloads),
            "unique_candidates": len({
                candidate_id for rows in measurement_rows.values() for candidate_id in rows
            }),
        }, indent=2))
        return

    selected_workloads = workloads
    if args.smoke:
        selected_workloads = [
            next(row for row in workloads if row["id"] == "sq_096"),
            next(row for row in workloads if row["id"] == "tail_190x250x250"),
        ]
        smoke_rows: dict[str, dict[str, dict[str, Any]]] = {}
        for workload in selected_workloads:
            item = state[workload["id"]]
            direct = item["pools"]["B4"][0]
            fallback = next(
                row for row in item["pools"]["B1"] if row["predicted_path"] == "fallback"
            )
            smoke_rows[workload["id"]] = {
                direct["candidate_id"]: direct,
                fallback["candidate_id"]: fallback,
            }
        measurement_rows = smoke_rows

    manifests: dict[str, dict[str, Any]] = {}
    manifests["B0_scalar"] = compile_dynamic("B0_scalar", None, config, args.force)
    manifests["B0_optimized"] = compile_dynamic("B0_optimized", None, config, args.force)
    manifests["B5_blis"] = compile_blis_frontend(args.force)
    unique_rows: dict[str, dict[str, Any]] = {}
    for rows in measurement_rows.values():
        unique_rows.update(rows)
    compile_failures = []
    for index, (candidate_id, row) in enumerate(sorted(unique_rows.items()), 1):
        try:
            manifests[candidate_id] = compile_dynamic(candidate_id, row, config, args.force)
        except Exception as exc:  # preserve every attempted compile as evidence
            compile_failures.append({"candidate_id": candidate_id, "error": str(exc)})
        if index % 25 == 0:
            print(f"compiled {index}/{len(unique_rows)} candidate binaries", flush=True)
    write_json(PROCESSED / "binary_manifests.json", manifests)
    write_json(PROCESSED / "compile_failures.json", compile_failures)

    trial_rows: list[dict[str, Any]] = []
    for workload in selected_workloads:
        for variant in ("B0_scalar", "B0_optimized", "B5_blis"):
            for trial in range(1, int(config["measurement"]["independent_trials"]) + 1):
                trial_rows.append(measure_executable(
                    manifests[variant], workload, config["measurement"], variant, trial, None
                ))
        candidate_items = measurement_rows[workload["id"]]
        for candidate_id, row in sorted(candidate_items.items()):
            manifest = manifests.get(candidate_id)
            if manifest is None:
                continue
            variant = "candidate:" + candidate_id
            for trial in range(1, int(config["measurement"]["independent_trials"]) + 1):
                trial_rows.append(measure_executable(
                    manifest, workload, config["measurement"], variant, trial, row
                ))
        print(f"measured {workload['id']} ({len(trial_rows)} total trial rows)", flush=True)

    write_csv(RAW / ("smoke_trials.csv" if args.smoke else "measurement_trials.csv"), trial_rows)
    aggregates = aggregate_trials(trial_rows)
    write_csv(PROCESSED / ("smoke_aggregates.csv" if args.smoke else "measurement_aggregates.csv"), aggregates)
    summary = {
        "status": "PASS" if not compile_failures and all(row["status"] == "PASS" for row in trial_rows) else "PARTIAL",
        "workload_count": len(selected_workloads),
        "tuning_workload_count": sum(bool(row["tune"]) for row in selected_workloads),
        "candidate_binary_count": len([key for key in manifests if key.startswith("m")]),
        "compile_failure_count": len(compile_failures),
        "trial_row_count": len(trial_rows),
        "aggregate_row_count": len(aggregates),
        "baseline_correctness": dict(Counter(
            row["status"] for row in trial_rows if row["variant"] in {"B0_scalar", "B0_optimized", "B5_blis"}
        )),
        "candidate_observed_paths": dict(Counter(
            row["observed_path"] for row in trial_rows if row["variant"].startswith("candidate:")
        )),
        "all_candidate_predictions_match": all(
            row["prediction_matches_observation"]
            for row in trial_rows if row["variant"].startswith("candidate:")
        ),
        "measurement_protocol": config["measurement"],
        "space_generation_wall_ms": round(space_generation_wall_ms, 6),
        "checker_decisions": len(workloads) * 2600,
        "checker_mean_us_per_candidate": round(
            space_generation_wall_ms * 1000.0 / (len(workloads) * 2600), 6
        ),
        "claim_boundary": config["claim_boundary"],
    }
    write_json(PROCESSED / ("smoke_summary.json" if args.smoke else "measurement_summary.json"), summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
