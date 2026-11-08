#!/usr/bin/env python3
"""Combine formal extension studies and compute paired bootstrap comparisons."""

from __future__ import annotations

import json
import math
from typing import Any

import numpy as np

from cgo_common import (
    PROCESSED,
    PROJECT,
    RAW,
    REPORTS,
    geometric_mean,
    read_csv,
    read_json,
    sha256,
    write_csv,
    write_json,
)


def final_map(rows: list[dict[str, Any]], method: str, budget: int) -> dict[tuple[str, int], float]:
    return {
        (row["workload_id"], int(row["seed"])): float(row["best_so_far_ms"])
        for row in rows
        if row["method"] == method and int(row["iteration"]) == budget
    }


def paired_bootstrap(
    name: str, left: dict[tuple[str, int], float], right: dict[tuple[str, int], float],
    seed: int = 20260715, replicates: int = 10000,
) -> dict[str, Any]:
    keys = sorted(set(left) & set(right))
    if set(left) != set(right) or not keys:
        raise ValueError(f"unpaired comparison {name}")
    log_ratios = np.asarray([math.log(right[key] / left[key]) for key in keys])
    rng = np.random.default_rng(seed)
    samples = rng.choice(log_ratios, size=(replicates, len(log_ratios)), replace=True)
    estimates = np.exp(samples.mean(axis=1))
    point = math.exp(float(np.mean(log_ratios)))
    return {
        "comparison": name,
        "pairs": len(keys),
        "left_speedup_over_right_gmean": point,
        "ci_low": float(np.quantile(estimates, 0.025)),
        "ci_high": float(np.quantile(estimates, 0.975)),
        "left_win_rate": float(np.mean([left[key] < right[key] for key in keys])),
        "tie_rate": float(np.mean([
            math.isclose(left[key], right[key], rel_tol=1.0e-12, abs_tol=1.0e-15)
            for key in keys
        ])),
    }


def multisource_final(
    rows: list[dict[str, Any]], method: str, budget: int,
) -> dict[tuple[str, int], float]:
    return {
        (row["workload_id"], int(row["seed"])): float(row["best_so_far_ms"])
        for row in rows
        if row["method"] == method and int(row["iteration"]) == budget
    }


