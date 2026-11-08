#!/usr/bin/env python3
"""Build pinned OpenBLAS Haswell and validate its public SGEMM path."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import subprocess
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
THESIS_DIR = PROJECT_DIR.parents[1]
DEFAULT_OPENBLAS = THESIS_DIR / "third_party" / "OpenBLAS"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openblas-root", type=Path, default=DEFAULT_OPENBLAS)
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    openblas = args.openblas_root.resolve()
    library = openblas / "libopenblas.a"
    build_command = [
        "make",
        "TARGET=HASWELL",
        "DYNAMIC_ARCH=0",
        "NOFORTRAN=1",
        "NO_LAPACK=1",
        "ONLY_CBLAS=1",
        "BUILD_SINGLE=1",
        "USE_THREAD=0",
        "NUM_THREADS=1",
        "-j8",
    ]
    if not args.skip_build:
        run(build_command, openblas)
    if not library.is_file():
        raise FileNotFoundError(f"OpenBLAS static library was not produced: {library}")

    build_dir = PROJECT_DIR / "build" / "openblas_haswell"
    raw_dir = PROJECT_DIR / "raw"
    processed_dir = PROJECT_DIR / "processed"
    report_dir = PROJECT_DIR / "reports"
    provenance_dir = PROJECT_DIR / "provenance"
    for directory in (build_dir, raw_dir, processed_dir, report_dir, provenance_dir):
        directory.mkdir(parents=True, exist_ok=True)
    source = PROJECT_DIR / "runtime" / "openblas_sgemm_probe.c"
    executable = build_dir / "openblas_sgemm_probe"
    compile_command = [
        "gcc", "-O3", "-march=haswell", str(source), "-I", str(openblas),
        str(library), "-lm", "-lpthread", "-o", str(executable),
    ]
    run(compile_command)
    raw_csv = raw_dir / "openblas_validation.csv"
    print("+", executable, ">", raw_csv, flush=True)
    result = subprocess.run([str(executable)], check=True, text=True, capture_output=True)
    raw_csv.write_text(result.stdout, encoding="utf-8")

    with raw_csv.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows or any(row["correct"] != "1" for row in rows):
        raise RuntimeError("OpenBLAS correctness validation failed")
    grouped: dict[tuple[int, int, int], list[float]] = {}
    for row in rows:
        key = (int(row["m"]), int(row["n"]), int(row["k"]))
        grouped.setdefault(key, []).append(float(row["gflops"]))
    shape_rows = [
        {
            "m": key[0], "n": key[1], "k": key[2],
            "median_gflops": statistics.median(values),
            "trial_count": len(values), "correct": True,
        }
        for key, values in sorted(grouped.items())
    ]
    summary = {
        "schema_version": 1,
        "experiment_id": "thesis.chapter3_multisource.openblas_runtime",
        "status": "pass",
        "library": str(library),
        "library_sha256": sha256(library),
        "source_revision": subprocess.check_output(
            ["git", "-C", str(openblas), "rev-parse", "HEAD"], text=True
        ).strip(),
        "build_command": build_command,
        "compile_command": compile_command,
        "shape_count": len(shape_rows),
        "trial_count": len(rows),
        "correct_count": len(rows),
        "shapes": shape_rows,
    }
    summary_path = processed_dir / "openblas_validation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    report_lines = [
        "# OpenBLAS Runtime Validation", "",
        f"Pinned OpenBLAS `{summary['source_revision']}` was built as a single-thread "
        "Haswell static library. All 4 shapes and 28 timed rows passed the independent "
        "reference check.", "",
        "| M x N x K | Median GFLOP/s | Correct |", "|---|---:|---|",
    ]
    for row in shape_rows:
        report_lines.append(
            f"| {row['m']} x {row['n']} x {row['k']} | {row['median_gflops']:.3f} | pass |"
        )
    report_lines.extend([
        "", "These host measurements validate the extracted OpenBLAS source and public "
        "SGEMM execution path. They are not used as K230 performance results.",
    ])
    report_path = report_dir / "openblas_runtime_validation.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "inputs": {str(source): sha256(source), str(library): sha256(library)},
        "outputs": {
            str(executable): sha256(executable), str(raw_csv): sha256(raw_csv),
            str(summary_path): sha256(summary_path), str(report_path): sha256(report_path),
        },
        "commands": {"build": build_command, "compile": compile_command},
    }
    (provenance_dir / "openblas_validation_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
