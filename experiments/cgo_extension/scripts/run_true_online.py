#!/usr/bin/env python3
"""Run a genuine select-execute-update loop on holdout workloads."""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np

from cgo_common import (
    BUILD,
    CHAPTER6,
    ONLINE_PRIOR,
    PROCESSED,
    PROVENANCE,
    PROJECT,
    RAW,
    REPORTS,
    build_contract_state,
    compile_blis_frontend,
    compile_candidate,
    ensure_tools,
    geometric_mean,
    load_config,
    load_workloads,
    measure_live,
    read_csv,
    read_json,
    sha256,
    write_csv,
    write_json,
)

sys.path.insert(0, str(ONLINE_PRIOR / "scripts"))
from online_prior import (  # noqa: E402
    FeatureSpace,
    choose_candidate,
    fit_posterior,
    raw_feature_names,
    raw_features,
)


METHODS = (
    "C0_random",
    "C1_static_blis",
    "C2_offline_calibrated",
    "C3_online_calibrated",
)


def prepare_context() -> dict[str, Any]:
    config = load_config()
    workloads = load_workloads()
    workload_map = {row["id"]: row for row in workloads}
    state = build_contract_state("f32", workloads, int(config["pool_size"]))
    corpus_path = ONLINE_PRIOR / "processed" / "calibration_corpus.csv"
    corpus = read_csv(corpus_path)
    if len(corpus) != len(workloads) * int(config["pool_size"]):
        raise ValueError("frozen calibration corpus is incomplete")
    by_workload: dict[str, list[int]] = {}
    for index, row in enumerate(corpus):
        candidate = state[row["workload_id"]]["rows"][row["candidate_id"]]
        row["static_score"] = float(candidate["score"])
        by_workload.setdefault(row["workload_id"], []).append(index)
    for workload_id, indices in by_workload.items():
        corpus_ids = {corpus[index]["candidate_id"] for index in indices}
        generated_ids = {row["candidate_id"] for row in state[workload_id]["pool"]}
        if corpus_ids != generated_ids:
            raise ValueError(f"candidate pool drift for {workload_id}")

    raw_x = np.vstack([raw_features(row, state, workload_map) for row in corpus])
    y = np.log(np.asarray([
        float(row["median_ms"]) / float(row["b5_median_ms"]) for row in corpus
    ]))
    design_mask = np.asarray([row["split"] == "design" for row in corpus])
    feature_space = FeatureSpace.fit(raw_feature_names(), raw_x[design_mask])
    x = feature_space.transform(raw_x)
    prior_summary = read_json(
        ONLINE_PRIOR / "processed" / "online_prior_summary.json"
    )
    selected = prior_summary["selected_hyperparameters"]
    posterior = fit_posterior(
        x[design_mask], y[design_mask], float(selected["prior_precision"]), 0.0001
    )
    return {
        "config": config,
        "workloads": workloads,
        "workload_map": workload_map,
        "state": state,
        "corpus": corpus,
        "by_workload": by_workload,
        "x": x,
        "y": y,
        "posterior": posterior,
        "temperature": float(selected["thompson_temperature"]),
        "feature_count": x.shape[1],
        "design_cases": int(np.sum(design_mask)),
    }


def compile_holdout_pool(context: dict[str, Any], workload_ids: list[str], force: bool) -> dict[str, Any]:
    unique: dict[str, dict[str, Any]] = {}
    for workload_id in workload_ids:
        for row in context["state"][workload_id]["pool"]:
            unique[row["candidate_id"]] = row
    manifests = {}
    for index, (candidate_id, row) in enumerate(sorted(unique.items()), 1):
        manifests[candidate_id] = compile_candidate(row, "f32", force=force)
        print(f"compiled online candidate {index}/{len(unique)}", flush=True)
    return manifests


