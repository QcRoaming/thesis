#!/usr/bin/env python3
"""Compile one dynamic kernel per variant and measure it across many shapes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import statistics
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_chapter5 as base  # noqa: E402


PROJECT = base.PROJECT
CONFIG = base.CONFIG
DYNAMIC_CONFIG = json.loads(
    (PROJECT / "data" / "dynamic_shapes.json").read_text(encoding="utf-8")
)
DYNAMIC_BUILD = PROJECT / "build" / "dynamic_multishape"
DYNAMIC_DRIVER = PROJECT / "runtime" / "dynamic_matmul_bench.cpp"
RAW_CSV = PROJECT / "raw" / "dynamic_multishape_trials.csv"
SUMMARY_JSON = PROJECT / "processed" / "dynamic_multishape_summary.json"
REPORT_MD = PROJECT / "reports" / "dynamic_multishape_results.md"


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
    return f"module @chapter5_payload attributes {{buddy.payload}} {{\n{indented}\n}}\n"


def fallback_schedule() -> str:
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compile_variant(variant: str) -> dict[str, Any]:
    direct = variant == "dynamic_blis"
    case = DYNAMIC_BUILD / variant
    case.mkdir(parents=True, exist_ok=True)
    symbol = "chapter5_" + variant
    input_mlir = case / "input.mlir"
    transformed = case / "transformed.mlir"
    llvm_mlir = case / "llvm.mlir"
    llvm_ir = case / "kernel.ll"
    executable = case / "benchmark"
    input_mlir.write_text(
        dynamic_payload(symbol, nested=direct)
        + (base.direct_schedule() if direct else fallback_schedule()),
        encoding="utf-8",
    )

    if direct:
        transform_command = [
            str(base.BUDDY_OPT), str(input_mlir), "--transform-interpreter",
            "--buddy-finalize-transform-payload", "--canonicalize", "--cse",
            "-o", str(transformed),
        ]
    else:
        transform_command = [
            str(base.MLIR_OPT), str(input_mlir), "--transform-interpreter",
            "-test-transform-dialect-erase-schedule", "--canonicalize", "--cse",
            "-o", str(transformed),
        ]
    base.run(transform_command, case / "01_transform.log")
    base.run(
        [str(base.MLIR_OPT), str(transformed), "--convert-linalg-to-loops",
         "--test-lower-to-llvm", "-o", str(llvm_mlir)],
        case / "02_lower.log",
    )
    base.run(
        [str(base.MLIR_TRANSLATE), "--mlir-to-llvmir", str(llvm_mlir),
         "-o", str(llvm_ir)],
        case / "03_translate.log",
    )

    command = [
        str(base.CXX), "-O3", "-march=native", "-std=c++17",
        f"-DKERNEL_SYMBOL={symbol}", str(DYNAMIC_DRIVER), str(llvm_ir),
    ]
    if direct:
        command.extend([
            "-DBLIS_ADAPTER_ENABLED=1", "-I" + str(base.BLIS_INCLUDE),
            str(base.ADAPTER), str(base.BLIS_LIBRARY), "-lpthread", "-lm",
        ])
    command.extend(["-o", str(executable)])
    base.run(command, case / "04_native_compile.log")
    symbols = base.run(["nm", "-C", str(executable)], case / "05_symbols.log").stdout
    transformed_text = transformed.read_text(encoding="utf-8")
    llvm_text = llvm_ir.read_text(encoding="utf-8")
    return {
        "variant": variant,
        "symbol": symbol,
        "executable": executable,
        "executable_sha256": sha256(executable),
        "llvm_ir_bytes": llvm_ir.stat().st_size,
        "has_dynamic_dims": "memref.dim" in transformed_text,
        "has_temporary_c": "memref<6x16xf32>" in transformed_text,
        "has_direct_call": "call void @buddy_blis_sgemm_6x16(" in llvm_text,
        "has_fringe_call": "call void @buddy_blis_sgemm_6x16_fringe(" in llvm_text,
        "has_blis_kernel_symbol": " T bli_sgemm_haswell_asm_6x16" in symbols,
    }


def expected_fringe_calls(shape: dict[str, Any], measurement: dict[str, int]) -> int:
    candidate = CONFIG["candidate"]
    m, k, n = shape["m"], shape["k"], shape["n"]
    m_panels = math.ceil(m / candidate["mr"])
    n_panels = math.ceil(n / candidate["nr"])
    full_panels = (m // candidate["mr"]) * (n // candidate["nr"])
    fringe_per_k_panel = m_panels * n_panels - full_panels
    k_panels = math.ceil(k / candidate["tile_k"])
    invocations = (measurement["warmups"] + measurement["repeats"]) * measurement["inner_iters"]
    return fringe_per_k_panel * k_panels * invocations


def run_trials(compiled: list[dict[str, Any]], measurement: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for shape in DYNAMIC_CONFIG["shapes"]:
        for variant in compiled:
            for trial in range(1, measurement["trials"] + 1):
                completed = base.run(
                    [
                        "taskset", "-c", str(measurement["cpu_affinity"]),
                        str(variant["executable"]), str(shape["m"]),
                        str(shape["k"]), str(shape["n"]),
                        str(measurement["warmups"]), str(measurement["repeats"]),
                        str(measurement["inner_iters"]),
                    ],
                    DYNAMIC_BUILD / variant["variant"] / "runs"
                    / f"{shape['id']}_trial_{trial:02d}.log",
                )
                parsed = list(csv.DictReader(io.StringIO(completed.stdout)))
                if not parsed or parsed[-1].get("status") != "PASS":
                    raise RuntimeError(f"failed dynamic measurement: {shape['id']} {variant['variant']}")
                values = parsed[-1]
                expected_fringe = (
                    expected_fringe_calls(shape, measurement)
                    if variant["variant"] == "dynamic_blis" else 0
                )
                observed_fringe = int(values["fringe_calls"])
                if observed_fringe != expected_fringe:
                    raise RuntimeError(
                        f"fringe count mismatch for {shape['id']}: "
                        f"expected {expected_fringe}, observed {observed_fringe}"
                    )
                rows.append({
                    "shape_id": shape["id"],
                    "m": shape["m"], "k": shape["k"], "n": shape["n"],
                    "expected_path": shape["expected_path"],
                    "variant": variant["variant"], "trial": trial,
                    "status": values["status"],
                    "median_ms": float(values["median_ms"]),
                    "min_ms": float(values["min_ms"]),
                    "max_ms": float(values["max_ms"]),
                    "mean_ms": float(values["mean_ms"]),
                    "stddev_ms": float(values["stddev_ms"]),
                    "p90_ms": float(values["p90_ms"]),
                    "gflops": float(values["gflops"]),
                    "max_abs_diff": float(values["max_abs_diff"]),
                    "max_rel_diff": float(values["max_rel_diff"]),
                    "checksum": float(values["checksum"]),
                    "output_aliases_c": int(values["output_aliases_c"]),
                    "fringe_calls": observed_fringe,
                    "expected_fringe_calls": expected_fringe,
                    "executable_sha256": variant["executable_sha256"],
                })
    return rows


def geometric_mean(values: list[float]) -> float:
    return math.exp(statistics.fmean(math.log(value) for value in values))


def bootstrap_interval(values: list[float], samples: int, seed: int) -> list[float]:
    rng = random.Random(seed)
    estimates = []
    for _ in range(samples):
        draw = [rng.choice(values) for _ in values]
        estimates.append(geometric_mean(draw))
    estimates.sort()
    lower = estimates[int(0.025 * samples)]
    upper = estimates[min(samples - 1, int(0.975 * samples))]
    return [lower, upper]


def summarize(rows: list[dict[str, Any]], compiled: list[dict[str, Any]], measurement: dict[str, int]) -> dict[str, Any]:
    shape_summaries = []
    for shape in DYNAMIC_CONFIG["shapes"]:
        selected = [row for row in rows if row["shape_id"] == shape["id"]]
        fallback = [row for row in selected if row["variant"] == "dynamic_fallback"]
        direct = [row for row in selected if row["variant"] == "dynamic_blis"]
        fallback_ms = statistics.median(row["median_ms"] for row in fallback)
        direct_ms = statistics.median(row["median_ms"] for row in direct)
        shape_summaries.append({
            "shape_id": shape["id"],
            "m": shape["m"], "k": shape["k"], "n": shape["n"],
            "expected_path": shape["expected_path"],
            "fallback_median_ms": fallback_ms,
            "blis_median_ms": direct_ms,
            "fallback_median_gflops": statistics.median(row["gflops"] for row in fallback),
            "blis_median_gflops": statistics.median(row["gflops"] for row in direct),
            "speedup": fallback_ms / direct_ms,
            "blis_trial_median_stddev_ms": statistics.pstdev(row["median_ms"] for row in direct),
            "max_abs_diff": max(row["max_abs_diff"] for row in direct),
            "fringe_calls_per_trial": sorted({row["fringe_calls"] for row in direct}),
            "expected_fringe_calls_per_trial": sorted({row["expected_fringe_calls"] for row in direct}),
        })

    speedups = [row["speedup"] for row in shape_summaries]
    direct_speedups = [row["speedup"] for row in shape_summaries if row["expected_path"] == "direct"]
    adapt_speedups = [row["speedup"] for row in shape_summaries if row["expected_path"] == "adapt"]
    return {
        "experiment_id": CONFIG["experiment_id"],
        "baseline_definition": (
            "Dynamic linalg.matmul is one-shot bufferized and lowered to "
            "scalar loops without explicit tiling or vectorization."
        ),
        "dynamic_kernel": {
            "input_types": ["tensor<?x?xf32>", "tensor<?x?xf32>", "tensor<?x?xf32>"],
            "compile_count": len(compiled),
            "one_binary_per_variant_for_all_shapes": True,
            "compiled_variants": [
                {key: (str(value) if isinstance(value, Path) else value)
                 for key, value in variant.items()}
                for variant in compiled
            ],
        },
        "measurement": measurement,
        "shape_summaries": shape_summaries,
        "overall": {
            "shape_count": len(shape_summaries),
            "direct_shape_count": len(direct_speedups),
            "adapt_shape_count": len(adapt_speedups),
            "trial_row_count": len(rows),
            "geometric_mean_speedup": geometric_mean(speedups),
            "geometric_mean_speedup_95ci_bootstrap": bootstrap_interval(
                speedups, measurement["bootstrap_samples"], measurement["bootstrap_seed"]
            ),
            "direct_geometric_mean_speedup": geometric_mean(direct_speedups),
            "adapt_geometric_mean_speedup": geometric_mean(adapt_speedups),
            "median_speedup": statistics.median(speedups),
            "all_correct": all(row["status"] == "PASS" for row in rows),
            "fringe_counts_match": all(
                row["fringe_calls"] == row["expected_fringe_calls"] for row in rows
            ),
        },
        "claim_boundary": (
            "One x86-64 AVX2/FMA host, f32 rank-2 row-major MemRefs, one dynamic "
            "kernel binary per variant, fixed 6x16 BLIS Haswell microkernel, and "
            "a scalar-loop dynamic fallback. The bootstrap interval resamples "
            "shapes, not hosts."
        ),
    }


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with RAW_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Dynamic-shape and multi-shape results", "",
        "同一个动态 scalar-loop fallback 二进制和同一个动态 BLIS 二进制分别覆盖全部 shape。", "",
        f"Baseline：{summary['baseline_definition']}", "",
        "| Shape | Path | Fallback ms | BLIS ms | BLIS GFLOP/s | Speedup | Fringe calls/trial |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary["shape_summaries"]:
        lines.append(
            f"| {row['shape_id']} | {row['expected_path']} | "
            f"{row['fallback_median_ms']:.6f} | {row['blis_median_ms']:.6f} | "
            f"{row['blis_median_gflops']:.3f} | {row['speedup']:.3f}x | "
            f"{row['fringe_calls_per_trial'][0]} |"
        )
    overall = summary["overall"]
    ci = overall["geometric_mean_speedup_95ci_bootstrap"]
    lines.extend([
        "", "## Aggregate", "",
        f"- Shape 数量：{overall['shape_count']}（direct {overall['direct_shape_count']}，adapt {overall['adapt_shape_count']}）。",
        f"- 独立 trial 行数：{overall['trial_row_count']}。",
        f"- Shape 级几何平均加速：{overall['geometric_mean_speedup']:.3f}x。",
        f"- Shape bootstrap 95% 区间：[{ci[0]:.3f}x, {ci[1]:.3f}x]。",
        f"- Direct shape 几何平均：{overall['direct_geometric_mean_speedup']:.3f}x。",
        f"- Adapt shape 几何平均：{overall['adapt_geometric_mean_speedup']:.3f}x。",
        "- 全部数值校验通过，且每个 trial 的 fringe 调用计数与解析计算一致。",
        "", "## Claim boundary", "", summary["claim_boundary"], "",
    ])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-registry", action="store_true")
    parser.add_argument("--trials", type=int)
    parser.add_argument("--repeats", type=int)
    args = parser.parse_args()

    measurement = dict(DYNAMIC_CONFIG["measurement"])
    if args.trials is not None:
        measurement["trials"] = args.trials
    if args.repeats is not None:
        measurement["repeats"] = args.repeats
    if not args.skip_build:
        base.ensure_tools()
    base.ensure_blis()
    compiled = [compile_variant("dynamic_fallback"), compile_variant("dynamic_blis")]
    rows = run_trials(compiled, measurement)
    summary = summarize(rows, compiled, measurement)
    write_outputs(rows, summary)
    if not args.skip_registry:
        base.refresh_registry()
    print(json.dumps({"status": "PASS", "summary": str(SUMMARY_JSON)}, indent=2))


if __name__ == "__main__":
    main()
