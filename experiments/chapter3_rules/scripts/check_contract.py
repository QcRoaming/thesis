#!/usr/bin/env python3
"""Classify one GEMM schedule as direct/adapt/fallback/reject."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from jlq.thesis.experiments.chapter3_rules.scripts.rulelib import assess_candidate, compatible_contract, load_contracts, load_tasks


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=DATA_DIR / "gemm_tasks.yaml")
    parser.add_argument(
        "--contracts", type=Path, default=DATA_DIR / "microkernel_contracts.yaml"
    )
    parser.add_argument("--task-id", default="matmul_aligned_192x256x256_f32")
    parser.add_argument("--tile-m", type=int, required=True)
    parser.add_argument("--tile-n", type=int, required=True)
    parser.add_argument("--tile-k", type=int, required=True)
    parser.add_argument("--packing", choices=("none", "ab"), default="ab")
    parser.add_argument("--no-vectorize", action="store_true")
    parser.add_argument("--ignore-cache-bounds", action="store_true")
    parser.add_argument("--disable-packing-adapter", action="store_true")
    parser.add_argument("--fail-on-reject", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = load_tasks(args.tasks)
    try:
        task = next(task for task in tasks if task.id == args.task_id)
    except StopIteration as exc:
        raise SystemExit(f"unknown task: {args.task_id}") from exc
    contract = compatible_contract(task, load_contracts(args.contracts))
    packed = args.packing == "ab"
    action, reason = assess_candidate(
        task,
        contract,
        tile_m=args.tile_m,
        tile_n=args.tile_n,
        tile_k=args.tile_k,
        pack_a=packed,
        pack_b=packed,
        vectorize=not args.no_vectorize,
        enforce_cache=not args.ignore_cache_bounds,
        packing_adapter=not args.disable_packing_adapter,
    )
    result = {
        "task": task.id,
        "contract": contract.id,
        "candidate": {
            "tile_m": args.tile_m,
            "tile_n": args.tile_n,
            "tile_k": args.tile_k,
            "packing": args.packing,
            "vectorize": not args.no_vectorize,
        },
        "action": action,
        "reason": reason,
        "kernel": contract.kernel if action in {"direct", "adapt"} else "generic_loop",
    }
    print(yaml.safe_dump(result, sort_keys=False), end="")
    if args.fail_on_reject and action == "reject":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
