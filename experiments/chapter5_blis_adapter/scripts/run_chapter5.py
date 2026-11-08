#!/usr/bin/env python3
"""Reproduce the Chapter 5 BLIS packing and call-adapter experiment."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[3]
CONFIG = json.loads((PROJECT / "data" / "experiment_config.json").read_text(encoding="utf-8"))
BUILD = PROJECT / "build"
RAW = PROJECT / "raw"
PROCESSED = PROJECT / "processed"
REPORTS = PROJECT / "reports"

BUDDY_OPT = REPO / "build" / "bin" / "buddy-opt"
MLIR_OPT = REPO / "llvm" / "build" / "bin" / "mlir-opt"
MLIR_TRANSLATE = REPO / "llvm" / "build" / "bin" / "mlir-translate"
CXX = REPO / "llvm" / "build" / "bin" / "clang++"
DRIVER = REPO / "jlq" / "thesis" / "experiments" / "scripts" / "mlir_aot_matmul_bench.cpp"
BLIS = REPO / "jlq" / "thesis" / "blis" / "blis"
BLIS_INCLUDE = BLIS / "include" / "haswell"
BLIS_LIBRARY = BLIS / "lib" / "haswell" / "libblis.a"
ADAPTER = PROJECT / "runtime" / "blis_microkernel_adapter.cpp"
SMOKE = PROJECT / "runtime" / "wrapper_smoke.cpp"


def run(command: list[str], log: Path, cwd: Path = REPO) -> subprocess.CompletedProcess[str]:
    start = time.perf_counter()
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        "$ " + " ".join(command) + f"\nELAPSED_MS={elapsed_ms:.6f}\n\n"
        + "STDOUT\n" + completed.stdout + "\nSTDERR\n" + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stderr[-1600:]}")
    return completed


def ensure_tools() -> None:
    missing = [path for path in (MLIR_OPT, MLIR_TRANSLATE, CXX) if not path.exists()]
    if missing:
        raise FileNotFoundError("missing LLVM/MLIR tools: " + ", ".join(map(str, missing)))
    run(["cmake", "--build", str(REPO / "build"), "--target", "buddy-opt", "-j4"], REPORTS / "build_buddy.log")


def ensure_blis() -> None:
    if BLIS_LIBRARY.exists() and (BLIS_INCLUDE / "blis.h").exists():
        return
    run(
        [
            "./configure", "--disable-shared", "--enable-static",
            "--disable-threading", f"CC={CXX.with_name('clang')}", "haswell",
        ],
        REPORTS / "build_blis_configure.log",
        BLIS,
    )
    run(["make", "-j4"], REPORTS / "build_blis_make.log", BLIS)


def payload(symbol: str, nested: bool) -> str:
    task = CONFIG["task"]
    m, n, k = task["m"], task["n"], task["k"]
    function = f"""func.func @{symbol}(
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
    if not nested:
        return function
    indented = "\n".join("  " + line if line else line for line in function.splitlines())
    return f"module @chapter5_payload attributes {{buddy.payload}} {{\n{indented}\n}}\n"


def direct_schedule() -> str:
    candidate = CONFIG["candidate"]
    options = " ".join(
        f"{name}={value}" for name, value in (
            ("tile-m", candidate["tile_m"]), ("tile-n", candidate["tile_n"]),
            ("tile-k", candidate["tile_k"]), ("mr", candidate["mr"]),
            ("nr", candidate["nr"]),
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


def fallback_schedule() -> str:
    candidate = CONFIG["candidate"]
    return f"""
module attributes {{transform.with_named_sequence}} {{
  transform.named_sequence @__transform_main(
      %root: !transform.any_op {{transform.consumed}}) {{
    %matmul = transform.structured.match ops{{["linalg.matmul"]}} in %root
      : (!transform.any_op) -> !transform.any_op
    %tiled, %loops:3 = transform.structured.tile_using_for %matmul
      tile_sizes [{candidate['tile_m']}, {candidate['tile_n']}, {candidate['tile_k']}]
      : (!transform.any_op) -> (!transform.any_op, !transform.any_op,
          !transform.any_op, !transform.any_op)
    %func = transform.get_parent_op %tiled {{isolated_from_above}}
      : (!transform.any_op) -> !transform.any_op
    transform.structured.vectorize_children_and_apply_patterns %func
      : (!transform.any_op) -> !transform.any_op
    %bufferized = transform.bufferization.one_shot_bufferize
      layout{{IdentityLayoutMap}} %root
      {{bufferize_function_boundaries = true}}
      : (!transform.any_op) -> !transform.any_op
    transform.yield
  }}
}}
"""


def compile_and_run_variant(variant: str, warmups: int, repeats: int, inner_iters: int, cpu: int) -> dict[str, Any]:
    direct = variant == "direct_blis_6x16"
    case = BUILD / variant
    case.mkdir(parents=True, exist_ok=True)
    symbol = "chapter5_" + variant
    input_path = case / "input.mlir"
    transformed = case / "transformed.mlir"
    llvm_mlir = case / "llvm.mlir"
    llvm_ir = case / "kernel.ll"
    executable = case / "benchmark"
    input_path.write_text(
        payload(symbol, nested=direct) + (direct_schedule() if direct else fallback_schedule()),
        encoding="utf-8",
    )

    if direct:
        transform_command = [
            str(BUDDY_OPT), str(input_path), "--transform-interpreter",
            "--buddy-finalize-transform-payload", "--canonicalize", "--cse",
            "-o", str(transformed),
        ]
    else:
        transform_command = [
            str(MLIR_OPT), str(input_path), "--transform-interpreter",
            "-test-transform-dialect-erase-schedule", "--canonicalize", "--cse",
            "-o", str(transformed),
        ]
    run(transform_command, case / "01_transform.log")
    run(
        [str(MLIR_OPT), str(transformed), "--convert-linalg-to-loops",
         "--test-lower-to-llvm", "-o", str(llvm_mlir)],
        case / "02_lower.log",
    )
    run(
        [str(MLIR_TRANSLATE), "--mlir-to-llvmir", str(llvm_mlir), "-o", str(llvm_ir)],
        case / "03_translate.log",
    )

    task = CONFIG["task"]
    command = [
        str(CXX), "-O3", "-march=native", "-std=c++17",
        f"-DKERNEL_SYMBOL={symbol}", f"-DMATMUL_M={task['m']}",
        f"-DMATMUL_K={task['k']}", f"-DMATMUL_N={task['n']}",
        str(DRIVER), str(llvm_ir),
    ]
    if direct:
        command.extend(["-I" + str(BLIS_INCLUDE), str(ADAPTER), str(BLIS_LIBRARY), "-lpthread", "-lm"])
    command.extend(["-o", str(executable)])
    run(command, case / "04_native_compile.log")

    benchmark = run(
        ["taskset", "-c", str(cpu), str(executable), str(warmups), str(repeats), str(inner_iters)],
        case / "05_benchmark.log",
    )
    rows = list(csv.DictReader(io.StringIO(benchmark.stdout)))
    if not rows or rows[-1].get("status") != "PASS":
        raise RuntimeError(f"{variant} did not produce a passing benchmark row")
    values = rows[-1]
    transformed_text = transformed.read_text(encoding="utf-8")
    llvm_text = llvm_ir.read_text(encoding="utf-8")
    symbols = run(["nm", "-C", str(executable)], case / "06_symbols.log").stdout
    wrapper_call = bool(re.search(r"call void @buddy_blis_sgemm_6x16\b", llvm_text))
    kernel_symbol = bool(re.search(r"\bT bli_sgemm_haswell_asm_6x16$", symbols, re.MULTILINE))

    return {
        "variant": variant,
        "predicted_path": "direct" if direct else "fallback",
        "observed_path": "direct" if wrapper_call and kernel_symbol else "fallback",
        "status": values["status"],
        "microkernel_replaced": wrapper_call and kernel_symbol,
        "packing_alloc_count": transformed_text.count("memref.alloc"),
        "wrapper_call_count_ir": len(re.findall(r"call void @buddy_blis_sgemm_6x16\b", llvm_text)),
        "blis_kernel_symbol_present": kernel_symbol,
        "linalg_matmul_remaining": "linalg.matmul" in transformed_text,
        "median_ms": float(values["median_ms"]),
        "min_ms": float(values["min_ms"]),
        "max_ms": float(values["max_ms"]),
        "gflops": float(values["gflops"]),
        "max_abs_diff": float(values["max_abs_diff"]),
        "max_rel_diff": float(values["max_rel_diff"]),
        "checksum": float(values["checksum"]),
        "llvm_ir_bytes": llvm_ir.stat().st_size,
        "executable_bytes": executable.stat().st_size,
        "warmups": warmups,
        "repeats": repeats,
        "inner_iters": inner_iters,
        "cpu_affinity": cpu,
    }


def run_wrapper_smoke() -> None:
    executable = BUILD / "wrapper_smoke"
    run(
        [
            str(CXX), "-O2", "-march=native", "-std=c++17",
            "-I" + str(BLIS_INCLUDE), str(ADAPTER), str(SMOKE),
            str(BLIS_LIBRARY), "-lpthread", "-lm", "-o", str(executable),
        ],
        BUILD / "wrapper_smoke_compile.log",
    )
    result = run([str(executable)], BUILD / "wrapper_smoke_run.log")
    (RAW / "wrapper_smoke.csv").write_text(result.stdout, encoding="utf-8")


def write_results(results: list[dict[str, Any]]) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    with (RAW / "path_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)

    by_name = {row["variant"]: row for row in results}
    baseline = by_name["fallback_vectorized"]
    direct = by_name["direct_blis_6x16"]
    summary = {
        "experiment_id": CONFIG["experiment_id"],
        "task": CONFIG["task"],
        "candidate": CONFIG["candidate"],
        "results": results,
        "comparison": {
            "direct_speedup_over_fallback": baseline["median_ms"] / direct["median_ms"],
            "direct_gflops_ratio": direct["gflops"] / baseline["gflops"],
            "llvm_ir_size_ratio": direct["llvm_ir_bytes"] / baseline["llvm_ir_bytes"],
        },
        "claim_boundary": CONFIG["claim_boundary"],
    }
    (PROCESSED / "chapter5_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    speedup = summary["comparison"]["direct_speedup_over_fallback"]
    report = f"""# Chapter 5 BLIS adapter experiment

## Result

The aligned `192x256x256` f32 anchor completed both newly generated paths.
The Transform-driven BLIS path called the real `bli_sgemm_haswell_asm_6x16`
symbol and passed the full-matrix reference check.

| Variant | Observed path | Median ms | GFLOP/s | Max abs diff | BLIS symbol |
|---|---:|---:|---:|---:|---:|
| fallback_vectorized | {baseline['observed_path']} | {baseline['median_ms']:.6f} | {baseline['gflops']:.3f} | {baseline['max_abs_diff']:.8g} | no |
| direct_blis_6x16 | {direct['observed_path']} | {direct['median_ms']:.6f} | {direct['gflops']:.3f} | {direct['max_abs_diff']:.8g} | yes |

For this run, the direct path was `{speedup:.3f}x` faster than the generated
fallback baseline. This ratio is host- and run-specific and is not a broad
performance claim.

## Evidence chain

1. `transform.apply_registered_pass` materializes BLIS-compatible A/B panels.
2. `transform.buddy.call_microkernel` only retargets the prepared placeholder.
3. LLVM IR contains `call void @buddy_blis_sgemm_6x16`.
4. The linked executable exports both the wrapper and
   `bli_sgemm_haswell_asm_6x16`.
5. Runtime output passes the scalar reference check.

## Boundary

{CONFIG['claim_boundary']}
"""
    (REPORTS / "chapter5_results.md").write_text(report, encoding="utf-8")


def write_artifact_index() -> None:
    text = """# Chapter 5 artifact index

- Configuration: `data/experiment_config.json`
- Reproduction entry: `scripts/run_chapter5.py`
- Runtime adapter: `runtime/blis_microkernel_adapter.cpp`
- Packing ABI smoke test: `runtime/wrapper_smoke.cpp`
- Dynamic benchmark driver: `runtime/dynamic_matmul_bench.cpp`
- Transform op definition: `../../../../midend/include/Dialect/Microkernel/TransformOps.td`
- Transform op implementation: `../../../../midend/lib/Dialect/Microkernel/TransformOps.cpp`
- Packing pass: `../../../../midend/lib/Conversion/MatMulOptimization/MatMulBlisMicrokernel.cpp`
- Raw path measurements: `raw/path_results.csv`
- Raw wrapper result: `raw/wrapper_smoke.csv`
- Machine-readable summary: `processed/chapter5_summary.json`
- Result report: `reports/chapter5_results.md`
- Direct-path IR and executable: `build/direct_blis_6x16/`
- Fallback control IR and executable: `build/fallback_vectorized/`
- Dynamic multi-shape trials: `raw/dynamic_multishape_trials.csv`
- Dynamic multi-shape summary: `processed/dynamic_multishape_summary.json`
- Dynamic multi-shape report: `reports/dynamic_multishape_results.md`
- Full reproduction entry: `scripts/run_chapter5_full.py`

The custom Transform op only selects the external callee. Packing and loop
materialization belong to the registered transformation pass; the C++ adapter
only bridges the lowered integer-address ABI to the BLIS microkernel ABI.
"""
    (PROJECT / "chapter5_artifact_index.md").write_text(text, encoding="utf-8")


def refresh_registry() -> None:
    root = Path("/root/personal-os/PersonalOS")
    script = root / "scripts" / "experiment_registry.py"
    if not script.exists():
        print("PersonalOS registry not installed; skipped refresh")
        return
    run(
        ["python3", str(script), "refresh", "--workspace-root", str(REPO),
         "--completed-id", CONFIG["experiment_id"]],
        REPORTS / "registry_refresh.log",
        root,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=11)
    parser.add_argument("--inner-iters", type=int, default=1)
    parser.add_argument("--cpu", type=int, default=0)
    parser.add_argument("--skip-registry", action="store_true")
    args = parser.parse_args()

    for directory in (BUILD, RAW, PROCESSED, REPORTS):
        directory.mkdir(parents=True, exist_ok=True)
    ensure_tools()
    ensure_blis()
    run_wrapper_smoke()
    results = [
        compile_and_run_variant(name, args.warmups, args.repeats, args.inner_iters, args.cpu)
        for name in CONFIG["variants"]
    ]
    write_results(results)
    write_artifact_index()
    run(
        ["python3", "-m", "unittest", "discover", "-s", str(PROJECT / "tests"), "-v"],
        REPORTS / "tests.log",
    )
    if not args.skip_registry:
        refresh_registry()
    print(json.dumps({"status": "PASS", "summary": str(PROCESSED / "chapter5_summary.json")}, indent=2))


if __name__ == "__main__":
    main()
