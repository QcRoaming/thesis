#!/usr/bin/env python3
"""Build the retained K230 external-validation package and refresh its registry entry."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT = SCRIPT_DIR.parent
WORKSPACE = PROJECT.parents[3]


def run(command: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


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
        "thesis.chapter6_external_validation",
    ], cwd=personal_os)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-registry", action="store_true")
    args = parser.parse_args()
    run([sys.executable, str(SCRIPT_DIR / "build_k230_external_package.py")])
    run([
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(PROJECT / "tests"),
        "-v",
    ])
    if not args.skip_registry:
        refresh_registry()


if __name__ == "__main__":
    main()
