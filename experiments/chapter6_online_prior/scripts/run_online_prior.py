#!/usr/bin/env python3
"""Reproduce the Chapter 6 online-prior extension end to end."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT / "scripts"
REPORTS = PROJECT / "reports"
TESTS = PROJECT / "tests"
WORKSPACE = PROJECT.parents[3]


def run(command: list[str], log_name: str) -> None:
    completed = subprocess.run(command, text=True, capture_output=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / log_name).write_text(
        "$ " + " ".join(command) + "\n\nSTDOUT\n" + completed.stdout
        + "\nSTDERR\n" + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(f"command failed: {' '.join(command)}\n{completed.stderr[-2000:]}")


def refresh_experiment_registry() -> None:
    personal_os = Path(os.environ.get("PERSONAL_OS_ROOT", "/root/personal-os/PersonalOS")).expanduser()
    registry = personal_os / "scripts" / "experiment_registry.py"
    if not registry.is_file():
        print(f"[registry] skipped; script not found: {registry}", flush=True)
        return
    subprocess.run(
        [
            sys.executable, str(registry), "refresh", "--workspace-root", str(WORKSPACE),
            "--completed-id", "thesis.chapter6_online_prior",
        ],
        cwd=personal_os,
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force-measure", action="store_true")
    parser.add_argument("--skip-measure", action="store_true")
    args = parser.parse_args()
    python = sys.executable
    if not args.skip_measure:
        command = [python, str(SCRIPTS / "measure_extended_corpus.py")]
        if args.force_measure:
            command.append("--force")
        run(command, "01_measure.log")
    run([python, str(SCRIPTS / "online_prior.py")], "02_calibrate.log")
    run(
        [python, "-m", "unittest", "discover", "-s", str(TESTS), "-v"],
        "03_tests.log",
    )
    refresh_experiment_registry()
    print((PROJECT / "processed" / "online_prior_summary.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
