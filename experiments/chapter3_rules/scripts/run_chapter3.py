#!/usr/bin/env python3
"""Reproduce every automated chapter 3 artifact in dependency order."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent


def find_workspace(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "llvm" / "build" / "bin" / "mlir-opt").exists():
            return candidate
    raise RuntimeError("workspace MLIR toolchain not found")


WORKSPACE = find_workspace(PROJECT_DIR)
RSCRIPT = Path("/usr/bin/Rscript")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-measurements", action="store_true")
    parser.add_argument("--force-measurements", action="store_true")
    parser.add_argument("--skip-figures", action="store_true")
    return parser.parse_args()


def run(python: Path, script: str, *arguments: str) -> None:
    command = [str(python), str(SCRIPT_DIR / script), *arguments]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=PROJECT_DIR, check=True)


def run_r(script: str, *arguments: str) -> None:
    if not RSCRIPT.is_file():
        raise FileNotFoundError(f"required R figure runtime is missing: {RSCRIPT}")
    command = [str(RSCRIPT), str(SCRIPT_DIR / script), *arguments]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=PROJECT_DIR, check=True)


def refresh_experiment_registry() -> None:
    personal_os = Path(
        os.environ.get("PERSONAL_OS_ROOT", "/root/personal-os/PersonalOS")
    ).expanduser()
    registry = personal_os / "scripts" / "experiment_registry.py"
    if not registry.is_file():
        print(f"[registry] skipped; script not found: {registry}", flush=True)
        return
    command = [
        sys.executable,
        str(registry),
        "refresh",
        "--workspace-root",
        str(WORKSPACE),
        "--completed-id",
        "thesis.chapter3_rules",
    ]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=personal_os, check=True)


def main() -> None:
    args = parse_args()
    python = Path(sys.executable)
    run(python, "extract_blis_facts.py")
    run(python, "resolve_rules.py")
    run(python, "validate_artifacts.py")
    if not args.skip_measurements:
        measurement_args = ("--force",) if args.force_measurements else ()
        run(python, "run_preliminary_mlir.py", *measurement_args)
    run(python, "build_chapter3_artifacts.py")
    if not args.skip_figures:
        run_r("plot_chapter3_figures.R")
    run(python, "build_chapter3_artifacts.py")
    run(python, "validate_artifacts.py")
    refresh_experiment_registry()
    print(f"Chapter 3 artifacts complete: {PROJECT_DIR / 'chapter3_artifact_index.md'}")


if __name__ == "__main__":
    main()
