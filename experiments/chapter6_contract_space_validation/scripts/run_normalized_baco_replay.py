#!/usr/bin/env python3
"""Replay BaCO on the frozen, vectorize-canonicalized measured Contract pool."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
CHAPTER6 = EXPERIMENTS / "chapter6_evaluation"
CHAPTER6_SCRIPTS = CHAPTER6 / "scripts"
sys.path.insert(0, str(CHAPTER6_SCRIPTS))

import run_tuning as chapter6_tuning  # noqa: E402
from chapter6lib import load_config, stable_key  # noqa: E402


PROCESSED = PROJECT / "processed"
REPLAY_BUILD = PROJECT / "build" / "e2_normalized_baco"
METHOD = "C_norm_baco"
SUITE = "normalized_contract"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as stream:
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


def schedule_key(row: dict[str, Any]) -> tuple[Any, ...]:
    if row["predicted_path"] not in {"direct", "adapt"}:
        raise ValueError(f"normalized Contract pool received {row['predicted_path']}")
    checks = row["checks"]
    return (
        int(row["tile_m"]), int(row["tile_n"]), int(row["tile_k"]),
        row["pack_mode"], row["predicted_path"],
        checks.get("mn_tail"), checks.get("k_tail")
    )


def canonical_schedule_id(key: tuple[Any, ...]) -> str:
    tile_m, tile_n, tile_k, pack_mode, path, mn_tail, k_tail = key
    return (
        f"m{tile_m}_n{tile_n}_k{tile_k}_p{pack_mode}_"
        f"path{path}_mn{mn_tail}_k{k_tail}"
    )


def canonical_ir_hash(candidate_id: str) -> str | None:
    path = CHAPTER6 / "build" / "binaries" / candidate_id / "kernel.ll"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    text = text.replace(f"chapter6_{candidate_id}", "chapter6_CANONICAL_SCHEDULE")
    return hashlib.sha256(text.encode()).hexdigest()


def choose_representative(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return min(rows, key=lambda row: (bool(row["vectorize"]), row["candidate_id"]))


def build_pools(
    base_pools: dict[str, dict[str, list[dict[str, Any]]]],
    corpus: dict[tuple[str, str], dict[str, Any]],
    pool_size: int,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]]]:
    pools: dict[str, list[dict[str, Any]]] = {}
    pool_rows: list[dict[str, Any]] = []
    equivalence_rows: list[dict[str, Any]] = []

    for workload_id, methods in base_pools.items():
        measured_contract: dict[str, dict[str, Any]] = {}
        for method_pool in methods.values():
            for row in method_pool:
                if (
                    row["predicted_path"] in {"direct", "adapt"}
                    and (workload_id, row["candidate_id"]) in corpus
                ):
                    measured_contract[row["candidate_id"]] = row

        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in measured_contract.values():
            groups[schedule_key(row)].append(row)
        representatives = {key: choose_representative(rows) for key, rows in groups.items()}

        old_keys: list[tuple[Any, ...]] = []
        for row in methods["B2"]:
            key = schedule_key(row)
            if key not in old_keys:
                old_keys.append(key)
        if len(old_keys) >= pool_size:
            raise RuntimeError(f"{workload_id}: normalization did not shrink the old B2 pool")

        backfill = sorted(
            (key for key in groups if key not in old_keys),
            key=lambda key: stable_key("B2", canonical_schedule_id(key))
        )
        selected_keys = old_keys + backfill[: pool_size - len(old_keys)]
        if len(selected_keys) != pool_size:
            raise RuntimeError(f"{workload_id}: normalized measured pool has fewer than {pool_size}")

        selected: list[dict[str, Any]] = []
        old_key_set = set(old_keys)
        for index, key in enumerate(selected_keys):
            representative = representatives[key]
            selected.append(representative)
            aliases = sorted(row["candidate_id"] for row in groups[key])
            ir_hashes = {candidate_id: canonical_ir_hash(candidate_id) for candidate_id in aliases}
            present_hashes = {value for value in ir_hashes.values() if value is not None}
            if len(aliases) > 1 and len(present_hashes) != 1:
                raise RuntimeError(
                    f"{workload_id}/{canonical_schedule_id(key)} aliases do not share canonical IR"
                )
            canonical_false_id = representative["candidate_id"].replace("_v1", "_v0")
            representative_ir = canonical_ir_hash(representative["candidate_id"])
            canonical_false_ir = canonical_ir_hash(canonical_false_id)
            false_ir_match: bool | str
            if representative_ir is None or canonical_false_ir is None:
                false_ir_match = "not_available"
            else:
                false_ir_match = representative_ir == canonical_false_ir
            if false_ir_match is False:
                raise RuntimeError(
                    f"{workload_id}/{representative['candidate_id']} conflicts with its v0 IR"
                )
            pool_rows.append({
                "workload_id": workload_id,
                "pool_index": index,
                "canonical_schedule_id": canonical_schedule_id(key),
                "measurement_candidate_id": representative["candidate_id"],
                "measurement_vectorize_value": bool(representative["vectorize"]),
                "canonical_vectorize_value": False,
                "canonical_false_candidate_id": canonical_false_id,
                "canonical_false_ir_match": false_ir_match,
                "measurement_uses_vectorize_alias": bool(representative["vectorize"]),
                "vectorize_liveness_evidence": (
                    "paired_canonical_IR"
                    if false_ir_match is True
                    else "static_microkernel_path_parameter_liveness"
                ),
                "predicted_path": representative["predicted_path"],
                "source": "old_B2_collapsed" if key in old_key_set else "deterministic_backfill",
                "alias_count_in_measured_contract_corpus": len(aliases),
                "alias_candidate_ids": ";".join(aliases),
                "canonical_ir_alias_match": len(aliases) == 1 or len(present_hashes) == 1
            })

        for key, rows in sorted(groups.items(), key=lambda item: canonical_schedule_id(item[0])):
            aliases = sorted(row["candidate_id"] for row in rows)
            ir_hashes = [canonical_ir_hash(candidate_id) for candidate_id in aliases]
            present = {value for value in ir_hashes if value is not None}
            equivalence_rows.append({
                "workload_id": workload_id,
                "canonical_schedule_id": canonical_schedule_id(key),
                "alias_count": len(aliases),
                "alias_candidate_ids": ";".join(aliases),
                "contains_vectorize_false": any(not row["vectorize"] for row in rows),
                "contains_vectorize_true": any(row["vectorize"] for row in rows),
                "canonical_ir_alias_match": len(aliases) == 1 or len(present) == 1,
                "selected_in_final_pool": key in set(selected_keys)
            })
        pools[workload_id] = selected
    return pools, pool_rows, equivalence_rows


def analyze(
    pools: dict[str, list[dict[str, Any]]],
    traces: list[dict[str, Any]],
    run_summaries: list[dict[str, Any]],
    aggregates: list[dict[str, str]],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    aggregate_index = {
        (row["workload_id"], row["candidate_id"]): row
        for row in aggregates if row["variant"].startswith("candidate:")
    }
    blis = {
        row["workload_id"]: float(row["median_ms"])
        for row in aggregates if row["variant"] == "B5_blis"
    }

    quality_rows: list[dict[str, Any]] = []
    pool_best: dict[str, float] = {}
    for workload_id, pool in pools.items():
        runtimes = []
        for row in pool:
            measured = aggregate_index[(workload_id, row["candidate_id"])]
            runtime = float(measured["median_ms"])
            normalized = blis[workload_id] / runtime
            runtimes.append(runtime)
            quality_rows.append({
                "workload_id": workload_id,
                "canonical_schedule_id": canonical_schedule_id(schedule_key(row)),
                "measurement_candidate_id": row["candidate_id"],
                "runtime_ms": runtime,
                "normalized_to_blis": normalized,
                "D80": normalized >= 0.80,
                "D90": normalized >= 0.90,
                "D95": normalized >= 0.95
            })
        pool_best[workload_id] = min(runtimes)

    grouped_traces: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in traces:
        grouped_traces[(row["workload_id"], int(row["seed"]))].append(row)
    convergence_rows: list[dict[str, Any]] = []
    for (workload_id, seed), rows in sorted(grouped_traces.items()):
        rows.sort(key=lambda row: int(row["iteration"]))
        threshold = pool_best[workload_id] / 0.90
        reached = next(
            (row for row in rows if float(row["best_so_far_ms"]) <= threshold), None
        )
        convergence_rows.append({
            "workload_id": workload_id,
            "seed": seed,
            "pool_best_runtime_ms": pool_best[workload_id],
            "threshold_90pct_pool_best_ms": threshold,
            "reached_90pct_pool_best": reached is not None,
            "time_to_90pct_iteration": (
                int(reached["iteration"]) if reached is not None else int(config["budget"]) + 1
            ),
            "right_censored": reached is None
        })

    old_quality = {
        row["method"]: row
        for row in read_csv(CHAPTER6 / "processed" / "space_quality_summary.csv")
    }["B2"]
    old_chapter6 = json.loads(
        (CHAPTER6 / "processed" / "chapter6_summary.json").read_text(encoding="utf-8")
    )
    old_fixed = next(
        row for row in old_chapter6["RQ4"]["fixed_budget"]
        if row["suite"] == "base" and row["label"] == "B2"
    )
    final_time = statistics.median(row["time_to_90pct_iteration"] for row in convergence_rows)
    final_d90 = sum(bool(row["D90"]) for row in quality_rows) / len(quality_rows)
    old_time = float(old_fixed["median_time_to_90pct_iteration"])
    old_d90 = float(old_quality["D90"])
    summary = {
        "status": "PASS",
        "method": METHOD,
        "protocol_frozen_before_outcome": True,
        "report_regardless_of_outcome": True,
        "compilation_performed": False,
        "hardware_measurement_performed": False,
        "objective_source": "chapter6_evaluation/processed/measurement_aggregates.csv",
        "pool_construction": (
            "collapse vectorize aliases in the frozen B2 pool, then backfill to 28 from the "
            "pre-performance measured Contract-candidate union using the original B2 stable hash"
        ),
        "canonical_representative_policy": (
            "prefer an existing vectorize=false measurement, otherwise use the lexical candidate ID"
        ),
        "pool_size_per_workload": int(config["pool_size"]),
        "workload_count": len(pools),
        "seeds": [int(seed) for seed in config["seeds"]],
        "budget": int(config["budget"]),
        "run_count": len(run_summaries),
        "trace_count": len(traces),
        "all_callbacks_valid": all(
            int(row["valid"]) == int(row["budget"]) for row in run_summaries
        ),
        "duplicate_callbacks": sum(int(row["duplicate_evaluations"]) for row in run_summaries),
        "normalized_final_method": {
            "D90": final_d90,
            "time_to_90pct_pool_best": final_time,
            "reached_90pct_pool_best_fraction": (
                sum(bool(row["reached_90pct_pool_best"]) for row in convergence_rows)
                / len(convergence_rows)
            ),
            "candidate_count": len(quality_rows)
        },
        "pre_normalization_ablation": {
            "D90": old_d90,
            "time_to_90pct_pool_best": old_time,
            "label": "pre-normalization ablation result"
        },
        "outcome_vs_pre_normalization": {
            "D90_delta": final_d90 - old_d90,
            "time_to_90pct_delta": final_time - old_time,
            "time_direction": (
                "better" if final_time < old_time else "worse" if final_time > old_time else "equal"
            )
        },
        "data_leakage_guard": (
            "pool collapse and backfill use only candidate metadata, historical pool membership "
            "and stable hashes; runtime is read only by the objective callback or final analysis"
        )
    }
    return quality_rows, convergence_rows, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analyze-only", action="store_true",
        help="reuse the already frozen replay traces and regenerate audits/summaries"
    )
    args = parser.parse_args()
    chapter6_config, workloads = load_config()
    experiment_config = json.loads(
        (PROJECT / "data" / "experiment_config.json").read_text(encoding="utf-8")
    )
    protocol = experiment_config["normalized_baco_replay"]
    tuning_workloads = [row["id"] for row in workloads if row["tune"]]
    expected = {
        "pool_size": int(protocol["pool_size"]),
        "budget": int(protocol["budget"]),
        "seeds": [int(seed) for seed in protocol["seeds"]],
        "workloads": int(protocol["workload_count"])
    }
    if not protocol["report_regardless_of_outcome"]:
        raise RuntimeError("frozen protocol must report regardless of outcome")
    if protocol["allow_compilation"] or protocol["allow_hardware_measurement"]:
        raise RuntimeError("normalized replay protocol must remain data-only")
    if int(chapter6_config["pool_size"]) != expected["pool_size"]:
        raise RuntimeError("Chapter 6 pool size drifted from the frozen protocol")
    if int(chapter6_config["budget"]) != expected["budget"]:
        raise RuntimeError("Chapter 6 budget drifted from the frozen protocol")
    if [int(seed) for seed in chapter6_config["seeds"]] != expected["seeds"]:
        raise RuntimeError("Chapter 6 seeds drifted from the frozen protocol")
    if len(tuning_workloads) != expected["workloads"]:
        raise RuntimeError("Chapter 6 workload count drifted from the frozen protocol")

    base_path = CHAPTER6 / "tuner" / "base_pools.json"
    aggregate_path = CHAPTER6 / "processed" / "measurement_aggregates.csv"
    base_pools = json.loads(base_path.read_text(encoding="utf-8"))
    aggregates = read_csv(aggregate_path)
    corpus = chapter6_tuning.corpus_lookup()
    pools, pool_rows, equivalence_rows = build_pools(
        base_pools, corpus, int(chapter6_config["pool_size"])
    )
    if set(pools) != set(tuning_workloads):
        raise RuntimeError("normalized pool workload IDs do not match the frozen tuning set")

    if args.analyze_only:
        traces = read_csv(PROCESSED / "e2_normalized_baco_traces.csv")
        run_summaries = read_csv(PROCESSED / "e2_normalized_baco_run_summaries.csv")
        if len(traces) != expected["workloads"] * len(expected["seeds"]) * expected["budget"]:
            raise RuntimeError("stored normalized replay trace count does not match the protocol")
        if len(run_summaries) != expected["workloads"] * len(expected["seeds"]):
            raise RuntimeError("stored normalized replay run count does not match the protocol")
    else:
        chapter6_tuning.TUNER = REPLAY_BUILD
        traces = []
        run_summaries = []
        pool_metadata = {
            (row["workload_id"], row["measurement_candidate_id"]): row for row in pool_rows
        }
        for workload_id in tuning_workloads:
            for seed in chapter6_config["seeds"]:
                run_trace, run_summary = chapter6_tuning.run_one(
                    SUITE, METHOD, workload_id, pools[workload_id], int(seed),
                    int(chapter6_config["budget"]), corpus, True
                )
                for row in run_trace:
                    metadata = pool_metadata[(workload_id, row["candidate_id"])]
                    row["canonical_schedule_id"] = metadata["canonical_schedule_id"]
                    row["measurement_candidate_id"] = row["candidate_id"]
                    row["candidate_id"] = metadata["canonical_schedule_id"]
                    row["pool_source"] = metadata["source"]
                run_summary["method"] = METHOD
                run_summary["normalization"] = "inactive vectorize removed before replay"
                traces.extend(run_trace)
                run_summaries.append(run_summary)
            print(f"completed {workload_id}: {len(chapter6_config['seeds'])} seeds", flush=True)

    quality_rows, convergence_rows, summary = analyze(
        pools, traces, run_summaries, aggregates, chapter6_config
    )
    summary["frozen_protocol"] = protocol
    summary["normalization_evidence"] = {
        "selected_measurements_using_vectorize_true_alias": sum(
            bool(row["measurement_uses_vectorize_alias"]) for row in pool_rows
        ),
        "selected_schedules_with_paired_canonical_ir": sum(
            row["canonical_false_ir_match"] is True for row in pool_rows
        ),
        "selected_schedules_without_paired_ir": sum(
            row["canonical_false_ir_match"] == "not_available" for row in pool_rows
        ),
        "multi_alias_measured_groups": sum(
            int(row["alias_count"]) > 1 for row in equivalence_rows
        ),
        "multi_alias_groups_with_matching_canonical_ir": sum(
            int(row["alias_count"]) > 1 and bool(row["canonical_ir_alias_match"])
            for row in equivalence_rows
        ),
        "boundary": (
            "paired existing IR is required to match when both aliases were compiled; schedules "
            "without a compiled v0 counterpart rely on the audited microkernel-path liveness rule"
        )
    }
    summary["input_sha256"] = {
        str(base_path.relative_to(EXPERIMENTS)): sha256_file(base_path),
        str(aggregate_path.relative_to(EXPERIMENTS)): sha256_file(aggregate_path),
        str((CHAPTER6 / "data" / "experiment_config.json").relative_to(EXPERIMENTS)): sha256_file(
            CHAPTER6 / "data" / "experiment_config.json"
        )
    }
    write_csv(PROCESSED / "e2_normalized_pool.csv", pool_rows)
    write_csv(PROCESSED / "e2_vectorize_equivalence_audit.csv", equivalence_rows)
    write_csv(PROCESSED / "e2_normalized_baco_traces.csv", traces)
    write_csv(PROCESSED / "e2_normalized_baco_run_summaries.csv", run_summaries)
    write_csv(PROCESSED / "e2_normalized_candidate_quality.csv", quality_rows)
    write_csv(PROCESSED / "e2_normalized_convergence.csv", convergence_rows)
    write_json(PROCESSED / "e2_normalized_baco_summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
