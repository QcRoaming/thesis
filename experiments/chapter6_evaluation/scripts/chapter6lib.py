#!/usr/bin/env python3
"""Shared workload, space, and pool logic for the Chapter 6 evaluation."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
REPO = EXPERIMENTS.parents[2]
CHAPTER3 = EXPERIMENTS / "chapter3_rules"
CHAPTER4 = EXPERIMENTS / "chapter4_space"
CHAPTER5 = EXPERIMENTS / "chapter5_blis_adapter"
INTEGRATED = EXPERIMENTS / "chapter4_5_integrated"
sys.path.insert(0, str(CHAPTER4 / "scripts"))

from chapter4lib import (  # noqa: E402
    Candidate,
    generate_spaces_for_task,
    load_inputs,
    raw_candidates,
    select_contract,
)


METHOD_TO_SPACE = {
    "B1": "generic",
    "B2": "contract_only",
    "B3": "expert_core",
    "B4": "expert_shell",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_key(*values: Any) -> str:
    return hashlib.sha256(":".join(map(str, values)).encode()).hexdigest()


def load_config() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config = load_json(PROJECT / "data" / "experiment_config.json")
    workload_data = load_json(PROJECT / "data" / "workloads.json")
    workloads = workload_data["workloads"]
    ids = [row["id"] for row in workloads]
    if len(workloads) != 36 or len(ids) != len(set(ids)):
        raise ValueError("the frozen Chapter 6 matrix must contain 36 unique workloads")
    if sum(bool(row["tune"]) for row in workloads) != 8:
        raise ValueError("the frozen Chapter 6 matrix must contain eight tuning workloads")
    if set(row["split"] for row in workloads) != {"design", "validation", "holdout"}:
        raise ValueError("design, validation, and holdout splits are all required")
    return config, workloads


def task_from_workload(workload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": workload["id"],
        "role": workload["family"],
        "operation": "linalg.matmul",
        "dtype": "f32",
        "shape": {"m": workload["m"], "k": workload["k"], "n": workload["n"]},
        "layout": {"a": "row_major", "b": "row_major", "c": "row_major"},
        "stride": {"a_inner": 1, "b_inner": 1, "c_inner": 1},
        "alignment_bytes": {"a": None, "b": None, "c": None},
        "target": {
            "machine": "x86_64",
            "architecture": "haswell",
            "features": ["avx2", "fma"],
            "vector_bits": 256,
            "cache_kib": {"l1d": 32, "l2": 256, "l3": 8192},
        },
        "threads": 1,
        "fallback_available": True,
        "available_adapters": {
            "packing": True,
            "mn_tail": True,
            "k_remainder": True,
            "layout_conversion": False,
            "alignment_copy": False,
        },
    }


def with_shell_ratio(space_config: dict[str, Any], ratio: float) -> dict[str, Any]:
    result = deepcopy(space_config)
    for item in result["configs"]:
        if item["id"] == "expert_shell":
            item["exploration_ratio"] = ratio
    return result


def compile_safe(row: dict[str, Any], guard: dict[str, Any]) -> bool:
    if row["predicted_path"] != "fallback" or not row["vectorize"]:
        return True
    tile_area = int(row["tile_m"]) * int(row["tile_n"])
    vector_work = tile_area * int(row["tile_k"])
    return (
        tile_area >= int(guard["minimum_vector_tile_area"])
        and vector_work <= int(guard["max_vector_ir_work"])
    )


def _hash_order(rows: list[dict[str, Any]], workload_id: str, method: str) -> list[dict[str, Any]]:
    # Candidate-only ordering maximizes binary reuse across shapes and is fixed
    # before performance measurement. Availability still depends on each space.
    return sorted(rows, key=lambda row: stable_key(method, row["candidate_id"]))


def select_pool(
    rows: list[dict[str, Any]], workload_id: str, method: str, size: int,
    reuse_frequency: Counter[str] | None = None, shell_fraction: float = 0.1,
) -> list[dict[str, Any]]:
    """Select a deterministic compile-safe pool without using measured runtime."""
    if len(rows) < size:
        raise ValueError(f"{workload_id} {method} has only {len(rows)} guarded candidates")
    if method == "B3" and reuse_frequency is not None:
        return sorted(
            rows,
            key=lambda row: (
                -reuse_frequency[row["candidate_id"]],
                stable_key(method, row["candidate_id"]),
            ),
        )[:size]
    if method != "B4":
        return _hash_order(rows, workload_id, method)[:size]

    core = [row for row in rows if row.get("is_core")]
    shell = [row for row in rows if row.get("is_shell")]
    shell_target = min(len(shell), math.ceil(size * shell_fraction))
    core_target = size - shell_target
    frequency = reuse_frequency or Counter()
    ranked_core = sorted(
        core,
        key=lambda row: (
            -frequency[row["candidate_id"]], -float(row["score"]), row["candidate_id"]
        ),
    )
    ranked_shell = sorted(
        shell,
        key=lambda row: (
            -frequency[row["candidate_id"]], -float(row["score"]),
            stable_key(workload_id, row["candidate_id"]),
        ),
    )
    selected = ranked_core[:core_target] + ranked_shell[:shell_target]
    if len(selected) < size:
        selected_ids = {row["candidate_id"] for row in selected}
        remainder = [row for row in ranked_core + ranked_shell if row["candidate_id"] not in selected_ids]
        selected.extend(remainder[: size - len(selected)])
    return selected


def build_space_state(
    workloads: list[dict[str, Any]], config: dict[str, Any], shell_ratio: float = 0.1,
) -> tuple[dict[str, Any], dict[str, Any]]:
    inputs = load_inputs(CHAPTER4)
    candidates = raw_candidates(inputs["space_config"]["raw_domain"])
    space_config = with_shell_ratio(inputs["space_config"], shell_ratio)
    state: dict[str, Any] = {}
    for workload in workloads:
        task = task_from_workload(workload)
        spaces, rows, selection_log = generate_spaces_for_task(
            task, candidates, inputs["contracts"], space_config
        )
        contract, _ = select_contract(task, inputs["contracts"])
        guarded_spaces = {
            name: [row for row in members if compile_safe(row, config["compile_cost_guard"])]
            for name, members in spaces.items()
        }
        state[task["id"]] = {
            "workload": workload,
            "task": task,
            "contract": contract,
            "rows": {row["candidate_id"]: row for row in rows},
            "spaces": spaces,
            "guarded_spaces": guarded_spaces,
            "selection_log": selection_log,
        }
    tuning_items = [item for item in state.values() if item["workload"]["tune"]]
    frequencies = {
        method: Counter(
            row["candidate_id"]
            for item in tuning_items
            for row in item["guarded_spaces"][space_name]
        )
        for method, space_name in METHOD_TO_SPACE.items()
    }
    for item in state.values():
        pools = {}
        for method, space_name in METHOD_TO_SPACE.items():
            available = item["guarded_spaces"][space_name]
            requested = int(config["pool_size"]) if item["workload"]["tune"] else min(
                int(config["pool_size"]), len(available)
            )
            pools[method] = select_pool(
                available, item["task"]["id"], method, requested, frequencies[method],
                shell_fraction=shell_ratio,
            )
        item["pools"] = pools
    return inputs, state


def space_summary(state: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for workload_id, item in state.items():
        raw_count = len(item["rows"])
        path_counts = Counter(row["predicted_path"] for row in item["rows"].values())
        row = {
            "workload_id": workload_id,
            "family": item["workload"]["family"],
            "split": item["workload"]["split"],
            "tune": item["workload"]["tune"],
            "raw_count": raw_count,
            "direct_count": path_counts["direct"],
            "adapt_count": path_counts["adapt"],
            "fallback_count": path_counts["fallback"],
            "reject_count": path_counts["reject"],
        }
        for method, space_name in METHOD_TO_SPACE.items():
            row[f"{method}_full_size"] = len(item["spaces"][space_name])
            row[f"{method}_guarded_size"] = len(item["guarded_spaces"][space_name])
            row[f"{method}_pool_size"] = len(item["pools"][method])
        result.append(row)
    return result


def shell_ratio_pools(
    workloads: list[dict[str, Any]], config: dict[str, Any], ratio: float,
) -> dict[str, list[dict[str, Any]]]:
    _, state = build_space_state(workloads, config, shell_ratio=ratio)
    return {workload["id"]: state[workload["id"]]["pools"]["B4"] for workload in workloads}


def candidate_from_row(row: dict[str, Any]) -> Candidate:
    return Candidate(
        int(row["tile_m"]), int(row["tile_n"]), int(row["tile_k"]),
        str(row["pack_mode"]), bool(row["vectorize"]),
    )


def pool_diagnostics(state: dict[str, Any]) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    for workload_id, item in state.items():
        diagnostics[workload_id] = {}
        for method, rows in item["pools"].items():
            diagnostics[workload_id][method] = {
                "count": len(rows),
                "paths": dict(Counter(row["predicted_path"] for row in rows)),
                "pack_modes": dict(Counter(row["pack_mode"] for row in rows)),
                "vectorized": sum(bool(row["vectorize"]) for row in rows),
                "core": sum(bool(row.get("is_core")) for row in rows),
                "shell": sum(bool(row.get("is_shell")) for row in rows),
            }
    return diagnostics
