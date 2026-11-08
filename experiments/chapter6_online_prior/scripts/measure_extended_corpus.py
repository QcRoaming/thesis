#!/usr/bin/env python3
"""Measure full Contract-only pools missing from the frozen Chapter 6 corpus."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
CHAPTER6 = EXPERIMENTS / "chapter6_evaluation"
CHAPTER6_SCRIPTS = CHAPTER6 / "scripts"
sys.path.insert(0, str(CHAPTER6_SCRIPTS))

from chapter6lib import build_space_state, load_config  # noqa: E402
from run_measurements import (  # noqa: E402
    aggregate_trials,
    compile_dynamic,
    measure_executable,
    write_csv,
    write_json,
)


RAW = PROJECT / "raw"
PROCESSED = PROJECT / "processed"
BUILD = PROJECT / "build"
SOURCE_AGGREGATES = CHAPTER6 / "processed" / "measurement_aggregates.csv"


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def pool_map(state: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        workload_id: {row["candidate_id"]: row for row in item["pools"]["B2"]}
        for workload_id, item in state.items()
    }


def combine_corpus(
    workloads: list[dict[str, Any]], pools: dict[str, dict[str, dict[str, Any]]],
    extension: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source = read_csv(SOURCE_AGGREGATES)
    source_lookup = {
        (row["workload_id"], row["candidate_id"]): row
        for row in source if row["variant"].startswith("candidate:")
    }
    extension_lookup = {
        (row["workload_id"], row["candidate_id"]): row for row in extension
    }
    baselines = {
        row["workload_id"]: row for row in source if row["variant"] == "B5_blis"
    }
    combined: list[dict[str, Any]] = []
    for workload in workloads:
        workload_id = workload["id"]
        if workload_id not in baselines:
            raise KeyError(f"missing B5 baseline for {workload_id}")
        for candidate_id in sorted(pools[workload_id]):
            key = (workload_id, candidate_id)
            row = extension_lookup.get(key) or source_lookup.get(key)
            if row is None:
                raise KeyError(f"missing real measurement for {workload_id}/{candidate_id}")
            if str(row["all_pass"]).lower() != "true":
                raise RuntimeError(f"non-passing measurement for {workload_id}/{candidate_id}")
            combined.append({
                **row,
                "b5_median_ms": baselines[workload_id]["median_ms"],
                "pool_source": "extended" if key in extension_lookup else "chapter6_frozen",
            })
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()

    for directory in (RAW, PROCESSED, BUILD):
        directory.mkdir(parents=True, exist_ok=True)

    config, workloads = load_config()
    _, state = build_space_state(workloads, config)
    pools = pool_map(state)
    non_tuning = [row for row in workloads if not row["tune"]]
    unique_rows: dict[str, dict[str, Any]] = {}
    for workload in non_tuning:
        unique_rows.update(pools[workload["id"]])

    plan = {
        "status": "PREPARED" if args.prepare_only else "RUNNING",
        "workload_count": len(non_tuning),
        "cases": len(non_tuning) * int(config["pool_size"]),
        "unique_candidate_binaries": len(unique_rows),
        "source_chapter6_aggregates": str(SOURCE_AGGREGATES),
    }
    write_json(PROCESSED / "extended_measurement_plan.json", plan)
    if args.prepare_only:
        print(json.dumps(plan, indent=2))
        return

    manifests: dict[str, dict[str, Any]] = {}
    for index, (candidate_id, row) in enumerate(sorted(unique_rows.items()), 1):
        manifests[candidate_id] = compile_dynamic(
            candidate_id, row, config, args.force and not args.skip_build
        )
        if index % 25 == 0:
            print(f"prepared {index}/{len(unique_rows)} candidate binaries", flush=True)

    trial_rows: list[dict[str, Any]] = []
    for workload in non_tuning:
        workload_id = workload["id"]
        for candidate_id, row in sorted(pools[workload_id].items()):
            for trial in range(1, int(config["measurement"]["independent_trials"]) + 1):
                trial_rows.append(measure_executable(
                    manifests[candidate_id], workload, config["measurement"],
                    "candidate:" + candidate_id, trial, row,
                ))
        print(f"measured {workload_id}: {len(pools[workload_id])} candidates", flush=True)

    write_csv(RAW / "extended_measurement_trials.csv", trial_rows)
    extension = aggregate_trials(trial_rows)
    write_csv(PROCESSED / "extended_measurement_aggregates.csv", extension)
    combined = combine_corpus(workloads, pools, extension)
    write_csv(PROCESSED / "calibration_corpus.csv", combined)
    summary = {
        "status": "PASS",
        "workload_count": len(workloads),
        "extended_workload_count": len(non_tuning),
        "contract_cases": len(combined),
        "extended_cases": len(extension),
        "trial_rows": len(trial_rows),
        "all_pass": all(str(row["all_pass"]).lower() == "true" for row in combined),
        "all_predictions_match": all(
            str(row["all_predictions_match"]).lower() == "true" for row in combined
        ),
        "split_case_counts": {
            split: sum(row["split"] == split for row in combined)
            for split in ("design", "validation", "holdout")
        },
    }
    write_json(PROCESSED / "extended_measurement_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