def main() -> None:
    f64 = read_json(PROCESSED / "f64_contract_summary.json")
    online = read_json(PROCESSED / "true_online_summary.json")
    optuna = read_json(PROCESSED / "optuna_summary.json")
    multisource = read_json(PROCESSED / "multisource_summary.json")
    online_traces = read_csv(RAW / "true_online_traces.csv")
    optuna_traces = read_csv(RAW / "optuna_traces.csv")
    multisource_traces = read_csv(RAW / "multisource_traces.csv")

    comparisons = [
        paired_bootstrap(
            "offline_calibrated_vs_random_budget5",
            final_map(online_traces, "C2_offline_calibrated", 5),
            final_map(online_traces, "C0_random", 5),
            seed=20260714,
        ),
        paired_bootstrap(
            "online_calibrated_vs_random_budget5",
            final_map(online_traces, "C3_online_calibrated", 5),
            final_map(online_traces, "C0_random", 5),
        ),
        paired_bootstrap(
            "online_calibrated_vs_optuna_tpe_budget5",
            final_map(online_traces, "C3_online_calibrated", 5),
            final_map(optuna_traces, "D1_optuna_tpe", 5),
            seed=20260716,
        ),
        paired_bootstrap(
            "online_calibrated_vs_random_budget25",
            final_map(online_traces, "C3_online_calibrated", 25),
            final_map(online_traces, "C0_random", 25),
            seed=20260717,
        ),
        paired_bootstrap(
            "online_calibrated_vs_optuna_tpe_budget25",
            final_map(online_traces, "C3_online_calibrated", 25),
            final_map(optuna_traces, "D1_optuna_tpe", 25),
            seed=20260718,
        ),
        paired_bootstrap(
            "blis_only_vs_naive_merge_budget5",
            multisource_final(multisource_traces, "S1_blis_only", 5),
            multisource_final(multisource_traces, "S3_naive_merge", 5),
            seed=20260719,
        ),
        paired_bootstrap(
            "calibrated_source_prior_vs_naive_merge_budget5",
            multisource_final(multisource_traces, "S4_calibrated", 5),
            multisource_final(multisource_traces, "S3_naive_merge", 5),
            seed=20260720,
        ),
        paired_bootstrap(
            "calibrated_source_prior_vs_blis_only_budget5",
            multisource_final(multisource_traces, "S4_calibrated", 5),
            multisource_final(multisource_traces, "S1_blis_only", 5),
            seed=20260721,
        ),
        paired_bootstrap(
            "calibrated_source_prior_vs_naive_merge_budget25",
            multisource_final(multisource_traces, "S4_calibrated", 25),
            multisource_final(multisource_traces, "S3_naive_merge", 25),
            seed=20260722,
        ),
    ]
    write_csv(PROCESSED / "paired_bootstrap_comparisons.csv", comparisons)

    online_fixed = read_csv(PROCESSED / "true_online_fixed_budget.csv")
    optuna_fixed = read_csv(PROCESSED / "optuna_fixed_budget.csv")
    multisource_fixed = read_csv(PROCESSED / "multisource_fixed_budget.csv")
    summary = {
        "status": "PASS" if all(
            item["status"] == "PASS" for item in (f64, online, optuna, multisource)
        ) else "FAIL",
        "experiment_id": "thesis.cgo_local_extension",
        "studies": {
            "f64_contract": f64,
            "true_online": online,
            "optuna_tpe": optuna,
            "multisource": multisource,
        },
        "paired_bootstrap": comparisons,
        "evidence_boundaries": [
            "Compatibility transfer is tested on f32 6x16 and f64 6x8 BLIS Haswell contracts.",
            "True-online and Optuna target objectives are fresh subprocess measurements.",
            "Multi-source ranking is an offline replay and never merges incompatible kernel ABIs.",
            "Cross-host generalization remains pending until a 14900-series archive is imported.",
        ],
    }
    write_json(PROCESSED / "cgo_extension_summary.json", summary)

    REPORTS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CGO Extension Results", "", f"Overall status: `{summary['status']}`", "",
        "## Additional dtype and Contract", "",
        f"The f64 dgemm 6x8 study covered {f64['workloads']} workloads and "
        f"{f64['trial_rows']} raw trial rows. Direct/adapt prediction agreement was "
        f"`{f64['all_predictions_match']}`. The geometric best-candidate ratio relative "
        f"to the full BLIS frontend was {float(f64['relative_to_blis_gmean']):.3f}.",
        "", "## Live tuner comparison", "",
        "| Method | Budget | Relative to BLIS | Relative to posthoc pool best |",
        "|---|---:|---:|---:|",
    ]
    for row in online_fixed + optuna_fixed:
        lines.append(
            f"| {row['method']} | {row['budget']} | "
            f"{float(row['relative_to_b5_gmean']):.3f} | "
            f"{float(row['relative_to_posthoc_pool_best_gmean']):.3f} |"
        )
    lines.extend([
        "", "## Source-labelled prior ablation", "",
        "| Method | Budget | Relative to pool best |", "|---|---:|---:|",
    ])
    for row in multisource_fixed:
        lines.append(
            f"| {row['method']} | {row['budget']} | "
            f"{float(row['relative_to_pool_best_gmean']):.3f} |"
        )
    lines.extend([
        "", "## Paired comparisons", "",
        "A speedup above 1 favors the left method.", "",
        "| Comparison | Pairs | Speedup | 95% CI | Left win rate | Tie rate |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in comparisons:
        lines.append(
            f"| {row['comparison']} | {row['pairs']} | "
            f"{float(row['left_speedup_over_right_gmean']):.3f} | "
            f"[{float(row['ci_low']):.3f}, {float(row['ci_high']):.3f}] | "
            f"{float(row['left_win_rate']):.3f} | {float(row['tie_rate']):.3f} |"
        )
    lines.extend(["", "## Boundaries", ""])
    lines.extend(f"- {item}" for item in summary["evidence_boundaries"])
    lines.append("")
    (REPORTS / "cgo_extension_results.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    output_paths = [
        PROCESSED / "cgo_extension_summary.json",
        PROCESSED / "paired_bootstrap_comparisons.csv",
        REPORTS / "cgo_extension_results.md",
        PROCESSED / "f64_contract_summary.json",
        PROCESSED / "true_online_summary.json",
        PROCESSED / "optuna_summary.json",
        PROCESSED / "multisource_summary.json",
    ]
    provenance = PROJECT / "provenance" / "cgo_extension_manifest.json"
    write_json(provenance, {
        "schema_version": 1,
        "experiment_id": summary["experiment_id"],
        "inputs": {
            str(PROJECT / "data" / "experiment_config.json"): sha256(
                PROJECT / "data" / "experiment_config.json"
            ),
        },
        "outputs": {str(path): sha256(path) for path in output_paths},
    })
    print(json.dumps({
        "status": summary["status"],
        "f64_workloads": f64["workloads"],
        "online_trace_rows": online["trace_rows"],
        "optuna_measurements": optuna["unique_measurements"],
        "multisource_trace_rows": multisource["trace_rows"],
        "comparisons": comparisons,
    }, indent=2))


if __name__ == "__main__":
    main()
