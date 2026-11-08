#!/usr/bin/env python3
"""Run Optuna TPE with the same finite pools and live-measurement budget."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from typing import Any

import optuna
from optuna.distributions import CategoricalDistribution
from optuna.trial import TrialState

from cgo_common import (
    BUILD,
    PROCESSED,
    PROVENANCE,
    PROJECT,
    RAW,
    REPORTS,
    geometric_mean,
    measure_live,
    read_csv,
    sha256,
    write_csv,
    write_json,
)
from run_true_online import (
    compile_holdout_pool,
    measure_baselines,
    prepare_context,
)


METHOD = "D1_optuna_tpe"


def run_trajectory(
    workload_id: str,
    seed: int,
    budget: int,
    context: dict[str, Any],
    manifests: dict[str, Any],
    b5_ms: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    indices = context["by_workload"][workload_id]
    rows = context["corpus"]
    candidate_ids = [rows[index]["candidate_id"] for index in indices]
    pool_best = min(float(rows[index]["median_ms"]) for index in indices)
    workload = context["workload_map"][workload_id]
    sampler = optuna.samplers.TPESampler(
        seed=seed,
        n_startup_trials=int(context["config"]["optuna"]["n_startup_trials"]),
    )
    study = optuna.create_study(direction="minimize", sampler=sampler)
    distribution = CategoricalDistribution(candidate_ids)
    seen: set[str] = set()
    traces: list[dict[str, Any]] = []
    callbacks: list[dict[str, Any]] = []
    best = float("inf")
    callback_index = 0
    max_callbacks = budget * 100
    while len(seen) < min(budget, len(candidate_ids)):
        callback_index += 1
        if callback_index > max_callbacks:
            raise RuntimeError(
                f"Optuna failed to produce {budget} unique candidates after {max_callbacks} callbacks"
            )
        trial = study.ask(fixed_distributions={"candidate_id": distribution})
        candidate_id = str(trial.params["candidate_id"])
        duplicate = candidate_id in seen
        callback = {
            "method": METHOD,
            "workload_id": workload_id,
            "seed": seed,
            "callback_index": callback_index,
            "optuna_trial_number": trial.number,
            "candidate_id": candidate_id,
            "duplicate": duplicate,
            "unique_evaluations_before_callback": len(seen),
        }
        if duplicate:
            study.tell(trial, state=TrialState.PRUNED)
            callback["state"] = "PRUNED_DUPLICATE"
            callbacks.append(callback)
            continue

        seen.add(candidate_id)
        candidate = context["state"][workload_id]["rows"][candidate_id]
        iteration = len(seen)
        log = (
            BUILD / "optuna" / workload_id / f"seed_{seed}"
            / f"iteration_{iteration:02d}_{candidate_id}.log"
        )
        measured = measure_live(
            manifests[candidate_id], workload, context["config"]["measurement"],
            log, candidate,
        )
        runtime = float(measured["median_ms"])
        study.tell(trial, runtime)
        callback.update({"state": "COMPLETE", "runtime_ms": runtime})
        callbacks.append(callback)
        best = min(best, runtime)
        traces.append({
            "protocol": "optuna_tpe_fresh_subprocess",
            "method": METHOD,
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
            "optuna_trial_number": trial.number,
            "callback_index": callback_index,
            "executable_sha256": measured["executable_sha256"],
            "benchmark_log": measured["log"],
            "observed_path": measured["observed_path"],
            "fringe_calls": int(measured["fringe_calls"]),
            "status": measured["status"],
        })
    return traces, callbacks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    context = prepare_context()
    required_version = str(context["config"]["optuna"]["version"])
    if optuna.__version__ != required_version:
        raise RuntimeError(
            f"Optuna version mismatch: expected {required_version}, got {optuna.__version__}"
        )
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

    trace_path = RAW / ("optuna_smoke_traces.csv" if args.smoke else "optuna_traces.csv")
    callback_path = RAW / (
        "optuna_smoke_callbacks.csv" if args.smoke else "optuna_callbacks.csv"
    )
    traces = [] if args.force or not trace_path.exists() else read_csv(trace_path)
    callbacks = [] if args.force or not callback_path.exists() else read_csv(callback_path)
    for workload_id in workload_ids:
        for seed in seeds:
            existing = [
                row for row in traces
                if row["workload_id"] == workload_id and int(row["seed"]) == seed
            ]
            if len(existing) == budget:
                continue
            traces = [
                row for row in traces
                if not (row["workload_id"] == workload_id and int(row["seed"]) == seed)
            ]
            callbacks = [
                row for row in callbacks
                if not (row["workload_id"] == workload_id and int(row["seed"]) == seed)
            ]
            new_traces, new_callbacks = run_trajectory(
                workload_id, seed, budget, context, manifests, b5[workload_id]
            )
            traces.extend(new_traces)
            callbacks.extend(new_callbacks)
            write_csv(trace_path, traces)
            write_csv(callback_path, callbacks)
            print(f"optuna {workload_id} seed={seed} complete", flush=True)

    budgets = (5,) if args.smoke else (5, 10, 15, 25)
    summary_rows = []
    for selected_budget in budgets:
        rows = [row for row in traces if int(row["iteration"]) == selected_budget]
        summary_rows.append({
            "method": METHOD,
            "budget": selected_budget,
            "trajectories": len(rows),
            "relative_to_b5_gmean": geometric_mean(
                float(row["relative_to_b5"]) for row in rows
            ),
            "relative_to_posthoc_pool_best_gmean": geometric_mean(
                float(row["relative_to_posthoc_pool_best"]) for row in rows
            ),
        })
    summary_csv = PROCESSED / (
        "optuna_smoke_fixed_budget.csv" if args.smoke else "optuna_fixed_budget.csv"
    )
    write_csv(summary_csv, summary_rows)
    duplicate_count = sum(str(row["duplicate"]).lower() == "true" for row in callbacks)
    summary = {
        "status": "PASS" if all(row["status"] == "PASS" for row in traces) else "FAIL",
        "experiment_id": context["config"]["experiment_id"],
        "mode": "smoke" if args.smoke else "formal",
        "method": METHOD,
        "optuna_version": optuna.__version__,
        "sampler": "TPESampler",
        "workloads": len(workload_ids),
        "seeds": seeds,
        "unique_budget": budget,
        "unique_measurements": len(traces),
        "callbacks": len(callbacks),
        "pruned_duplicate_callbacks": duplicate_count,
        "objective_cache_hits": 0,
        "posthoc_pool_best_used_by_policy": False,
        "claim_boundary": context["config"]["claim_boundary"],
    }
    summary_path = PROCESSED / (
        "optuna_smoke_summary.json" if args.smoke else "optuna_summary.json"
    )
    write_json(summary_path, summary)
    REPORTS.mkdir(parents=True, exist_ok=True)
    report = REPORTS / ("optuna_smoke_results.md" if args.smoke else "optuna_results.md")
    lines = [
        "# Optuna TPE Results", "",
        f"- status: `{summary['status']}`",
        f"- Optuna: `{summary['optuna_version']}`",
        f"- unique measurements: {summary['unique_measurements']}",
        f"- pruned duplicate callbacks: {summary['pruned_duplicate_callbacks']}",
        "", "| Budget | Relative to BLIS | Relative to posthoc pool best |",
        "|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['budget']} | {float(row['relative_to_b5_gmean']):.3f} | "
            f"{float(row['relative_to_posthoc_pool_best_gmean']):.3f} |"
        )
    lines.extend([
        "", "Duplicate suggestions are pruned without execution and do not consume the unique-candidate budget.",
        "", "## Claim boundary", "", context["config"]["claim_boundary"], "",
    ])
    report.write_text("\n".join(lines), encoding="utf-8")
    manifest_path = PROVENANCE / (
        "optuna_smoke_manifest.json" if args.smoke else "optuna_manifest.json"
    )
    write_json(manifest_path, {
        "schema_version": 1,
        "experiment_id": context["config"]["experiment_id"],
        "mode": summary["mode"],
        "python": sys.version,
        "platform": platform.platform(),
        "optuna": optuna.__version__,
        "inputs": {
            str(PROJECT / "data" / "experiment_config.json"): sha256(PROJECT / "data" / "experiment_config.json"),
        },
        "outputs": {
            str(trace_path): sha256(trace_path),
            str(callback_path): sha256(callback_path),
            str(summary_csv): sha256(summary_csv),
            str(summary_path): sha256(summary_path),
            str(report): sha256(report),
        },
    })
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
