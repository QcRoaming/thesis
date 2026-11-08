#!/usr/bin/env python3
"""Run the complete local CGO-strengthening experiment sequence."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT / "scripts"
WORKSPACE = PROJECT.parents[3]


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    print("$ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=PROJECT, check=True, env=env)


def refresh_registry() -> None:
    if os.environ.get("CGO_EXTENSION_SKIP_REGISTRY") == "1":
        print("[registry] skipped by CGO_EXTENSION_SKIP_REGISTRY=1", flush=True)
        return
    root = Path(
        os.environ.get("PERSONAL_OS_ROOT", "/root/personal-os/PersonalOS")
    ).expanduser()
    script = root / "scripts" / "experiment_registry.py"
    try:
        available = script.is_file()
    except OSError as error:
        print(f"[registry] skipped; cannot access {script}: {error}", flush=True)
        return
    if not available:
        print(f"[registry] skipped; script not found: {script}", flush=True)
        return
    subprocess.run([
        sys.executable, str(script), "refresh", "--workspace-root", str(WORKSPACE),
        "--completed-id", "thesis.cgo_local_extension",
    ], cwd=root, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    common = []
    if args.smoke:
        common.append("--smoke")
    if args.force:
        common.append("--force")
    run([sys.executable, str(SCRIPTS / "run_f64_contract.py"), *common])
    run([
        sys.executable, str(SCRIPTS / "run_true_online.py"), *common,
        "--skip-build",
    ])
    run([sys.executable, str(SCRIPTS / "run_optuna.py"), *common])
    run([
        sys.executable, str(SCRIPTS / "run_multisource_ablation.py"),
        *( ["--smoke"] if args.smoke else [] ),
    ])
    if not args.smoke:
        run([sys.executable, str(SCRIPTS / "analyze_extension.py")])
    test_env = os.environ.copy()
    test_env["CGO_EXTENSION_TEST_MODE"] = "smoke" if args.smoke else "formal"
    run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        env=test_env,
    )
    if not args.smoke:
        refresh_registry()


if __name__ == "__main__":
    main()
