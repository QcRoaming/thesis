#!/usr/bin/env python3
"""Run static anchor, dynamic multi-shape statistics, tests, and registry refresh."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_chapter5 as base  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--skip-registry", action="store_true")
    args = parser.parse_args()

    scripts = base.PROJECT / "scripts"
    static_command = [sys.executable, str(scripts / "run_chapter5.py"), "--skip-registry"]
    dynamic_command = [
        sys.executable, str(scripts / "run_dynamic_multishape.py"),
        "--skip-build", "--skip-registry",
    ]
    if args.quick:
        static_command.extend(["--warmups", "1", "--repeats", "3"])
        dynamic_command.extend(["--trials", "1", "--repeats", "3"])

    base.run(static_command, base.REPORTS / "full_static.log")
    base.run(dynamic_command, base.REPORTS / "full_dynamic.log")
    base.run(
        [sys.executable, "-m", "unittest", "discover", "-s",
         str(base.PROJECT / "tests"), "-v"],
        base.REPORTS / "full_tests.log",
    )
    if not args.skip_registry:
        base.refresh_registry()
    print(json.dumps({
        "status": "PASS",
        "static_summary": str(base.PROCESSED / "chapter5_summary.json"),
        "dynamic_summary": str(base.PROCESSED / "dynamic_multishape_summary.json"),
    }, indent=2))


if __name__ == "__main__":
    main()
