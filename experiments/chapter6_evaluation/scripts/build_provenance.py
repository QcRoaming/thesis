#!/usr/bin/env python3
"""Freeze Chapter 6 source, toolchain, host, and output provenance."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
REPO = EXPERIMENTS.parents[2]
OUTPUT = PROJECT / "provenance"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture(command: list[str]) -> str:
    completed = subprocess.run(command, text=True, capture_output=True)
    return (completed.stdout or completed.stderr).strip()


def record(path: Path) -> dict[str, object]:
    return {"path": str(path.relative_to(REPO)), "bytes": path.stat().st_size, "sha256": sha256(path)}


def main() -> None:
    source_paths = [
        PROJECT / "data" / "workloads.json",
        PROJECT / "data" / "experiment_config.json",
        EXPERIMENTS / "chapter3_rules" / "data" / "microkernel_contracts.yaml",
        EXPERIMENTS / "chapter3_rules" / "data" / "expert_rules.yaml",
        EXPERIMENTS / "chapter3_rules" / "verification" / "human_signoffs.json",
        EXPERIMENTS / "chapter4_space" / "scripts" / "chapter4lib.py",
        EXPERIMENTS / "chapter5_blis_adapter" / "runtime" / "blis_microkernel_adapter.cpp",
        REPO / "midend" / "lib" / "Conversion" / "MatMulOptimization" / "MatMulBlisMicrokernel.cpp",
    ]
    evidence_paths = [
        PROJECT / "processed" / "measurement_aggregates.csv",
        PROJECT / "processed" / "tuning_traces.csv",
        PROJECT / "processed" / "chapter6_summary.json",
        PROJECT / "reports" / "chapter6_results.md",
    ]
    baco = EXPERIMENTS.parent / "third_party" / "baco"
    manifest = {
        "schema_version": 1,
        "experiment_id": "thesis.chapter6_evaluation",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "host": {
            "uname": capture(["uname", "-a"]),
            "lscpu": capture(["lscpu"]),
        },
        "toolchain": {
            "clang": capture([str(REPO / "llvm" / "build" / "bin" / "clang++"), "--version"]),
            "mlir_opt": capture([str(REPO / "llvm" / "build" / "bin" / "mlir-opt"), "--version"]),
            "buddy_opt_sha256": sha256(REPO / "build" / "bin" / "buddy-opt"),
            "baco_commit": capture(["git", "-C", str(baco), "rev-parse", "HEAD"]),
            "blis_library_sha256": sha256(EXPERIMENTS.parent / "blis" / "blis" / "lib" / "haswell" / "libblis.a"),
        },
        "sources": [record(path) for path in source_paths],
        "evidence": [record(path) for path in evidence_paths],
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "manifest": str(OUTPUT / "manifest.json")}, indent=2))


if __name__ == "__main__":
    main()
