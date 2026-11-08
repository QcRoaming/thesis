#!/usr/bin/env python3
"""Generate generic, kernel-aware, and ablation GEMM candidate spaces."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from itertools import product
from pathlib import Path

from jlq.thesis.experiments.chapter3_rules.scripts.rulelib import (
    Candidate,
    assess_candidate,
    compatible_contract,
    load_contracts,
    load_tasks,
    load_yaml,
)


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "output"

SPACES = (
    "generic",
    "expert",
    "expert_remove_mr_nr",
    "expert_remove_cache_blocking",
    "expert_remove_packing",
    "expert_remove_compatibility_checker",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=DATA_DIR / "gemm_tasks.yaml")
    parser.add_argument(
        "--contracts", type=Path, default=DATA_DIR / "microkernel_contracts.yaml"
    )
    parser.add_argument("--rules", type=Path, default=DATA_DIR / "expert_rules.yaml")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "candidates.csv")
    parser.add_argument(
        "--summary", type=Path, default=OUTPUT_DIR / "space_summary.json"
    )
    parser.add_argument(
        "--spaces",
        nargs="+",
        choices=SPACES,
        default=list(SPACES),
        help="spaces to materialize",
    )
    return parser.parse_args()


def candidate_id(
    task_id: str,
    space: str,
    tile_m: int,
    tile_n: int,
    tile_k: int,
    pack: bool,
    vectorize: bool,
) -> str:
    return (
        f"{task_id}:{space}:{tile_m}x{tile_n}x{tile_k}:"
        f"p{int(pack)}:v{int(vectorize)}"
    )


def make_candidate(
    *,
    task,
    contract,
    space: str,
    tile_m: int,
    tile_n: int,
    tile_k: int,
    pack: bool,
    vectorize: bool,
    enforce_cache: bool,
    packing_adapter: bool,
    eligibility: str,
) -> Candidate:
    action, reason = assess_candidate(
        task,
        contract,
        tile_m=tile_m,
        tile_n=tile_n,
        tile_k=tile_k,
        pack_a=pack,
        pack_b=pack,
        vectorize=vectorize,
        enforce_cache=enforce_cache,
        packing_adapter=packing_adapter,
    )
    if eligibility == "all":
        eligible = True
    elif eligibility == "executable":
        eligible = action != "reject"
    elif eligibility == "kernel":
        eligible = action in {"direct", "adapt"}
    else:
        raise ValueError(f"unknown eligibility policy: {eligibility}")
    return Candidate(
        id=candidate_id(task.id, space, tile_m, tile_n, tile_k, pack, vectorize),
        task_id=task.id,
        space=space,
        tile_m=tile_m,
        tile_n=tile_n,
        tile_k=tile_k,
        micro_m=contract.mr,
        micro_n=contract.nr,
        pack_a=pack,
        pack_b=pack,
        vectorize=vectorize,
        kernel=contract.kernel if action in {"direct", "adapt"} else "generic_loop",
        action=action,
        reason=reason,
        tuner_eligible=eligible,
    )


def generate_for_task(task, contract, rules: dict, spaces: list[str]) -> list[Candidate]:
    baseline = rules["generic_baseline"]
    tile_m_values = [int(value) for value in baseline["tile_m"]]
    tile_n_values = [int(value) for value in baseline["tile_n"]]
    tile_k_values = [int(value) for value in baseline["tile_k"]]
    result: list[Candidate] = []

    if "generic" in spaces:
        for tile_m, tile_n, tile_k, packing, vectorize in product(
            tile_m_values,
            tile_n_values,
            tile_k_values,
            baseline["packing"],
            baseline["vectorize"],
        ):
            result.append(
                make_candidate(
                    task=task,
                    contract=contract,
                    space="generic",
                    tile_m=tile_m,
                    tile_n=tile_n,
                    tile_k=tile_k,
                    pack=packing == "ab",
                    vectorize=bool(vectorize),
                    enforce_cache=True,
                    packing_adapter=True,
                    eligibility="executable",
                )
            )

    variant_config = {
        "expert": (True, True, True, "kernel"),
        "expert_remove_mr_nr": (True, True, True, "executable"),
        "expert_remove_cache_blocking": (False, True, True, "kernel"),
        "expert_remove_packing": (True, False, False, "executable"),
        "expert_remove_compatibility_checker": (True, True, True, "all"),
    }
    for space, (enforce_cache, pack, packing_adapter, eligibility) in variant_config.items():
        if space not in spaces:
            continue
        for tile_m, tile_n, tile_k in product(
            tile_m_values, tile_n_values, tile_k_values
        ):
            result.append(
                make_candidate(
                    task=task,
                    contract=contract,
                    space=space,
                    tile_m=tile_m,
                    tile_n=tile_n,
                    tile_k=tile_k,
                    pack=pack,
                    vectorize=True,
                    enforce_cache=enforce_cache,
                    packing_adapter=packing_adapter,
                    eligibility=eligibility,
                )
            )
    return result


def build_summary(candidates: list[Candidate]) -> dict:
    grouped: dict[tuple[str, str], list[Candidate]] = {}
    for candidate in candidates:
        grouped.setdefault((candidate.task_id, candidate.space), []).append(candidate)
    rows = []
    for (task_id, space), items in sorted(grouped.items()):
        actions = Counter(item.action for item in items)
        rows.append(
            {
                "task_id": task_id,
                "space": space,
                "generated": len(items),
                "tuner_eligible": sum(item.tuner_eligible for item in items),
                **{action: actions[action] for action in ("direct", "adapt", "fallback", "reject")},
            }
        )
    return {"schema_version": 1, "spaces": rows}


def main() -> None:
    args = parse_args()
    tasks = load_tasks(args.tasks)
    contracts = load_contracts(args.contracts)
    rules = load_yaml(args.rules)
    candidates: list[Candidate] = []
    for task in tasks:
        contract = compatible_contract(task, contracts)
        candidates.extend(generate_for_task(task, contract, rules, args.spaces))
    if not candidates:
        raise SystemExit("no candidates generated")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(candidates[0].to_row())
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidate.to_row() for candidate in candidates)
    summary = build_summary(candidates)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(candidates)} candidates to {args.output}")
    print(f"wrote {args.summary}")


if __name__ == "__main__":
    main()
