#!/usr/bin/env python3
"""Validate manually returned K230 CSV files and summarize measurements."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent
WORKSPACE = PROJECT.parents[3]
EXPECTED_FILES = {
    "k230_gemm_scalar.csv": "scalar",
    "k230_gemm_rvv.csv": "rvv",
    "k230_gemm_openblas.csv": "openblas",
}
OPTIONAL_METADATA_FILES = (
    "linux_metadata.raw.log",
    "rtsmart_metadata.raw.log",
)
EXPERIMENT_ID = "thesis.k230_rvv_backend"
PAPER_SELECTION = WORKSPACE / "jlq" / "thesis" / "experiments" / "data" / "paper_evidence_selection.json"
PAPER_CATALOG_BUILDER = (
    WORKSPACE / "jlq" / "thesis" / "experiments" / "scripts" / "build_paper_evidence_catalog.py"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def geometric_mean(values: list[float]) -> float:
    if not values or any(value <= 0.0 for value in values):
        raise ValueError("geometric mean requires positive values")
    return math.exp(sum(math.log(value) for value in values) / len(values))


def build_comparisons(aggregates: list[dict[str, object]]) -> dict[str, object]:
    medians = {
        (str(row["binary"]), str(row["workload"]), str(row["candidate"])): float(
            row["median_gflops"]
        )
        for row in aggregates
    }
    rvv_workloads = sorted(
        workload
        for binary, workload, candidate in medians
        if binary == "rvv" and candidate == "scalar"
    )

    best_rvv_rows: list[dict[str, object]] = []
    winner_counts: dict[str, int] = {}
    for workload in rvv_workloads:
        scalar = medians[("rvv", workload, "scalar")]
        options = [
            (candidate, value)
            for (binary, row_workload, candidate), value in medians.items()
            if binary == "rvv" and row_workload == workload and candidate != "scalar"
        ]
        if not options:
            continue
        candidate, value = max(options, key=lambda item: item[1])
        winner_counts[candidate] = winner_counts.get(candidate, 0) + 1
        best_rvv_rows.append(
            {
                "workload": workload,
                "candidate": candidate,
                "median_gflops": value,
                "scalar_median_gflops": scalar,
                "speedup_vs_scalar": value / scalar,
            }
        )

    openblas_rows: list[dict[str, object]] = []
    for workload in rvv_workloads:
        full_key = ("openblas", workload, "openblas_full")
        scalar_key = ("openblas", workload, "scalar")
        if full_key not in medians or scalar_key not in medians:
            continue
        full = medians[full_key]
        scalar = medians[scalar_key]
        openblas_rows.append(
            {
                "workload": workload,
                "median_gflops": full,
                "scalar_median_gflops": scalar,
                "speedup_vs_scalar": full / scalar,
            }
        )

    candidate_transfer: list[dict[str, object]] = []
    rvv_candidates = sorted(
        {
            candidate
            for binary, _, candidate in medians
            if binary == "rvv" and candidate != "scalar"
        }
    )
    for candidate in rvv_candidates:
        ratios = [
            medians[("rvv", workload, candidate)] / medians[("rvv", workload, "scalar")]
            for workload in rvv_workloads
            if ("rvv", workload, candidate) in medians
        ]
        if not ratios:
            continue
        candidate_transfer.append(
            {
                "candidate": candidate,
                "workloads": len(ratios),
                "geomean_speedup_vs_scalar": geometric_mean(ratios),
                "wins_over_scalar": sum(ratio > 1.0 for ratio in ratios),
            }
        )

    return {
        "rvv_best_vs_scalar": {
            "workloads": len(best_rvv_rows),
            "geomean_speedup": (
                geometric_mean([float(row["speedup_vs_scalar"]) for row in best_rvv_rows])
                if best_rvv_rows else None
            ),
            "winner_counts": winner_counts,
            "by_workload": best_rvv_rows,
        },
        "openblas_full_vs_scalar": {
            "workloads": len(openblas_rows),
            "geomean_speedup": (
                geometric_mean([float(row["speedup_vs_scalar"]) for row in openblas_rows])
                if openblas_rows else None
            ),
            "by_workload": openblas_rows,
        },
        "rvv_candidate_transfer": candidate_transfer,
    }


def update_evidence_selection(summary: dict[str, object]) -> None:
    selection = json.loads(PAPER_SELECTION.read_text(encoding="utf-8"))
    entry = next(
        (row for row in selection["entries"] if row.get("id") == EXPERIMENT_ID),
        None,
    )
    if entry is None:
        raise RuntimeError(f"missing paper evidence selection entry: {EXPERIMENT_ID}")
    comparisons = summary["comparisons"]
    rvv_speedup = comparisons["rvv_best_vs_scalar"]["geomean_speedup"]
    openblas_speedup = comparisons["openblas_full_vs_scalar"]["geomean_speedup"]
    entry.update(
        {
            "tier": "supporting_main_text",
            "body_eligible": True,
            "recommended_sections": [
                "Cross-architecture K230 evaluation",
                "Discussion: transferable compatibility knowledge and calibrated performance priors",
            ],
            "decision": (
                "Physical K230 RT-Smart measurements are available for scalar, explicit-RVV "
                "and full OpenBLAS paths across eight workloads. Use as supporting "
                "cross-architecture evidence under the recorded board configuration."
            ),
            "usable_claims": [
                (
                    f"The physical K230 run produced {summary['row_count']} correct timing rows "
                    "across eight workloads, including non-divisible fringe shapes."
                ),
                (
                    "Selecting the best measured explicit-RVV candidate per workload achieved "
                    f"a {rvv_speedup:.2f}x geometric-mean speedup over its in-process scalar "
                    "control."
                ),
                (
                    "The complete OpenBLAS RISCV64_ZVL128B SGEMM path achieved a "
                    f"{openblas_speedup:.2f}x geometric-mean speedup over the in-process scalar "
                    "control."
                ),
                (
                    "No fixed source-derived schedule dominated all workloads; generic, "
                    "OpenBLAS-derived and cross-source candidates won different shapes, while "
                    "the BLIS-derived fixed candidate was not a reliable performance prior."
                ),
            ],
            "evidence_files": [
                "jlq/thesis/experiments/k230_rvv_backend/processed/k230_board_summary.json",
                "jlq/thesis/experiments/k230_rvv_backend/provenance/elf_manifest.json",
                "jlq/thesis/experiments/k230_rvv_backend/provenance/deployment_manifest.json",
                "jlq/thesis/experiments/k230_rvv_backend/reports/k230_elf_results.md",
            ],
        }
    )
    PAPER_SELECTION.write_text(
        json.dumps(selection, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    subprocess.run([sys.executable, str(PAPER_CATALOG_BUILDER)], cwd=WORKSPACE, check=True)


def refresh_experiment_registry(summary: dict[str, object]) -> None:
    personal_os = Path(os.environ.get("PERSONAL_OS_ROOT", "/root/personal-os/PersonalOS")).expanduser()
    registry = personal_os / "scripts" / "experiment_registry.py"
    if not registry.is_file():
        print(f"[registry] skipped; script not found: {registry}", flush=True)
        return
    registry_data_path = personal_os / "registries" / "experiments.json"
    registry_data = json.loads(registry_data_path.read_text(encoding="utf-8"))
    entry = next(
        (row for row in registry_data["entries"] if row.get("id") == EXPERIMENT_ID),
        None,
    )
    if entry is None:
        raise RuntimeError(f"missing PersonalOS experiment entry: {EXPERIMENT_ID}")
    entry.update(
        {
            "status": "complete_method_evidence",
            "claim_boundary": (
                "Physical K230 C908 RT-Smart results are available for the recorded scalar, "
                "explicit-RVV and complete OpenBLAS binaries across eight workloads. Claims "
                "are limited to this board, toolchain, runtime and harness; they do not "
                "establish universal RISC-V performance generalization."
            ),
            "evidence_files": [
                "jlq/thesis/experiments/k230_rvv_backend/processed/k230_board_summary.json",
                "jlq/thesis/experiments/k230_rvv_backend/provenance/elf_manifest.json",
                "jlq/thesis/experiments/k230_rvv_backend/provenance/deployment_manifest.json",
                "jlq/thesis/experiments/k230_rvv_backend/reports/k230_elf_results.md",
            ],
            "reproduce_command": (
                "python3 jlq/thesis/experiments/k230_rvv_backend/scripts/"
                "run_board_via_serial.py --port /dev/ttyACM1 --output-dir "
                "jlq/thesis/experiments/k230_rvv_backend/raw/board_results && "
                "python3 jlq/thesis/experiments/k230_rvv_backend/scripts/"
                "import_board_results.py "
                "jlq/thesis/experiments/k230_rvv_backend/raw/board_results"
            ),
            "automation": {
                "auto_refresh": True,
                "producer": (
                    "jlq/thesis/experiments/k230_rvv_backend/scripts/"
                    "import_board_results.py"
                ),
            },
        }
    )
    registry_data_path.write_text(
        json.dumps(registry_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    subprocess.run(
        [
            sys.executable, str(registry), "refresh", "--workspace-root", str(WORKSPACE),
            "--completed-id", EXPERIMENT_ID,
        ],
        cwd=personal_os,
        check=True,
    )


def summarize_results(result_dir: Path) -> dict[str, object]:
    result_dir = result_dir.resolve()
    missing = [name for name in EXPECTED_FILES if not (result_dir / name).is_file()]
    if missing:
        raise RuntimeError("missing K230 result files: " + ", ".join(missing))
    rows: list[dict[str, str]] = []
    input_files: list[dict[str, object]] = []
    for filename, binary_id in EXPECTED_FILES.items():
        path = result_dir / filename
        with path.open(newline="", encoding="utf-8") as stream:
            file_rows = list(csv.DictReader(stream))
        if not file_rows or any(row.get("binary") != binary_id for row in file_rows):
            raise RuntimeError(f"binary identity mismatch in {path}")
        rows.extend(file_rows)
        input_files.append({"path": str(path), "sha256": sha256(path), "rows": len(file_rows)})
    metadata_files = [
        {"path": str(result_dir / filename), "sha256": sha256(result_dir / filename)}
        for filename in OPTIONAL_METADATA_FILES
        if (result_dir / filename).is_file()
    ]
    if not rows:
        raise RuntimeError("no k230_gemm_*.csv board results found")
    if any(row["correct"] != "1" for row in rows):
        raise RuntimeError("K230 correctness failure in returned board results")
    if any(
        not math.isfinite(float(row["time_seconds"]))
        or not math.isfinite(float(row["gflops"]))
        or float(row["time_seconds"]) <= 0.0
        or float(row["gflops"]) <= 0.0
        for row in rows
    ):
        raise RuntimeError("non-finite or non-positive K230 timing result")
    grouped: dict[tuple[str, str, str], list[float]] = {}
    for row in rows:
        grouped.setdefault((row["binary"], row["workload"], row["candidate"]), []).append(float(row["gflops"]))
    aggregates = [
        {
            "binary": key[0], "workload": key[1], "candidate": key[2],
            "median_gflops": statistics.median(values), "trials": len(values),
        }
        for key, values in sorted(grouped.items())
    ]
    best_by_binary_workload: list[dict[str, object]] = []
    for binary in sorted({row["binary"] for row in aggregates}):
        for workload in sorted({row["workload"] for row in aggregates if row["binary"] == binary}):
            options = [
                row for row in aggregates
                if row["binary"] == binary and row["workload"] == workload
            ]
            best_by_binary_workload.append(max(options, key=lambda row: float(row["median_gflops"])))
    return {
        "schema_version": 1, "experiment_id": EXPERIMENT_ID,
        "status": "board_results_imported", "row_count": len(rows),
        "aggregate_count": len(aggregates), "all_correct": True,
        "input_files": input_files, "metadata_files": metadata_files,
        "aggregates": aggregates,
        "best_by_binary_workload": best_by_binary_workload,
        "comparisons": build_comparisons(aggregates),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_dir", type=Path)
    args = parser.parse_args()
    result_dir = args.result_dir.resolve()
    summary = summarize_results(result_dir)
    processed = PROJECT / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    summary_path = processed / "k230_board_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    manifest_path = PROJECT / "provenance" / "elf_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = summary["status"]
    manifest["board_results"] = {
        "directory": str(result_dir),
        "summary": str(summary_path),
        "summary_sha256": sha256(summary_path),
        "input_files": summary["input_files"],
        "metadata_files": summary["metadata_files"],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    subprocess.run(
        [sys.executable, str(PROJECT / "scripts" / "render_k230_report.py")],
        cwd=PROJECT,
        check=True,
    )
    update_evidence_selection(summary)
    refresh_experiment_registry(summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
