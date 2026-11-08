#!/usr/bin/env python3
"""Import and summarize K230 OpenBLAS Contract-pool board results."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import shutil
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parents[3]

from run_k230_external_via_serial import protocol, validate_rows  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def geometric_mean(values: list[float]) -> float:
    return math.exp(sum(math.log(max(value, 1.0e-300)) for value in values) / len(values))


def cluster_bootstrap(
    values: dict[str, float], replicates: int = 20000
) -> tuple[float, float]:
    keys = sorted(values)
    rng = random.Random(20260722)
    samples: list[float] = []
    for _ in range(replicates):
        draw = [values[rng.choice(keys)] for _ in keys]
        samples.append(geometric_mean(draw))
    samples.sort()
    return samples[int(0.025 * replicates)], samples[int(0.975 * replicates)]


def refresh_registry(output_root: Path) -> None:
    if output_root != PROJECT:
        return
    personal_os = Path(
        os.environ.get("PERSONAL_OS_ROOT", "/root/personal-os/PersonalOS")
    ).expanduser()
    registry = personal_os / "scripts" / "experiment_registry.py"
    if not registry.is_file():
        print(f"[registry] skipped; script not found: {registry}", flush=True)
        return
    subprocess.run(
        [
            sys.executable,
            str(registry),
            "refresh",
            "--root",
            str(personal_os),
            "--workspace-root",
            str(WORKSPACE),
        ],
        cwd=PROJECT,
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--output-root", type=Path, default=PROJECT)
    args = parser.parse_args()
    source = args.result_dir.resolve()
    output_root = args.output_root.resolve()
    csv_path = source / "k230_openblas_contract_pool.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(csv_path)
    rows = read_csv(csv_path)
    required = {
        "variant", "candidate_id", "predicted_path", "workload_id", "m", "k", "n",
        "tile_m", "tile_n", "tile_k", "trial", "time_seconds", "gflops",
        "projection_error", "correct", "pack_a_seconds", "pack_b_seconds",
        "kernel_seconds", "scatter_seconds", "kernel_calls", "fringe_calls",
    }
    if not rows or not required.issubset(rows[0]):
        raise ValueError("K230 CSV schema is incomplete")
    if any(row["correct"] != "1" for row in rows):
        raise ValueError("K230 CSV contains a failed correctness row")
    if not args.allow_partial:
        validate_rows(
            rows,
            protocol(PROJECT / "processed" / "k230_candidate_matrix.json", 3),
        )

    expected_workloads = {
        row["id"]
        for row in json.loads(
            (PROJECT / "data" / "transformer_workloads.json").read_text(encoding="utf-8")
        )["workloads"]
    }
    observed_workloads = {row["workload_id"] for row in rows}
    if not args.allow_partial and observed_workloads != expected_workloads:
        raise ValueError(
            f"incomplete workload set: observed={sorted(observed_workloads)}, "
            f"expected={sorted(expected_workloads)}"
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = output_root / "raw" / "k230_external" / f"board_results_{stamp}"
    shutil.copytree(source, archive)

    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["workload_id"], row["variant"], row["candidate_id"])].append(row)
    aggregates: list[dict[str, Any]] = []
    for (workload_id, variant, candidate_id), values in sorted(grouped.items()):
        first = values[0]
        elapsed = [float(row["time_seconds"]) for row in values]
        pack = [float(row["pack_a_seconds"]) + float(row["pack_b_seconds"]) for row in values]
        kernel = [float(row["kernel_seconds"]) for row in values]
        scatter = [float(row["scatter_seconds"]) for row in values]
        median_elapsed = statistics.median(elapsed)
        trial_cv = (
            statistics.stdev(elapsed) / statistics.fmean(elapsed)
            if len(elapsed) > 1 else 0.0
        )
        aggregates.append({
            "workload_id": workload_id,
            "variant": variant,
            "candidate_id": candidate_id,
            "predicted_path": first["predicted_path"],
            "m": int(first["m"]), "k": int(first["k"]), "n": int(first["n"]),
            "tile_m": int(first["tile_m"]), "tile_n": int(first["tile_n"]),
            "tile_k": int(first["tile_k"]),
            "trials": len(values),
            "median_seconds": median_elapsed,
            "trial_cv": trial_cv,
            "median_gflops": statistics.median(float(row["gflops"]) for row in values),
            "median_pack_seconds": statistics.median(pack),
            "median_kernel_seconds": statistics.median(kernel),
            "median_scatter_seconds": statistics.median(scatter),
            "pack_fraction": statistics.median(pack) / median_elapsed if median_elapsed else 0.0,
            "kernel_fraction": statistics.median(kernel) / median_elapsed if median_elapsed else 0.0,
            "scatter_fraction": statistics.median(scatter) / median_elapsed if median_elapsed else 0.0,
            "kernel_calls": int(values[0]["kernel_calls"]),
            "fringe_calls": int(values[0]["fringe_calls"]),
        })

    by_workload: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in aggregates:
        by_workload[row["workload_id"]].append(row)
    summary_rows: list[dict[str, Any]] = []
    for workload_id, values in sorted(by_workload.items()):
        adapters = [row for row in values if row["variant"] == "contract_adapter"]
        baseline = next(row for row in values if row["variant"] == "openblas_full")
        best = min(adapters, key=lambda row: (row["median_seconds"], row["candidate_id"]))
        summary_rows.append({
            "workload_id": workload_id,
            "m": best["m"], "k": best["k"], "n": best["n"],
            "candidate_count": len(adapters),
            "best_candidate_id": best["candidate_id"],
            "best_tile_m": best["tile_m"], "best_tile_n": best["tile_n"],
            "best_tile_k": best["tile_k"],
            "best_predicted_path": best["predicted_path"],
            "best_adapter_seconds": best["median_seconds"],
            "openblas_seconds": baseline["median_seconds"],
            "adapter_relative_to_openblas": baseline["median_seconds"] / best["median_seconds"],
            "best_adapter_trial_cv": best["trial_cv"],
            "openblas_trial_cv": baseline["trial_cv"],
            "best_pack_fraction": best["pack_fraction"],
            "best_kernel_fraction": best["kernel_fraction"],
            "best_scatter_fraction": best["scatter_fraction"],
            "best_fringe_calls": best["fringe_calls"],
        })

    ratios_by_workload = {
        str(row["workload_id"]): float(row["adapter_relative_to_openblas"])
        for row in summary_rows
    }
    ratios = list(ratios_by_workload.values())
    lower, upper = cluster_bootstrap(ratios_by_workload)
    exact_qwen = [
        value for workload_id, value in ratios_by_workload.items()
        if "fringe" not in workload_id
    ]
    direct = [
        float(row["adapter_relative_to_openblas"])
        for row in summary_rows if row["best_predicted_path"] == "direct"
    ]
    adapt = [
        float(row["adapter_relative_to_openblas"])
        for row in summary_rows if row["best_predicted_path"] == "adapt"
    ]
    aggregate_cvs = [float(row["trial_cv"]) for row in aggregates]
    summary = {
        "schema_version": 2,
        "experiment_id": "thesis.chapter6_external_validation.k230_openblas",
        "status": "PASS",
        "workloads": len(summary_rows),
        "correctness_rows": len(rows),
        "adapter_relative_to_openblas_geomean": geometric_mean(ratios),
        "adapter_relative_to_openblas_ci95": [lower, upper],
        "exact_qwen_adapter_relative_to_openblas_geomean": geometric_mean(exact_qwen),
        "direct_adapter_relative_to_openblas_geomean": geometric_mean(direct),
        "adapt_adapter_relative_to_openblas_geomean": geometric_mean(adapt),
        "adapter_wins": sum(value > 1.0 for value in ratios),
        "direct_workloads": sum(row["best_predicted_path"] == "direct" for row in summary_rows),
        "adapt_workloads": sum(row["best_predicted_path"] == "adapt" for row in summary_rows),
        "measurement_groups": len(aggregates),
        "median_trial_cv": statistics.median(aggregate_cvs),
        "max_trial_cv": max(aggregate_cvs),
        "groups_trial_cv_over_5pct": sum(value > 0.05 for value in aggregate_cvs),
        "best_adapter_max_trial_cv": max(
            float(row["best_adapter_trial_cv"]) for row in summary_rows
        ),
        "openblas_max_trial_cv": max(
            float(row["openblas_trial_cv"]) for row in summary_rows
        ),
        "max_projection_error": max(float(row["projection_error"]) for row in rows),
        "source_csv_sha256": sha256(csv_path),
        "archived_result_dir": str(archive),
    }
    write_csv(output_root / "processed" / "k230_external_aggregates.csv", aggregates)
    write_csv(output_root / "processed" / "k230_external_summary.csv", summary_rows)
    write_json(output_root / "processed" / "k230_external_summary.json", summary)

    report = [
        "# K230 OpenBLAS external-backend results",
        "",
        f"- Status: **{summary['status']}**",
        f"- Workloads: {summary['workloads']}",
        "- Adapter / OpenBLAS geometric relative performance: "
        f"{summary['adapter_relative_to_openblas_geomean']:.4f} "
        f"(workload bootstrap 95% CI [{lower:.4f}, {upper:.4f}])",
        "- Exact-Qwen-shape adapter / OpenBLAS geometric relative performance: "
        f"{summary['exact_qwen_adapter_relative_to_openblas_geomean']:.4f}",
        f"- Median/max group trial CV: {summary['median_trial_cv']:.2%} / "
        f"{summary['max_trial_cv']:.2%}; groups above 5%: "
        f"{summary['groups_trial_cv_over_5pct']}",
        f"- Max best-adapter/OpenBLAS trial CV: "
        f"{summary['best_adapter_max_trial_cv']:.2%} / "
        f"{summary['openblas_max_trial_cv']:.2%}",
        f"- Max projection error: {summary['max_projection_error']:.3g}",
        "",
        "| Workload | Shape MxKxN | Best tile | Path | Adapter / OpenBLAS performance | Pack share |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for row in summary_rows:
        report.append(
            f"| {row['workload_id']} | {row['m']}x{row['k']}x{row['n']} | "
            f"{row['best_tile_m']}x{row['best_tile_n']}x{row['best_tile_k']} | "
            f"{row['best_predicted_path']} | {row['adapter_relative_to_openblas']:.4f} | "
            f"{row['best_pack_fraction']:.2%} |"
        )
    report.extend([
        "",
        "Relative performance is computed as OpenBLAS time divided by adapter time; values above "
        "1 mean that the generated Contract adapter is faster. The comparison uses complete "
        "single-thread OpenBLAS SGEMM. "
        "They are kernel-package measurements rather than end-to-end model latency.",
        "",
    ])
    report_path = output_root / "reports" / "k230_external_results.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report), encoding="utf-8")
    refresh_registry(output_root)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
