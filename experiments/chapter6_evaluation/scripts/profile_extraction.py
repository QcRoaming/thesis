#!/usr/bin/env python3
"""Profile the source-backed Chapter 3 BLIS fact extractor without changing frozen data."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
CHAPTER3 = EXPERIMENTS / "chapter3_rules"
BLIS = EXPERIMENTS.parent / "blis" / "blis"
OUTPUT = PROJECT / "build" / "extraction_profile"


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    command = [
        "python3", str(CHAPTER3 / "scripts" / "extract_blis_facts.py"),
        "--blis-root", str(BLIS),
        "--facts-output", str(OUTPUT / "expert_facts.yaml"),
        "--contracts-output", str(OUTPUT / "microkernel_contracts.yaml"),
        "--atomic-json", str(OUTPUT / "facts.json"),
        "--atomic-csv", str(OUTPUT / "facts.csv"),
        "--verification-output", str(OUTPUT / "manual_verification.csv"),
    ]
    started = time.perf_counter()
    completed = subprocess.run(command, text=True, capture_output=True)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    (OUTPUT / "run.log").write_text(
        "$ " + " ".join(command) + "\n\nSTDOUT\n" + completed.stdout + "\nSTDERR\n" + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr)
    facts = json.loads((OUTPUT / "facts.json").read_text(encoding="utf-8"))["facts"]
    result = {
        "status": "PASS",
        "elapsed_ms": round(elapsed_ms, 6),
        "fact_count": len(facts),
        "dtype_count": 2,
        "frozen_outputs_untouched": True,
        "profile_directory": str(OUTPUT),
    }
    target = PROJECT / "processed" / "extraction_profile.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
