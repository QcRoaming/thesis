#!/usr/bin/env python3
"""Verify the archived thesis evidence without rerunning hardware experiments."""

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FAILURES = []


def fail(message):
    FAILURES.append(message)
    print(f"FAIL {message}")


def check_manifest(relative_path):
    manifest = ROOT / relative_path
    if not manifest.is_file():
        fail(f"missing manifest: {relative_path}")
        return
    count = 0
    for line_number, line in enumerate(manifest.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            expected, name = line.split(maxsplit=1)
            name = name.lstrip("*")
            path = Path(name)
            if len(expected) != 64 or any(part == ".." for part in path.parts) or path.is_absolute():
                raise ValueError("invalid checksum entry")
            artifact = manifest.parent / path
            actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
            if actual != expected.lower():
                fail(f"checksum mismatch: {relative_path}:{line_number} ({name})")
            count += 1
        except (ValueError, OSError) as exc:
            fail(f"invalid or missing artifact: {relative_path}:{line_number} ({exc})")
    print(f"checked {relative_path}: {count} files")


def check_json_status(relative_path, expected_status="PASS", require_correct=False):
    try:
        data = json.loads((ROOT / relative_path).read_text())
        if data.get("status") != expected_status:
            fail(f"unexpected status in {relative_path}: {data.get('status')!r}")
        if require_correct and data.get("all_correct") is not True:
            fail(f"correctness flag is not true: {relative_path}")
    except (OSError, ValueError) as exc:
        fail(f"cannot read {relative_path}: {exc}")


def check_evidence_paths():
    relative_path = "experiments/data/paper_evidence_selection.json"
    try:
        entries = json.loads((ROOT / relative_path).read_text())["entries"]
        count = 0
        for entry in entries:
            for name in entry["evidence_files"]:
                path = Path(name)
                if path.parts[:2] != ("jlq", "thesis") or ".." in path.parts:
                    fail(f"invalid evidence path: {name}")
                    continue
                if not (ROOT.joinpath(*path.parts[2:])).is_file():
                    fail(f"missing evidence for {entry['id']}: {name}")
                count += 1
        print(f"checked evidence catalog: {len(entries)} entries, {count} file references")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        fail(f"cannot read evidence catalog: {exc}")


def main():
    pdf = ROOT / "nwputhesis/build/graduate.pdf"
    try:
        with pdf.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                fail("graduate.pdf has no PDF header")
        print(f"checked existing PDF: {pdf.relative_to(ROOT)}")
    except OSError as exc:
        fail(f"missing existing PDF: {exc}")

    check_evidence_paths()
    for path in (
        "compiler_snapshot/SHA256SUMS.txt",
        "experiments/x86_cross_host/results/thesis-x86-result--20260716T115026Z.tar.gz.sha256",
        "experiments/chapter6_external_validation/returned/i9/chapter6-i9-result-20260722T085806Z.tar.gz.sha256",
        "experiments/k230_rvv_backend/raw/board_results_20260716_rtsmart_valid/sha256sums.txt",
        "experiments/chapter6_external_validation/raw/k230_external/board_results_20260722T055157Z/sha256sums.txt",
        "experiments/chapter6_application_validation/raw/k230_mlir_closure/board_results_20260722T032147Z/sha256sums.txt",
    ):
        check_manifest(path)

    for path in (
        "experiments/processed/final_experiment_audit.json",
        "experiments/chapter6_external_validation/processed/i9_external_summary.json",
        "experiments/chapter6_external_validation/processed/k230_external_summary.json",
        "experiments/chapter6_application_validation/processed/k230_mlir_closure_summary.json",
    ):
        check_json_status(path)
    check_json_status(
        "experiments/k230_rvv_backend/processed/k230_board_summary.json",
        expected_status="board_results_imported",
        require_correct=True,
    )

    if FAILURES:
        print(f"verification failed: {len(FAILURES)} issue(s)")
        return 1
    print("PASS: thesis files and archived i9/K230 evidence are intact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
