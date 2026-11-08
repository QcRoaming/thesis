#!/usr/bin/env python3
"""Reproduce extraction, runtime validation and package tests."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent
WORKSPACE = PROJECT.parents[3]


def refresh_experiment_registry() -> None:
    personal_os = Path(os.environ.get("PERSONAL_OS_ROOT", "/root/personal-os/PersonalOS")).expanduser()
    registry = personal_os / "scripts" / "experiment_registry.py"
    if not registry.is_file():
        print(f"[registry] skipped; script not found: {registry}", flush=True)
        return
    subprocess.run(
        [
            sys.executable, str(registry), "refresh", "--workspace-root", str(WORKSPACE),
            "--completed-id", "thesis.chapter3_multisource",
        ],
        cwd=personal_os,
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-openblas-build", action="store_true")
    args = parser.parse_args()
    subprocess.run([sys.executable, str(PROJECT / "scripts/extract_multisource.py")], check=True)
    validate = [sys.executable, str(PROJECT / "scripts/validate_openblas.py")]
    if args.skip_openblas_build:
        validate.append("--skip-build")
    subprocess.run(validate, check=True)
    subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(PROJECT / "tests"), "-v"],
        check=True,
    )
    refresh_experiment_registry()


if __name__ == "__main__":
    main()
