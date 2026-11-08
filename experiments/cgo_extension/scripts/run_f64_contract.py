#!/usr/bin/env python3
"""Measure the full f64 Haswell dgemm 6x8 Contract-only corpus."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from cgo_common import (
    BUILD,
    PROJECT,
    PROCESSED,
    PROVENANCE,
    RAW,
    REPORTS,
    aggregate_trials,
    build_contract_state,
    compile_blis_frontend,
    compile_candidate,
    ensure_tools,
    geometric_mean,
    load_config,
    load_workloads,
    measure_live,
    read_csv,
    sha256,
    write_csv,
    write_json,
)


def trial_key(row: dict[str, Any]) -> tuple[str, str, int]:
    return str(row["workload_id"]), str(row["variant"]), int(row["trial"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()

    config = load_config()
    all_workloads = load_workloads()
    workloads = all_workloads
    if args.smoke:
        workloads = [
            next(row for row in all_workloads if row["id"] == "sq_096"),
            next(row for row in all_workloads if row["id"] == "tail_065x067x070"),
        ]
    ensure_tools(build_buddy=not args.skip_build)
    state = build_contract_state("f64", all_workloads, int(config["pool_size"]))

    pool_rows = []
    unique_candidates: dict[str, dict[str, Any]] = {}
    for workload in all_workloads:
        item = state[workload["id"]]
        for rank, row in enumerate(item["pool"], 1):
            pool_rows.append({
                "dtype": "f64",
                "workload_id": workload["id"],
                "family": workload["family"],
                "split": workload["split"],
                "rank": rank,
                **row,
            })
            unique_candidates[row["candidate_id"]] = row
    write_csv(PROCESSED / "f64_contract_pools.csv", pool_rows)
    write_json(PROCESSED / "f64_space_summary.json", {
        "workloads": len(all_workloads),
        "pool_size": int(config["pool_size"]),
        "raw_candidates_per_workload": len(next(iter(state.values()))["rows"]),
        "contract_candidates_per_workload": {
            workload_id: len(item["contract_rows"])
            for workload_id, item in state.items()
        },
        "selected_path_counts": dict(Counter(
            row["predicted_path"] for row in pool_rows
        )),
        "contract_ids": sorted({item["contract"]["id"] for item in state.values()}),
    })

    if args.smoke:
        selected_ids = {
            state["sq_096"]["pool"][0]["candidate_id"],
            state["tail_065x067x070"]["pool"][0]["candidate_id"],
        }
        unique_candidates = {
            candidate_id: row for candidate_id, row in unique_candidates.items()
            if candidate_id in selected_ids
        }

    manifests = {}
    for index, (candidate_id, row) in enumerate(sorted(unique_candidates.items()), 1):
        manifests[candidate_id] = compile_candidate(row, "f64", force=args.force)
        print(f"compiled f64 candidate {index}/{len(unique_candidates)}", flush=True)
    blis_manifest = compile_blis_frontend("f64", force=args.force)
    write_json(PROCESSED / ("f64_smoke_manifests.json" if args.smoke else "f64_manifests.json"), {
        "candidates": manifests,
        "B5_blis": blis_manifest,
    })

    trial_path = RAW / ("f64_smoke_trials.csv" if args.smoke else "f64_contract_trials.csv")
    existing = [] if args.force or not trial_path.exists() else read_csv(trial_path)
    completed = {trial_key(row) for row in existing}
    trials: list[dict[str, Any]] = list(existing)
    trial_count = 1 if args.smoke else int(config["measurement"]["independent_trials"])
    measurement = dict(config["measurement"])

    for workload in workloads:
        item = state[workload["id"]]
        members = item["pool"]
        if args.smoke:
            members = [members[0]]
        variants: list[tuple[str, dict[str, Any] | None, dict[str, Any]]] = [
            ("B5_blis", None, blis_manifest),
        ]
        variants.extend(
            ("candidate:" + row["candidate_id"], row, manifests[row["candidate_id"]])
            for row in members
        )
        for variant, row, manifest in variants:
            for trial in range(1, trial_count + 1):
                key = (workload["id"], variant, trial)
                if key in completed:
                    continue
                log = BUILD / "f64_measurements" / workload["id"] / variant.replace(":", "_") / f"trial_{trial:02d}.log"
                measured = measure_live(manifest, workload, measurement, log, row)
                record = {
                    "dtype": "f64",
                    "workload_id": workload["id"],
                    "family": workload["family"],
                    "split": workload["split"],
                    "m": workload["m"],
                    "k": workload["k"],
                    "n": workload["n"],
                    "variant": variant,
                    "trial": trial,
                    "candidate_id": row["candidate_id"] if row else None,
                    "predicted_path": row["predicted_path"] if row else "baseline",
                    "observed_path": measured.get("observed_path", "baseline"),
                    **measured,
                }
                record["prediction_matches_observation"] = (
                    row is None or record["predicted_path"] == record["observed_path"]
                )
                trials.append(record)
                completed.add(key)
        write_csv(trial_path, trials)
        print(f"measured f64 {workload['id']} ({len(trials)} trial rows)", flush=True)

    aggregates = aggregate_trials(trials)
    aggregate_path = PROCESSED / (
        "f64_smoke_aggregates.csv" if args.smoke else "f64_contract_aggregates.csv"
    )
    write_csv(aggregate_path, aggregates)
    by_workload: dict[str, list[dict[str, Any]]] = {}
    for row in aggregates:
        by_workload.setdefault(str(row["workload_id"]), []).append(row)
    best_rows = []
    for workload_id, rows in sorted(by_workload.items()):
        baseline = next(row for row in rows if row["variant"] == "B5_blis")
        candidates = [row for row in rows if str(row["variant"]).startswith("candidate:")]
        best = min(candidates, key=lambda row: float(row["median_ms"]))
        best_rows.append({
            "workload_id": workload_id,
            "family": best["family"],
            "split": best["split"],
            "best_candidate_id": best["candidate_id"],
            "best_candidate_ms": best["median_ms"],
            "blis_frontend_ms": baseline["median_ms"],
            "relative_to_blis": float(baseline["median_ms"]) / float(best["median_ms"]),
            "observed_path": best["observed_path"],
        })
    write_csv(PROCESSED / ("f64_smoke_best.csv" if args.smoke else "f64_best_by_workload.csv"), best_rows)

    summary = {
        "status": "PASS" if all(row["all_pass"] for row in aggregates) else "FAIL",
        "experiment_id": config["experiment_id"],
        "mode": "smoke" if args.smoke else "formal",
        "dtype": "f64",
        "contract": "haswell_f64_gemm_6x8",
        "workloads": len(workloads),
        "candidate_binaries": len(manifests),
        "trial_rows": len(trials),
        "aggregate_rows": len(aggregates),
        "predicted_paths": dict(Counter(
            row["predicted_path"] for row in trials if row["candidate_id"]
        )),
        "observed_paths": dict(Counter(
            row["observed_path"] for row in trials if row["candidate_id"]
        )),
        "all_predictions_match": all(
            bool(row["prediction_matches_observation"])
            for row in trials if row["candidate_id"]
        ),
        "relative_to_blis_gmean": geometric_mean(
            float(row["relative_to_blis"]) for row in best_rows
        ) if best_rows else None,
        "claim_boundary": config["claim_boundary"],
    }
    summary_path = PROCESSED / ("f64_smoke_summary.json" if args.smoke else "f64_contract_summary.json")
    write_json(summary_path, summary)

    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS / ("f64_smoke_results.md" if args.smoke else "f64_contract_results.md")
    report_path.write_text(
        "# f64 BLIS Contract Results\n\n"
        f"- mode: `{summary['mode']}`\n"
        f"- status: `{summary['status']}`\n"
        f"- contract: `{summary['contract']}`\n"
        f"- workloads: {summary['workloads']}\n"
        f"- candidate binaries: {summary['candidate_binaries']}\n"
        f"- trial rows: {summary['trial_rows']}\n"
        f"- observed paths: `{json.dumps(summary['observed_paths'], sort_keys=True)}`\n"
        f"- all checker predictions matched: `{summary['all_predictions_match']}`\n"
        f"- best-candidate/BLIS geometric ratio: {summary['relative_to_blis_gmean']:.3f}\n\n"
        "The ratio is `BLIS frontend time / best generated-candidate time`; values below 1 mean the full BLIS frontend is faster.\n\n"
        "## Claim boundary\n\n" + config["claim_boundary"] + "\n",
        encoding="utf-8",
    )
    manifest_path = PROVENANCE / ("f64_smoke_manifest.json" if args.smoke else "f64_manifest.json")
    write_json(manifest_path, {
        "schema_version": 1,
        "experiment_id": config["experiment_id"],
        "mode": summary["mode"],
        "python": sys.version,
        "platform": platform.platform(),
        "inputs": {
            str(PROJECT / "data" / "experiment_config.json"): sha256(PROJECT / "data" / "experiment_config.json"),
            str(PROJECT.parent / "chapter6_evaluation" / "data" / "workloads.json"): sha256(PROJECT.parent / "chapter6_evaluation" / "data" / "workloads.json"),
            str(PROJECT / "runtime" / "generic_matmul_bench.cpp"): sha256(PROJECT / "runtime" / "generic_matmul_bench.cpp"),
            str(PROJECT / "runtime" / "blis_microkernel_adapter.cpp"): sha256(PROJECT / "runtime" / "blis_microkernel_adapter.cpp"),
        },
        "outputs": {
            str(trial_path): sha256(trial_path),
            str(aggregate_path): sha256(aggregate_path),
            str(summary_path): sha256(summary_path),
            str(report_path): sha256(report_path),
        },
    })
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
