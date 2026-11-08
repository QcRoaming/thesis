#!/usr/bin/env python3
"""Reusable Transform Dialect to native measurement runner for Chapter 4."""

from __future__ import annotations

import csv
import io
import json
import os
import re
import resource
import subprocess
import time
from pathlib import Path
from typing import Any

from chapter4lib import Candidate, PROJECT_DIR


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "llvm" / "build" / "bin" / "mlir-opt").exists():
            return candidate
    raise RuntimeError(f"could not find MLIR toolchain above {start}")


REPO_ROOT = find_repo_root(PROJECT_DIR)
MLIR_OPT = REPO_ROOT / "llvm" / "build" / "bin" / "mlir-opt"
MLIR_TRANSLATE = REPO_ROOT / "llvm" / "build" / "bin" / "mlir-translate"
CXX = REPO_ROOT / "llvm" / "build" / "bin" / "clang++"
DRIVER = PROJECT_DIR.parent / "scripts" / "mlir_aot_matmul_bench.cpp"


def payload(symbol: str, task: dict[str, Any]) -> str:
    if task["dtype"] != "f32":
        raise ValueError("the current native benchmark driver supports f32 only")
    m, k, n = (task["shape"][key] for key in ("m", "k", "n"))
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


def transform_schedule(candidate: Candidate, template_path: str) -> str:
    vector_step = """
    %func = transform.get_parent_op %tiled {isolated_from_above}
      : (!transform.any_op) -> !transform.any_op
    transform.structured.vectorize_children_and_apply_patterns %func
      : (!transform.any_op) -> !transform.any_op
""" if candidate.vectorize else ""
    return f"""
module attributes {{transform.with_named_sequence, chapter4.template_path = \"{template_path}\"}} {{
  transform.named_sequence @__transform_main(
      %module_op: !transform.any_op {{transform.consumed}}) {{
    %matmul = transform.structured.match ops{{[\"linalg.matmul\"]}} in %module_op
      : (!transform.any_op) -> !transform.any_op
    %tiled, %loops:3 = transform.structured.tile_using_for %matmul
      tile_sizes [{candidate.tile_m}, {candidate.tile_n}, {candidate.tile_k}]
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


def run_command(command: list[str], log_path: Path) -> tuple[int, float, str]:
    start = time.perf_counter()
    completed = subprocess.run(command, text=True, capture_output=True)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    log_path.write_text(
        "$ " + " ".join(command) + "\n\nSTDOUT\n" + completed.stdout + "\nSTDERR\n" + completed.stderr,
        encoding="utf-8",
    )
    return completed.returncode, elapsed_ms, completed.stderr.strip()


def _failure(stage: str, error: str, timings: dict[str, float]) -> dict[str, Any]:
    return {
        "compile_status": "fail",
        "correctness_status": "not_attempted",
        "status": "COMPILE_FAIL",
        "failure_stage": stage,
        "failure_reason": error[-1200:],
        "observed_path": "reject",
        "microkernel_replaced": False,
        **{key: round(value, 6) for key, value in timings.items()},
    }


def evaluate_transform(
    task: dict[str, Any],
    candidate: Candidate,
    predicted_path: str,
    template_path: str,
    case_dir: Path,
    warmups: int = 1,
    repeats: int = 2,
    inner_iters: int = 2,
    cpu_affinity: int = 0,
    force: bool = False,
) -> dict[str, Any]:
    case_dir.mkdir(parents=True, exist_ok=True)
    cache = case_dir / "measurement.json"
    if cache.exists() and not force:
        return json.loads(cache.read_text(encoding="utf-8"))

    symbol = "chapter4_" + re.sub(r"[^A-Za-z0-9_]", "_", case_dir.name)
    input_mlir = case_dir / "input.mlir"
    transformed_mlir = case_dir / "transformed.mlir"
    llvm_mlir = case_dir / "llvm.mlir"
    llvm_ir = case_dir / "kernel.ll"
    executable = case_dir / "benchmark"
    input_mlir.write_text(payload(symbol, task) + transform_schedule(candidate, template_path), encoding="utf-8")
    manifest = {
        "task_id": task["id"],
        "candidate": candidate.__dict__,
        "predicted_path": predicted_path,
        "template_path": template_path,
        "packing_requested_by_policy": candidate.pack_mode == "ab",
        "packing_materialized_by_transform": False,
        "claim_boundary": (
            "The template executes real tiling/vectorization and finite loop-bound handling. "
            "This prototype does not yet materialize BLIS panel packing or a BLIS call."
        ),
    }
    (case_dir / "template_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    timings: dict[str, float] = {}
    rc, timings["transform_ms"], error = run_command(
        [
            str(MLIR_OPT),
            str(input_mlir),
            "--transform-interpreter",
            "-test-transform-dialect-erase-schedule",
            "--canonicalize",
            "--cse",
            "-o",
            str(transformed_mlir),
        ],
        case_dir / "01_transform.log",
    )
    if rc:
        result = _failure("transform", error, timings)
        cache.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result

    rc, lower_ms, error = run_command(
        [str(MLIR_OPT), str(transformed_mlir), "--convert-linalg-to-loops", "--test-lower-to-llvm", "-o", str(llvm_mlir)],
        case_dir / "02_lower_dialect.log",
    )
    timings["lowering_ms"] = lower_ms
    if not rc:
        rc, translate_ms, error = run_command(
            [str(MLIR_TRANSLATE), "--mlir-to-llvmir", str(llvm_mlir), "-o", str(llvm_ir)],
            case_dir / "03_translate.log",
        )
        timings["lowering_ms"] += translate_ms
    if rc:
        result = _failure("lowering", error, timings)
        cache.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result

    ir_text = llvm_ir.read_text(encoding="utf-8", errors="replace")
    replaced = bool(re.search(r"\b(?:bli_[sd]gemm|cblas_[sd]gemm)\b", ir_text))
    m, k, n = (task["shape"][key] for key in ("m", "k", "n"))
    rc, timings["native_compile_ms"], error = run_command(
        [
            str(CXX),
            "-O3",
            "-march=native",
            "-std=c++17",
            f"-DKERNEL_SYMBOL={symbol}",
            f"-DMATMUL_M={m}",
            f"-DMATMUL_K={k}",
            f"-DMATMUL_N={n}",
            str(DRIVER),
            str(llvm_ir),
            "-o",
            str(executable),
        ],
        case_dir / "04_native_compile.log",
    )
    if rc:
        result = _failure("native_compile", error, timings)
        result["microkernel_replaced"] = replaced
        cache.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result

    env = os.environ.copy()
    env.update({"OMP_NUM_THREADS": "1", "BLIS_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})

    def set_stack_limit() -> None:
        limit = 65536 * 1024
        resource.setrlimit(resource.RLIMIT_STACK, (limit, limit))

    start = time.perf_counter()
    benchmark = subprocess.run(
        ["taskset", "-c", str(cpu_affinity), str(executable), str(warmups), str(repeats), str(inner_iters)],
        text=True,
        capture_output=True,
        env=env,
        preexec_fn=set_stack_limit,
    )
    timings["benchmark_wall_ms"] = (time.perf_counter() - start) * 1000.0
    (case_dir / "05_benchmark.log").write_text(
        "STDOUT\n" + benchmark.stdout + "\nSTDERR\n" + benchmark.stderr, encoding="utf-8"
    )
    parsed = list(csv.DictReader(io.StringIO(benchmark.stdout)))
    values = parsed[-1] if parsed else {}
    passed = benchmark.returncode == 0 and values.get("status") == "PASS"
    result = {
        "compile_status": "pass",
        "correctness_status": "pass" if passed else "fail",
        "status": "PASS" if passed else "CORRECTNESS_FAIL",
        "failure_stage": "" if passed else "runtime_or_correctness",
        "failure_reason": "" if passed else (benchmark.stderr.strip()[-1200:] or values.get("status", "no output")),
        "observed_path": "direct" if replaced else "fallback",
        "microkernel_replaced": replaced,
        "llvm_ir_bytes": llvm_ir.stat().st_size,
        "executable_bytes": executable.stat().st_size,
        "warmups": warmups,
        "repeats": repeats,
        "inner_iters": inner_iters,
        "cpu_affinity": cpu_affinity,
        **{key: round(value, 6) for key, value in timings.items()},
        **{key: values.get(key, "") for key in (
            "median_ms", "min_ms", "max_ms", "mean_ms", "stddev_ms", "p90_ms", "gflops",
            "max_abs_diff", "max_rel_diff", "checksum", "output_aliases_c",
        )},
    }
    cache.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
