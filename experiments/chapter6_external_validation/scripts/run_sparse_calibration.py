#!/usr/bin/env python3
"""Run the frozen sparse-calibration finite-pool replay on one x86 corpus."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
CONFIG_PATH = PROJECT / "data" / "experiment_config.json"
FAMILIES = ("k_small", "m_skinny", "model_rect", "n_skinny", "square", "tail")
METHODS = (
    "N0_uniform_without_replacement",
    "D0_data_only_thompson",
    "D1_expert_plus_data_thompson",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_int(*parts: Any) -> int:
    text = ":".join(map(str, parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(text).digest()[:8], "big")


def geometric_mean(values: Iterable[float]) -> float:
    clean = [max(float(value), 1.0e-300) for value in values]
    return math.exp(sum(math.log(value) for value in clean) / len(clean))


def is_true(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def load_workloads(path: Path) -> dict[str, dict[str, Any]]:
    document = read_json(path)
    if document.get("declaration_status") != "frozen_before_measurement":
        raise ValueError("source workload matrix is not frozen")
    workloads = {row["id"]: row for row in document["workloads"]}
    if len(workloads) != len(document["workloads"]):
        raise ValueError("duplicate workload IDs")
    return workloads


def canonicalize_pool(
    path: Path, workloads: dict[str, dict[str, Any]], minimum_size: int
) -> dict[str, list[dict[str, Any]]]:
    raw_by_workload: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(path):
        raw_by_workload[row["workload_id"]].append(row)
    if set(raw_by_workload) != set(workloads):
        raise ValueError("pool/workload ID mismatch")
    pools: dict[str, list[dict[str, Any]]] = {}
    for workload_id, values in sorted(raw_by_workload.items()):
        aliases: dict[tuple[int, int, int], list[dict[str, str]]] = defaultdict(list)
        for row in values:
            if row["pack_mode"] != "ab":
                raise ValueError(f"non-Contract packing in {workload_id}")
            key = (int(row["tile_m"]), int(row["tile_n"]), int(row["tile_k"]))
            aliases[key].append(row)
        pool: list[dict[str, Any]] = []
        for (tile_m, tile_n, tile_k), variants in sorted(aliases.items()):
            variants.sort(key=lambda row: (is_true(row["vectorize"]), row["candidate_id"]))
            representative = variants[0]
            score = float(representative["score"])
            if is_true(representative["vectorize"]):
                score -= 5.0
            pool.append({
                "workload_id": workload_id,
                "canonical_id": f"tm{tile_m}_tn{tile_n}_tk{tile_k}",
                "source_candidate_id": representative["candidate_id"],
                "tile_m": tile_m,
                "tile_n": tile_n,
                "tile_k": tile_k,
                "predicted_path": representative["predicted_path"],
                "active_static_score": score,
                "split": workloads[workload_id]["split"],
                "family": workloads[workload_id]["family"],
            })
        if len(pool) < minimum_size:
            raise ValueError(f"{workload_id} has only {len(pool)} canonical candidates")
        pools[workload_id] = pool
    return pools


def load_host_corpus(
    path: Path,
    environment_id: str,
    pools: dict[str, list[dict[str, Any]]],
    workloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    candidates: dict[tuple[str, str], dict[str, str]] = {}
    baselines: dict[str, float] = {}
    for row in read_csv(path):
        if row["variant"] == "B5_blis":
            baselines[row["workload_id"]] = float(row["median_ms"])
        elif row["variant"].startswith("candidate:"):
            candidates[(row["workload_id"], row["candidate_id"])] = row
    if set(baselines) != set(workloads):
        raise ValueError("aggregate corpus does not contain every BLIS baseline")
    records: list[dict[str, Any]] = []
    by_workload: dict[str, list[int]] = defaultdict(list)
    for workload_id, pool in sorted(pools.items()):
        for candidate in pool:
            key = (workload_id, candidate["source_candidate_id"])
            measured = candidates.get(key)
            if measured is None:
                raise KeyError(f"missing measured canonical representative: {key}")
            if not is_true(measured["all_pass"]):
                raise ValueError(f"failed measured candidate: {key}")
            if measured["observed_path"] != candidate["predicted_path"]:
                raise ValueError(f"path mismatch: {key}")
            record = dict(candidate)
            record.update({
                "environment": environment_id,
                "runtime_ms": float(measured["median_ms"]),
                "b5_ms": baselines[workload_id],
            })
            by_workload[workload_id].append(len(records))
            records.append(record)
    return {"records": records, "by_workload": dict(by_workload), "baselines": baselines}


def feature_names() -> list[str]:
    names = [
        "active_static_score",
        "log2_tile_m", "log2_tile_n", "log2_tile_k",
        "log2_tile_m_over_m", "log2_tile_n_over_n", "log2_tile_k_over_k",
        "m_divisible_by_tile_m", "n_divisible_by_tile_n", "k_divisible_by_tile_k",
        "m_remainder_fraction", "n_remainder_fraction", "k_remainder_fraction",
        "log2_m_block_count", "log2_n_block_count", "log2_k_block_count",
        "log2_tile_area", "log2_tile_volume", "log2_arithmetic_intensity",
        "adapt_path",
    ]
    for family in FAMILIES:
        names.extend([
            f"family_{family}", f"family_{family}_x_static",
            f"family_{family}_x_m_ratio", f"family_{family}_x_n_ratio",
            f"family_{family}_x_k_ratio",
        ])
    return names


def raw_features(row: dict[str, Any], workload: dict[str, Any]) -> np.ndarray:
    tile_m, tile_n, tile_k = float(row["tile_m"]), float(row["tile_n"]), float(row["tile_k"])
    m, n, k = float(workload["m"]), float(workload["n"]), float(workload["k"])
    static = float(row["active_static_score"]) / 100.0
    ratios = [math.log2(tile_m / m), math.log2(tile_n / n), math.log2(tile_k / k)]
    intensity = 2.0 * tile_m * tile_n * tile_k / (
        4.0 * (tile_m * tile_k + tile_k * tile_n + 2.0 * tile_m * tile_n)
    )
    values = [
        static,
        math.log2(tile_m), math.log2(tile_n), math.log2(tile_k),
        *ratios,
        float(m % tile_m == 0), float(n % tile_n == 0), float(k % tile_k == 0),
        (m % tile_m) / m, (n % tile_n) / n, (k % tile_k) / k,
        math.log2(math.ceil(m / tile_m)), math.log2(math.ceil(n / tile_n)),
        math.log2(math.ceil(k / tile_k)), math.log2(tile_m * tile_n),
        math.log2(tile_m * tile_n * tile_k), math.log2(intensity),
        float(row["predicted_path"] == "adapt"),
    ]
    for family in FAMILIES:
        active = float(workload["family"] == family)
        values.extend([
            active, active * static, active * ratios[0], active * ratios[1],
            active * ratios[2],
        ])
    return np.asarray(values, dtype=float)


def selected_positions(mode: str) -> tuple[list[int], list[str]]:
    names = feature_names()
    expert = {name for name in names if name == "active_static_score" or name.endswith("_x_static")}
    selected = names if mode == "expert_plus_data" else [name for name in names if name not in expert]
    return [names.index(name) for name in selected], selected


@dataclass
class Posterior:
    mean: np.ndarray
    covariance: np.ndarray
    noise_variance: float


def fit_posterior(
    x: np.ndarray, y: np.ndarray, prior_precision: float, minimum_noise: float
) -> Posterior:
    dimension = x.shape[1]
    precision = np.eye(dimension) * prior_precision
    precision[0, 0] = prior_precision * 0.01
    initial_covariance = np.linalg.inv(precision + x.T @ x)
    initial_mean = initial_covariance @ (x.T @ y)
    residual = y - x @ initial_mean
    noise = max(float(np.mean(residual * residual)), minimum_noise)
    covariance = np.linalg.inv(precision + (x.T @ x) / noise)
    mean = covariance @ ((x.T @ y) / noise)
    covariance = (covariance + covariance.T) * 0.5
    return Posterior(mean, covariance, noise)


def calibration_order(
    records: list[dict[str, Any]], by_workload: dict[str, list[int]], seed: int
) -> list[int]:
    workload_ids = [
        workload_id for workload_id, indices in by_workload.items()
        if records[indices[0]]["split"] in {"design", "validation"}
    ]
    workload_ids.sort(key=lambda value: stable_int("workload", seed, value))
    queues: dict[str, list[int]] = {}
    for workload_id in workload_ids:
        queues[workload_id] = sorted(
            by_workload[workload_id],
            key=lambda index: stable_int(seed, workload_id, records[index]["canonical_id"]),
        )
    order: list[int] = []
    while True:
        progressed = False
        for workload_id in workload_ids:
            if queues[workload_id]:
                order.append(queues[workload_id].pop(0))
                progressed = True
        if not progressed:
            return order


def posterior_draw(posterior: Posterior, seed: int, scale: float) -> np.ndarray:
    eigenvalues, eigenvectors = np.linalg.eigh(posterior.covariance)
    root = eigenvectors @ np.diag(np.sqrt(np.maximum(eigenvalues, 0.0)))
    rng = np.random.default_rng(seed)
    return posterior.mean + scale * root @ rng.standard_normal(len(posterior.mean))


def load_measurement_costs(path: Path) -> dict[tuple[str, str], float]:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in read_csv(path):
        if row["variant"].startswith("candidate:"):
            grouped[(row["workload_id"], row["candidate_id"])].append(
                float(row["benchmark_wall_ms"])
            )
    return {key: statistics.median(values) for key, values in grouped.items()}


def load_compile_costs(path: Path) -> dict[str, float]:
    document = read_json(path)
    return {
        candidate_id: float(manifest["pipeline_ms"])
        for candidate_id, manifest in document["candidates"].items()
    }


def cluster_bootstrap(
    rows: list[dict[str, Any]], seed: int, replicates: int
) -> tuple[float, float, float]:
    by_workload: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        by_workload[row["workload_id"]].append(math.log(float(row["speedup"])))
    workload_logs = np.asarray([
        float(np.mean(values)) for _, values in sorted(by_workload.items())
    ])
    point = math.exp(float(workload_logs.mean()))
    rng = np.random.default_rng(seed)
    samples = np.empty(replicates, dtype=float)
    for start in range(0, replicates, 1000):
        count = min(1000, replicates - start)
        indices = rng.integers(0, len(workload_logs), size=(count, len(workload_logs)))
        samples[start:start + count] = np.exp(workload_logs[indices].mean(axis=1))
    lower, upper = np.quantile(samples, [0.025, 0.975])
    return point, float(lower), float(upper)


def run_replay(
    config: dict[str, Any],
    workloads: dict[str, dict[str, Any]],
    host: dict[str, Any],
    measurement_costs: dict[tuple[str, str], float],
    compile_costs: dict[str, float],
    smoke: bool,
) -> dict[str, Any]:
    sparse = config["sparse_calibration"]
    calibration_budgets = sparse["calibration_row_budgets"][:2] if smoke else sparse["calibration_row_budgets"]
    calibration_seeds = sparse["calibration_seeds"][:1] if smoke else sparse["calibration_seeds"]
    search_seeds = sparse["search_seeds"][:2] if smoke else sparse["search_seeds"]
    records = host["records"]
    by_workload = host["by_workload"]
    holdouts = sorted(
        workload_id for workload_id, indices in by_workload.items()
        if records[indices[0]]["split"] == "holdout"
    )
    full_raw = np.vstack([
        raw_features(row, workloads[row["workload_id"]]) for row in records
    ])
    calibration_metadata_mask = np.asarray([
        row["split"] in {"design", "validation"} for row in records
    ])
    positions: dict[str, list[int]] = {}
    matrices: dict[str, np.ndarray] = {}
    feature_lists: dict[str, list[str]] = {}
    for mode in ("data_only", "expert_plus_data"):
        positions[mode], feature_lists[mode] = selected_positions(mode)
        raw = full_raw[:, positions[mode]]
        mean = raw[calibration_metadata_mask].mean(axis=0)
        scale = raw[calibration_metadata_mask].std(axis=0)
        scale[scale < 1.0e-9] = 1.0
        matrices[mode] = np.column_stack((np.ones(len(raw)), (raw - mean) / scale))

    trajectories: list[dict[str, Any]] = []
    calibration_rows: list[dict[str, Any]] = []
    fit_timings: dict[tuple[int, int, str], float] = {}
    subset_lookup: dict[tuple[int, int], list[int]] = {}
    model_lookup: dict[tuple[int, int, str], Posterior] = {}
    for calibration_seed in calibration_seeds:
        order = calibration_order(records, by_workload, int(calibration_seed))
        for calibration_budget in calibration_budgets:
            selected = order[: int(calibration_budget)]
            subset_lookup[(int(calibration_seed), int(calibration_budget))] = selected
            for index in selected:
                row = records[index]
                calibration_rows.append({
                    "calibration_seed": calibration_seed,
                    "calibration_budget": calibration_budget,
                    "environment": row["environment"],
                    "workload_id": row["workload_id"],
                    "split": row["split"],
                    "canonical_id": row["canonical_id"],
                    "source_candidate_id": row["source_candidate_id"],
                    "runtime_ms": row["runtime_ms"],
                })
            y = np.asarray([
                math.log(records[index]["runtime_ms"] / records[index]["b5_ms"])
                for index in selected
            ])
            for mode in ("data_only", "expert_plus_data"):
                started = time.perf_counter()
                model_lookup[(int(calibration_seed), int(calibration_budget), mode)] = fit_posterior(
                    matrices[mode][selected], y,
                    float(sparse["prior_precision"]),
                    float(sparse["minimum_noise_variance"]),
                )
                fit_timings[(int(calibration_seed), int(calibration_budget), mode)] = (
                    time.perf_counter() - started
                ) * 1000.0

    for calibration_budget in calibration_budgets:
        for calibration_seed in calibration_seeds:
            for workload_id in holdouts:
                indices = sorted(
                    by_workload[workload_id], key=lambda index: records[index]["canonical_id"]
                )
                oracle = min(records[index]["runtime_ms"] for index in indices)
                for search_seed in search_seeds:
                    for method in METHODS:
                        if method == "N0_uniform_without_replacement":
                            rng = np.random.default_rng(stable_int(
                                "uniform", calibration_budget, calibration_seed,
                                search_seed, workload_id,
                            ))
                            ordered = [indices[value] for value in rng.permutation(len(indices))]
                        else:
                            mode = "data_only" if method.startswith("D0") else "expert_plus_data"
                            posterior = model_lookup[(int(calibration_seed), int(calibration_budget), mode)]
                            draw = posterior_draw(
                                posterior,
                                stable_int(method, calibration_budget, calibration_seed, search_seed, workload_id),
                                float(sparse["posterior_sampling_scale"]),
                            )
                            predictions = matrices[mode][indices] @ draw
                            ordered = [
                                indices[value] for value in sorted(
                                    range(len(indices)),
                                    key=lambda value: (predictions[value], records[indices[value]]["canonical_id"]),
                                )
                            ]
                        best = math.inf
                        cumulative_wall = 0.0
                        for iteration, index in enumerate(ordered, start=1):
                            row = records[index]
                            best = min(best, float(row["runtime_ms"]))
                            cost = measurement_costs[(workload_id, row["source_candidate_id"])]
                            cumulative_wall += cost
                            trajectories.append({
                                "environment": row["environment"],
                                "calibration_budget": calibration_budget,
                                "calibration_seed": calibration_seed,
                                "search_seed": search_seed,
                                "method": method,
                                "workload_id": workload_id,
                                "family": row["family"],
                                "iteration": iteration,
                                "canonical_id": row["canonical_id"],
                                "source_candidate_id": row["source_candidate_id"],
                                "runtime_ms": row["runtime_ms"],
                                "best_so_far_ms": best,
                                "pool_oracle_ms": oracle,
                                "oracle_fraction": oracle / best,
                                "measurement_wall_ms": cost,
                                "cumulative_measurement_wall_ms": cumulative_wall,
                                "holdout_target_read_after_order_frozen": True,
                            })

    checkpoints = set(map(int, sparse["search_checkpoints"]))
    fixed = [dict(row) for row in trajectories if int(row["iteration"]) in checkpoints]
    t95: list[dict[str, Any]] = []
    grouped_trajectories: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in trajectories:
        key = (
            row["calibration_budget"], row["calibration_seed"], row["search_seed"],
            row["method"], row["workload_id"],
        )
        grouped_trajectories[key].append(row)
    for key, values in sorted(grouped_trajectories.items()):
        hit = next(
            row for row in values
            if float(row["oracle_fraction"]) >= float(sparse["oracle_fraction"])
        )
        t95.append({
            "calibration_budget": key[0],
            "calibration_seed": key[1],
            "search_seed": key[2],
            "method": key[3],
            "workload_id": key[4],
            "evaluations_to_95_oracle": hit["iteration"],
            "measurement_wall_to_95_ms": hit["cumulative_measurement_wall_ms"],
        })

    fixed_lookup = {
        (
            row["calibration_budget"], row["calibration_seed"], row["search_seed"],
            row["workload_id"], row["iteration"], row["method"],
        ): row for row in fixed
    }
    pairs = (
        ("D1_expert_plus_data_thompson", "D0_data_only_thompson"),
        ("D0_data_only_thompson", "N0_uniform_without_replacement"),
        ("D1_expert_plus_data_thompson", "N0_uniform_without_replacement"),
    )
    ratios: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    for test, reference in pairs:
        for calibration_budget in calibration_budgets:
            for checkpoint in sorted(checkpoints):
                selected: list[dict[str, Any]] = []
                for calibration_seed in calibration_seeds:
                    for search_seed in search_seeds:
                        for workload_id in holdouts:
                            prefix = (
                                calibration_budget, calibration_seed, search_seed,
                                workload_id, checkpoint,
                            )
                            test_row = fixed_lookup[(*prefix, test)]
                            reference_row = fixed_lookup[(*prefix, reference)]
                            value = {
                                "test_method": test,
                                "reference_method": reference,
                                "calibration_budget": calibration_budget,
                                "search_budget": checkpoint,
                                "calibration_seed": calibration_seed,
                                "search_seed": search_seed,
                                "workload_id": workload_id,
                                "speedup": float(reference_row["best_so_far_ms"]) / float(test_row["best_so_far_ms"]),
                            }
                            selected.append(value)
                            ratios.append(value)
                point, lower, upper = cluster_bootstrap(
                    selected,
                    int(sparse["bootstrap_seed"]) + int(calibration_budget) * 31 + checkpoint,
                    int(sparse["bootstrap_replicates"] if not smoke else 1000),
                )
                comparisons.append({
                    "test_method": test,
                    "reference_method": reference,
                    "calibration_budget": calibration_budget,
                    "search_budget": checkpoint,
                    "paired_runs": len(selected),
                    "clustered_workloads": len(holdouts),
                    "gmean_speedup": point,
                    "ci95_lower": lower,
                    "ci95_upper": upper,
                    "ci_excludes_one_in_favor": lower > 1.0,
                })

    t95_lookup = {
        (
            row["calibration_budget"], row["calibration_seed"], row["search_seed"],
            row["workload_id"], row["method"],
        ): row for row in t95
    }
    costs: list[dict[str, Any]] = []
    for calibration_budget in calibration_budgets:
        for method, mode in (
            ("D0_data_only_thompson", "data_only"),
            ("D1_expert_plus_data_thompson", "expert_plus_data"),
        ):
            calibration_total: list[float] = []
            calibration_without_compile: list[float] = []
            savings: list[float] = []
            evaluation_savings: list[float] = []
            for calibration_seed in calibration_seeds:
                selected = subset_lookup[(int(calibration_seed), int(calibration_budget))]
                measurement = sum(
                    measurement_costs[(records[index]["workload_id"], records[index]["source_candidate_id"])]
                    for index in selected
                )
                unique_candidates = {records[index]["source_candidate_id"] for index in selected}
                compile_wall = sum(compile_costs[candidate] for candidate in unique_candidates)
                fit_wall = fit_timings[(int(calibration_seed), int(calibration_budget), mode)]
                calibration_without_compile.append(measurement + fit_wall)
                calibration_total.append(measurement + fit_wall + compile_wall)
                for search_seed in search_seeds:
                    for workload_id in holdouts:
                        baseline = t95_lookup[(
                            calibration_budget, calibration_seed, search_seed,
                            workload_id, "N0_uniform_without_replacement",
                        )]
                        tested = t95_lookup[(
                            calibration_budget, calibration_seed, search_seed,
                            workload_id, method,
                        )]
                        savings.append(
                            float(baseline["measurement_wall_to_95_ms"])
                            - float(tested["measurement_wall_to_95_ms"])
                        )
                        evaluation_savings.append(
                            float(baseline["evaluations_to_95_oracle"])
                            - float(tested["evaluations_to_95_oracle"])
                        )
            mean_saving = float(np.mean(savings))
            mean_evaluation_saving = float(np.mean(evaluation_savings))
            mean_complete_cost = float(np.mean(calibration_total))
            mean_without_compile = float(np.mean(calibration_without_compile))
            costs.append({
                "method": method,
                "calibration_budget": calibration_budget,
                "mean_calibration_wall_without_compile_ms": mean_without_compile,
                "mean_complete_calibration_wall_ms": mean_complete_cost,
                "mean_measurement_wall_saved_per_future_workload_ms": mean_saving,
                "mean_evaluations_saved_per_future_workload": mean_evaluation_saving,
                "break_even_workloads_without_compile": (
                    mean_without_compile / mean_saving if mean_saving > 0 else None
                ),
                "break_even_workloads_with_compile": (
                    mean_complete_cost / mean_saving if mean_saving > 0 else None
                ),
            })
    return {
        "trajectories": trajectories,
        "calibration_rows": calibration_rows,
        "fixed": fixed,
        "t95": t95,
        "ratios": ratios,
        "comparisons": comparisons,
        "costs": costs,
        "feature_lists": feature_lists,
        "calibration_budgets": calibration_budgets,
        "calibration_seeds": calibration_seeds,
        "search_seeds": search_seeds,
        "holdouts": holdouts,
    }


def write_report(output_root: Path, environment_id: str, result: dict[str, Any]) -> None:
    primary = [
        row for row in result["comparisons"]
        if row["test_method"] == "D1_expert_plus_data_thompson"
        and row["reference_method"] == "D0_data_only_thompson"
    ]
    lines = [
        "# Sparse calibration external validation",
        "",
        f"- Environment: `{environment_id}`",
        f"- Holdout workloads: {len(result['holdouts'])}",
        "- Policy: finite-pool posterior Thompson ordering; every holdout target is read only after the ordering is frozen.",
        "",
        "## Expert+Data vs Data-only",
        "",
        "| Calibration rows | Search budget | Speedup | 95% CI | Significant |",
        "|---:|---:|---:|---:|:---:|",
    ]
    for row in primary:
        lines.append(
            f"| {row['calibration_budget']} | {row['search_budget']} | "
            f"{row['gmean_speedup']:.4f}x | "
            f"[{row['ci95_lower']:.4f}, {row['ci95_upper']:.4f}] | "
            f"{'yes' if row['ci_excludes_one_in_favor'] else 'no'} |"
        )
    lines.extend([
        "",
        "## Cost boundary",
        "",
        "Calibration cost includes measured benchmark-process wall time, model fitting, and unique candidate compilation where requested. Break-even is reported rather than assumed.",
        "",
        "This report is a finite-pool replay over an independently measured target corpus. It is not a new live compilation run and it does not establish end-to-end model speedup.",
        "",
    ])
    report = output_root / "reports" / "sparse_calibration_results.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--environment-id", required=True)
    parser.add_argument("--output-root", type=Path, default=PROJECT)
    parser.add_argument("--workloads", type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    corpus_root = args.corpus_root.resolve()
    output_root = args.output_root.resolve()
    workloads_path = (
        args.workloads.resolve() if args.workloads
        else EXPERIMENTS / "chapter6_evaluation" / "data" / "workloads.json"
    )
    inputs = {
        "config": CONFIG_PATH,
        "workloads": workloads_path,
        "pool_metadata": corpus_root / "processed" / "f64_contract_pools.csv",
        "aggregates": corpus_root / "processed" / "f64_contract_aggregates.csv",
        "trials": corpus_root / "raw" / "f64_contract_trials.csv",
        "manifests": corpus_root / "processed" / "f64_manifests.json",
    }
    missing = [str(path) for path in inputs.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing sparse-calibration inputs: " + ", ".join(missing))
    config = read_json(CONFIG_PATH)
    workloads = load_workloads(workloads_path)
    pools = canonicalize_pool(
        inputs["pool_metadata"], workloads,
        max(config["sparse_calibration"]["search_checkpoints"]),
    )
    host = load_host_corpus(
        inputs["aggregates"], args.environment_id, pools, workloads
    )
    measurement_costs = load_measurement_costs(inputs["trials"])
    compile_costs = load_compile_costs(inputs["manifests"])
    result = run_replay(
        config, workloads, host, measurement_costs, compile_costs, args.smoke
    )
    raw = output_root / "raw"
    processed = output_root / "processed"
    provenance = output_root / "provenance"
    write_csv(raw / "sparse_calibration_rows.csv", result["calibration_rows"])
    write_csv(raw / "sparse_trajectories.csv", result["trajectories"])
    write_csv(processed / "sparse_fixed_budget.csv", result["fixed"])
    write_csv(processed / "sparse_time_to95.csv", result["t95"])
    write_csv(processed / "sparse_paired_ratios.csv", result["ratios"])
    write_csv(processed / "sparse_paired_comparisons.csv", result["comparisons"])
    write_csv(processed / "sparse_calibration_costs.csv", result["costs"])
    summary = {
        "schema_version": 1,
        "experiment_id": config["experiment_id"],
        "environment": args.environment_id,
        "status": "SMOKE_PASS" if args.smoke else "PASS",
        "policy": "finite_pool_posterior_thompson_ordering",
        "calibration_budgets": result["calibration_budgets"],
        "calibration_seeds": result["calibration_seeds"],
        "search_seeds": result["search_seeds"],
        "holdout_workloads": len(result["holdouts"]),
        "trajectory_rows": len(result["trajectories"]),
        "comparisons": result["comparisons"],
        "costs": result["costs"],
        "feature_counts_with_intercept": {
            key: len(value) + 1 for key, value in result["feature_lists"].items()
        },
        "host": {"platform": platform.platform(), "python": platform.python_version()},
        "claim_boundary": config["claim_boundary"],
    }
    write_json(processed / "sparse_summary.json", summary)
    write_report(output_root, args.environment_id, result)
    outputs = [
        raw / "sparse_calibration_rows.csv",
        raw / "sparse_trajectories.csv",
        processed / "sparse_paired_comparisons.csv",
        processed / "sparse_calibration_costs.csv",
        processed / "sparse_summary.json",
        output_root / "reports" / "sparse_calibration_results.md",
    ]
    write_json(provenance / "sparse_manifest.json", {
        "schema_version": 1,
        "environment": args.environment_id,
        "inputs": {name: {"path": str(path), "sha256": sha256(path)} for name, path in inputs.items()},
        "outputs": {str(path.relative_to(output_root)): sha256(path) for path in outputs},
    })
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
