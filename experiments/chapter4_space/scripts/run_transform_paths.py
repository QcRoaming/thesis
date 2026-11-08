#!/usr/bin/env python3
"""Execute direct/adapt/fallback policy examples through real MLIR AOT."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from chapter4lib import (
    Candidate,
    PROJECT_DIR,
    check_candidate,
    load_inputs,
    select_contract,
    write_csv,
)
from transform_runner import evaluate_transform


CASES = [
    {
        "id": "direct_anchor",
        "task_id": "anchor_192x256x256_f32",
        "candidate": Candidate(24, 32, 64, "ab", True),
        "expected_path": "direct",
        "template": "contract_direct_schedule",
    },
    {
        "id": "adapt_mnk_tail",
        "task_id": "tail_190x250x250_f32",
        "candidate": Candidate(24, 32, 64, "ab", True),
        "expected_path": "adapt",
        "template": "finite_tail_adapt_schedule",
    },
    {
        "id": "fallback_feature_miss",
        "task_id": "feature_mismatch_192x256x256_f32",
        "candidate": Candidate(24, 32, 64, "none", False),
        "expected_path": "fallback",
        "template": "generic_fallback_schedule",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT_DIR)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project = args.project.resolve()
    inputs = load_inputs(project)
    tasks = {task["id"]: task for task in inputs["tasks"]}
    tuning = inputs["space_config"]["smoke_tuning"]
    rows = []
    for case in CASES:
        task = tasks[case["task_id"]]
        contract, _ = select_contract(task, inputs["contracts"])
        decision = check_candidate(case["candidate"], task, contract)
        if decision.path != case["expected_path"]:
            raise AssertionError(f"{case['id']}: expected {case['expected_path']}, got {decision.path}")
        print(f"[{case['id']}] predicted={decision.path}", flush=True)
        measured = evaluate_transform(
            task,
            case["candidate"],
            decision.path,
            case["template"],
            project / "build" / "transform_paths" / case["id"],
            warmups=int(tuning["warmups"]),
            repeats=int(tuning["repeats"]),
            inner_iters=int(tuning["inner_iters"]),
            force=args.force,
        )
        rows.append(
            {
                "case_id": case["id"],
                "task_id": task["id"],
                "template": case["template"],
                **case["candidate"].__dict__,
                "contract_id": contract["id"] if contract else None,
                "predicted_path": decision.path,
                "reason_codes": decision.reason_codes,
                "actions": decision.actions,
                **measured,
            }
        )
    write_csv(project / "raw" / "transform_paths.csv", rows)
    summary = {
        "case_count": len(rows),
        "compile_pass_count": sum(row["compile_status"] == "pass" for row in rows),
        "correctness_pass_count": sum(row["correctness_status"] == "pass" for row in rows),
        "predicted_path_counts": {path: sum(row["predicted_path"] == path for row in rows) for path in ("direct", "adapt", "fallback")},
        "observed_path_counts": {path: sum(row["observed_path"] == path for row in rows) for path in ("direct", "adapt", "fallback", "reject")},
        "observed_replacement_count": sum(bool(row["microkernel_replaced"]) for row in rows),
    }
    (project / "processed" / "transform_paths_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    report = [
        "# Chapter 4 Transform Path Validation",
        "",
        "The three rows exercise real parameterized Transform Dialect, lowering, LLVM IR translation, native compilation, execution, and correctness checking.",
        "",
        f"- Compile passes: **{summary['compile_pass_count']}/{summary['case_count']}**",
        f"- Correctness passes: **{summary['correctness_pass_count']}/{summary['case_count']}**",
        f"- Observed BLIS replacements: **{summary['observed_replacement_count']}**",
        "",
        "`predicted_path` is the Compatibility Checker result. `observed_path` is inferred from emitted LLVM IR.",
        "The current template materializes tiling/vectorization and finite loop-bound handling, but not BLIS panel packing or a BLIS call; therefore a predicted direct/adapt policy remains observed fallback.",
        "",
        "Raw measurements: `raw/transform_paths.csv`.",
        "Per-case IR, commands, logs, and manifests: `build/transform_paths/`.",
        "",
    ]
    (project / "reports" / "transform_path_validation.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
