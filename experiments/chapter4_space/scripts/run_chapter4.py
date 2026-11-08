#!/usr/bin/env python3
"""One-command reproduction driver for the Chapter 4 artifact package."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent
SCRIPT = PROJECT / "scripts"
PLOT_PYTHON = Path("/buddy-mlir/jlq/skills/.venv/bin/python")


def find_workspace(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "jlq" / "thesis" / "experiments").is_dir():
            return candidate
    raise RuntimeError("buddy-mlir workspace root not found")


WORKSPACE = find_workspace(PROJECT)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force-measurements", action="store_true", help="recompile and rerun native candidates")
    return parser.parse_args()


def run(name: str, command: list[str]) -> None:
    print(f"[{name}] {' '.join(command)}", flush=True)
    completed = subprocess.run(command, text=True, capture_output=True)
    log = PROJECT / "reports" / f"reproduce_{name}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        "$ " + " ".join(command) + "\n\nSTDOUT\n" + completed.stdout + "\nSTDERR\n" + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode:
        raise SystemExit(f"{name} failed; see {log}")


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
        "thesis.chapter4_space",
    ]
    print(f"[registry] {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=personal_os, check=True)


def main() -> None:
    args = parse_args()
    python = sys.executable
    force = ["--force"] if args.force_measurements else []
    steps = [
        ("spaces", [python, str(SCRIPT / "generate_spaces.py")]),
        ("transform", [python, str(SCRIPT / "run_transform_paths.py"), *force]),
    ]
    frozen_tuning = PROJECT / "processed" / "baco_tuning_summary.json"
    if args.force_measurements or not frozen_tuning.exists():
        steps.append(("baco", [python, str(SCRIPT / "run_baco_tuner.py"), *force]))
    else:
        print(f"[baco] reuse frozen complete tuning trace: {frozen_tuning}", flush=True)
    steps.extend(
        [
            ("tables", [python, str(SCRIPT / "build_tables.py")]),
            ("figures", [str(PLOT_PYTHON), str(SCRIPT / "plot_chapter4_figures.py")]),
            ("tests", [python, "-m", "unittest", "discover", "-s", str(PROJECT / "tests"), "-v"]),
            ("reports", [python, str(SCRIPT / "build_reports.py")]),
        ]
    )
    for name, command in steps:
        run(name, command)
    refresh_experiment_registry()
    print(f"Chapter 4 reproduction complete: {PROJECT}")


if __name__ == "__main__":
    main()
