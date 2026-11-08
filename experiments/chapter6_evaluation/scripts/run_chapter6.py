#!/usr/bin/env python3
"""One-command reproduction entry for the complete Chapter 6 evidence package."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
REPO = EXPERIMENTS.parents[2]
FIGURE_PYTHON = REPO / "jlq" / "skills" / ".venv" / "bin" / "python"
REPORTS = PROJECT / "reports"


def run(command: list[str], log_name: str) -> None:
    completed = subprocess.run(command, cwd=REPO, text=True, capture_output=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / log_name).write_text(
        "$ " + " ".join(command) + "\n\nSTDOUT\n" + completed.stdout + "\nSTDERR\n" + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(f"failed: {' '.join(command)}\n{completed.stderr[-2000:]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force-measurements", action="store_true")
    parser.add_argument("--force-tuning", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    python = sys.executable
    scripts = PROJECT / "scripts"
    run([python, str(scripts / "profile_extraction.py")], "01_extraction_profile.log")
    measurement = [python, str(scripts / "run_measurements.py")]
    if args.force_measurements:
        measurement.append("--force")
    if args.skip_build:
        measurement.append("--skip-build")
    run(measurement, "02_measurements.log")
    run([python, str(scripts / "run_measurements.py"), "--prepare-only", "--skip-build"], "03_refresh_pools.log")
    tuning = [python, str(scripts / "run_tuning.py"), "--suite", "all"]
    if args.force_tuning:
        tuning.append("--force")
    run(tuning, "04_tuning.log")
    run([python, str(scripts / "analyze_results.py")], "05_analysis.log")
    run([python, str(scripts / "build_provenance.py")], "06_provenance.log")
    run([str(FIGURE_PYTHON), str(scripts / "plot_chapter6_figures.py")], "07_figures.log")
    run([str(FIGURE_PYTHON), str(scripts / "qa_figures.py")], "08_figure_qa.log")
    run([python, "-m", "unittest", "discover", "-s", str(PROJECT / "tests"), "-v"], "09_tests.log")
    run([python, str(EXPERIMENTS / "scripts" / "build_paper_evidence_catalog.py")], "10_paper_catalog.log")
    registry = Path("/root/personal-os/PersonalOS")
    run([
        python, str(registry / "scripts" / "experiment_registry.py"), "refresh",
        "--workspace-root", str(REPO), "--completed-id", "thesis.chapter6_evaluation",
    ], "11_registry_refresh.log")
    print(json.dumps({
        "status": "PASS",
        "summary": str(PROJECT / "processed" / "chapter6_summary.json"),
        "report": str(PROJECT / "reports" / "chapter6_results.md"),
        "figures": str(PROJECT / "figures"),
    }, indent=2))


if __name__ == "__main__":
    main()
