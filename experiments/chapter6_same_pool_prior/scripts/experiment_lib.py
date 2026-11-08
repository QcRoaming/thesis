#!/usr/bin/env python3
"""Shared data, calibration, statistics, and audit helpers."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
CONFIG_PATH = PROJECT / "data" / "experiment_config.json"
RAW = PROJECT / "raw"
PROCESSED = PROJECT / "processed"
REPORTS = PROJECT / "reports"
PROVENANCE = PROJECT / "provenance"
BUILD = PROJECT / "build"

CGO_SCRIPTS = EXPERIMENTS / "cgo_extension" / "scripts"
if str(CGO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(CGO_SCRIPTS))

from cgo_common import microkernel_schedule  # noqa: E402


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )


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


def stable_hash(*parts: Any) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def geometric_mean(values: Iterable[float]) -> float:
    clean = [max(float(value), 1.0e-300) for value in values]
    if not clean:
        raise ValueError("geometric mean requires at least one value")
    return math.exp(sum(math.log(value) for value in clean) / len(clean))


def load_config() -> dict[str, Any]:
    return read_json(CONFIG_PATH)


def resolve_experiment_path(relative: str) -> Path:
    path = (EXPERIMENTS / relative).resolve()
    if EXPERIMENTS.resolve() not in path.parents:
        raise ValueError(f"path escapes experiment root: {relative}")
    return path


def load_workloads(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    document = read_json(resolve_experiment_path(config["workloads"]))
    if document.get("declaration_status") != "frozen_before_measurement":
        raise ValueError("workload matrix must be frozen before measurement")
    workloads = {row["id"]: row for row in document["workloads"]}
    if len(workloads) != len(document["workloads"]):
        raise ValueError("duplicate workload IDs")
    return workloads


def _is_true(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def canonicalize_pool(
    config: dict[str, Any], workloads: dict[str, dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Remove codegen aliases and retain one measured representative per tile tuple."""
    rows = read_csv(resolve_experiment_path(config["pool_metadata"]))
    raw_by_workload: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        raw_by_workload[row["workload_id"]].append(row)
    if set(raw_by_workload) != set(workloads):
        raise ValueError("pool/workload ID mismatch")

    canonical: dict[str, list[dict[str, Any]]] = {}
    for workload_id, workload_rows in sorted(raw_by_workload.items()):
        aliases: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)
        for row in workload_rows:
            if row["pack_mode"] != "ab":
                raise ValueError(f"non-Contract packing in {workload_id}: {row['candidate_id']}")
            key = (int(row["tile_m"]), int(row["tile_n"]), int(row["tile_k"]))
            aliases[key].append(row)

        selected: list[dict[str, Any]] = []
        for (tile_m, tile_n, tile_k), variants in sorted(aliases.items()):
            variants = sorted(
                variants,
                key=lambda row: (_is_true(row["vectorize"]), row["candidate_id"]),
            )
            representative = variants[0]
            active_score = float(representative["score"])
            if _is_true(representative["vectorize"]):
                active_score -= 5.0
            selected.append({
                "workload_id": workload_id,
                "canonical_id": f"tm{tile_m}_tn{tile_n}_tk{tile_k}",
                "source_candidate_id": representative["candidate_id"],
                "source_aliases": json.dumps(
                    [row["candidate_id"] for row in variants], separators=(",", ":")
                ),
                "tile_m": tile_m,
                "tile_n": tile_n,
                "tile_k": tile_k,
                "pack_mode": "ab",
                "predicted_path": representative["predicted_path"],
                "active_static_score": active_score,
                "source_vectorize": _is_true(representative["vectorize"]),
                "split": workloads[workload_id]["split"],
                "family": workloads[workload_id]["family"],
            })
        if len(selected) < int(config["budget"]):
            raise ValueError(
                f"canonical pool {workload_id} has {len(selected)} candidates, "
                f"below budget {config['budget']}"
            )
        canonical[workload_id] = selected
    return canonical


