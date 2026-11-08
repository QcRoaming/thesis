#!/usr/bin/env python3
"""Ablate source-labelled BLIS/OpenBLAS soft priors on one hard-valid pool."""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
from typing import Any, Callable

import numpy as np

from cgo_common import (
    PROCESSED,
    PROVENANCE,
    PROJECT,
    RAW,
    REPORTS,
    geometric_mean,
    sha256,
    stable_key,
    write_csv,
    write_json,
)
from run_true_online import prepare_context


METHODS = (
    "S0_conflict_aware_hard",
    "S1_blis_only",
    "S2_openblas_only",
    "S3_naive_merge",
    "S4_calibrated",
)


def proximity(value: float, target: float) -> float:
    return math.exp(-abs(math.log2(value / target)))


def source_score(
    candidate: dict[str, Any], workload: dict[str, Any], source: str,
) -> float:
    tile_m = float(candidate["tile_m"])
    tile_n = float(candidate["tile_n"])
    tile_k = float(candidate["tile_k"])
    if source == "BLIS":
        mr, nr, mc, kc, nc = 6, 16, 168, 256, 4080
        block_scores = (
            proximity(tile_m, min(mc, int(workload["m"]))),
            proximity(tile_k, min(kc, int(workload["k"]))),
            proximity(tile_n, min(nc, int(workload["n"]))),
        )
    elif source == "OpenBLAS":
        mr, nr, p, q = 8, 4, 320, 320
        # OpenBLAS R is runtime-derived on Haswell, so it contributes no
        # fabricated N-block target. The missing feature is explicit.
        block_scores = (
            proximity(tile_m, min(p, int(workload["m"]))),
            proximity(tile_k, min(q, int(workload["k"]))),
        )
    else:
        raise KeyError(source)
    compatibility = (
        float(int(candidate["tile_m"]) % mr == 0)
        + float(int(candidate["tile_n"]) % nr == 0)
        + float(candidate["pack_mode"] == "ab")
    ) / 3.0
    shape_fit = (
        1.0 - (int(workload["m"]) % int(candidate["tile_m"])) / int(workload["m"])
        + 1.0 - (int(workload["n"]) % int(candidate["tile_n"])) / int(workload["n"])
        + 1.0 - (int(workload["k"]) % int(candidate["tile_k"])) / int(workload["k"])
    ) / 3.0
    return 0.45 * compatibility + 0.35 * float(np.mean(block_scores)) + 0.20 * shape_fit


