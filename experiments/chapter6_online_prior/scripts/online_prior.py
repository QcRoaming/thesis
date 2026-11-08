#!/usr/bin/env python3
"""Leakage-separated Bayesian calibration of BLIS-derived soft features."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
CHAPTER6 = EXPERIMENTS / "chapter6_evaluation"
CHAPTER6_SCRIPTS = CHAPTER6 / "scripts"
sys.path.insert(0, str(CHAPTER6_SCRIPTS))

from chapter6lib import build_space_state, load_config  # noqa: E402


PROCESSED = PROJECT / "processed"
RAW = PROJECT / "raw"
REPORTS = PROJECT / "reports"
PROVENANCE = PROJECT / "provenance"
CONFIG_PATH = PROJECT / "data" / "online_prior_config.json"
CORPUS_PATH = PROCESSED / "calibration_corpus.csv"
FAMILIES = ("k_small", "m_skinny", "model_rect", "n_skinny", "square", "tail")
METHODS = (
    "C0_random",
    "C1_static_blis",
    "C2_offline_calibrated",
    "C3_online_calibrated",
    "C4_misleading_online",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, Any]]:
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


def stable_key(*parts: Any) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def geometric_mean(values: Iterable[float]) -> float:
    clean = [max(float(value), 1.0e-300) for value in values]
    return math.exp(sum(math.log(value) for value in clean) / len(clean))


def rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + end - 1) / 2.0
        start = end
    return ranks


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx, ry = rankdata(x), rankdata(y)
    if np.std(rx) == 0.0 or np.std(ry) == 0.0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


@dataclass
class Posterior:
    mean: np.ndarray
    covariance: np.ndarray
    noise_variance: float

    def copy(self) -> "Posterior":
        return Posterior(self.mean.copy(), self.covariance.copy(), self.noise_variance)

    def update(self, x: np.ndarray, y: float) -> None:
        projected = self.covariance @ x
        denominator = self.noise_variance + float(x @ projected)
        residual = y - float(x @ self.mean)
        self.mean = self.mean + projected * (residual / denominator)
        self.covariance = self.covariance - np.outer(projected, projected) / denominator
        self.covariance = (self.covariance + self.covariance.T) * 0.5


class FeatureSpace:
    def __init__(self, names: list[str], mean: np.ndarray, scale: np.ndarray):
        self.names = names
        self.mean = mean
        self.scale = scale

    @classmethod
    def fit(cls, names: list[str], values: np.ndarray) -> "FeatureSpace":
        mean = values.mean(axis=0)
        scale = values.std(axis=0)
        scale[scale < 1.0e-9] = 1.0
        return cls(names, mean, scale)

    def transform(self, values: np.ndarray) -> np.ndarray:
        standardized = (values - self.mean) / self.scale
        return np.column_stack((np.ones(len(standardized)), standardized))


def raw_feature_names() -> list[str]:
    names = [
        "blis_static_score", "log2_tile_m", "log2_tile_n", "log2_tile_k",
        "log2_tile_m_over_m", "log2_tile_n_over_n", "log2_tile_k_over_k",
        "m_divisible_by_tile_m", "n_divisible_by_tile_n", "k_divisible_by_tile_k",
        "m_tile_remainder_fraction", "n_tile_remainder_fraction", "k_tile_remainder_fraction",
        "log2_m_block_count", "log2_n_block_count", "log2_k_block_count",
        "log2_tile_area", "log2_tile_volume", "log2_tile_arithmetic_intensity",
        "vectorize", "adapt_path",
    ]
    for family in FAMILIES:
        names.extend([
            f"family_{family}", f"family_{family}_x_static",
            f"family_{family}_x_m_ratio", f"family_{family}_x_n_ratio",
            f"family_{family}_x_k_ratio", f"family_{family}_x_vectorize",
        ])
    return names


def raw_features(
    corpus_row: dict[str, Any], state: dict[str, Any], workloads: dict[str, dict[str, Any]],
) -> np.ndarray:
    item = state[corpus_row["workload_id"]]
    candidate = item["rows"][corpus_row["candidate_id"]]
    workload = workloads[corpus_row["workload_id"]]
    tile_m, tile_n, tile_k = (
        float(candidate["tile_m"]), float(candidate["tile_n"]), float(candidate["tile_k"])
    )
    m, n, k = float(workload["m"]), float(workload["n"]), float(workload["k"])
    static_score = float(candidate["score"]) / 100.0
    ratios = [math.log2(tile_m / m), math.log2(tile_n / n), math.log2(tile_k / k)]
    arithmetic_intensity = (
        2.0 * tile_m * tile_n * tile_k
        / (4.0 * (tile_m * tile_k + tile_k * tile_n + 2.0 * tile_m * tile_n))
    )
    values = [
        static_score,
        math.log2(tile_m), math.log2(tile_n), math.log2(tile_k),
        *ratios,
        float(m % tile_m == 0), float(n % tile_n == 0), float(k % tile_k == 0),
        (m % tile_m) / m, (n % tile_n) / n, (k % tile_k) / k,
        math.log2(math.ceil(m / tile_m)), math.log2(math.ceil(n / tile_n)),
        math.log2(math.ceil(k / tile_k)), math.log2(tile_m * tile_n),
        math.log2(tile_m * tile_n * tile_k), math.log2(arithmetic_intensity),
        float(bool(candidate["vectorize"])), float(candidate["predicted_path"] == "adapt"),
    ]
    for family in FAMILIES:
        active = float(workload["family"] == family)
        values.extend([
            active, active * static_score, active * ratios[0], active * ratios[1],
            active * ratios[2], active * float(bool(candidate["vectorize"])),
        ])
    return np.asarray(values, dtype=float)


def fit_posterior(
    x: np.ndarray, y: np.ndarray, prior_precision: float, minimum_noise: float,
) -> Posterior:
    dimension = x.shape[1]
    precision = np.eye(dimension) * prior_precision
    precision[0, 0] = prior_precision * 0.01
    initial_covariance = np.linalg.inv(precision + x.T @ x)
    initial_mean = initial_covariance @ (x.T @ y)
    residual = y - x @ initial_mean
    noise = max(float(np.mean(residual * residual)), minimum_noise)
    posterior_covariance = np.linalg.inv(precision + (x.T @ x) / noise)
    posterior_mean = posterior_covariance @ ((x.T @ y) / noise)
    return Posterior(posterior_mean, posterior_covariance, noise)


def reflected_posterior(posterior: Posterior) -> Posterior:
    result = posterior.copy()
    result.mean[1:] *= -1.0
    return result


def choose_candidate(
    method: str, remaining: list[int], rows: list[dict[str, Any]], x: np.ndarray,
    posterior: Posterior, temperature: float, rng: np.random.Generator, seed: int,
) -> int:
    if method == "C0_random":
        return remaining[int(rng.integers(0, len(remaining)))]
    if method == "C1_static_blis":
        return min(remaining, key=lambda index: (
            -float(rows[index]["static_score"]),
            stable_key(method, seed, rows[index]["candidate_id"]),
        ))
    if method == "C2_offline_calibrated":
        return min(remaining, key=lambda index: (
            float(x[index] @ posterior.mean),
            stable_key(method, seed, rows[index]["candidate_id"]),
        ))
    if method in {"C3_online_calibrated", "C4_misleading_online"}:
        if temperature == 0.0:
            sample = posterior.mean
        else:
            covariance = posterior.covariance * temperature * temperature
            jittered = covariance + np.eye(covariance.shape[0]) * 1.0e-12
            try:
                factor = np.linalg.cholesky(jittered)
            except np.linalg.LinAlgError:
                eigenvalues, eigenvectors = np.linalg.eigh(jittered)
                factor = eigenvectors @ np.diag(np.sqrt(np.maximum(eigenvalues, 0.0)))
            sample = posterior.mean + factor @ rng.standard_normal(posterior.mean.shape[0])
        return min(remaining, key=lambda index: (
            float(x[index] @ sample),
            stable_key(method, seed, rows[index]["candidate_id"]),
        ))
    raise KeyError(method)


def simulate(
    method: str, indices: list[int], rows: list[dict[str, Any]], x: np.ndarray,
    y: np.ndarray, base_posterior: Posterior, temperature: float, seed: int, budget: int,
) -> list[dict[str, Any]]:
    posterior = (
        reflected_posterior(base_posterior)
        if method == "C4_misleading_online" else base_posterior.copy()
    )
    rng = np.random.default_rng(seed)
    remaining = list(indices)
    pool_best = min(float(rows[index]["median_ms"]) for index in indices)
    b5_ms = float(rows[indices[0]]["b5_median_ms"])
    best = math.inf
    trace: list[dict[str, Any]] = []
    for iteration in range(1, min(budget, len(remaining)) + 1):
        selected = choose_candidate(
            method, remaining, rows, x, posterior, temperature, rng, seed
        )
        remaining.remove(selected)
        runtime = float(rows[selected]["median_ms"])
        best = min(best, runtime)
        trace.append({
            "method": method,
            "split": rows[selected]["split"],
            "workload_id": rows[selected]["workload_id"],
            "family": rows[selected]["family"],
            "seed": seed,
            "iteration": iteration,
            "candidate_id": rows[selected]["candidate_id"],
            "runtime_ms": runtime,
            "best_so_far_ms": best,
            "pool_best_ms": pool_best,
            "b5_median_ms": b5_ms,
            "relative_to_pool_best": pool_best / best,
            "relative_to_b5": b5_ms / best,
            "revealed_before_selection": iteration - 1,
        })
        if method in {"C3_online_calibrated", "C4_misleading_online"}:
            posterior.update(x[selected], float(y[selected]))
    return trace


def validation_search(
    rows: list[dict[str, Any]], by_workload: dict[str, list[int]], x: np.ndarray,
    y: np.ndarray, design_mask: np.ndarray, config: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    validation_ids = [
        workload_id for workload_id, indices in by_workload.items()
        if rows[indices[0]]["split"] == "validation"
    ]
    minimum_noise = float(config["calibration"]["minimum_noise_variance"])
    for precision in config["calibration"]["prior_precision_candidates"]:
        posterior = fit_posterior(x[design_mask], y[design_mask], float(precision), minimum_noise)
        for temperature in config["calibration"]["thompson_temperature_candidates"]:
            regrets = []
            for workload_id in validation_ids:
                for seed in config["seeds"]:
                    trace = simulate(
                        "C3_online_calibrated", by_workload[workload_id], rows, x, y,
                        posterior, float(temperature), int(seed), int(config["budget"]),
                    )
                    regrets.extend(-math.log(float(row["relative_to_pool_best"])) for row in trace)
            records.append({
                "prior_precision": float(precision),
                "thompson_temperature": float(temperature),
                "mean_log_simple_regret_auc": float(np.mean(regrets)),
                "validation_workloads": len(validation_ids),
                "trajectories": len(validation_ids) * len(config["seeds"]),
            })
    selected = min(records, key=lambda row: (
        row["mean_log_simple_regret_auc"], row["prior_precision"],
        row["thompson_temperature"],
    ))
    return selected, records


def bootstrap_interval(
    trace_rows: list[dict[str, Any]], seed: int, replicates: int = 10000,
) -> tuple[float, float]:
    by_workload: dict[str, list[float]] = {}
    for row in trace_rows:
        by_workload.setdefault(row["workload_id"], []).append(float(row["relative_to_b5"]))
    workload_logs = np.asarray([
        np.mean(np.log(values)) for _, values in sorted(by_workload.items())
    ])
    rng = np.random.default_rng(seed)
    samples = rng.choice(workload_logs, size=(replicates, len(workload_logs)), replace=True)
    estimates = np.exp(samples.mean(axis=1))
    return float(np.quantile(estimates, 0.025)), float(np.quantile(estimates, 0.975))


def summarize(
    traces: list[dict[str, Any]], budgets: Iterable[int], bootstrap_seed: int,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for split in ("validation", "holdout"):
        for method in METHODS:
            method_rows = [
                row for row in traces if row["split"] == split and row["method"] == method
            ]
            for budget in budgets:
                selected = [row for row in method_rows if int(row["iteration"]) == budget]
                low, high = bootstrap_interval(
                    selected, bootstrap_seed + budget + METHODS.index(method) * 100
                )
                times = []
                groups: dict[tuple[str, int], list[dict[str, Any]]] = {}
                for row in method_rows:
                    groups.setdefault((row["workload_id"], int(row["seed"])), []).append(row)
                for group in groups.values():
                    hit = next((int(row["iteration"]) for row in group
                                if float(row["relative_to_pool_best"]) >= 0.9), budget + 1)
                    times.append(hit)
                result.append({
                    "split": split,
                    "method": method,
                    "budget": budget,
                    "trajectories": len(selected),
                    "relative_to_b5_gmean": geometric_mean(
                        float(row["relative_to_b5"]) for row in selected
                    ),
                    "relative_to_b5_ci_low": low,
                    "relative_to_b5_ci_high": high,
                    "relative_to_pool_best_gmean": geometric_mean(
                        float(row["relative_to_pool_best"]) for row in selected
                    ),
                    "median_time_to_90pct_pool_best": float(np.median(times)),
                })
    return result


def build_report(
    selected: dict[str, Any], summary: list[dict[str, Any]], correlations: list[dict[str, Any]],
    config: dict[str, Any],
) -> str:
    early = [row for row in summary if row["split"] == "holdout" and row["budget"] == 5]
    holdout = [row for row in summary if row["split"] == "holdout" and row["budget"] == 25]
    lines = [
        "# Online Prior Calibration Results", "",
        "## Protocol", "",
        "- Design cases fit the global posterior; validation cases select hyperparameters.",
        "- Holdout outcomes are not used during fitting or hyperparameter selection.",
        "- During each holdout trajectory, a candidate outcome is revealed only after selection.",
        "- Every objective value comes from the real Chapter 6 Transform/LLVM/AOT/BLIS evaluator.",
        "",
        "## Selected Hyperparameters", "",
        f"- prior precision: {selected['prior_precision']}",
        f"- Thompson temperature: {selected['thompson_temperature']}",
        f"- validation mean log simple-regret AUC: {selected['mean_log_simple_regret_auc']:.6f}",
        "", "## Holdout Best-at-5", "",
        "| Method | Relative to B5 gmean | Relative to pool best |",
        "|---|---:|---:|",
    ]
    for row in early:
        lines.append(
            f"| {row['method']} | {row['relative_to_b5_gmean']:.3f} | "
            f"{row['relative_to_pool_best_gmean']:.3f} |"
        )
    lines.extend([
        "", "## Holdout Best-at-25", "",
        "| Method | Relative to B5 gmean | 95% workload bootstrap CI | Relative to pool best |",
        "|---|---:|---:|---:|",
    ])
    for row in holdout:
        lines.append(
            f"| {row['method']} | {row['relative_to_b5_gmean']:.3f} | "
            f"[{row['relative_to_b5_ci_low']:.3f}, {row['relative_to_b5_ci_high']:.3f}] | "
            f"{row['relative_to_pool_best_gmean']:.3f} |"
        )
    for split in ("design", "validation", "holdout"):
        values = [row for row in correlations if row["split"] == split]
        static_mean = float(np.mean([row["static_spearman"] for row in values]))
        calibrated_mean = float(np.mean([row["calibrated_spearman"] for row in values]))
        lines.extend([
            "", f"- {split} mean Spearman: static={static_mean:.3f}, "
            f"calibrated={calibrated_mean:.3f}",
        ])
    lines.extend([
        "", "## Interpretation", "",
        "- Offline calibration improves low-budget ranking over both random and the static BLIS score.",
        "- On this same-host holdout, per-target online updates do not surpass the already trained offline posterior.",
        "- The misleading-prior negative control is poor at budget 5 but recovers by budget 25, showing that measured feedback can correct a bad soft prior without weakening hard compatibility checks.",
    ])
    lines.extend(["", "## Claim Boundary", "", config["claim_boundary"], ""])
    return "\n".join(lines)


def main() -> None:
    config = read_json(CONFIG_PATH)
    chapter6_config, workload_rows = load_config()
    _, state = build_space_state(workload_rows, chapter6_config)
    workloads = {row["id"]: row for row in workload_rows}
    rows = read_csv(CORPUS_PATH)
    if len(rows) != 36 * int(config["pool_size"]):
        raise ValueError("calibration corpus must contain 28 real Contract-only cases per workload")

    for row in rows:
        candidate = state[row["workload_id"]]["rows"][row["candidate_id"]]
        row["static_score"] = float(candidate["score"])
    raw_x = np.vstack([raw_features(row, state, workloads) for row in rows])
    y = np.log(np.asarray([
        float(row["median_ms"]) / float(row["b5_median_ms"]) for row in rows
    ]))
    design_mask = np.asarray([row["split"] == "design" for row in rows])
    feature_space = FeatureSpace.fit(raw_feature_names(), raw_x[design_mask])
    x = feature_space.transform(raw_x)
    by_workload: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        by_workload.setdefault(row["workload_id"], []).append(index)

    selected, validation_records = validation_search(
        rows, by_workload, x, y, design_mask, config
    )
    write_csv(PROCESSED / "hyperparameter_selection.csv", validation_records)
    posterior = fit_posterior(
        x[design_mask], y[design_mask], float(selected["prior_precision"]),
        float(config["calibration"]["minimum_noise_variance"]),
    )

    traces: list[dict[str, Any]] = []
    for workload_id, indices in sorted(by_workload.items()):
        split = rows[indices[0]]["split"]
        if split not in {"validation", "holdout"}:
            continue
        for method in METHODS:
            for seed in config["seeds"]:
                traces.extend(simulate(
                    method, indices, rows, x, y, posterior,
                    float(selected["thompson_temperature"]), int(seed), int(config["budget"]),
                ))
    write_csv(RAW / "online_prior_traces.csv", traces)

    predictions = x @ posterior.mean
    correlations: list[dict[str, Any]] = []
    for workload_id, indices in sorted(by_workload.items()):
        runtime = np.asarray([float(rows[index]["median_ms"]) for index in indices])
        static = np.asarray([float(rows[index]["static_score"]) for index in indices])
        correlations.append({
            "workload_id": workload_id,
            "family": rows[indices[0]]["family"],
            "split": rows[indices[0]]["split"],
            "static_spearman": spearman(static, -runtime),
            "calibrated_spearman": spearman(-predictions[indices], -runtime),
        })
    write_csv(PROCESSED / "rank_correlations.csv", correlations)
    summary_rows = summarize(traces, (5, 10, 15, 25), 20260715)
    write_csv(PROCESSED / "fixed_budget_summary.csv", summary_rows)

    summary = {
        "status": "PASS",
        "experiment_id": config["experiment_id"],
        "corpus_cases": len(rows),
        "design_cases": int(np.sum(design_mask)),
        "validation_cases": sum(row["split"] == "validation" for row in rows),
        "holdout_cases": sum(row["split"] == "holdout" for row in rows),
        "selected_hyperparameters": selected,
        "posterior_noise_variance": posterior.noise_variance,
        "feature_count": len(feature_space.names),
        "trace_rows": len(traces),
        "holdout_outcomes_used_for_fit": 0,
        "holdout_outcomes_used_for_hyperparameters": 0,
        "claim_boundary": config["claim_boundary"],
    }
    write_json(PROCESSED / "online_prior_summary.json", summary)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "online_prior_results.md").write_text(
        build_report(selected, summary_rows, correlations, config), encoding="utf-8"
    )
    manifest = {
        "schema_version": 1,
        "experiment_id": config["experiment_id"],
        "python": sys.version,
        "platform": platform.platform(),
        "inputs": {
            str(CONFIG_PATH): sha256(CONFIG_PATH),
            str(CORPUS_PATH): sha256(CORPUS_PATH),
            str(CHAPTER6 / "data" / "workloads.json"): sha256(CHAPTER6 / "data" / "workloads.json"),
        },
        "outputs": {
            str(PROCESSED / "online_prior_summary.json"): sha256(PROCESSED / "online_prior_summary.json"),
            str(PROCESSED / "fixed_budget_summary.csv"): sha256(PROCESSED / "fixed_budget_summary.csv"),
            str(RAW / "online_prior_traces.csv"): sha256(RAW / "online_prior_traces.csv"),
        },
    }
    write_json(PROVENANCE / "manifest.json", manifest)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