def pool_fingerprint(pool: list[dict[str, Any]]) -> str:
    payload = [
        {
            "canonical_id": row["canonical_id"],
            "tile_m": int(row["tile_m"]),
            "tile_n": int(row["tile_n"]),
            "tile_k": int(row["tile_k"]),
        }
        for row in pool
    ]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load_host_corpus(
    environment: dict[str, Any],
    pools: dict[str, list[dict[str, Any]]],
    workloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    rows = read_csv(resolve_experiment_path(environment["aggregates"]))
    candidate_values: dict[tuple[str, str], dict[str, Any]] = {}
    baselines: dict[str, float] = {}
    for row in rows:
        if row["variant"] == "B5_blis":
            baselines[row["workload_id"]] = float(row["median_ms"])
        elif row["variant"].startswith("candidate:"):
            candidate_values[(row["workload_id"], row["candidate_id"])] = row
    if set(baselines) != set(workloads):
        raise ValueError(f"{environment['id']} does not contain every B5 baseline")

    records: list[dict[str, Any]] = []
    by_workload: dict[str, list[int]] = defaultdict(list)
    for workload_id, pool in sorted(pools.items()):
        for candidate in pool:
            key = (workload_id, candidate["source_candidate_id"])
            if key not in candidate_values:
                raise KeyError(f"missing measured canonical representative: {key}")
            measured = candidate_values[key]
            if not _is_true(measured["all_pass"]):
                raise ValueError(f"failed measured candidate: {key}")
            if measured["observed_path"] != candidate["predicted_path"]:
                raise ValueError(f"path mismatch for {key}")
            runtime = float(measured["median_ms"])
            record = dict(candidate)
            record.update({
                "environment": environment["id"],
                "environment_label": environment["label"],
                "runtime_ms": runtime,
                "b5_ms": baselines[workload_id],
                "relative_to_b5": baselines[workload_id] / runtime,
            })
            by_workload[workload_id].append(len(records))
            records.append(record)
    return {
        "environment": environment,
        "records": records,
        "by_workload": dict(by_workload),
        "baselines": baselines,
    }


FAMILIES = ("k_small", "m_skinny", "model_rect", "n_skinny", "square", "tail")


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
            f"family_{family}",
            f"family_{family}_x_static",
            f"family_{family}_x_m_ratio",
            f"family_{family}_x_n_ratio",
            f"family_{family}_x_k_ratio",
        ])
    return names


def raw_features(row: dict[str, Any], workload: dict[str, Any]) -> np.ndarray:
    tile_m, tile_n, tile_k = (
        float(row["tile_m"]), float(row["tile_n"]), float(row["tile_k"])
    )
    m, n, k = float(workload["m"]), float(workload["n"]), float(workload["k"])
    static_score = float(row["active_static_score"]) / 100.0
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
        float(row["predicted_path"] == "adapt"),
    ]
    for family in FAMILIES:
        active = float(workload["family"] == family)
        values.extend([
            active, active * static_score, active * ratios[0],
            active * ratios[1], active * ratios[2],
        ])
    return np.asarray(values, dtype=float)


@dataclass
class FeatureSpace:
    mean: np.ndarray
    scale: np.ndarray

    @classmethod
    def fit(cls, values: np.ndarray) -> "FeatureSpace":
        mean = values.mean(axis=0)
        scale = values.std(axis=0)
        scale[scale < 1.0e-9] = 1.0
        return cls(mean, scale)

    def transform(self, values: np.ndarray) -> np.ndarray:
        standardized = (values - self.mean) / self.scale
        return np.column_stack((np.ones(len(standardized)), standardized))


@dataclass
class Posterior:
    mean: np.ndarray
    covariance: np.ndarray
    noise_variance: float


