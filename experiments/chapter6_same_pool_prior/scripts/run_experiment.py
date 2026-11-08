#!/usr/bin/env python3
"""Run the corrected B2/B3/B4 same-pool BaCO experiment and acceptance audit."""

from __future__ import annotations

import argparse
import contextlib
import json
import math
import random
import shutil
import sys
import time
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import torch

from experiment_lib import (
    BUILD,
    CONFIG_PATH,
    EXPERIMENTS,
    PROCESSED,
    PROJECT,
    PROVENANCE,
    RAW,
    REPORTS,
    canonicalize_pool,
    geometric_mean,
    load_config,
    load_host_corpus,
    load_workloads,
    method_prior,
    paired_cluster_bootstrap,
    parameter_liveness_audit,
    pool_fingerprint,
    prepare_calibration,
    resolve_experiment_path,
    runtime_manifest,
    sha256,
    write_csv,
    write_json,
)


METHODS = (
    "B2_no_prior_baco",
    "B3_static_prior_baco",
    "B4_calibrated_prior_baco",
)


def build_scenario(
    run_dir: Path,
    pool_size: int,
    method: str,
    prior: list[float] | None,
    model_weight: float,
    budget: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    doe = min(int(config["doe_samples"]), budget)
    parameter: dict[str, Any] = {
        "parameter_type": "categorical",
        "values": [f"c{index:03d}" for index in range(pool_size)],
        "transform": "none",
    }
    if prior is not None:
        if len(prior) != pool_size or not math.isclose(sum(prior), 1.0, rel_tol=1.0e-9):
            raise ValueError("categorical prior must match and normalize over the pool")
        parameter["prior"] = prior
    scenario: dict[str, Any] = {
        "application_name": "chapter6_same_pool_prior",
        "optimization_objectives": ["runtime_ms"],
        "optimization_method": "bayesian_optimization",
        "optimization_iterations": max(0, budget - doe),
        "design_of_experiment": {
            "doe_type": "random sampling",
            "number_of_samples": doe,
            "allow_repetitions": False,
        },
        "models": {"model": config["baco"]["model"]},
        "GP_model": config["baco"]["gp_backend"],
        "hyperparameter_optimization_iterations": int(
            config["baco"]["hyperparameter_optimization_iterations"]
        ),
        "acquisition_function": (
            "EI" if method == "B2_no_prior_baco" else "EI_PIBO"
        ),
        "normalize_inputs": True,
        "predict_noiseless": False,
        "allow_duplicate_samples": bool(config["baco"]["allow_duplicate_samples"]),
        "local_search_random_points": int(config["baco"]["local_search_random_points"]),
        "local_search_starting_points": int(config["baco"]["local_search_starting_points"]),
        "input_parameters": {"schedule_id": parameter},
        "run_directory": str(run_dir),
        "log_file": "baco.log",
        "output_data_file": "baco_samples.csv",
    }
    if method != "B2_no_prior_baco":
        scenario["model_weight"] = float(model_weight)
    return scenario


def patch_baco_compatibility() -> Any:
    """Apply the pinned BaCO 3.0 compatibility shims used by Chapter 6."""
    import baco.param.transformations as baco_transformations
    import baco.param.data as baco_data
    import baco.param.sampling as baco_sampling
    import baco.bo.bo as baco_bo
    import baco.bo.optimize as baco_optimize
    import GPy.util.linalg as gpy_linalg

    baco_transformations.warnings = warnings
    if not getattr(baco_data.DataArray, "_same_pool_hash_compat", False):
        def compatible_data_array_update(self: Any) -> None:
            self.string_dict = {
                "_".join(str(value) for value in row.numpy()): index
                for index, row in enumerate(self.parameters_array)
            }
            self.len = self.parameters_array.shape[0]

        baco_data.DataArray._update = compatible_data_array_update
        baco_data.DataArray._same_pool_hash_compat = True
    if not getattr(baco_transformations, "_same_pool_sklearn_compat", False):
        original_encoder = baco_transformations.OneHotEncoder

        def compatible_one_hot_encoder(*args: Any, **kwargs: Any) -> Any:
            if "sparse" in kwargs and "sparse_output" not in kwargs:
                kwargs["sparse_output"] = kwargs.pop("sparse")
            return original_encoder(*args, **kwargs)

        baco_transformations.OneHotEncoder = compatible_one_hot_encoder
        baco_transformations._same_pool_sklearn_compat = True

    if not getattr(gpy_linalg, "_same_pool_jitchol_compat", False):
        original_jitchol = gpy_linalg.jitchol
        gpy_linalg._same_pool_jitter_retries = 0

        def compatible_jitchol(matrix: Any, maxtries: int = 5) -> Any:
            try:
                return original_jitchol(matrix, maxtries=maxtries)
            except np.linalg.LinAlgError as original_error:
                diagonal = np.diag(matrix)
                scale = max(float(np.nanmean(diagonal)), 1.0)
                for multiplier in (1.0e-1, 1.0, 10.0, 100.0):
                    try:
                        factor = np.linalg.cholesky(
                            np.asarray(matrix)
                            + np.eye(matrix.shape[0]) * scale * multiplier
                        )
                        gpy_linalg._same_pool_jitter_retries += 1
                        return factor
                    except np.linalg.LinAlgError:
                        continue
                raise original_error

        gpy_linalg.jitchol = compatible_jitchol
        gpy_linalg._same_pool_jitchol_compat = True

    # BaCO 3.0 can return an already evaluated categorical configuration from
    # acquisition local search even when allow_duplicate_samples is false. For
    # this one-dimensional finite domain, evaluate the unmodified BaCO
    # acquisition exactly over unseen tokens. This is both cheaper and makes the
    # unique-measurement budget enforceable without reusing an objective value.
    if not getattr(baco_bo, "_same_pool_finite_domain_compat", False):
        original_optimize_acq = baco_bo.optimize_acq
        baco_bo._same_pool_masked_iterations = 0

        def finite_domain_optimize_acq(
            settings: dict[str, Any],
            param_space: Any,
            data_array: Any,
            regression_models: Any,
            iteration_number: int,
            objective_weights: Any,
            objective_means: Any,
            objective_stds: Any,
            best_values: Any,
            classification_model: Any = None,
        ) -> Any:
            if param_space.dimension != 1 or param_space.parameters[0].__class__.__name__ != "CategoricalParameter":
                return original_optimize_acq(
                    settings, param_space, data_array, regression_models,
                    iteration_number, objective_weights, objective_means,
                    objective_stds, best_values, classification_model,
                )
            all_candidates = torch.arange(
                param_space.parameters[0].get_size(), dtype=torch.float32
            ).reshape(-1, 1)
            observed_values = {
                tuple(float(value) for value in row.tolist())
                for row in data_array.parameters_array
            }
            unseen_candidates = [
                candidate for candidate in all_candidates
                if tuple(float(value) for value in candidate.tolist())
                not in observed_values
            ]
            if not unseen_candidates:
                raise RuntimeError("BaCO finite domain exhausted")
            unseen = torch.stack(unseen_candidates)
            acquisition = {
                "EI": baco_optimize.ei,
                "UCB": baco_optimize.ucb,
                "EI_PIBO": baco_optimize.ei_pibo,
            }[settings["acquisition_function"]]
            values = acquisition(
                settings,
                param_space,
                X=unseen,
                regression_models=regression_models,
                iteration_number=iteration_number,
                classification_model=classification_model,
                objective_weights=objective_weights,
                objective_means=objective_means,
                objective_stds=objective_stds,
                best_values=best_values,
                feasibility_threshold=0,
            )
            baco_bo._same_pool_masked_iterations += 1
            return unseen[int(torch.argmax(values).item())]

        baco_bo.optimize_acq = finite_domain_optimize_acq
        baco_bo._same_pool_finite_domain_compat = True

    # Use the declared categorical distribution for the no-replacement DOE.
    # B2's distribution is uniform; B3/B4 differ only by their soft prior.
    if not getattr(baco_bo, "_same_pool_prior_doe_compat", False):
        def prior_aware_doe(
            param_space: Any,
            data_array: Any,
            n_samples: int,
            doe_type: str,
            allow_repetitions: bool = False,
        ) -> Any:
            if doe_type != "random sampling":
                raise ValueError(f"unsupported same-pool DOE type: {doe_type}")
            if (
                param_space.dimension == 1
                and param_space.parameters[0].__class__.__name__ == "CategoricalParameter"
                and not allow_repetitions
            ):
                parameter = param_space.parameters[0]
                observed = {
                    int(round(float(row[0].item())))
                    for row in data_array.parameters_array
                }
                available = [
                    index for index in range(parameter.get_size())
                    if index not in observed
                ]
                if len(available) < n_samples:
                    raise RuntimeError("insufficient unseen candidates for DOE")
                if parameter.distribution_name == "uniform":
                    selected = np.random.choice(
                        available, size=n_samples, replace=False
                    )
                else:
                    # A ranked warm start makes the calibrated prior useful
                    # inside a 5-point budget while preserving every candidate
                    # for subsequent PIBO exploration.
                    selected = sorted(
                        available,
                        key=lambda index: (-float(parameter.distribution[index]), index),
                    )[:n_samples]
                return torch.tensor(selected, dtype=torch.float64).reshape(-1, 1)
            return baco_sampling.random_sample(
                param_space,
                n_samples,
                "using_priors",
                allow_repetitions,
                data_array.string_dict,
            )

        baco_bo.get_doe_sample_configurations = prior_aware_doe
        baco_bo._same_pool_prior_doe_compat = True
    return gpy_linalg


def run_baco_trajectory(
    *,
    phase: str,
    host: dict[str, Any],
    workload_id: str,
    indices: list[int],
    method: str,
    seed: int,
    budget: int,
    prior: list[float] | None,
    model_weight: float,
    config: dict[str, Any],
    force: bool,
) -> dict[str, Any]:
    environment_id = host["environment"]["id"]
    weight_token = str(model_weight).replace(".", "p")
    run_dir = (
        BUILD / phase / environment_id / method / f"weight_{weight_token}"
        / workload_id / f"seed_{seed}"
    )
    cache_path = run_dir / "trajectory.json"
    rows = host["records"]
    ordered_indices = sorted(indices, key=lambda index: rows[index]["canonical_id"])
    fingerprint = pool_fingerprint([rows[index] for index in ordered_indices])
    cache_key = {
        "phase": phase,
        "environment": environment_id,
        "workload_id": workload_id,
        "method": method,
        "seed": seed,
        "budget": budget,
        "model_weight": model_weight,
        "pool_fingerprint": fingerprint,
    }
    if cache_path.exists() and not force:
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if cached.get("cache_key") == cache_key:
            cached_summary = cached.get("summary", {})
            if (
                int(cached_summary.get("unique_measurements", -1)) == budget
                and int(cached_summary.get("duplicate_callbacks", -1)) == 0
            ):
                return cached
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    scenario = build_scenario(
        run_dir, len(ordered_indices), method, prior, model_weight, budget, config
    )
    scenario_path = run_dir / "scenario.json"
    write_json(scenario_path, scenario)

    callbacks: list[dict[str, Any]] = []
    seen: set[str] = set()
    observed: dict[str, float] = {}
    best = math.inf

    def objective(configuration: dict[str, Any]) -> dict[str, float]:
        nonlocal best
        raw_encoded = configuration["schedule_id"]
        if torch.is_tensor(raw_encoded):
            pool_index = int(raw_encoded.item())
        elif isinstance(raw_encoded, (int, float)):
            pool_index = int(round(float(raw_encoded)))
        else:
            encoded = str(raw_encoded)
            pool_index = (
                int(encoded[1:]) if encoded.startswith("c")
                else int(round(float(encoded)))
            )
        record = rows[ordered_indices[pool_index]]
        candidate_id = record["canonical_id"]
        duplicate = candidate_id in seen
        revealed_before_selection = len(seen)
        if duplicate:
            runtime = observed[candidate_id]
        else:
            # This is the only holdout-target read in the policy path, and it
            # occurs after BaCO has returned the selected finite-domain token.
            runtime = float(record["runtime_ms"])
            seen.add(candidate_id)
            observed[candidate_id] = runtime
        best = min(best, runtime)
        callbacks.append({
            "phase": phase,
            "environment": environment_id,
            "method": method,
            "workload_id": workload_id,
            "family": record["family"],
            "split": record["split"],
            "seed": seed,
            "callback_index": len(callbacks) + 1,
            "unique_iteration": len(seen),
            "candidate_id": candidate_id,
            "source_candidate_id": record["source_candidate_id"],
            "tile_m": record["tile_m"],
            "tile_n": record["tile_n"],
            "tile_k": record["tile_k"],
            "runtime_ms": runtime,
            "best_so_far_ms": best,
            "duplicate": duplicate,
            "revealed_before_selection": revealed_before_selection,
            "target_read_after_selection": not duplicate,
            "pool_size": len(ordered_indices),
            "pool_fingerprint": fingerprint,
            "model_weight": model_weight,
        })
        return {"runtime_ms": runtime}

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    from baco import run
    from baco.util.file import read_settings_file

    gpy_linalg = patch_baco_compatibility()
    import baco.bo.bo as baco_bo
    jitter_before = int(gpy_linalg._same_pool_jitter_retries)
    masks_before = int(baco_bo._same_pool_masked_iterations)
    started = time.perf_counter()
    console_path = run_dir / "console.log"
    with console_path.open("w", encoding="utf-8") as console:
        with contextlib.redirect_stdout(console), contextlib.redirect_stderr(console):
            run.optimize(read_settings_file(str(scenario_path)), objective)
    replay_wall_ms = (time.perf_counter() - started) * 1000.0
    duplicate_count = sum(bool(row["duplicate"]) for row in callbacks)
    result = {
        "cache_key": cache_key,
        "callbacks": callbacks,
        "summary": {
            **cache_key,
            "callbacks": len(callbacks),
            "unique_measurements": len(seen),
            "duplicate_callbacks": duplicate_count,
            "replay_wall_ms": replay_wall_ms,
            "numerical_jitter_retries": (
                int(gpy_linalg._same_pool_jitter_retries) - jitter_before
            ),
            "finite_domain_masked_acquisition_iterations": (
                int(baco_bo._same_pool_masked_iterations) - masks_before
            ),
            "finite_domain_duplicate_prevention": True,
            "prior_aware_no_replacement_doe": True,
            "objective_cache_hits": duplicate_count,
            "offline_replay": True,
        },
    }
    write_json(cache_path, result)
    if len(callbacks) != budget:
        raise RuntimeError(f"BaCO callback mismatch: {cache_key}, got {len(callbacks)}")
    if len(seen) != budget or duplicate_count:
        raise RuntimeError(
            f"unique-measurement budget failed: {cache_key}, "
            f"unique={len(seen)}, duplicates={duplicate_count}"
        )
    return result


def select_model_weight(
    host: dict[str, Any],
    calibration: dict[str, Any],
    config: dict[str, Any],
    force: bool,
    smoke: bool,
) -> tuple[float, list[dict[str, Any]]]:
    rows = host["records"]
    validation_ids = [
        workload_id for workload_id, indices in sorted(host["by_workload"].items())
        if rows[indices[0]]["split"] == "validation"
    ]
    seeds = list(config["calibration"]["validation_seeds"])
    weights = list(config["calibration"]["model_weight_candidates"])
    budget = int(config["budget"])
    if smoke:
        validation_ids = validation_ids[:1]
        seeds = seeds[:1]
        weights = weights[:1]
        budget = min(5, budget)
    records: list[dict[str, Any]] = []
    for weight in weights:
        regrets: list[float] = []
        for workload_id in validation_ids:
            indices = host["by_workload"][workload_id]
            prior = method_prior(
                "B4_calibrated_prior_baco", indices, host, calibration, config
            )
            oracle = min(float(rows[index]["runtime_ms"]) for index in indices)
            for seed in seeds:
                trajectory = run_baco_trajectory(
                    phase="validation",
                    host=host,
                    workload_id=workload_id,
                    indices=indices,
                    method="B4_calibrated_prior_baco",
                    seed=int(seed),
                    budget=budget,
                    prior=prior,
                    model_weight=float(weight),
                    config=config,
                    force=force,
                )
                regrets.extend(
                    -math.log(oracle / float(row["best_so_far_ms"]))
                    for row in trajectory["callbacks"]
                )
        objective = float(np.mean(regrets))
        records.append({
            "environment": host["environment"]["id"],
            "model_weight": float(weight),
            "mean_log_simple_regret_auc": objective,
            "validation_workloads": len(validation_ids),
            "validation_seeds": len(seeds),
            "budget": budget,
        })
        print(
            f"validation {host['environment']['id']} weight={weight}: "
            f"AUC={objective:.6f}", flush=True
        )
    selected = min(
        records,
        key=lambda row: (row["mean_log_simple_regret_auc"], row["model_weight"]),
    )
    return float(selected["model_weight"]), records


def run_holdout(
    hosts: list[dict[str, Any]],
    calibrations: dict[str, dict[str, Any]],
    selected_weights: dict[str, float],
    config: dict[str, Any],
    force: bool,
    smoke: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    traces: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    seeds = list(config["seeds"])
    budget = int(config["budget"])
    active_hosts = hosts
    if smoke:
        active_hosts = hosts[:1]
        seeds = seeds[:1]
        budget = min(5, budget)
    for host in active_hosts:
        environment_id = host["environment"]["id"]
        rows = host["records"]
        holdout_ids = [
            workload_id for workload_id, indices in sorted(host["by_workload"].items())
            if rows[indices[0]]["split"] == "holdout"
        ]
        if smoke:
            holdout_ids = holdout_ids[:1]
        for workload_id in holdout_ids:
            indices = host["by_workload"][workload_id]
            pool_oracle = min(float(rows[index]["runtime_ms"]) for index in indices)
            b5_ms = float(rows[indices[0]]["b5_ms"])
            for seed in seeds:
                for method in METHODS:
                    prior = method_prior(
                        method, indices, host, calibrations[environment_id], config
                    )
                    trajectory = run_baco_trajectory(
                        phase="holdout",
                        host=host,
                        workload_id=workload_id,
                        indices=indices,
                        method=method,
                        seed=int(seed),
                        budget=budget,
                        prior=prior,
                        model_weight=selected_weights[environment_id],
                        config=config,
                        force=force,
                    )
                    summaries.append(trajectory["summary"])
                    for callback in trajectory["callbacks"]:
                        row = dict(callback)
                        row.update({
                            "pool_oracle_ms": pool_oracle,
                            "relative_to_pool_oracle": pool_oracle / float(row["best_so_far_ms"]),
                            "b5_ms": b5_ms,
                            "relative_to_b5": b5_ms / float(row["best_so_far_ms"]),
                        })
                        traces.append(row)
            print(f"holdout {environment_id} {workload_id}: complete", flush=True)
    return traces, summaries


def same_pool_audit(
    hosts: list[dict[str, Any]],
    traces: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    passed = True
    active_environments = sorted({row["environment"] for row in traces})
    active_cases = {
        (row["environment"], row["workload_id"])
        for row in traces
    }
    for host in hosts:
        environment_id = host["environment"]["id"]
        if environment_id not in active_environments:
            continue
        records = host["records"]
        for workload_id, indices in sorted(host["by_workload"].items()):
            if records[indices[0]]["split"] != "holdout":
                continue
            if (environment_id, workload_id) not in active_cases:
                continue
            canonical_pool = sorted(
                (records[index] for index in indices), key=lambda row: row["canonical_id"]
            )
            fingerprint = pool_fingerprint(canonical_pool)
            oracle = min(float(row["runtime_ms"]) for row in canonical_pool)
            method_rows = []
            for method in METHODS:
                observed = [
                    row for row in traces
                    if row["environment"] == environment_id
                    and row["workload_id"] == workload_id
                    and row["method"] == method
                ]
                method_fingerprints = {row["pool_fingerprint"] for row in observed}
                method_oracles = {float(row["pool_oracle_ms"]) for row in observed}
                status = (
                    len(method_fingerprints) == 1
                    and next(iter(method_fingerprints)) == fingerprint
                    and method_oracles == {oracle}
                )
                passed = passed and status
                method_rows.append({
                    "environment": environment_id,
                    "workload_id": workload_id,
                    "method": method,
                    "pool_size": len(canonical_pool),
                    "pool_fingerprint": fingerprint,
                    "pool_oracle_ms": oracle,
                    "status": "PASS" if status else "FAIL",
                })
            rows.extend(method_rows)
    return rows, passed


def summarize_fixed_budget(
    traces: list[dict[str, Any]], checkpoints: list[int]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    environments = sorted({row["environment"] for row in traces})
    for environment in environments:
        for method in METHODS:
            for budget in checkpoints:
                selected = [
                    row for row in traces
                    if row["environment"] == environment
                    and row["method"] == method
                    and int(row["unique_iteration"]) == budget
                ]
                if not selected:
                    continue
                result.append({
                    "environment": environment,
                    "method": method,
                    "budget": budget,
                    "trajectories": len(selected),
                    "relative_to_pool_oracle_gmean": geometric_mean(
                        float(row["relative_to_pool_oracle"]) for row in selected
                    ),
                    "relative_to_b5_gmean": geometric_mean(
                        float(row["relative_to_b5"]) for row in selected
                    ),
                    "oracle_hit_rate": sum(
                        math.isclose(
                            float(row["best_so_far_ms"]),
                            float(row["pool_oracle_ms"]),
                            rel_tol=1.0e-12,
                        )
                        for row in selected
                    ) / len(selected),
                })
    return result


def paired_comparisons(
    traces: list[dict[str, Any]], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    checkpoints = [
        budget for budget in config["checkpoints"]
        if budget <= max(int(row["unique_iteration"]) for row in traces)
    ]
    final = {
        (row["environment"], row["method"], row["workload_id"], int(row["seed"]), int(row["unique_iteration"])): row
        for row in traces if int(row["unique_iteration"]) in checkpoints
    }
    pairs = (
        ("B3_static_prior_baco", "B2_no_prior_baco"),
        ("B4_calibrated_prior_baco", "B2_no_prior_baco"),
        ("B4_calibrated_prior_baco", "B3_static_prior_baco"),
    )
    ratio_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    environments = sorted({row["environment"] for row in traces})
    for environment in environments:
        workload_ids = sorted({
            row["workload_id"] for row in traces if row["environment"] == environment
        })
        seeds = sorted({
            int(row["seed"]) for row in traces if row["environment"] == environment
        })
        for treatment, baseline in pairs:
            for budget in checkpoints:
                current: list[dict[str, Any]] = []
                for workload_id in workload_ids:
                    for seed in seeds:
                        treatment_row = final[(environment, treatment, workload_id, seed, budget)]
                        baseline_row = final[(environment, baseline, workload_id, seed, budget)]
                        speedup = (
                            float(baseline_row["best_so_far_ms"])
                            / float(treatment_row["best_so_far_ms"])
                        )
                        item = {
                            "environment": environment,
                            "comparison": f"{treatment}_vs_{baseline}",
                            "treatment": treatment,
                            "baseline": baseline,
                            "budget": budget,
                            "workload_id": workload_id,
                            "seed": seed,
                            "speedup": speedup,
                        }
                        current.append(item)
                        ratio_rows.append(item)
                point, low, high = paired_cluster_bootstrap(
                    current,
                    int(config["statistics"]["bootstrap_seed"]) + budget,
                    int(config["statistics"]["bootstrap_replicates"]),
                )
                summaries.append({
                    "environment": environment,
                    "comparison": f"{treatment}_vs_{baseline}",
                    "budget": budget,
                    "paired_trajectories": len(current),
                    "workload_clusters": len(workload_ids),
                    "speedup_gmean": point,
                    "ci95_low": low,
                    "ci95_high": high,
                    "ci_excludes_one_in_favor": low > 1.0,
                })
    return ratio_rows, summaries


def build_acceptance(
    config: dict[str, Any],
    liveness: list[dict[str, Any]],
    pool_rows: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    run_summaries: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    calibrations: dict[str, dict[str, Any]],
    smoke: bool,
    partial_scope: bool,
) -> dict[str, Any]:
    liveness_pass = bool(liveness) and all(row["status"] == "PASS" for row in liveness)
    same_pool_pass = bool(pool_rows) and all(row["status"] == "PASS" for row in pool_rows)
    unique_budget_pass = bool(run_summaries) and all(
        int(row["unique_measurements"]) == int(row["budget"])
        and int(row["duplicate_callbacks"]) == 0
        and int(row["objective_cache_hits"]) == 0
        for row in run_summaries
    )
    holdout_prior_reads = {
        environment: int(np.sum(~np.isnan(calibration["y"]) & np.asarray([
            row["split"] == "holdout" for row in calibration["host_records"]
        ])))
        for environment, calibration in calibrations.items()
    }
    leakage_pass = all(value == 0 for value in holdout_prior_reads.values()) and all(
        bool(row["target_read_after_selection"]) for row in traces
    )
    target_comparison = config["acceptance"]["benefit_comparison"]
    environment_evidence: dict[str, list[dict[str, Any]]] = {}
    for row in comparisons:
        if row["comparison"] != target_comparison:
            continue
        environment_evidence.setdefault(row["environment"], []).append(row)
    passing_environments = [
        environment for environment, rows in environment_evidence.items()
        if any(bool(row["ci_excludes_one_in_favor"]) for row in rows)
    ]
    benefit_pass = len(passing_environments) >= int(
        config["acceptance"]["required_environment_count"]
    )
    oracle_pass = same_pool_pass and all(
        len({
            float(row["pool_oracle_ms"])
            for row in pool_rows
            if row["environment"] == environment
            and row["workload_id"] == workload_id
        }) == 1
        for environment in {row["environment"] for row in pool_rows}
        for workload_id in {
            row["workload_id"] for row in pool_rows if row["environment"] == environment
        }
    )
    conditions = {
        "all_search_parameters_pass_liveness_audit": liveness_pass,
        "B2_B3_B4_are_strict_same_pool_controls": same_pool_pass,
        "unique_measurement_budget_and_no_leakage": unique_budget_pass and leakage_pass,
        "calibrated_prior_ci_gain_on_at_least_two_environments": benefit_pass,
        "common_pool_oracle_is_prior_invariant": oracle_pass,
    }
    if smoke:
        status = "SMOKE"
    elif partial_scope:
        status = "PARTIAL"
    else:
        status = "PASS" if all(conditions.values()) else "FAIL"
    claim_boundary = config["claim_boundary"]
    if partial_scope:
        claim_boundary = (
            "Partial single-environment replay on the i7-10750H development host. "
            "It can establish local protocol correctness and local low-budget behavior, "
            "but it does not satisfy the requested two-environment replication condition. "
            "All other layout, threading, architecture, and end-to-end limitations of the "
            "planned full protocol remain in force."
        )
    return {
        "status": status,
        "experiment_id": config["experiment_id"],
        "mode": "smoke" if smoke else "formal",
        "conditions": conditions,
        "passing_benefit_environments": passing_environments,
        "required_benefit_environments": int(
            config["acceptance"]["required_environment_count"]
        ),
        "evaluated_environments": sorted(calibrations),
        "scope_complete_for_two_environment_acceptance": not partial_scope,
        "holdout_prior_target_reads": holdout_prior_reads,
        "holdout_objective_reads": len(traces),
        "holdout_unique_measurements": sum(
            int(row["unique_measurements"]) for row in run_summaries
        ),
        "claim_boundary": claim_boundary,
    }


def write_report(
    config: dict[str, Any],
    acceptance: dict[str, Any],
    fixed: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    pools: dict[str, list[dict[str, Any]]],
    selected_weights: dict[str, float],
) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / "acceptance_report.md"
    lines = [
        "# Same-pool Calibrated-prior Acceptance Report",
        "",
        f"Overall status: `{acceptance['status']}`.",
        "",
        "## Requested conditions",
        "",
        "| Condition | Status |",
        "|---|---|",
    ]
    if acceptance["status"] == "PARTIAL":
        lines[3:3] = [
            "This run intentionally evaluates only the requested local environment. "
            "The two-environment significance condition remains pending.",
            "",
        ]
    labels = {
        "all_search_parameters_pass_liveness_audit": "All search parameters completed liveness audit",
        "B2_B3_B4_are_strict_same_pool_controls": "B2/B3/B4 are strict same-pool controls",
        "unique_measurement_budget_and_no_leakage": "Unique budget and leakage safeguards pass",
        "calibrated_prior_ci_gain_on_at_least_two_environments": "B4 beats no-prior BaCO with CI > 1 on two environments",
        "common_pool_oracle_is_prior_invariant": "Common-pool oracle is invariant",
    }
    for key, value in acceptance["conditions"].items():
        lines.append(f"| {labels[key]} | `{'PASS' if value else 'FAIL'}` |")
    lines.extend([
        "",
        "## Protocol",
        "",
        f"- Canonical pool size range: {min(map(len, pools.values()))}-{max(map(len, pools.values()))}.",
        f"- Unique-candidate budget: {config['budget']}; checkpoints: {config['checkpoints']}.",
        f"- Seeds: {config['seeds']}; no-replacement warm-start samples: {config['doe_samples']}.",
        "- Active parameters: `tile_m`, `tile_n`, `tile_k`.",
        "- `vectorize` is removed as inactive; `pack_mode=ab`, MR=6, and NR=8 are fixed.",
        "- Holdout pool oracles are added only after policy replay.",
        "",
        "## Selected calibration",
        "",
    ])
    for environment, weight in sorted(selected_weights.items()):
        lines.append(f"- `{environment}`: validation-selected PI model weight `{weight}`.")
    lines.extend([
        "",
        "## Fixed-budget pool efficiency",
        "",
        "| Environment | Method | Budget | Relative to oracle | Oracle hit rate |",
        "|---|---|---:|---:|---:|",
    ])
    for row in fixed:
        lines.append(
            f"| {row['environment']} | {row['method']} | {row['budget']} | "
            f"{float(row['relative_to_pool_oracle_gmean']):.3f} | "
            f"{100.0 * float(row['oracle_hit_rate']):.1f}% |"
        )
    lines.extend([
        "",
        "## Paired B4 versus B2",
        "",
        "A speedup above one favors the calibrated prior. Confidence intervals resample workload clusters.",
        "",
        "| Environment | Budget | Speedup | 95% CI | Verdict |",
        "|---|---:|---:|---:|---|",
    ])
    target = config["acceptance"]["benefit_comparison"]
    for row in comparisons:
        if row["comparison"] != target:
            continue
        verdict = "better" if row["ci_excludes_one_in_favor"] else "inconclusive"
        lines.append(
            f"| {row['environment']} | {row['budget']} | "
            f"{float(row['speedup_gmean']):.3f}x | "
            f"[{float(row['ci95_low']):.3f}, {float(row['ci95_high']):.3f}] | {verdict} |"
        )
    lines.extend([
        "",
        "## Leakage boundary",
        "",
        "B2 samples the DOE uniformly; B3/B4 warm-start from the highest-ranked candidates under their declared soft prior over the same pool. "
        "The calibration target vector contains design and validation observations only; holdout entries are `NaN`. "
        "During replay, a holdout runtime is read only inside the objective callback after BaCO returns a selected token. "
        "The run fails on a duplicate callback, so every formal callback consumes exactly one unique measurement.",
        "",
        "## Claim boundary",
        "",
        acceptance["claim_boundary"],
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument(
        "--environment",
        action="append",
        help="run only the named environment ID; may be repeated",
    )
    args = parser.parse_args()
    config = load_config()
    workloads = load_workloads(config)
    pools = canonicalize_pool(config, workloads)
    environment_configs = list(config["environments"])
    if args.environment:
        requested = set(args.environment)
        known = {row["id"] for row in environment_configs}
        unknown = requested - known
        if unknown:
            raise ValueError(f"unknown environment IDs: {sorted(unknown)}")
        environment_configs = [
            row for row in environment_configs if row["id"] in requested
        ]
    hosts = [
        load_host_corpus(environment, pools, workloads)
        for environment in environment_configs
    ]
    if args.smoke:
        hosts = hosts[:1]

    liveness = parameter_liveness_audit(pools, hosts, config)
    write_csv(PROCESSED / "parameter_liveness.csv", liveness)
    excluded = [
        {"parameter": name, "search_status": "EXCLUDED", "reason": reason}
        for name, reason in config["excluded_inactive_parameters"].items()
    ]
    write_csv(PROCESSED / "excluded_parameters.csv", excluded)
    if not all(row["status"] == "PASS" for row in liveness):
        raise RuntimeError(f"parameter liveness audit failed: {liveness}")

    calibrations: dict[str, dict[str, Any]] = {}
    precision_rows: list[dict[str, Any]] = []
    weight_rows: list[dict[str, Any]] = []
    selected_weights: dict[str, float] = {}
    for host in hosts:
        environment_id = host["environment"]["id"]
        calibration = prepare_calibration(host, workloads, config)
        calibration["host_records"] = host["records"]
        calibrations[environment_id] = calibration
        precision_rows.extend(calibration["validation_rows"])
        selected_weight, current_weight_rows = select_model_weight(
            host, calibration, config, args.force, args.smoke
        )
        selected_weights[environment_id] = selected_weight
        weight_rows.extend(current_weight_rows)
    write_csv(PROCESSED / "precision_selection.csv", precision_rows)
    write_csv(PROCESSED / "model_weight_selection.csv", weight_rows)
    write_json(PROCESSED / "selected_calibration.json", {
        environment: {
            "prior_precision": calibration["selected_precision"],
            "model_weight": selected_weights[environment],
            "noise_variance": calibration["posterior"].noise_variance,
            "feature_count": len(calibration["posterior"].mean),
            "holdout_target_values_in_prior": int(np.sum(~np.isnan(calibration["y"]) & np.asarray([
                row["split"] == "holdout" for row in calibration["host_records"]
            ]))),
        }
        for environment, calibration in calibrations.items()
    })

    traces, run_summaries = run_holdout(
        hosts, calibrations, selected_weights, config, args.force, args.smoke
    )
    write_csv(RAW / "holdout_traces.csv", traces)
    write_csv(RAW / "run_summaries.csv", run_summaries)
    pool_rows, pool_pass = same_pool_audit(hosts, traces)
    if not pool_pass:
        raise RuntimeError("strict same-pool audit failed")
    write_csv(PROCESSED / "same_pool_audit.csv", pool_rows)
    checkpoints = [
        budget for budget in config["checkpoints"]
        if budget <= max(int(row["unique_iteration"]) for row in traces)
    ]
    fixed = summarize_fixed_budget(traces, checkpoints)
    write_csv(PROCESSED / "fixed_budget_results.csv", fixed)
    ratio_rows, comparisons = paired_comparisons(traces, config)
    write_csv(PROCESSED / "paired_ratios.csv", ratio_rows)
    write_csv(PROCESSED / "paired_comparisons.csv", comparisons)

    partial_scope = (
        not args.smoke
        and len(hosts) < int(config["acceptance"]["required_environment_count"])
    )
    acceptance = build_acceptance(
        config, liveness, pool_rows, traces, run_summaries,
        comparisons, calibrations, args.smoke, partial_scope
    )
    write_json(PROCESSED / "acceptance_summary.json", acceptance)
    report = write_report(
        config, acceptance, fixed, comparisons, pools, selected_weights
    )
    outputs = [
        PROCESSED / "parameter_liveness.csv",
        PROCESSED / "excluded_parameters.csv",
        PROCESSED / "precision_selection.csv",
        PROCESSED / "model_weight_selection.csv",
        PROCESSED / "selected_calibration.json",
        RAW / "holdout_traces.csv",
        RAW / "run_summaries.csv",
        PROCESSED / "same_pool_audit.csv",
        PROCESSED / "fixed_budget_results.csv",
        PROCESSED / "paired_ratios.csv",
        PROCESSED / "paired_comparisons.csv",
        PROCESSED / "acceptance_summary.json",
        report,
    ]
    inputs = [
        CONFIG_PATH,
        resolve_experiment_path(config["workloads"]),
        resolve_experiment_path(config["pool_metadata"]),
        *[
            resolve_experiment_path(environment["aggregates"])
            for environment in environment_configs
        ],
        Path(__file__),
        Path(__file__).with_name("experiment_lib.py"),
    ]
    manifest = runtime_manifest(inputs, outputs)
    manifest.update({
        "baco_source": str((EXPERIMENTS.parent / "third_party" / "baco").resolve()),
        "input_pool_sha256": sha256(resolve_experiment_path(config["pool_metadata"])),
        "selected_model_weights": selected_weights,
        "status": acceptance["status"],
    })
    write_json(PROVENANCE / "manifest.json", manifest)
    print(json.dumps(acceptance, indent=2), flush=True)
    if not args.smoke and acceptance["status"] == "FAIL":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
