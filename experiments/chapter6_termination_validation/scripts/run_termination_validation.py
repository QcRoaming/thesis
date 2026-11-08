#!/usr/bin/env python3
"""Run the three pre-registered termination validation experiments."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
REPO = EXPERIMENTS.parents[2]
RAW = PROJECT / "raw"
PROCESSED = PROJECT / "processed"
REPORTS = PROJECT / "reports"
PROVENANCE = PROJECT / "provenance"
BUILD = PROJECT / "build"

SAME_POOL_SCRIPTS = EXPERIMENTS / "chapter6_same_pool_prior" / "scripts"
CGO_SCRIPTS = EXPERIMENTS / "cgo_extension" / "scripts"
for path in (SAME_POOL_SCRIPTS, CGO_SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import experiment_lib as base  # noqa: E402
import run_experiment as baco_runner  # noqa: E402
import cgo_common  # noqa: E402


METHODS = (
    "B2_no_prior_baco",
    "D0_data_only_baco",
    "D1_expert_plus_data_baco",
)
MODEL_METHODS = METHODS[1:]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_path(relative: str) -> Path:
    path = (EXPERIMENTS / relative).resolve()
    if EXPERIMENTS.resolve() not in path.parents:
        raise ValueError(f"source path escapes experiment root: {relative}")
    return path


def load_state() -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    config = read_json(PROJECT / "data" / "experiment_config.json")
    same_pool_config = read_json(source_path(config["source_same_pool_config"]))
    workloads = base.load_workloads(same_pool_config)
    pools = base.canonicalize_pool(same_pool_config, workloads)
    environment = next(
        row for row in same_pool_config["environments"]
        if row["id"] == config["environment"]
    )
    host = base.load_host_corpus(environment, pools, workloads)
    return config, same_pool_config, workloads, pools, host


def selected_feature_names(mode: str) -> list[str]:
    names = base.feature_names()
    expert = {
        name for name in names
        if name == "active_static_score" or name.endswith("_x_static")
    }
    if mode == "data_only":
        return [name for name in names if name not in expert]
    if mode == "expert_plus_data":
        return names
    raise KeyError(mode)


def prepare_model(
    mode: str,
    host: dict[str, Any],
    workloads: dict[str, dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    started = time.perf_counter()
    rows = host["records"]
    all_names = base.feature_names()
    names = selected_feature_names(mode)
    positions = [all_names.index(name) for name in names]
    raw_all = np.vstack([
        base.raw_features(row, workloads[row["workload_id"]]) for row in rows
    ])
    raw_x = raw_all[:, positions]
    design_mask = np.asarray([row["split"] == "design" for row in rows])
    validation_mask = np.asarray([row["split"] == "validation" for row in rows])
    holdout_mask = np.asarray([row["split"] == "holdout" for row in rows])
    y = np.full(len(rows), np.nan, dtype=float)
    for index, row in enumerate(rows):
        if row["split"] in set(config["calibration"]["target_splits"]):
            y[index] = math.log(float(row["runtime_ms"]) / float(row["b5_ms"]))
    feature_space = base.FeatureSpace.fit(raw_x[design_mask])
    x = feature_space.transform(raw_x)
    minimum_noise = float(config["calibration"]["minimum_noise_variance"])
    validation_rows: list[dict[str, Any]] = []
    candidates: list[tuple[float, float, Any]] = []
    validation_budget = max(int(value) for value in config["checkpoints"])
    for precision in config["calibration"]["prior_precision_candidates"]:
        posterior = base.fit_posterior(
            x[design_mask], y[design_mask], float(precision), minimum_noise
        )
        regrets: list[float] = []
        for workload_id, indices in sorted(host["by_workload"].items()):
            if rows[indices[0]]["split"] != "validation":
                continue
            order = sorted(
                indices,
                key=lambda index: (
                    float(x[index] @ posterior.mean),
                    rows[index]["canonical_id"],
                ),
            )
            oracle = min(float(rows[index]["runtime_ms"]) for index in indices)
            best = math.inf
            for index in order[:validation_budget]:
                best = min(best, float(rows[index]["runtime_ms"]))
                regrets.append(-math.log(oracle / best))
        objective = float(np.mean(regrets))
        validation_rows.append({
            "model": mode,
            "prior_precision": float(precision),
            "mean_log_simple_regret_auc": objective,
            "design_target_rows": int(design_mask.sum()),
            "validation_target_rows": int(validation_mask.sum()),
            "validation_budget": validation_budget,
        })
        candidates.append((objective, float(precision), posterior))
    _, selected_precision, posterior = min(
        candidates, key=lambda item: (item[0], item[1])
    )
    fit_wall_ms = (time.perf_counter() - started) * 1000.0
    return {
        "mode": mode,
        "feature_names": names,
        "excluded_feature_names": [name for name in all_names if name not in names],
        "x": x,
        "y": y,
        "posterior": posterior,
        "selected_precision": selected_precision,
        "validation_rows": validation_rows,
        "fit_wall_ms": fit_wall_ms,
        "design_mask": design_mask,
        "validation_mask": validation_mask,
        "holdout_mask": holdout_mask,
    }


def model_prior(
    model: dict[str, Any],
    indices: list[int],
    host: dict[str, Any],
    config: dict[str, Any],
) -> list[float]:
    rows = host["records"]
    ordered = sorted(indices, key=lambda index: rows[index]["canonical_id"])
    prediction = model["x"][ordered] @ model["posterior"].mean
    scale = max(math.sqrt(model["posterior"].noise_variance), 0.05)
    return base.normalize_probabilities(
        -prediction / scale,
        float(config["calibration"]["prior_probability_floor"]),
    ).tolist()


def load_measurement_costs(config: dict[str, Any]) -> dict[tuple[str, str], float]:
    costs: dict[tuple[str, str], float] = defaultdict(float)
    for row in read_csv(source_path(config["source_trials"])):
        if not row["variant"].startswith("candidate:"):
            continue
        costs[(row["workload_id"], row["candidate_id"])] += float(
            row["benchmark_wall_ms"]
        )
    return dict(costs)


def run_trajectories(
    config: dict[str, Any],
    host: dict[str, Any],
    models: dict[str, dict[str, Any]],
    measurement_costs: dict[tuple[str, str], float],
    force: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    baco_runner.BUILD = BUILD
    rows = host["records"]
    traces: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    holdout_ids = [
        workload_id for workload_id, indices in sorted(host["by_workload"].items())
        if rows[indices[0]]["split"] == "holdout"
    ]
    total_runs = len(holdout_ids) * len(METHODS) * len(config["seeds"])
    completed = 0
    for workload_id in holdout_ids:
        indices = host["by_workload"][workload_id]
        oracle = min(float(rows[index]["runtime_ms"]) for index in indices)
        fingerprint = base.pool_fingerprint([rows[index] for index in indices])
        for method in METHODS:
            if method == "B2_no_prior_baco":
                prior = None
            elif method == "D0_data_only_baco":
                prior = model_prior(models["data_only"], indices, host, config)
            else:
                prior = model_prior(models["expert_plus_data"], indices, host, config)
            for seed in config["seeds"]:
                trajectory = baco_runner.run_baco_trajectory(
                    phase="termination_holdout_v1",
                    host=host,
                    workload_id=workload_id,
                    indices=indices,
                    method=method,
                    seed=int(seed),
                    budget=len(indices),
                    prior=prior,
                    model_weight=float(config["model_weight"]),
                    config={
                        **read_json(source_path(config["source_same_pool_config"])),
                        "doe_samples": int(config["doe_samples"]),
                    },
                    force=force,
                )
                cumulative_wall = 0.0
                for callback in trajectory["callbacks"]:
                    cost_key = (
                        callback["workload_id"], callback["source_candidate_id"]
                    )
                    measurement_wall = measurement_costs[cost_key]
                    cumulative_wall += measurement_wall
                    enriched = dict(callback)
                    enriched.update({
                        "pool_oracle_ms": oracle,
                        "oracle_fraction": oracle / float(callback["best_so_far_ms"]),
                        "candidate_measurement_wall_ms": measurement_wall,
                        "cumulative_measurement_wall_ms": cumulative_wall,
                    })
                    traces.append(enriched)
                summary = dict(trajectory["summary"])
                summary.update({
                    "pool_oracle_ms": oracle,
                    "pool_fingerprint": fingerprint,
                    "pool_exhausted": len(trajectory["callbacks"]) == len(indices),
                    "measurement_wall_ms": cumulative_wall,
                })
                summaries.append(summary)
                completed += 1
                print(
                    f"trajectory {completed}/{total_runs}: {workload_id} "
                    f"{method} seed={seed}",
                    flush=True,
                )
    return traces, summaries


def fixed_budget_results(
    traces: list[dict[str, Any]], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_run: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in traces:
        by_run[(row["workload_id"], row["method"], int(row["seed"]))].append(row)
    fixed: list[dict[str, Any]] = []
    t95: list[dict[str, Any]] = []
    threshold = float(config["time_to_oracle"]["fraction"])
    for (workload_id, method, seed), values in sorted(by_run.items()):
        values.sort(key=lambda row: int(row["unique_iteration"]))
        first = values[0]
        for checkpoint in config["checkpoints"]:
            row = values[int(checkpoint) - 1]
            fixed.append({
                "environment": row["environment"],
                "workload_id": workload_id,
                "family": row["family"],
                "method": method,
                "seed": seed,
                "budget": int(checkpoint),
                "best_ms": float(row["best_so_far_ms"]),
                "pool_oracle_ms": float(row["pool_oracle_ms"]),
                "oracle_fraction": float(row["oracle_fraction"]),
            })
        hit = next(row for row in values if float(row["oracle_fraction"]) >= threshold)
        t95.append({
            "environment": hit["environment"],
            "workload_id": workload_id,
            "family": hit["family"],
            "method": method,
            "seed": seed,
            "pool_size": int(hit["pool_size"]),
            "evaluations_to_95_oracle": int(hit["unique_iteration"]),
            "measurement_wall_to_95_ms": float(hit["cumulative_measurement_wall_ms"]),
            "kernel_runtime_lower_bound_to_95_ms": sum(
                float(row["runtime_ms"])
                for row in values[: int(hit["unique_iteration"])]
            ),
            "oracle_fraction_at_hit": float(hit["oracle_fraction"]),
            "reached": True,
        })
    aggregate: list[dict[str, Any]] = []
    for checkpoint in config["checkpoints"]:
        for method in METHODS:
            selected = [
                row for row in fixed
                if row["budget"] == checkpoint and row["method"] == method
            ]
            aggregate.append({
                "method": method,
                "budget": checkpoint,
                "runs": len(selected),
                "workloads": len({row["workload_id"] for row in selected}),
                "gmean_oracle_fraction": base.geometric_mean(
                    row["oracle_fraction"] for row in selected
                ),
                "mean_best_ms": float(np.mean([row["best_ms"] for row in selected])),
            })
    return fixed, aggregate, t95


def paired_comparisons(
    fixed: list[dict[str, Any]], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lookup = {
        (row["workload_id"], row["seed"], row["budget"], row["method"]): row
        for row in fixed
    }
    pairs = (
        ("D1_expert_plus_data_baco", "D0_data_only_baco"),
        ("D0_data_only_baco", "B2_no_prior_baco"),
        ("D1_expert_plus_data_baco", "B2_no_prior_baco"),
    )
    ratios: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    for test, reference in pairs:
        for budget in config["checkpoints"]:
            selected: list[dict[str, Any]] = []
            keys = sorted({
                (row["workload_id"], row["seed"])
                for row in fixed if row["budget"] == budget
            })
            for workload_id, seed in keys:
                test_row = lookup[(workload_id, seed, budget, test)]
                ref_row = lookup[(workload_id, seed, budget, reference)]
                value = {
                    "test_method": test,
                    "reference_method": reference,
                    "budget": budget,
                    "workload_id": workload_id,
                    "seed": seed,
                    "speedup": float(ref_row["best_ms"]) / float(test_row["best_ms"]),
                }
                selected.append(value)
                ratios.append(value)
            point, lower, upper = base.paired_cluster_bootstrap(
                selected,
                int(config["statistics"]["bootstrap_seed"]) + budget,
                int(config["statistics"]["bootstrap_replicates"]),
            )
            comparisons.append({
                "test_method": test,
                "reference_method": reference,
                "budget": budget,
                "paired_runs": len(selected),
                "clustered_workloads": len({row["workload_id"] for row in selected}),
                "gmean_speedup": point,
                "ci95_lower": lower,
                "ci95_upper": upper,
                "ci_excludes_one_in_favor": lower > 1.0,
            })
    return ratios, comparisons


def summarize_time_to_95(t95: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for method in METHODS:
        selected = [row for row in t95 if row["method"] == method]
        evaluations = np.asarray([
            float(row["evaluations_to_95_oracle"]) for row in selected
        ])
        wall = np.asarray([
            float(row["measurement_wall_to_95_ms"]) for row in selected
        ])
        output.append({
            "method": method,
            "runs": len(selected),
            "workloads": len({row["workload_id"] for row in selected}),
            "mean_evaluations_to_95_oracle": float(evaluations.mean()),
            "median_evaluations_to_95_oracle": float(np.median(evaluations)),
            "p90_evaluations_to_95_oracle": float(np.quantile(evaluations, 0.90)),
            "mean_measurement_wall_to_95_ms": float(wall.mean()),
            "median_measurement_wall_to_95_ms": float(np.median(wall)),
            "all_runs_reached_95_oracle": all(bool(row["reached"]) for row in selected),
        })
    return output


def calibration_costs(
    config: dict[str, Any],
    host: dict[str, Any],
    models: dict[str, dict[str, Any]],
    measurement_costs: dict[tuple[str, str], float],
    t95: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    calibration_records = [
        row for row in host["records"]
        if row["split"] in set(config["calibration"]["target_splits"])
    ]
    measurement_wall = sum(
        measurement_costs[(row["workload_id"], row["source_candidate_id"])]
        for row in calibration_records
    )
    manifests = read_json(source_path(config["source_manifests"]))["candidates"]
    unique_candidates = sorted({row["source_candidate_id"] for row in calibration_records})
    compile_wall = sum(float(manifests[candidate]["pipeline_ms"]) for candidate in unique_candidates)
    by_key = {
        (row["workload_id"], row["seed"], row["method"]): row for row in t95
    }
    holdouts = sorted({row["workload_id"] for row in t95})
    output: list[dict[str, Any]] = []
    for method, mode in (
        ("D0_data_only_baco", "data_only"),
        ("D1_expert_plus_data_baco", "expert_plus_data"),
    ):
        per_workload: list[dict[str, float]] = []
        for workload_id in holdouts:
            eval_savings = []
            wall_savings = []
            for seed in config["seeds"]:
                baseline = by_key[(workload_id, int(seed), "B2_no_prior_baco")]
                tested = by_key[(workload_id, int(seed), method)]
                eval_savings.append(
                    float(baseline["evaluations_to_95_oracle"])
                    - float(tested["evaluations_to_95_oracle"])
                )
                wall_savings.append(
                    float(baseline["measurement_wall_to_95_ms"])
                    - float(tested["measurement_wall_to_95_ms"])
                )
            per_workload.append({
                "eval": float(np.mean(eval_savings)),
                "wall": float(np.mean(wall_savings)),
            })
        mean_eval_saving = float(np.mean([row["eval"] for row in per_workload]))
        mean_wall_saving = float(np.mean([row["wall"] for row in per_workload]))
        fit_wall = float(models[mode]["fit_wall_ms"])
        no_compile_cost = measurement_wall + fit_wall
        complete_cost = compile_wall + no_compile_cost
        horizon = int(config["time_to_oracle"]["amortization_horizon_holdout_workloads"])
        observed_wall_saving = sum(row["wall"] for row in per_workload)
        observed_eval_saving = sum(row["eval"] for row in per_workload)
        output.append({
            "method": method,
            "calibration_target_rows": len(calibration_records),
            "design_target_rows": sum(row["split"] == "design" for row in calibration_records),
            "validation_target_rows": sum(row["split"] == "validation" for row in calibration_records),
            "unique_compiled_candidates": len(unique_candidates),
            "observed_calibration_measurement_wall_ms": measurement_wall,
            "observed_unique_compile_pipeline_wall_ms": compile_wall,
            "model_fit_wall_ms": fit_wall,
            "calibration_wall_without_compile_ms": no_compile_cost,
            "complete_calibration_wall_ms": complete_cost,
            "mean_evaluations_saved_per_future_workload_vs_b2": mean_eval_saving,
            "mean_measurement_wall_saved_per_future_workload_vs_b2_ms": mean_wall_saving,
            "observed_holdout_evaluations_saved_vs_b2": observed_eval_saving,
            "observed_holdout_measurement_wall_saved_vs_b2_ms": observed_wall_saving,
            "count_break_even_workloads": (
                len(calibration_records) / mean_eval_saving if mean_eval_saving > 0 else None
            ),
            "wall_break_even_workloads_without_compile": (
                no_compile_cost / mean_wall_saving if mean_wall_saving > 0 else None
            ),
            "wall_break_even_workloads_with_compile": (
                complete_cost / mean_wall_saving if mean_wall_saving > 0 else None
            ),
            "amortization_horizon_workloads": horizon,
            "amortized_within_horizon_without_compile": (
                mean_wall_saving > 0 and observed_wall_saving >= no_compile_cost
            ),
            "amortized_within_horizon_with_compile": (
                mean_wall_saving > 0 and observed_wall_saving >= complete_cost
            ),
        })
    return output


def second_microkernel_audit(
    config: dict[str, Any],
    workloads: dict[str, dict[str, Any]],
    summaries: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    generator = EXPERIMENTS / "chapter4_space" / "scripts" / "chapter4lib.py"
    runtime_registry = EXPERIMENTS / "cgo_extension" / "scripts" / "cgo_common.py"
    adapter = EXPERIMENTS / "cgo_extension" / "runtime" / "blis_microkernel_adapter.cpp"
    compiler_pass = REPO / "midend" / "lib" / "Conversion" / "MatMulOptimization" / "MatMulBlisMicrokernel.cpp"
    before = sha256(generator)
    source = generator.read_text(encoding="utf-8")
    contract_specific_tokens = {
        token: len(re.findall(re.escape(token), source, flags=re.IGNORECASE))
        for token in ("f32", "f64", "6x16", "6x8", "sgemm", "dgemm")
    }
    generated = cgo_common.build_contract_state(
        "f64", list(workloads.values()), pool_size=28
    )
    contract_ids = sorted({item["contract"]["id"] for item in generated.values()})
    paths = defaultdict(int)
    for item in generated.values():
        for row in item["pool"]:
            paths[row["predicted_path"]] += 1
    after = sha256(generator)

    pool_rows = read_csv(EXPERIMENTS / "cgo_extension" / "processed" / "f64_contract_pools.csv")
    manifest_document = read_json(source_path(config["source_manifests"]))
    candidates = manifest_document["candidates"]
    runtime_rows: list[dict[str, Any]] = []
    measurement = {"warmups": 1, "repeats": 3, "inner_iters": 1}
    for expected_path in ("direct", "adapt"):
        selected = next(
            row for row in pool_rows
            if row["predicted_path"] == expected_path and row["candidate_id"] in candidates
        )
        workload = workloads[selected["workload_id"]]
        result = cgo_common.measure_live(
            candidates[selected["candidate_id"]],
            workload,
            measurement,
            BUILD / "second_microkernel" / f"{expected_path}.log",
            row=selected,
        )
        runtime_rows.append({
            "package": "blis_haswell_f64_6x8",
            "workload_id": workload["id"],
            "candidate_id": selected["candidate_id"],
            "predicted_path": expected_path,
            "observed_path": result["observed_path"],
            "status": result["status"],
            "max_abs_diff": result["max_abs_diff"],
            "fringe_calls": int(float(result.get("fringe_calls", 0))),
            "expected_fringe_calls": int(result["expected_fringe_calls"]),
            "benchmark_wall_ms": result["benchmark_wall_ms"],
            "executable_sha256": result["executable_sha256"],
        })

    formal = read_json(
        EXPERIMENTS / "cgo_extension" / "processed" / "f64_contract_summary.json"
    )
    compiler_text = compiler_pass.read_text(encoding="utf-8")
    registry_text = runtime_registry.read_text(encoding="utf-8")
    adapter_text = adapter.read_text(encoding="utf-8")
    all_search_complete = all(
        int(row["unique_measurements"]) == int(row["budget"])
        and int(row["duplicate_callbacks"]) == 0
        and bool(row["pool_exhausted"])
        for row in summaries
    )
    conditions = {
        "core_generator_hash_unchanged": before == after,
        "core_generator_has_no_contract_specific_tokens": all(
            count == 0 for count in contract_specific_tokens.values()
        ),
        "f64_contract_selected_for_all_workloads": contract_ids == ["haswell_f64_gemm_6x8"],
        "generated_pool_contains_direct_and_adapt": paths["direct"] > 0 and paths["adapt"] > 0,
        "fresh_direct_and_adapt_runtime_pass": all(
            row["status"] == "PASS" and row["predicted_path"] == row["observed_path"]
            for row in runtime_rows
        ),
        "formal_36_workload_path_audit_pass": (
            formal["status"] == "PASS" and formal["all_predictions_match"]
        ),
        "full_pool_search_completes_without_duplicates": all_search_complete,
        "kernel_and_adapter_symbols_registered": all(
            symbol in adapter_text
            for symbol in (
                "bli_dgemm_haswell_asm_6x8",
                "buddy_blis_dgemm_6x8",
                "buddy_blis_dgemm_6x8_fringe",
            )
        ),
        "compiler_uses_shared_element_type_codegen": (
            "elementType.isF32()" in compiler_text
            and "elementType.isF64()" in compiler_text
            and "getFloatAttr(elementType" in compiler_text
        ),
    }
    second_microkernel_go = all(conditions.values())
    audit = {
        "second_microkernel_status": "GO" if second_microkernel_go else "NO_GO",
        "independent_backend_status": "NOT_TESTED",
        "validation_mode": "Post-hoc structural audit of the existing f64 package plus fresh direct/adapt executions; not a clean-room replay from an f32-only revision.",
        "core_generator_sha256_before": before,
        "core_generator_sha256_after": after,
        "core_generator_contract_specific_token_counts": contract_specific_tokens,
        "generated_workloads": len(generated),
        "generated_pool_rows": sum(len(item["pool"]) for item in generated.values()),
        "generated_path_counts": dict(sorted(paths.items())),
        "selected_contract_ids": contract_ids,
        "formal_candidate_binaries": formal["candidate_binaries"],
        "formal_trial_rows": formal["trial_rows"],
        "formal_path_predictions_match": formal["all_predictions_match"],
        "runtime_registry_is_descriptor_driven": "DTYPES =" not in registry_text,
        "runtime_registry_boundary": "The experiment runtime still uses an explicit two-entry DTYPES registry; this is package registration, not generic backend discovery.",
        "compiler_boundary": "The shared materialization pass accepts f32/f64 and emits element-type-generic packing loops. No separate f64 code-generation branch is present, but the pass is not arbitrary-dtype or arbitrary-ABI generic.",
        "conditions": conditions,
        "claim_boundary": "This establishes that the current system supports a second BLIS Haswell microkernel Contract (f64 6x8) with the unchanged core space generator. Because the f64 support predates this post-hoc audit, it is not a clean-room history proof. It does not establish a second library, ISA, or independent backend.",
    }
    return audit, runtime_rows


def build_acceptance(
    comparisons: list[dict[str, Any]],
    costs: list[dict[str, Any]],
    extension: dict[str, Any],
) -> dict[str, Any]:
    expert_rows = [
        row for row in comparisons
        if row["test_method"] == "D1_expert_plus_data_baco"
        and row["reference_method"] == "D0_data_only_baco"
    ]
    expert_go = len(expert_rows) == 2 and all(
        row["ci95_lower"] > 1.0 for row in expert_rows
    )
    expert_cost = next(
        row for row in costs if row["method"] == "D1_expert_plus_data_baco"
    )
    practical_go = bool(expert_cost["amortized_within_horizon_with_compile"])
    second_go = extension["second_microkernel_status"] == "GO"
    return {
        "schema_version": 1,
        "experiment_id": "thesis.chapter6_termination_validation",
        "status": "GO" if expert_go and practical_go and second_go else "MIXED",
        "termination_decisions": {
            "claim_expert_performance_rules_have_incremental_value": (
                "GO" if expert_go else "STOP"
            ),
            "claim_practical_search_savings_after_calibration": (
                "GO" if practical_go else "STOP"
            ),
            "claim_second_microkernel_contract_is_extensible": (
                "GO" if second_go else "STOP"
            ),
            "claim_independent_backend_extensibility": "NOT_TESTED",
        },
        "conditions": {
            "expert_plus_data_ci_above_one_at_budget_5_and_10": expert_go,
            "complete_calibration_cost_amortized_within_12_holdouts": practical_go,
            "second_microkernel_contract_gate": second_go,
        },
        "thesis_viability_if_performance_gates_fail": "YES_WITH_REFRAMING",
        "thesis_boundary": "A master's thesis remains defensible as a compiler-system construction and rigorous boundary study: hard compatibility knowledge, executable Transform/LLVM/BLIS integration, negative evidence for soft performance transfer, calibration economics, and a scoped second-Contract extension. It must not claim broadly beneficial expert performance priors or backend-agnostic extensibility without supporting evidence.",
    }


def write_report(
    config: dict[str, Any],
    aggregate: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    t95_summary: list[dict[str, Any]],
    costs: list[dict[str, Any]],
    extension: dict[str, Any],
    acceptance: dict[str, Any],
) -> None:
    aggregate_lookup = {(row["method"], row["budget"]): row for row in aggregate}
    comparison_lookup = {
        (row["test_method"], row["reference_method"], row["budget"]): row
        for row in comparisons
    }
    lines = [
        "# Three termination validation results",
        "",
        "## Registered decisions",
        "",
    ]
    for key, value in acceptance["termination_decisions"].items():
        lines.append(f"- `{key}`: **{value}**")
    lines.extend(["", "## Data-only vs Expert+Data", ""])
    for budget in config["checkpoints"]:
        data = aggregate_lookup[("D0_data_only_baco", budget)]
        expert = aggregate_lookup[("D1_expert_plus_data_baco", budget)]
        comp = comparison_lookup[(
            "D1_expert_plus_data_baco", "D0_data_only_baco", budget
        )]
        lines.append(
            f"- Budget {budget}: Data-only oracle fraction "
            f"{data['gmean_oracle_fraction']:.4f}; Expert+Data "
            f"{expert['gmean_oracle_fraction']:.4f}; paired speedup "
            f"{comp['gmean_speedup']:.4f} "
            f"(95% CI {comp['ci95_lower']:.4f}-{comp['ci95_upper']:.4f})."
        )
    lines.extend([
        "",
        "The hard Contract and candidate pool are shared. Therefore this comparison",
        "tests only the incremental value of BLIS-derived soft performance-score",
        "features after target data are available.",
        "",
        "## Time-to-95%-oracle and amortization",
        "",
    ])
    for row in t95_summary:
        lines.append(
            f"- `{row['method']}` reaches 95%-oracle in "
            f"{row['mean_evaluations_to_95_oracle']:.2f} evaluations on average "
            f"(median {row['median_evaluations_to_95_oracle']:.1f}, "
            f"p90 {row['p90_evaluations_to_95_oracle']:.1f})."
        )
    lines.append("")
    for row in costs:
        break_even = row["wall_break_even_workloads_with_compile"]
        break_even_text = "infinite" if break_even is None else f"{break_even:.1f} workloads"
        lines.append(
            f"- `{row['method']}`: {row['calibration_target_rows']} calibration target "
            f"rows, {row['complete_calibration_wall_ms'] / 1000.0:.2f} s complete "
            f"observed cost, {row['mean_evaluations_saved_per_future_workload_vs_b2']:.3f} "
            f"mean evaluations saved per holdout, compile-inclusive break-even "
            f"{break_even_text}; amortized in 12 workloads = "
            f"{row['amortized_within_horizon_with_compile']}."
        )
    lines.extend([
        "",
        "Cost accounting uses measured compiler pipeline and benchmark subprocess wall",
        "times. The kernel-runtime-only values remain lower bounds and are not used for",
        "the practical gate.",
        "",
        "## Second microkernel package", "",
        f"- Second Contract status: **{extension['second_microkernel_status']}**.",
        f"- Generated workloads: {extension['generated_workloads']}; pool rows: "
        f"{extension['generated_pool_rows']}; paths: {extension['generated_path_counts']}.",
        f"- Frozen formal evidence: {extension['formal_candidate_binaries']} binaries and "
        f"{extension['formal_trial_rows']} trial rows, path match = "
        f"{extension['formal_path_predictions_match']}.",
        f"- Independent backend status: **{extension['independent_backend_status']}**.",
        f"- Validation mode: {extension['validation_mode']}",
        "",
        extension["claim_boundary"],
        "",
        "## Thesis interpretation", "",
        acceptance["thesis_boundary"],
        "",
        f"Claim boundary: {config['claim_boundary']}",
    ])
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "termination_validation_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    for directory in (RAW, PROCESSED, REPORTS, PROVENANCE, BUILD):
        directory.mkdir(parents=True, exist_ok=True)

    config, same_pool_config, workloads, pools, host = load_state()
    pool_audit = [{
        "workload_id": workload_id,
        "split": workloads[workload_id]["split"],
        "pool_size": len(pool),
        "pool_fingerprint": base.pool_fingerprint(pool),
        "active_tuple_count": len({
            (row["tile_m"], row["tile_n"], row["tile_k"]) for row in pool
        }),
    } for workload_id, pool in sorted(pools.items())]
    base.write_csv(PROCESSED / "common_pool_audit.csv", pool_audit)

    models = {
        "data_only": prepare_model("data_only", host, workloads, config),
        "expert_plus_data": prepare_model("expert_plus_data", host, workloads, config),
    }
    feature_rows = []
    precision_rows = []
    model_summary = {}
    for mode, model in models.items():
        feature_rows.extend({
            "model": mode,
            "feature": name,
            "included": name in model["feature_names"],
            "expert_performance_feature": (
                name == "active_static_score" or name.endswith("_x_static")
            ),
        } for name in base.feature_names())
        precision_rows.extend(model["validation_rows"])
        model_summary[mode] = {
            "feature_count_with_intercept": len(model["feature_names"]) + 1,
            "included_features": model["feature_names"],
            "excluded_features": model["excluded_feature_names"],
            "selected_prior_precision": model["selected_precision"],
            "noise_variance": model["posterior"].noise_variance,
            "fit_wall_ms": model["fit_wall_ms"],
            "holdout_target_values_in_model": int(np.isfinite(
                model["y"][model["holdout_mask"]]
            ).sum()),
        }
    base.write_csv(PROCESSED / "feature_ablation.csv", feature_rows)
    base.write_csv(PROCESSED / "precision_selection.csv", precision_rows)
    base.write_json(PROCESSED / "model_summary.json", model_summary)

    measurement_costs = load_measurement_costs(config)
    traces, summaries = run_trajectories(
        config, host, models, measurement_costs, args.force
    )
    base.write_csv(RAW / "termination_traces.csv", traces)
    base.write_csv(RAW / "trajectory_summaries.csv", summaries)
    fixed, aggregate, t95 = fixed_budget_results(traces, config)
    t95_summary = summarize_time_to_95(t95)
    ratios, comparisons = paired_comparisons(fixed, config)
    costs = calibration_costs(config, host, models, measurement_costs, t95)
    extension, runtime_rows = second_microkernel_audit(config, workloads, summaries)
    acceptance = build_acceptance(comparisons, costs, extension)

    base.write_csv(PROCESSED / "fixed_budget_results.csv", fixed)
    base.write_csv(PROCESSED / "fixed_budget_aggregate.csv", aggregate)
    base.write_csv(PROCESSED / "paired_ratios.csv", ratios)
    base.write_csv(PROCESSED / "paired_comparisons.csv", comparisons)
    base.write_csv(PROCESSED / "time_to_95_oracle.csv", t95)
    base.write_csv(PROCESSED / "time_to_95_summary.csv", t95_summary)
    base.write_csv(PROCESSED / "calibration_costs.csv", costs)
    base.write_csv(PROCESSED / "second_microkernel_runtime.csv", runtime_rows)
    base.write_json(PROCESSED / "second_microkernel_audit.json", extension)
    base.write_json(PROCESSED / "acceptance_summary.json", acceptance)
    write_report(
        config, aggregate, comparisons, t95_summary, costs, extension, acceptance
    )

    inputs = [
        PROJECT / "data" / "experiment_config.json",
        PROJECT / "data" / "kernel_packages.json",
        source_path(config["source_same_pool_config"]),
        source_path(config["source_workloads"]),
        source_path(config["source_trials"]),
        source_path(config["source_manifests"]),
        EXPERIMENTS / "chapter4_space" / "scripts" / "chapter4lib.py",
        EXPERIMENTS / "cgo_extension" / "runtime" / "blis_microkernel_adapter.cpp",
        REPO / "midend" / "lib" / "Conversion" / "MatMulOptimization" / "MatMulBlisMicrokernel.cpp",
    ]
    outputs = [
        RAW / "termination_traces.csv",
        PROCESSED / "paired_comparisons.csv",
        PROCESSED / "time_to_95_oracle.csv",
        PROCESSED / "time_to_95_summary.csv",
        PROCESSED / "calibration_costs.csv",
        PROCESSED / "second_microkernel_audit.json",
        PROCESSED / "acceptance_summary.json",
        REPORTS / "termination_validation_report.md",
    ]
    base.write_json(PROVENANCE / "manifest.json", {
        "schema_version": 1,
        "experiment_id": config["experiment_id"],
        "inputs": {str(path): sha256(path) for path in inputs},
        "outputs": {str(path): sha256(path) for path in outputs},
        "same_pool_source_schema": same_pool_config["schema_version"],
    })
    print(json.dumps(acceptance, indent=2), flush=True)


if __name__ == "__main__":
    main()