def fit_posterior(
    x: np.ndarray,
    y: np.ndarray,
    prior_precision: float,
    minimum_noise: float,
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
    return Posterior(mean, covariance, noise)


def prepare_calibration(
    host: dict[str, Any],
    workloads: dict[str, dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    rows = host["records"]
    raw_x = np.vstack([raw_features(row, workloads[row["workload_id"]]) for row in rows])
    # Holdout targets are deliberately absent from the calibration object. The
    # objective callback owns those values during policy replay.
    y = np.full(len(rows), np.nan, dtype=float)
    for index, row in enumerate(rows):
        if row["split"] in {"design", "validation"}:
            y[index] = math.log(float(row["runtime_ms"]) / float(row["b5_ms"]))
    design_mask = np.asarray([row["split"] == "design" for row in rows])
    feature_space = FeatureSpace.fit(raw_x[design_mask])
    x = feature_space.transform(raw_x)
    validation_rows: list[dict[str, Any]] = []
    candidates: list[tuple[float, float, Posterior]] = []
    budget = int(config["budget"])
    minimum_noise = float(config["calibration"]["minimum_noise_variance"])
    for precision in config["calibration"]["prior_precision_candidates"]:
        posterior = fit_posterior(
            x[design_mask], y[design_mask], float(precision), minimum_noise
        )
        regrets: list[float] = []
        for workload_id, indices in sorted(host["by_workload"].items()):
            if rows[indices[0]]["split"] != "validation":
                continue
            order = sorted(
                indices,
                key=lambda index: (
                    float(x[index] @ posterior.mean), rows[index]["canonical_id"]
                ),
            )
            oracle = min(float(rows[index]["runtime_ms"]) for index in indices)
            best = math.inf
            for index in order[:budget]:
                best = min(best, float(rows[index]["runtime_ms"]))
                regrets.append(-math.log(oracle / best))
        objective = float(np.mean(regrets))
        validation_rows.append({
            "environment": host["environment"]["id"],
            "prior_precision": float(precision),
            "mean_log_simple_regret_auc": objective,
            "design_rows": int(np.sum(design_mask)),
            "validation_workloads": sum(
                rows[indices[0]]["split"] == "validation"
                for indices in host["by_workload"].values()
            ),
        })
        candidates.append((objective, float(precision), posterior))
    _, selected_precision, posterior = min(candidates, key=lambda item: (item[0], item[1]))
    return {
        "x": x,
        "y": y,
        "feature_space": feature_space,
        "posterior": posterior,
        "selected_precision": selected_precision,
        "validation_rows": validation_rows,
        "design_mask": design_mask,
    }


def normalize_probabilities(values: np.ndarray, floor: float) -> np.ndarray:
    shifted = values - float(np.max(values))
    weights = np.exp(np.clip(shifted, -50.0, 0.0))
    weights = np.maximum(weights, floor)
    return weights / float(np.sum(weights))


def method_prior(
    method: str,
    indices: list[int],
    host: dict[str, Any],
    calibration: dict[str, Any],
    config: dict[str, Any],
) -> list[float] | None:
    rows = host["records"]
    # This order is the categorical token order used by run_baco_trajectory.
    indices = sorted(indices, key=lambda index: rows[index]["canonical_id"])
    floor = float(config["calibration"]["prior_probability_floor"])
    if method == "B2_no_prior_baco":
        return None
    if method == "B3_static_prior_baco":
        scores = np.asarray([float(rows[index]["active_static_score"]) for index in indices])
        scale = max(float(np.std(scores)), 1.0)
        return normalize_probabilities((scores - float(np.mean(scores))) / scale, floor).tolist()
    if method == "B4_calibrated_prior_baco":
        prediction = calibration["x"][indices] @ calibration["posterior"].mean
        scale = max(math.sqrt(calibration["posterior"].noise_variance), 0.05)
        return normalize_probabilities(-prediction / scale, floor).tolist()
    raise KeyError(method)


def parameter_liveness_audit(
    pools: dict[str, list[dict[str, Any]]],
    hosts: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    parameters = list(config["active_search_parameters"])
    parameter_index = {"tile_m": 0, "tile_n": 1, "tile_k": 2}
    host_values = {
        host["environment"]["id"]: {
            (row["workload_id"], row["canonical_id"]): float(row["runtime_ms"])
            for row in host["records"]
        }
        for host in hosts
    }
    result: list[dict[str, Any]] = []
    for parameter in parameters:
        dimension = parameter_index[parameter]
        domain_values: set[int] = set()
        pairs: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
        workloads_with_pair: set[str] = set()
        for workload_id, pool in pools.items():
            for row in pool:
                domain_values.add(int(row[parameter]))
            for left_index, left in enumerate(pool):
                left_tuple = (int(left["tile_m"]), int(left["tile_n"]), int(left["tile_k"]))
                for right in pool[left_index + 1:]:
                    right_tuple = (
                        int(right["tile_m"]), int(right["tile_n"]), int(right["tile_k"])
                    )
                    if left_tuple[dimension] == right_tuple[dimension]:
                        continue
                    if all(
                        left_tuple[index] == right_tuple[index]
                        for index in range(3) if index != dimension
                    ):
                        pairs.append((workload_id, left, right))
                        workloads_with_pair.add(workload_id)

        schedule_changed = False
        objective_changes: dict[str, int] = {key: 0 for key in host_values}
        for workload_id, left, right in pairs:
            if microkernel_schedule(left, "f64") != microkernel_schedule(right, "f64"):
                schedule_changed = True
            for environment, values in host_values.items():
                left_value = values[(workload_id, left["canonical_id"])]
                right_value = values[(workload_id, right["canonical_id"])]
                if not math.isclose(left_value, right_value, rel_tol=0.0, abs_tol=1.0e-15):
                    objective_changes[environment] += 1
        consumed_token = parameter.replace("_", "-")
        schedule_probe = microkernel_schedule(next(iter(pools.values()))[0], "f64")
        consumed = consumed_token in schedule_probe
        status = (
            "PASS" if len(domain_values) > 1 and pairs and schedule_changed
            and consumed and all(value > 0 for value in objective_changes.values())
            else "FAIL"
        )
        result.append({
            "parameter": parameter,
            "status": status,
            "domain_value_count": len(domain_values),
            "one_factor_pair_count": len(pairs),
            "workloads_with_one_factor_pair": len(workloads_with_pair),
            "consumed_by_transform_schedule": consumed,
            "schedule_text_changes_under_perturbation": schedule_changed,
            **{
                f"objective_changing_pairs_{environment}": count
                for environment, count in sorted(objective_changes.items())
            },
        })
    return result


def paired_cluster_bootstrap(
    ratios: list[dict[str, Any]], seed: int, replicates: int
) -> tuple[float, float, float]:
    by_workload: dict[str, list[float]] = defaultdict(list)
    for row in ratios:
        by_workload[row["workload_id"]].append(math.log(float(row["speedup"])))
    workload_logs = np.asarray([
        float(np.mean(values)) for _, values in sorted(by_workload.items())
    ])
    point = math.exp(float(np.mean(workload_logs)))
    rng = np.random.default_rng(seed)
    samples = rng.choice(
        workload_logs, size=(replicates, len(workload_logs)), replace=True
    )
    estimates = np.exp(samples.mean(axis=1))
    return point, float(np.quantile(estimates, 0.025)), float(np.quantile(estimates, 0.975))


def runtime_manifest(inputs: list[Path], outputs: list[Path]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "experiment_id": load_config()["experiment_id"],
        "python": sys.version,
        "platform": platform.platform(),
        "inputs": {str(path): sha256(path) for path in inputs},
        "outputs": {str(path): sha256(path) for path in outputs},
    }