def measure_baselines(
    context: dict[str, Any], workload_ids: list[str], force: bool, smoke: bool,
) -> dict[str, float]:
    path = RAW / ("true_online_smoke_b5.csv" if smoke else "true_online_b5.csv")
    if path.exists() and not force:
        existing = read_csv(path)
    else:
        existing = []
    by_id = {row["workload_id"]: row for row in existing}
    manifest = compile_blis_frontend("f32", force=force)
    measurement = context["config"]["measurement"]
    for workload_id in workload_ids:
        if workload_id in by_id:
            continue
        workload = context["workload_map"][workload_id]
        samples = []
        trial_count = 1 if smoke else int(measurement["independent_trials"])
        for trial in range(1, trial_count + 1):
            samples.append(measure_live(
                manifest, workload, measurement,
                BUILD / "true_online" / "b5" / workload_id / f"trial_{trial:02d}.log",
            ))
        row = {
            "workload_id": workload_id,
            "trials": trial_count,
            "median_ms": float(np.median([sample["median_ms"] for sample in samples])),
            "executable_sha256": manifest["executable_sha256"],
            "all_pass": all(sample["status"] == "PASS" for sample in samples),
        }
        existing.append(row)
        by_id[workload_id] = row
        write_csv(path, existing)
    return {workload_id: float(by_id[workload_id]["median_ms"]) for workload_id in workload_ids}


def run_trajectory(
    method: str,
    workload_id: str,
    seed: int,
    budget: int,
    context: dict[str, Any],
    manifests: dict[str, Any],
    b5_ms: float,
) -> list[dict[str, Any]]:
    indices = list(context["by_workload"][workload_id])
    rows = context["corpus"]
    x = context["x"]
    posterior = context["posterior"].copy()
    rng = np.random.default_rng(seed)
    remaining = list(indices)
    workload = context["workload_map"][workload_id]
    pool_best = min(float(rows[index]["median_ms"]) for index in indices)
    best = math.inf
    trace = []
    for iteration in range(1, min(budget, len(remaining)) + 1):
        selected = choose_candidate(
            method, remaining, rows, x, posterior, context["temperature"], rng, seed
        )
        remaining.remove(selected)
        candidate_id = rows[selected]["candidate_id"]
        candidate = context["state"][workload_id]["rows"][candidate_id]
        log = (
            BUILD / "true_online" / workload_id / method / f"seed_{seed}"
            / f"iteration_{iteration:02d}_{candidate_id}.log"
        )
        measured = measure_live(
            manifests[candidate_id], workload, context["config"]["measurement"],
            log, candidate,
        )
        runtime = float(measured["median_ms"])
        best = min(best, runtime)
        trace.append({
            "protocol": "true_online_fresh_subprocess",
            "method": method,
            "split": workload["split"],
            "workload_id": workload_id,
            "family": workload["family"],
            "seed": seed,
            "iteration": iteration,
            "candidate_id": candidate_id,
            "runtime_ms": runtime,
            "best_so_far_ms": best,
            "live_b5_ms": b5_ms,
            "posthoc_frozen_pool_best_ms": pool_best,
            "relative_to_b5": b5_ms / best,
            "relative_to_posthoc_pool_best": pool_best / best,
            "revealed_before_selection": iteration - 1,
            "fresh_process": True,
            "objective_cache_hit": False,
            "executable_sha256": measured["executable_sha256"],
            "benchmark_log": measured["log"],
            "observed_path": measured["observed_path"],
            "fringe_calls": int(measured["fringe_calls"]),
            "status": measured["status"],
        })
        if method == "C3_online_calibrated":
            posterior.update(x[selected], math.log(runtime / b5_ms))
    return trace


