#!/usr/bin/env python3
"""Replay unmodified BaCO over the frozen real Chapter 6 measurement corpus."""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import random
import shutil
import sys
import time
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import torch


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from chapter6lib import PROJECT, load_config  # noqa: E402
from run_measurements import write_csv, write_json  # noqa: E402


PROCESSED = PROJECT / "processed"
RAW = PROJECT / "raw"
TUNER = PROJECT / "tuner"


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def build_scenario(run_dir: Path, count: int, budget: int) -> dict[str, Any]:
    doe = min(4, budget)
    return {
        "application_name": "chapter6_kernel_aware_gemm",
        "optimization_objectives": ["runtime_ms"],
        "optimization_method": "bayesian_optimization",
        "optimization_iterations": max(0, budget - doe),
        "design_of_experiment": {
            "doe_type": "random sampling",
            "number_of_samples": doe,
            "allow_repetitions": False,
        },
        "models": {"model": "gaussian_process"},
        "GP_model": "gpy",
        "hyperparameter_optimization_iterations": 1,
        "acquisition_function": "EI",
        "normalize_inputs": True,
        "predict_noiseless": False,
        "allow_duplicate_samples": False,
        "local_search_random_points": 100,
        "local_search_starting_points": 5,
        "input_parameters": {
            "schedule_index": {
                "parameter_type": "categorical",
                "values": [f"s{index:03d}" for index in range(count)],
                "parameter_default": "s000",
                "transform": "none",
            }
        },
        "feasible_output": {
            "enable_feasible_predictor": True,
            "name": "Valid",
            "true_value": "True",
            "false_value": "False",
        },
        "run_directory": str(run_dir),
        "log_file": "baco.log",
        "output_data_file": "baco_samples.csv",
    }


def corpus_lookup() -> dict[tuple[str, str], dict[str, Any]]:
    rows = read_csv(PROCESSED / "measurement_aggregates.csv")
    return {
        (row["workload_id"], row["candidate_id"]): row
        for row in rows if row["variant"].startswith("candidate:")
    }