def ordered_indices(
    method: str,
    indices: list[int],
    seed: int,
    context: dict[str, Any],
) -> list[int]:
    rows = context["corpus"]
    workload_id = rows[indices[0]]["workload_id"]
    workload = context["workload_map"][workload_id]
    state = context["state"][workload_id]

    def candidate(index: int) -> dict[str, Any]:
        return state["rows"][rows[index]["candidate_id"]]

    if method == "S0_conflict_aware_hard":
        return sorted(
            indices,
            key=lambda index: stable_key(method, seed, rows[index]["candidate_id"]),
        )
    if method == "S1_blis_only":
        score: Callable[[int], float] = lambda index: source_score(
            candidate(index), workload, "BLIS"
        )
        return sorted(indices, key=lambda index: (
            -score(index), stable_key(method, seed, rows[index]["candidate_id"])
        ))
    if method == "S2_openblas_only":
        score = lambda index: source_score(candidate(index), workload, "OpenBLAS")
        return sorted(indices, key=lambda index: (
            -score(index), stable_key(method, seed, rows[index]["candidate_id"])
        ))
    if method == "S3_naive_merge":
        score = lambda index: 0.5 * (
            source_score(candidate(index), workload, "BLIS")
            + source_score(candidate(index), workload, "OpenBLAS")
        )
        return sorted(indices, key=lambda index: (
            -score(index), stable_key(method, seed, rows[index]["candidate_id"])
        ))
    if method == "S4_calibrated":
        prediction = context["x"] @ context["posterior"].mean
        return sorted(indices, key=lambda index: (
            float(prediction[index]), stable_key(method, seed, rows[index]["candidate_id"])
        ))
    raise KeyError(method)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
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

    traces = []
    score_rows = []
    for workload_id in workload_ids:
        indices = context["by_workload"][workload_id]
        rows = context["corpus"]
        workload = context["workload_map"][workload_id]
        pool_best = min(float(rows[index]["median_ms"]) for index in indices)
        for index in indices:
            candidate = context["state"][workload_id]["rows"][rows[index]["candidate_id"]]
            blis = source_score(candidate, workload, "BLIS")
            openblas = source_score(candidate, workload, "OpenBLAS")
            score_rows.append({
                "workload_id": workload_id,
                "candidate_id": rows[index]["candidate_id"],
                "blis_score": blis,
                "openblas_score": openblas,
                "naive_merge_score": 0.5 * (blis + openblas),
                "measured_ms": rows[index]["median_ms"],
            })
        for method in METHODS:
            for seed in seeds:
                order = ordered_indices(method, indices, seed, context)
                best = float("inf")
                for iteration, index in enumerate(order[:budget], 1):
                    runtime = float(rows[index]["median_ms"])
                    best = min(best, runtime)
                    traces.append({
                        "protocol": "offline_frozen_real_corpus",
                        "method": method,
                        "workload_id": workload_id,
                        "family": workload["family"],
                        "split": workload["split"],
                        "seed": seed,
                        "iteration": iteration,
                        "candidate_id": rows[index]["candidate_id"],
                        "runtime_ms": runtime,
                        "best_so_far_ms": best,
                        "pool_best_ms": pool_best,
                        "relative_to_pool_best": pool_best / best,
                    })

    trace_path = RAW / (
        "multisource_smoke_traces.csv" if args.smoke else "multisource_traces.csv"
    )
    write_csv(trace_path, traces)
    score_path = PROCESSED / (
        "multisource_smoke_scores.csv" if args.smoke else "multisource_source_scores.csv"
    )
    write_csv(score_path, score_rows)
    budgets = (5,) if args.smoke else (5, 10, 15, 25)
    summary_rows = []
    for method in METHODS:
        for selected_budget in budgets:
            selected = [
                row for row in traces
                if row["method"] == method and int(row["iteration"]) == selected_budget
            ]
            summary_rows.append({
                "method": method,
                "budget": selected_budget,
                "trajectories": len(selected),
                "relative_to_pool_best_gmean": geometric_mean(
                    float(row["relative_to_pool_best"]) for row in selected
                ),
            })
    summary_csv = PROCESSED / (
        "multisource_smoke_fixed_budget.csv" if args.smoke
        else "multisource_fixed_budget.csv"
    )
    write_csv(summary_csv, summary_rows)
    summary = {
        "status": "PASS",
        "experiment_id": context["config"]["experiment_id"],
        "mode": "smoke" if args.smoke else "formal",
        "protocol": "offline_replay_over_real_compiled_candidate_corpus",
        "hard_contract": "BLIS Haswell f32 6x16 for every executable",
        "soft_sources": ["BLIS", "OpenBLAS"],
        "openblas_runtime_derived_r_fabricated": False,
        "incompatible_hard_contracts_merged": False,
        "workloads": len(workload_ids),
        "seeds": seeds,
        "budget": budget,
        "trace_rows": len(traces),
        "claim_boundary": (
            "This ablation compares source-labelled soft rankings on the same BLIS-hard-valid "
            "candidate pool. It does not claim that an OpenBLAS 8x4 internal kernel can be called "
            "through the BLIS 6x16 packing ABI. Outcomes are offline replays of real compiled runs."
        ),
    }
    summary_path = PROCESSED / (
        "multisource_smoke_summary.json" if args.smoke else "multisource_summary.json"
    )
    write_json(summary_path, summary)
    REPORTS.mkdir(parents=True, exist_ok=True)
    report = REPORTS / (
        "multisource_smoke_results.md" if args.smoke else "multisource_results.md"
    )
    lines = [
        "# Multi-source Prior Ablation", "",
        f"- status: `{summary['status']}`",
        f"- hard executable contract: `{summary['hard_contract']}`",
        f"- incompatible hard contracts merged: `{summary['incompatible_hard_contracts_merged']}`",
        "", "| Method | Budget | Relative to pool best |",
        "|---|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['method']} | {row['budget']} | "
            f"{float(row['relative_to_pool_best_gmean']):.3f} |"
        )
    lines.extend([
        "", "OpenBLAS Haswell `R` is runtime-derived and is intentionally left missing rather than guessed.",
        "", "## Claim boundary", "", summary["claim_boundary"], "",
    ])
    report.write_text("\n".join(lines), encoding="utf-8")
    manifest_path = PROVENANCE / (
        "multisource_smoke_manifest.json" if args.smoke else "multisource_manifest.json"
    )
    multisource_facts = PROJECT.parent / "chapter3_multisource" / "data" / "multisource_facts.yaml"
    conflicts = PROJECT.parent / "chapter3_multisource" / "data" / "conflicts.yaml"
    write_json(manifest_path, {
        "schema_version": 1,
        "experiment_id": context["config"]["experiment_id"],
        "mode": summary["mode"],
        "python": sys.version,
        "platform": platform.platform(),
        "inputs": {
            str(multisource_facts): sha256(multisource_facts),
            str(conflicts): sha256(conflicts),
            str(PROJECT.parent / "chapter6_online_prior" / "processed" / "calibration_corpus.csv"): sha256(PROJECT.parent / "chapter6_online_prior" / "processed" / "calibration_corpus.csv"),
        },
        "outputs": {
            str(trace_path): sha256(trace_path),
            str(score_path): sha256(score_path),
            str(summary_csv): sha256(summary_csv),
            str(summary_path): sha256(summary_path),
            str(report): sha256(report),
        },
    })
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
