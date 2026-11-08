#!/usr/bin/env python3
"""Run all host-side application-validation generation and checks."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT / "scripts"
WORKSPACE = PROJECT.parents[3]


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=PROJECT, check=True)


def refresh_registry() -> None:
    personal_os = Path(
        os.environ.get("PERSONAL_OS_ROOT", "/root/personal-os/PersonalOS")
    ).expanduser()
    registry = personal_os / "scripts" / "experiment_registry.py"
    if not registry.is_file():
        print(f"[registry] skipped; script not found: {registry}", flush=True)
        return
    run([
        sys.executable,
        str(registry),
        "refresh",
        "--root",
        str(personal_os),
        "--workspace-root",
        str(WORKSPACE),
        "--completed-id",
        "thesis.chapter6_application_validation",
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-k230-build", action="store_true")
    parser.add_argument("--run-local-x86", action="store_true")
    parser.add_argument("--run-local-qualification", action="store_true")
    parser.add_argument("--cpu", type=int)
    parser.add_argument("--skip-registry", action="store_true")
    args = parser.parse_args()
    python = sys.executable
    run([python, str(SCRIPTS / "extract_qwen_shape_trace.py")])
    if not args.skip_k230_build:
        run([python, str(SCRIPTS / "build_k230_mlir_closure.py")])
    if args.run_local_x86:
        local_command = [python, str(SCRIPTS / "run_local_x86_trace_pool.py")]
        if args.cpu is not None:
            local_command.extend(["--cpu", str(args.cpu)])
        run(local_command)
    if args.run_local_qualification:
        run([python, str(SCRIPTS / "qualify_local_x86_measurement.py")])
    weighted = [python, str(SCRIPTS / "analyze_trace_weighted_results.py")]
    local_root = PROJECT / "targets" / "i7_10750h"
    if (local_root / "processed" / "summary.json").is_file():
        local_summary = json.loads(
            (local_root / "processed" / "summary.json").read_text(encoding="utf-8")
        )
        if local_summary.get("status") == "PASS":
            weighted.extend(["--local-x86-root", str(local_root)])
    run(weighted)
    run([python, str(SCRIPTS / "render_application_status.py")])
    run([python, "-m", "unittest", "discover", "-s", "tests", "-v"])
    if not args.skip_registry:
        refresh_registry()


if __name__ == "__main__":
    main()
