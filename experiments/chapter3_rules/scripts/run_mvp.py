#!/usr/bin/env python3
"""Run the complete BLIS fact-to-search-space MVP."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "output"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("proxy", "native"), default="proxy")
    parser.add_argument("--budget", type=int, default=16)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--spaces",
        nargs="+",
        help="spaces passed to the tuner; default: all generated spaces",
    )
    return parser.parse_args()


def run(*arguments: str) -> None:
    subprocess.run([sys.executable, *arguments], cwd=PROJECT_DIR, check=True)


def main() -> None:
    args = parse_args()
    run(str(SCRIPT_DIR / "extract_blis_facts.py"))
    run(str(SCRIPT_DIR / "generate_candidates.py"))
    trace = OUTPUT_DIR / f"tuning_trace_{args.backend}.csv"
    tuning_summary = OUTPUT_DIR / f"tuning_summary_{args.backend}.md"
    tuner_args = [
        str(SCRIPT_DIR / "run_tuner.py"),
        "--backend",
        args.backend,
        "--budget",
        str(args.budget),
        "--seed",
        str(args.seed),
        "--output",
        str(trace),
        "--summary",
        str(tuning_summary),
    ]
    if args.spaces:
        tuner_args.extend(["--spaces", *args.spaces])
    run(*tuner_args)
    run(
        str(SCRIPT_DIR / "summarize_rules.py"),
        "--trace",
        str(trace),
        "--output",
        str(OUTPUT_DIR / f"mvp_report_{args.backend}.md"),
    )
    print(f"MVP complete: {OUTPUT_DIR / f'mvp_report_{args.backend}.md'}")


if __name__ == "__main__":
    main()