def summarize(traces: list[dict[str, Any]], budgets: tuple[int, ...]) -> list[dict[str, Any]]:
    result = []
    for method in METHODS:
        method_rows = [row for row in traces if row["method"] == method]
        for budget in budgets:
            selected = [row for row in method_rows if int(row["iteration"]) == budget]
            if not selected:
                continue
            result.append({
                "method": method,
                "budget": budget,
                "trajectories": len(selected),
                "relative_to_b5_gmean": geometric_mean(
                    float(row["relative_to_b5"]) for row in selected
                ),
                "relative_to_posthoc_pool_best_gmean": geometric_mean(
                    float(row["relative_to_posthoc_pool_best"]) for row in selected
                ),
                "best_so_far_ms_gmean": geometric_mean(
                    float(row["best_so_far_ms"]) for row in selected
                ),
            })
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    ensure_tools(build_buddy=not args.skip_build)
    context = prepare_context()
    workload_ids = [
        row["id"] for row in context["workloads"] if row["split"] == "holdout"
    ]
    seeds = list(context["config"]["seeds"])
    budget = int(context["config"]["budget"])
    if args.smoke:
        workload_ids = ["tail_065x067x070"]
        seeds = seeds[:1]
        budget = 5
    manifests = compile_holdout_pool(context, workload_ids, args.force)
    b5 = measure_baselines(context, workload_ids, args.force, args.smoke)

    trace_path = RAW / ("true_online_smoke_traces.csv" if args.smoke else "true_online_traces.csv")
    traces = [] if args.force or not trace_path.exists() else read_csv(trace_path)
    expected_iterations = budget
    for workload_id in workload_ids:
        for method in METHODS:
            for seed in seeds:
                key_rows = [
                    row for row in traces
                    if row["workload_id"] == workload_id
                    and row["method"] == method
                    and int(row["seed"]) == seed
                ]
                if len(key_rows) == expected_iterations:
                    continue
                traces = [
                    row for row in traces
                    if not (
                        row["workload_id"] == workload_id
                        and row["method"] == method
                        and int(row["seed"]) == seed
                    )
                ]
                traces.extend(run_trajectory(
                    method, workload_id, seed, budget, context, manifests, b5[workload_id]
                ))
                write_csv(trace_path, traces)
                print(
                    f"true-online {workload_id} {method} seed={seed} complete",
                    flush=True,
                )

    budgets = (5,) if args.smoke else (5, 10, 15, 25)
    summary_rows = summarize(traces, budgets)
    summary_csv = PROCESSED / (
        "true_online_smoke_summary.csv" if args.smoke else "true_online_fixed_budget.csv"
    )
    write_csv(summary_csv, summary_rows)
    summary = {
        "status": "PASS" if all(row["status"] == "PASS" for row in traces) else "FAIL",
        "experiment_id": context["config"]["experiment_id"],
        "mode": "smoke" if args.smoke else "formal",
        "protocol": "select_then_fresh_subprocess_then_update",
        "workloads": len(workload_ids),
        "methods": list(METHODS),
        "seeds": seeds,
        "budget": budget,
        "trace_rows": len(traces),
        "fresh_process_rows": sum(str(row["fresh_process"]).lower() == "true" for row in traces),
        "objective_cache_hits": sum(str(row["objective_cache_hit"]).lower() == "true" for row in traces),
        "design_cases_for_initial_posterior": context["design_cases"],
        "holdout_candidate_outcomes_used_before_selection": 0,
        "posthoc_pool_best_used_by_policy": False,
        "claim_boundary": context["config"]["claim_boundary"],
    }
    summary_path = PROCESSED / (
        "true_online_smoke_summary.json" if args.smoke else "true_online_summary.json"
    )
    write_json(summary_path, summary)
    REPORTS.mkdir(parents=True, exist_ok=True)
    report = REPORTS / (
        "true_online_smoke_results.md" if args.smoke else "true_online_results.md"
    )
    lines = [
        "# True Online Calibration Results", "",
        f"- status: `{summary['status']}`",
        f"- workloads: {summary['workloads']}",
        f"- trajectories: {len(workload_ids) * len(METHODS) * len(seeds)}",
        f"- fresh objective processes: {summary['fresh_process_rows']}",
        f"- objective cache hits: {summary['objective_cache_hits']}",
        "", "| Method | Budget | Relative to BLIS | Relative to posthoc pool best |",
        "|---|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['method']} | {row['budget']} | "
            f"{float(row['relative_to_b5_gmean']):.3f} | "
            f"{float(row['relative_to_posthoc_pool_best_gmean']):.3f} |"
        )
    lines.extend([
        "", "The frozen full-pool value is used only for posthoc normalization; it is not visible to any policy.",
        "", "## Claim boundary", "", context["config"]["claim_boundary"], "",
    ])
    report.write_text("\n".join(lines), encoding="utf-8")
    manifest_path = PROVENANCE / (
        "true_online_smoke_manifest.json" if args.smoke else "true_online_manifest.json"
    )
    write_json(manifest_path, {
        "schema_version": 1,
        "experiment_id": context["config"]["experiment_id"],
        "mode": summary["mode"],
        "python": sys.version,
        "platform": platform.platform(),
        "inputs": {
            str(ONLINE_PRIOR / "processed" / "calibration_corpus.csv"): sha256(ONLINE_PRIOR / "processed" / "calibration_corpus.csv"),
            str(ONLINE_PRIOR / "processed" / "online_prior_summary.json"): sha256(ONLINE_PRIOR / "processed" / "online_prior_summary.json"),
            str(CHAPTER6 / "data" / "workloads.json"): sha256(CHAPTER6 / "data" / "workloads.json"),
        },
        "outputs": {
            str(trace_path): sha256(trace_path),
            str(summary_csv): sha256(summary_csv),
            str(summary_path): sha256(summary_path),
            str(report): sha256(report),
        },
    })
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
