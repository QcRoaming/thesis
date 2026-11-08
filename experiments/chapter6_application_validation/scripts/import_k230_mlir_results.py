#!/usr/bin/env python3
"""Validate and summarize returned K230 MLIR closure measurements."""

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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def refresh_project_state(output_root: Path) -> None:
    if output_root != PROJECT:
        return
    subprocess.run(
        [sys.executable, str(PROJECT / "scripts" / "render_application_status.py")],
        cwd=PROJECT,
        check=True,
    )
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


def geometric_mean(values: list[float]) -> float:
    return math.exp(sum(math.log(max(value, 1.0e-300)) for value in values) / len(values))


def cluster_bootstrap(values: dict[str, float], replicates: int = 20000) -> tuple[float, float]:
    keys = sorted(values)
    rng = random.Random(20260719)
    samples: list[float] = []
    for _ in range(replicates):
        draw = [values[rng.choice(keys)] for _ in keys]
        samples.append(geometric_mean(draw))
    samples.sort()
    return samples[int(0.025 * replicates)], samples[int(0.975 * replicates)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir", type=Path)
    parser.add_argument("--output-root", type=Path, default=PROJECT)
    args = parser.parse_args()
    source = args.result_dir.resolve()
    output_root = args.output_root.resolve()
    csv_path = source / "k230_mlir_closure.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(csv_path)
    rows = read_csv(csv_path)
    required = {
        "variant", "case_id", "workload_id", "candidate_id", "expected_path",
        "m", "k", "n", "tile_m", "tile_n", "tile_k", "trial",
        "time_seconds", "gflops", "projection_error", "correct",
        "observed_path", "path_match", "kernel_calls", "fringe_calls",
        "k_tail_calls", "adapter_calls",
    }
    if not rows or not required.issubset(rows[0]):
        raise ValueError("K230 MLIR closure CSV schema is incomplete")
    if any(row["correct"] != "1" for row in rows):
        raise ValueError("K230 MLIR closure contains a correctness failure")

    cases_document = json.loads(
        (PROJECT / "data" / "k230_mlir_closure_cases.json").read_text(encoding="utf-8")
    )
    expected_cases = {row["id"] for row in cases_document["cases"]}
    expected_variants = {
        "c_adapter_direct", "mlir_transform_adapter", "openblas_full"
    }
    observed_cases = {row["case_id"] for row in rows}
    observed_variants = {row["variant"] for row in rows}
    if observed_cases != expected_cases:
        raise ValueError(f"case mismatch: {observed_cases} != {expected_cases}")
    if observed_variants != expected_variants:
        raise ValueError(f"variant mismatch: {observed_variants} != {expected_variants}")
    for row in rows:
        if row["variant"] != "openblas_full" and row["path_match"] != "1":
            raise ValueError(f"adapter path mismatch in {row['case_id']}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = output_root / "raw" / "k230_mlir_closure" / f"board_results_{stamp}"
    shutil.copytree(source, archive)

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["case_id"], row["variant"])].append(row)
    aggregates: list[dict[str, Any]] = []
    for (case_id, variant), values in sorted(grouped.items()):
        first = values[0]
        elapsed = [float(row["time_seconds"]) for row in values]
        aggregates.append({
            "case_id": case_id,
            "workload_id": first["workload_id"],
            "candidate_id": first["candidate_id"],
            "variant": variant,
            "expected_path": first["expected_path"],
            "observed_path": first["observed_path"],
            "m": int(first["m"]), "k": int(first["k"]), "n": int(first["n"]),
            "tile_m": int(first["tile_m"]), "tile_n": int(first["tile_n"]),
            "tile_k": int(first["tile_k"]),
            "trials": len(values),
            "median_seconds": statistics.median(elapsed),
            "mean_seconds": statistics.fmean(elapsed),
            "trial_cv": statistics.stdev(elapsed) / statistics.fmean(elapsed)
            if len(elapsed) > 1 else 0.0,
            "median_gflops": statistics.median(float(row["gflops"]) for row in values),
            "max_projection_error": max(float(row["projection_error"]) for row in values),
            "kernel_calls": int(first["kernel_calls"]),
            "fringe_calls": int(first["fringe_calls"]),
            "k_tail_calls": int(first["k_tail_calls"]),
        })

    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in aggregates:
        by_case[row["case_id"]].append(row)
    summaries: list[dict[str, Any]] = []
    parity: dict[str, float] = {}
    for case_id, values in sorted(by_case.items()):
        variants = {row["variant"]: row for row in values}
        direct = variants["c_adapter_direct"]
        mlir = variants["mlir_transform_adapter"]
        library = variants["openblas_full"]
        parity[case_id] = float(direct["median_seconds"]) / float(mlir["median_seconds"])
        summaries.append({
            "case_id": case_id,
            "workload_id": mlir["workload_id"],
            "shape": f"{mlir['m']}x{mlir['k']}x{mlir['n']}",
            "candidate_id": mlir["candidate_id"],
            "expected_path": mlir["expected_path"],
            "c_adapter_seconds": direct["median_seconds"],
            "mlir_adapter_seconds": mlir["median_seconds"],
            "openblas_seconds": library["median_seconds"],
            "c_adapter_over_mlir_adapter": parity[case_id],
            "mlir_adapter_relative_to_openblas": (
                float(library["median_seconds"]) / float(mlir["median_seconds"])
            ),
            "mlir_trial_cv": mlir["trial_cv"],
            "fringe_calls": mlir["fringe_calls"],
            "k_tail_calls": mlir["k_tail_calls"],
        })
    point = geometric_mean(list(parity.values()))
    lower, upper = cluster_bootstrap(parity)
    parity_pass = lower <= 1.0 <= upper or abs(point - 1.0) <= 0.05
    summary = {
        "schema_version": 1,
        "experiment_id": "thesis.chapter6_application_validation.k230_mlir_closure",
        "status": "PASS" if parity_pass else "BOUNDARY",
        "correctness_rows": len(rows),
        "cases": len(summaries),
        "variants": len(expected_variants),
        "c_adapter_over_mlir_adapter_geomean": point,
        "c_adapter_over_mlir_adapter_ci95": [lower, upper],
        "parity_acceptance": parity_pass,
        "mlir_adapter_relative_to_openblas_geomean": geometric_mean(
            [float(row["mlir_adapter_relative_to_openblas"]) for row in summaries]
        ),
        "source_csv_sha256": sha256(csv_path),
        "archived_result_dir": str(archive),
        "claim_boundary": json.loads(
            (PROJECT / "data" / "experiment_config.json").read_text(encoding="utf-8")
        )["claim_boundary"],
    }
    write_csv(output_root / "processed" / "k230_mlir_closure_aggregates.csv", aggregates)
    write_csv(output_root / "processed" / "k230_mlir_closure_summary.csv", summaries)
    write_json(output_root / "processed" / "k230_mlir_closure_summary.json", summary)

    report = [
        "# K230 MLIR/Transform closure results",
        "",
        f"- Status: **{summary['status']}**",
        f"- Correct rows: {summary['correctness_rows']}",
        "- C-adapter / MLIR-adapter geometric ratio: "
        f"{point:.4f} (cluster bootstrap 95% CI [{lower:.4f}, {upper:.4f}])",
        "- MLIR-adapter / complete-OpenBLAS geometric relative performance: "
        f"{summary['mlir_adapter_relative_to_openblas_geomean']:.4f}",
        "",
        "| Case | Shape | Path | C / MLIR time | MLIR / OpenBLAS performance | CV |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for row in summaries:
        report.append(
            f"| {row['case_id']} | {row['shape']} | {row['expected_path']} | "
            f"{row['c_adapter_over_mlir_adapter']:.4f} | "
            f"{row['mlir_adapter_relative_to_openblas']:.4f} | "
            f"{row['mlir_trial_cv']:.2%} |"
        )
    report.extend([
        "",
        "The C and MLIR variants call the same candidate-specific C-interface adapter, which reuses the frozen OpenBLAS packing and internal sgemm_kernel source. This is representative closure evidence, not a full-pool rerun.",
        "",
    ])
    report_path = output_root / "reports" / "k230_mlir_closure_results.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report), encoding="utf-8")
    refresh_project_state(output_root)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