def run_one(
    suite: str, label: str, workload_id: str, pool: list[dict[str, Any]], seed: int,
    budget: int, corpus: dict[tuple[str, str], dict[str, Any]], force: bool,
    permit_callback_budget_over_pool: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    run_dir = TUNER / "runs" / suite / label / workload_id / f"seed_{seed}"
    output_path = run_dir / "trace.json"
    summary_path = run_dir / "summary.json"
    if output_path.exists() and summary_path.exists() and not force:
        return (
            json.loads(output_path.read_text(encoding="utf-8")),
            json.loads(summary_path.read_text(encoding="utf-8")),
        )
    if len(pool) < budget and not permit_callback_budget_over_pool:
        raise ValueError(f"{suite}/{label}/{workload_id} pool {len(pool)} < budget {budget}")
    missing = [row["candidate_id"] for row in pool if (workload_id, row["candidate_id"]) not in corpus]
    if missing:
        raise KeyError(f"measurement corpus missing {suite}/{label}/{workload_id}: {missing[:5]}")
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    scenario = build_scenario(run_dir, len(pool), budget)
    scenario_path = run_dir / "scenario.json"
    write_json(scenario_path, scenario)

    callbacks: list[dict[str, Any]] = []
    cumulative_equivalent_ms = 0.0
    best = float("inf")

    def objective(configuration: dict[str, Any]) -> dict[str, Any]:
        nonlocal cumulative_equivalent_ms, best
        callback_started = time.perf_counter()
        encoded = configuration["schedule_index"]
        index = int(str(encoded)[1:]) if str(encoded).startswith("s") else int(round(float(encoded)))
        candidate = pool[index]
        measured = corpus[(workload_id, candidate["candidate_id"])]
        valid = measured["all_pass"].lower() == "true" and measured["all_predictions_match"].lower() == "true"
        runtime = float(measured["median_ms"]) if valid else 1.0e9
        evaluator_ms = float(measured["compile_pipeline_ms"]) + float(measured["median_benchmark_wall_ms"])
        cumulative_equivalent_ms += evaluator_ms
        if valid:
            best = min(best, runtime)
        callback_ms = (time.perf_counter() - callback_started) * 1000.0
        callbacks.append({
            "suite": suite,
            "label": label,
            "workload_id": workload_id,
            "seed": seed,
            "iteration": len(callbacks) + 1,
            "schedule_index": index,
            "candidate_id": candidate["candidate_id"],
            "predicted_path": measured["predicted_path"],
            "observed_path": measured["observed_path"],
            "runtime_ms": runtime,
            "best_so_far_ms": best,
            "Valid": valid,
            "evaluator_equivalent_ms": evaluator_ms,
            "cumulative_equivalent_ms": cumulative_equivalent_ms,
            "replay_callback_ms": callback_ms,
        })
        return {"runtime_ms": runtime, "Valid": valid}

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    from baco import run
    import baco.param.transformations as baco_transformations
    from baco.util.file import read_settings_file
    import GPy.util.linalg as gpy_linalg

    # BaCO 3.0.0's categorical preprocessing references the standard-library
    # warnings module without importing it. Injecting the module preserves the
    # pinned third-party source while making the categorical lookup executable.
    baco_transformations.warnings = warnings
    if not getattr(baco_transformations, "_chapter6_sklearn_compat", False):
        original_encoder = baco_transformations.OneHotEncoder

        def compatible_one_hot_encoder(*args: Any, **kwargs: Any) -> Any:
            if "sparse" in kwargs and "sparse_output" not in kwargs:
                kwargs["sparse_output"] = kwargs.pop("sparse")
            return original_encoder(*args, **kwargs)

        baco_transformations.OneHotEncoder = compatible_one_hot_encoder
        baco_transformations._chapter6_sklearn_compat = True

    # A repeated categorical point can drive GPy through an ill-conditioned
    # intermediate covariance during hyperparameter fitting. Keep GPy's native
    # jitter path first, then use a deterministic wider diagonal retry without
    # changing the observations or BaCO's candidate-selection logic.
    if not getattr(gpy_linalg, "_chapter6_jitchol_compat", False):
        original_jitchol = gpy_linalg.jitchol
        gpy_linalg._chapter6_jitter_retries = 0

        def compatible_jitchol(matrix: Any, maxtries: int = 5) -> Any:
            try:
                return original_jitchol(matrix, maxtries=maxtries)
            except np.linalg.LinAlgError as original_error:
                diagonal = np.diag(matrix)
                scale = max(float(np.nanmean(diagonal)), 1.0)
                for multiplier in (1e-1, 1.0, 10.0, 100.0):
                    try:
                        factor = np.linalg.cholesky(
                            np.asarray(matrix) + np.eye(matrix.shape[0]) * scale * multiplier
                        )
                        gpy_linalg._chapter6_jitter_retries += 1
                        return factor
                    except np.linalg.LinAlgError:
                        continue
                raise original_error

        gpy_linalg.jitchol = compatible_jitchol
        gpy_linalg._chapter6_jitchol_compat = True

    jitter_retries_before = int(gpy_linalg._chapter6_jitter_retries)

    replay_started = time.perf_counter()
    console_path = run_dir / "console.log"
    with console_path.open("w", encoding="utf-8") as console:
        with contextlib.redirect_stdout(console), contextlib.redirect_stderr(console):
            run.optimize(read_settings_file(str(scenario_path)), objective)
    replay_wall_ms = (time.perf_counter() - replay_started) * 1000.0
    numerical_jitter_retries = int(gpy_linalg._chapter6_jitter_retries) - jitter_retries_before
    unique = len({row["candidate_id"] for row in callbacks})
    if len(callbacks) != budget:
        raise RuntimeError(
            f"BaCO budget mismatch {suite}/{label}/{workload_id}/seed{seed}: "
            f"callbacks={len(callbacks)}, budget={budget}"
        )
    summary = {
        "suite": suite,
        "label": label,
        "workload_id": workload_id,
        "seed": seed,
        "pool_size": len(pool),
        "budget": budget,
        "evaluated": len(callbacks),
        "unique": unique,
        "duplicate_evaluations": len(callbacks) - unique,
        "valid": sum(bool(row["Valid"]) for row in callbacks),
        "best_runtime_ms": min(row["runtime_ms"] for row in callbacks if row["Valid"]),
        "final_equivalent_ms": callbacks[-1]["cumulative_equivalent_ms"],
        "replay_wall_ms": replay_wall_ms,
        "offline_replay": True,
        "baco_compatibility_shim": "inject warnings, map OneHotEncoder sparse to sparse_output, and retry exhausted GPy Cholesky jitter",
        "numerical_jitter_retries": numerical_jitter_retries,
    }
    write_json(output_path, callbacks)
    write_json(summary_path, summary)
    return callbacks, summary


def suite_pools(suite: str) -> dict[str, dict[str, list[dict[str, Any]]]]:
    if suite == "base":
        raw = json.loads((TUNER / "base_pools.json").read_text(encoding="utf-8"))
        return {method: {workload: pools[method] for workload, pools in raw.items()} for method in ("B1", "B2", "B3", "B4")}
    if suite == "ablation":
        raw = json.loads((TUNER / "ablation_pools.json").read_text(encoding="utf-8"))
        labels = next(iter(raw.values())).keys()
        return {label: {workload: pools[label] for workload, pools in raw.items()} for label in labels}
    if suite == "shell":
        raw = json.loads((TUNER / "shell_ratio_pools.json").read_text(encoding="utf-8"))
        return {ratio: pools for ratio, pools in raw.items()}
    raise ValueError(suite)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("base", "ablation", "shell", "all"), default="all")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--label", help="run one label within a single selected suite")
    args = parser.parse_args()
    config, _ = load_config()
    corpus = corpus_lookup()
    suites = ("base", "ablation", "shell") if args.suite == "all" else (args.suite,)
    trace_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for suite in suites:
        pools_by_label = suite_pools(suite)
        labels = list(pools_by_label)
        if args.label:
            if args.suite == "all" or args.label not in pools_by_label:
                raise ValueError("--label requires one suite and a label in that suite")
            labels = [args.label]
        if args.smoke:
            labels = labels[:1]
        for label in labels:
            workloads = list(pools_by_label[label])
            if args.smoke:
                workloads = workloads[:1]
            seeds = config["seeds"][:1] if args.smoke else config["seeds"]
            budget = 6 if args.smoke else int(config["budget"])
            for workload_id in workloads:
                for seed in seeds:
                    trace, summary = run_one(
                        suite, label, workload_id, pools_by_label[label][workload_id],
                        int(seed), budget, corpus, args.force,
                    )
                    summary.setdefault("numerical_jitter_retries", 0)
                    trace_rows.extend(trace)
                    summaries.append(summary)
            print(f"completed {suite}/{label}: {len(summaries)} runs total", flush=True)
    suffix = "_smoke" if args.smoke else ""
    if args.label:
        suffix += f"_{args.suite}_{args.label}"
    write_csv(PROCESSED / f"tuning_traces{suffix}.csv", trace_rows)
    write_csv(PROCESSED / f"tuning_run_summaries{suffix}.csv", summaries)
    write_json(PROCESSED / f"tuning_status{suffix}.json", {
        "status": "PASS",
        "suites": list(suites),
        "run_count": len(summaries),
        "trace_count": len(trace_rows),
        "all_valid": all(row["valid"] == row["budget"] for row in summaries),
        "all_unique": all(row["unique"] == row["budget"] for row in summaries),
        "duplicate_evaluations": sum(row["duplicate_evaluations"] for row in summaries),
        "duplicate_policy_note": "BaCO 3.0.0 may repeat categorical points despite allow_duplicate_samples=false; callback budget and unique points are reported separately.",
        "offline_replay": True,
        "measurement_source": "processed/measurement_aggregates.csv",
        "seeds": config["seeds"] if not args.smoke else config["seeds"][:1],
        "budget": int(config["budget"]) if not args.smoke else 6,
    })
    print(json.dumps({"status": "PASS", "runs": len(summaries), "traces": len(trace_rows)}, indent=2))


if __name__ == "__main__":
    main()
