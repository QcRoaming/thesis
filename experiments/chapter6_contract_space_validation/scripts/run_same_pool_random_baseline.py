#!/usr/bin/env python3
"""Compare BaCO with uniform random search on the same frozen normalized pool.

The primary budget is the number of unique candidate queries.  BaCO is allowed
extra callbacks because its pinned categorical optimizer may repeat a point;
random search uses a deterministic permutation without replacement.  Both
methods only read the pre-existing Chapter 6 objective corpus.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
CHAPTER6 = EXPERIMENTS / "chapter6_evaluation"
SCRIPT_DIR = PROJECT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(CHAPTER6 / "scripts"))

import run_normalized_baco_replay as normalized_replay  # noqa: E402
import run_tuning as chapter6_tuning  # noqa: E402
from chapter6lib import load_config  # noqa: E402


PROCESSED = PROJECT / "processed"
REPLAY_BUILD = PROJECT / "build" / "e2_same_pool_comparison"
SUITE = "same_pool_unique_budget"
LABEL = "C_norm_baco_unique_budget"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_random_order(
    workload_id: str, seed: int, pool: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Create the complete order without consulting any objective value."""
    material = f"same-pool-random-v1:{workload_id}:{seed}".encode()
    derived_seed = int.from_bytes(hashlib.sha256(material).digest()[:8], "big")
    order = list(pool)
    random.Random(derived_seed).shuffle(order)
    return order


def unique_prefix(
    callbacks: list[dict[str, Any]], unique_budget: int
) -> tuple[list[dict[str, Any]], int]:
    seen: set[str] = set()
    prefix: list[dict[str, Any]] = []
    callback_count = 0
    best = float("inf")
    for callback in callbacks:
        callback_count += 1
        candidate_id = str(callback["candidate_id"])
        if candidate_id in seen:
            continue
        seen.add(candidate_id)
        best = min(best, float(callback["runtime_ms"]))
        row = dict(callback)
        row["callback_iteration"] = callback_count
        row["unique_query"] = len(prefix) + 1
        row["best_so_far_unique_ms"] = best
        prefix.append(row)
        if len(prefix) == unique_budget:
            return prefix, callback_count
    raise RuntimeError(
        f"BaCO produced only {len(prefix)} unique candidates in {callback_count} callbacks"
    )


def cluster_bootstrap_mean_ci(
    rows: list[dict[str, Any]], value_key: str, samples: int, seed: int
) -> tuple[float, float, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[str(row["workload_id"])].append(float(row[value_key]))
    workloads = sorted(grouped)
    observed = statistics.mean(
        value for workload_id in workloads for value in grouped[workload_id]
    )
    rng = random.Random(seed)
    draws = []
    for _ in range(samples):
        sampled = [rng.choice(workloads) for _ in workloads]
        values = [value for workload_id in sampled for value in grouped[workload_id]]
        draws.append(statistics.mean(values))
    draws.sort()
    lower = draws[int(0.025 * (len(draws) - 1))]
    upper = draws[int(0.975 * (len(draws) - 1))]
    return observed, lower, upper


def summarize_method(
    rows: list[dict[str, Any]], pool_best: dict[str, float], budgets: list[int],
    unique_budget: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["workload_id"]), int(row["seed"]))].append(row)
    run_rows: list[dict[str, Any]] = []
    for (workload_id, seed), trace in sorted(grouped.items()):
        trace.sort(key=lambda row: int(row["unique_query"]))
        if len(trace) != unique_budget:
            raise RuntimeError(f"{workload_id}/seed{seed}: expected {unique_budget} unique queries")
        threshold = pool_best[workload_id] / 0.90
        reached = next(
            (row for row in trace if float(row["best_so_far_unique_ms"]) <= threshold), None
        )
        result: dict[str, Any] = {
            "workload_id": workload_id,
            "seed": seed,
            "reached_90pct_pool_best": reached is not None,
            "time_to_90pct_unique_query": (
                int(reached["unique_query"]) if reached is not None else unique_budget + 1
            ),
            "right_censored": reached is None,
        }
        for budget in budgets:
            row = trace[budget - 1]
            result[f"best_fraction_at_{budget}"] = (
                pool_best[workload_id] / float(row["best_so_far_unique_ms"])
            )
        run_rows.append(result)
    summary: dict[str, Any] = {
        "run_count": len(run_rows),
        "reached_90pct_pool_best_fraction": statistics.mean(
            float(row["reached_90pct_pool_best"]) for row in run_rows
        ),
        "median_time_to_90pct_unique_query": statistics.median(
            int(row["time_to_90pct_unique_query"]) for row in run_rows
        ),
        "right_censored_run_count": sum(bool(row["right_censored"]) for row in run_rows),
    }
    for budget in budgets:
        values = [float(row[f"best_fraction_at_{budget}"]) for row in run_rows]
        summary[f"median_best_fraction_at_{budget}"] = statistics.median(values)
        summary[f"mean_best_fraction_at_{budget}"] = statistics.mean(values)
    return run_rows, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analyze-only", action="store_true",
        help="reuse stored callback and random traces and regenerate summaries",
    )
    args = parser.parse_args()

    chapter6_config, workloads = load_config()
    validation_config_path = PROJECT / "data" / "experiment_config.json"
    validation_config = json.loads(validation_config_path.read_text(encoding="utf-8"))
    protocol = validation_config["same_pool_random_baseline"]
    unique_budget = int(protocol["unique_query_budget"])
    callback_cap = int(protocol["baco_callback_cap"])
    budgets = [int(value) for value in protocol["reported_budgets"]]
    seeds = [int(value) for value in protocol["seeds"]]
    tuning_workloads = [str(row["id"]) for row in workloads if row["tune"]]
    if not protocol["report_regardless_of_outcome"]:
        raise RuntimeError("same-pool comparison must report regardless of outcome")
    if protocol["allow_compilation"] or protocol["allow_hardware_measurement"]:
        raise RuntimeError("same-pool comparison must remain data-only")
    if int(protocol["pool_size"]) != int(chapter6_config["pool_size"]):
        raise RuntimeError("comparison pool size drifted")
    if unique_budget != int(chapter6_config["budget"]):
        raise RuntimeError("comparison unique-query budget drifted")
    if seeds != [int(seed) for seed in chapter6_config["seeds"]]:
        raise RuntimeError("comparison seeds drifted")
    if len(tuning_workloads) != int(protocol["workload_count"]):
        raise RuntimeError("comparison workload count drifted")
    if max(budgets) != unique_budget:
        raise RuntimeError("reported budgets must end at the unique-query budget")

    base_path = CHAPTER6 / "tuner" / "base_pools.json"
    aggregate_path = CHAPTER6 / "processed" / "measurement_aggregates.csv"
    base_pools = json.loads(base_path.read_text(encoding="utf-8"))
    aggregates = read_csv(aggregate_path)
    corpus = chapter6_tuning.corpus_lookup()
    pools, pool_rows, _ = normalized_replay.build_pools(
        base_pools, corpus, int(protocol["pool_size"])
    )
    if set(pools) != set(tuning_workloads):
        raise RuntimeError("comparison pool workload IDs drifted")
    metadata = {
        (str(row["workload_id"]), str(row["measurement_candidate_id"])): row
        for row in pool_rows
    }
    aggregate_index = {
        (str(row["workload_id"]), str(row["candidate_id"])): row
        for row in aggregates if str(row["variant"]).startswith("candidate:")
    }
    pool_best = {
        workload_id: min(
            float(aggregate_index[(workload_id, row["candidate_id"])]["median_ms"])
            for row in pool
        )
        for workload_id, pool in pools.items()
    }

    if args.analyze_only:
        baco_callbacks = read_csv(PROCESSED / "e2_same_pool_baco_callbacks.csv")
        baco_unique_rows = read_csv(PROCESSED / "e2_same_pool_baco_unique_traces.csv")
        random_rows = read_csv(PROCESSED / "e2_random_search_traces.csv")
        callback_rows = read_csv(PROCESSED / "e2_same_pool_baco_callback_summaries.csv")
    else:
        chapter6_tuning.TUNER = REPLAY_BUILD
        baco_callbacks: list[dict[str, Any]] = []
        baco_unique_rows: list[dict[str, Any]] = []
        random_rows: list[dict[str, Any]] = []
        callback_rows: list[dict[str, Any]] = []
        for workload_id in tuning_workloads:
            for seed in seeds:
                callbacks, run_summary = chapter6_tuning.run_one(
                    SUITE, LABEL, workload_id, pools[workload_id], seed,
                    callback_cap, corpus, True,
                    permit_callback_budget_over_pool=True,
                )
                unique_rows, callbacks_to_budget = unique_prefix(callbacks, unique_budget)
                for callback in callbacks:
                    pool_meta = metadata[(workload_id, str(callback["candidate_id"]))]
                    callback["canonical_schedule_id"] = pool_meta["canonical_schedule_id"]
                    callback["measurement_candidate_id"] = callback["candidate_id"]
                for row in unique_rows:
                    pool_meta = metadata[(workload_id, str(row["candidate_id"]))]
                    row["canonical_schedule_id"] = pool_meta["canonical_schedule_id"]
                    row["measurement_candidate_id"] = row["candidate_id"]
                    row["method"] = "C_norm_baco"
                baco_callbacks.extend(callbacks)
                baco_unique_rows.extend(unique_rows)
                callback_rows.append({
                    "workload_id": workload_id,
                    "seed": seed,
                    "callback_cap": callback_cap,
                    "full_callback_count": len(callbacks),
                    "full_unique_count": int(run_summary["unique"]),
                    "callbacks_to_25_unique": callbacks_to_budget,
                    "duplicates_before_25_unique": callbacks_to_budget - unique_budget,
                    "numerical_jitter_retries": int(run_summary["numerical_jitter_retries"]),
                })

                order = stable_random_order(workload_id, seed, pools[workload_id])
                best = float("inf")
                for query, candidate in enumerate(order[:unique_budget], start=1):
                    measured = aggregate_index[(workload_id, candidate["candidate_id"])]
                    runtime = float(measured["median_ms"])
                    best = min(best, runtime)
                    pool_meta = metadata[(workload_id, candidate["candidate_id"])]
                    random_rows.append({
                        "method": "uniform_random_without_replacement",
                        "workload_id": workload_id,
                        "seed": seed,
                        "unique_query": query,
                        "canonical_schedule_id": pool_meta["canonical_schedule_id"],
                        "measurement_candidate_id": candidate["candidate_id"],
                        "predicted_path": candidate["predicted_path"],
                        "runtime_ms": runtime,
                        "best_so_far_unique_ms": best,
                        "order_key_uses_objective": False,
                    })
            print(f"completed {workload_id}: {len(seeds)} paired seeds", flush=True)

    baco_run_rows, baco_summary = summarize_method(
        baco_unique_rows, pool_best, budgets, unique_budget
    )
    random_run_rows, random_summary = summarize_method(
        random_rows, pool_best, budgets, unique_budget
    )
    baco_index = {
        (str(row["workload_id"]), int(row["seed"])): row for row in baco_run_rows
    }
    random_index = {
        (str(row["workload_id"]), int(row["seed"])): row for row in random_run_rows
    }
    paired_rows: list[dict[str, Any]] = []
    for key in sorted(baco_index):
        baco_row = baco_index[key]
        random_row = random_index[key]
        row: dict[str, Any] = {
            "workload_id": key[0],
            "seed": key[1],
            "baco_reached_90pct": baco_row["reached_90pct_pool_best"],
            "random_reached_90pct": random_row["reached_90pct_pool_best"],
            "reached_difference": (
                int(bool(baco_row["reached_90pct_pool_best"]))
                - int(bool(random_row["reached_90pct_pool_best"]))
            ),
            "baco_t90_unique": baco_row["time_to_90pct_unique_query"],
            "random_t90_unique": random_row["time_to_90pct_unique_query"],
            "random_minus_baco_t90": (
                int(random_row["time_to_90pct_unique_query"])
                - int(baco_row["time_to_90pct_unique_query"])
            ),
        }
        for budget in budgets:
            baco_value = float(baco_row[f"best_fraction_at_{budget}"])
            random_value = float(random_row[f"best_fraction_at_{budget}"])
            row[f"baco_best_fraction_at_{budget}"] = baco_value
            row[f"random_best_fraction_at_{budget}"] = random_value
            row[f"baco_minus_random_at_{budget}"] = baco_value - random_value
        paired_rows.append(row)

    samples = int(protocol["bootstrap_samples"])
    paired_summary: dict[str, Any] = {}
    for budget in budgets:
        key = f"baco_minus_random_at_{budget}"
        mean, lower, upper = cluster_bootstrap_mean_ci(
            paired_rows, key, samples, 20260813 + budget
        )
        paired_summary[f"budget_{budget}"] = {
            "mean_best_fraction_difference": mean,
            "workload_cluster_bootstrap_95pct_ci": [lower, upper],
            "baco_wins": sum(float(row[key]) > 1.0e-12 for row in paired_rows),
            "ties": sum(abs(float(row[key])) <= 1.0e-12 for row in paired_rows),
            "random_wins": sum(float(row[key]) < -1.0e-12 for row in paired_rows),
        }
    reached_mean, reached_lower, reached_upper = cluster_bootstrap_mean_ci(
        paired_rows, "reached_difference", samples, 20260851
    )
    t90_mean, t90_lower, t90_upper = cluster_bootstrap_mean_ci(
        paired_rows, "random_minus_baco_t90", samples, 20260852
    )
    paired_summary["reached_fraction_difference"] = {
        "baco_minus_random": reached_mean,
        "workload_cluster_bootstrap_95pct_ci": [reached_lower, reached_upper],
    }
    paired_summary["right_censored_t90_difference"] = {
        "random_minus_baco_unique_queries": t90_mean,
        "workload_cluster_bootstrap_95pct_ci": [t90_lower, t90_upper],
        "censor_value": unique_budget + 1,
    }

    summary = {
        "status": "PASS",
        "protocol_frozen_before_outcome": True,
        "report_regardless_of_outcome": True,
        "compilation_performed": False,
        "hardware_measurement_performed": False,
        "objective_source": "chapter6_evaluation/processed/measurement_aggregates.csv",
        "pool_source": "processed/e2_normalized_pool.csv rebuilt from frozen inputs",
        "pool_size_per_workload": int(protocol["pool_size"]),
        "workload_count": len(tuning_workloads),
        "seeds": seeds,
        "unique_query_budget": unique_budget,
        "reported_budgets": budgets,
        "run_count_per_method": len(baco_run_rows),
        "baco": {
            **baco_summary,
            "callback_cap_per_run": callback_cap,
            "full_callback_count": sum(int(row["full_callback_count"]) for row in callback_rows),
            "callbacks_consumed_to_unique_budget": sum(
                int(row["callbacks_to_25_unique"]) for row in callback_rows
            ),
            "duplicate_callbacks_before_unique_budget": sum(
                int(row["duplicates_before_25_unique"]) for row in callback_rows
            ),
            "max_callbacks_to_unique_budget": max(
                int(row["callbacks_to_25_unique"]) for row in callback_rows
            ),
        },
        "random": {
            **random_summary,
            "sampling": "deterministic uniform permutation without replacement",
            "ordering_uses_objective": False,
            "callback_count": len(random_rows),
            "duplicate_queries": 0,
        },
        "paired_comparison": paired_summary,
        "D90_is_static_pool_property": True,
        "D90": sum(
            float(row["normalized_to_blis"]) >= 0.90
            for row in read_csv(PROCESSED / "e2_normalized_candidate_quality.csv")
        ) / (len(tuning_workloads) * int(protocol["pool_size"])),
        "claim_boundary": (
            "The comparison isolates search order only within the frozen 28-candidate measured "
            "subpool. It does not estimate the performance distribution of the full normalized "
            "Contract space or require new compilation or hardware measurements."
        ),
        "frozen_protocol": protocol,
        "input_sha256": {
            str(base_path.relative_to(EXPERIMENTS)): sha256_file(base_path),
            str(aggregate_path.relative_to(EXPERIMENTS)): sha256_file(aggregate_path),
            str(validation_config_path.relative_to(EXPERIMENTS)): sha256_file(validation_config_path),
        },
    }

    write_csv(PROCESSED / "e2_same_pool_baco_callbacks.csv", baco_callbacks)
    write_csv(PROCESSED / "e2_same_pool_baco_unique_traces.csv", baco_unique_rows)
    write_csv(PROCESSED / "e2_random_search_traces.csv", random_rows)
    write_csv(PROCESSED / "e2_same_pool_baco_callback_summaries.csv", callback_rows)
    write_csv(PROCESSED / "e2_baco_random_paired.csv", paired_rows)
    write_json(PROCESSED / "e2_baco_random_summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
