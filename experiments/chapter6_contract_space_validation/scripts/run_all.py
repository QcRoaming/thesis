#!/usr/bin/env python3
"""Run E1-E4 Contract, schedule-space, reuse, and economics validation."""

from __future__ import annotations

import argparse
import ast
import copy
import csv
import hashlib
import json
import math
import random
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
CHAPTER4 = EXPERIMENTS / "chapter4_space"
CHAPTER6 = EXPERIMENTS / "chapter6_evaluation"
TERMINATION = EXPERIMENTS / "chapter6_termination_validation"
EXTERNAL = EXPERIMENTS / "chapter6_external_validation"
APPLICATION = EXPERIMENTS / "chapter6_application_validation"
CGO = EXPERIMENTS / "cgo_extension"

sys.path.insert(0, str(CHAPTER4 / "scripts"))
sys.path.insert(0, str(CHAPTER6 / "scripts"))

from chapter4lib import check_candidate, load_inputs, load_yaml, raw_candidates, select_contract  # noqa: E402
from chapter6lib import build_space_state, load_config  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value
                for key, value in row.items()
            })


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def percentile(values: Iterable[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return math.nan
    position = (len(ordered) - 1) * q
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return float(ordered[low])
    return float(ordered[low] * (high - position) + ordered[high] * (position - low))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nested_set(value: dict[str, Any], dotted: str, replacement: Any) -> None:
    cursor: Any = value
    parts = dotted.split(".")
    for part in parts[:-1]:
        cursor = cursor[part]
    cursor[parts[-1]] = replacement


def package_descriptor(package: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    return {
        "operation": package["operation"],
        "dtype": package["dtype"],
        "target": {
            "machine": package["target"]["machine"],
            "architecture": package["target"]["architecture"],
            "features": list(package["target"]["required_features"])
        },
        "kernel": copy.deepcopy(package["kernel"]),
        "layout": copy.deepcopy(package["layout"]),
        "packing": copy.deepcopy(package["packing"]),
        "abi": copy.deepcopy(package["abi"]),
        "provenance": copy.deepcopy(package["provenance"]),
        "shape": copy.deepcopy(template["shape"]),
        "beta_mode": template["beta_mode"],
        "fallback_available": template["fallback_available"]
    }


def classify_descriptor(descriptor: dict[str, Any], package: dict[str, Any]) -> dict[str, str]:
    def result(path: str, phase: str, field: str, diagnostic: str) -> dict[str, str]:
        return {"path": path, "phase": phase, "field": field, "diagnostic": diagnostic}

    if descriptor["provenance"]["source_revision"] != package["provenance"]["source_revision"]:
        return result("reject", "provenance", "provenance.source_revision", "SOURCE_REVISION_MISMATCH")
    if descriptor["provenance"]["source_sha256"] != package["provenance"]["source_sha256"]:
        return result("reject", "provenance", "provenance.source_sha256", "SOURCE_HASH_MISMATCH")
    if descriptor["operation"] != package["operation"]:
        return result("reject", "compatibility", "operation", "OPERATION_MISMATCH")
    if descriptor["dtype"] != package["dtype"]:
        return result("fallback", "compatibility", "dtype", "DTYPE_MISMATCH")
    if descriptor["target"]["machine"] != package["target"]["machine"]:
        return result("reject", "compatibility", "target.machine", "TARGET_MACHINE_MISMATCH")
    if descriptor["target"]["architecture"] != package["target"]["architecture"]:
        return result("reject", "compatibility", "target.architecture", "TARGET_ARCH_MISMATCH")
    required = set(package["target"]["required_features"])
    if not required.issubset(set(descriptor["target"]["features"])):
        return result("reject", "compatibility", "target.features", "ISA_FEATURE_MISSING")
    for field in ("mr", "nr", "k_step"):
        if descriptor["kernel"][field] != package["kernel"][field]:
            dotted = f"kernel.{field}"
            return result("reject", "kernel", dotted, f"{field.upper()}_MISMATCH")
    if descriptor["layout"]["inner_stride"] != package["layout"]["inner_stride"]:
        return result("fallback", "layout", "layout.inner_stride", "INNER_STRIDE_MISMATCH")
    for field in ("a", "b", "c"):
        if descriptor["layout"][field] != package["layout"][field]:
            return result("fallback", "layout", f"layout.{field}", "LAYOUT_MISMATCH")
    if descriptor["packing"]["schema_id"] != package["packing"]["schema_id"]:
        return result("reject", "packing", "packing.schema_id", "PACKING_SCHEMA_MISMATCH")
    if descriptor["packing"]["panel_order"] != package["packing"]["panel_order"]:
        return result("reject", "packing", "packing.panel_order", "PACKING_ORDER_MISMATCH")
    if descriptor["abi"]["schema_id"] != package["abi"]["schema_id"]:
        return result("reject", "abi", "abi.schema_id", "ABI_SCHEMA_MISMATCH")
    if descriptor["abi"]["auxiliary_schema"] != package["abi"]["auxiliary_schema"]:
        return result("reject", "abi", "abi.auxiliary_schema", "AUX_SCHEMA_MISMATCH")
    if descriptor["beta_mode"] not in package["capabilities"]["beta_modes"]:
        return result("fallback", "capability", "beta_mode", "BETA_MODE_UNSUPPORTED")

    shape = descriptor["shape"]
    mn_tail = shape["m"] % package["kernel"]["mr"] or shape["n"] % package["kernel"]["nr"]
    k_tail = shape["k"] % package["kernel"]["k_step"]
    if mn_tail and not package["capabilities"]["mn_tail"]:
        return result("fallback", "capability", "shape", "MN_TAIL_UNSUPPORTED")
    if k_tail and not package["capabilities"]["k_tail"]:
        return result("fallback", "capability", "shape", "K_TAIL_UNSUPPORTED")
    if mn_tail or k_tail:
        return result("adapt", "adaptation", "shape", "FINITE_TAIL_ADAPTER")
    return result("direct", "dispatch", "none", "DIRECT_CONTRACT_MATCH")


def run_e1() -> dict[str, Any]:
    package_data = load_json(PROJECT / "data" / "package_contracts.json")
    oracle = load_json(PROJECT / "data" / "mutation_oracle.json")
    rows: list[dict[str, Any]] = []
    for package in package_data["packages"]:
        rotating = oracle["rotating_kernel_dimension"][package["id"]]
        for blueprint in oracle["case_blueprint"]:
            descriptor = package_descriptor(package, oracle["templates"][blueprint["template"]])
            mutation = blueprint["mutation"]
            mutation_field = "none"
            if mutation is not None:
                mutation_field = mutation["field"]
                replacement = mutation["value"]
                if mutation_field == "dtype":
                    replacement = "f64" if package["dtype"] == "f32" else "f32"
                elif mutation_field == "kernel.rotating_dimension":
                    mutation_field = rotating
                    replacement = package["kernel"][rotating.split(".")[-1]] + 1
                nested_set(descriptor, mutation_field, replacement)
            predicted = classify_descriptor(descriptor, package)
            dangerous = mutation is not None
            expected_path = blueprint["expected_path"]
            expected_field = blueprint["expected_field"]
            if expected_field == "kernel.rotating_dimension":
                expected_field = rotating
            false_accept = dangerous and predicted["path"] == "direct"
            valid = not dangerous
            false_reject = valid and expected_path in {"direct", "adapt"} and predicted["path"] in {"fallback", "reject"}
            rows.append({
                "case_id": f"{package['id']}::{blueprint['suffix']}",
                "package_id": package["id"],
                "library": package["library"],
                "mutation_field": mutation_field,
                "dangerous_mutation": dangerous,
                "expected_path": expected_path,
                "predicted_path": predicted["path"],
                "expected_phase": blueprint["expected_phase"],
                "predicted_phase": predicted["phase"],
                "expected_field": expected_field,
                "predicted_field": predicted["field"],
                "diagnostic": predicted["diagnostic"],
                "path_correct": predicted["path"] == expected_path,
                "phase_correct": predicted["phase"] == blueprint["expected_phase"],
                "field_correct": predicted["field"] == expected_field,
                "false_accept": false_accept,
                "false_reject": false_reject,
                "safely_downgraded_or_rejected": dangerous and predicted["path"] != "direct"
            })

    fault_rows = []
    worker = PROJECT / "scripts" / "fault_worker.py"
    for mode in ("scrambled_b_panel", "broken_beta_tail"):
        completed = subprocess.run(
            [sys.executable, str(worker), mode], check=True, capture_output=True, text=True
        )
        fault_rows.append(json.loads(completed.stdout))

    mutations = [row for row in rows if row["dangerous_mutation"]]
    summary = {
        "case_count": len(rows),
        "package_count": len(package_data["packages"]),
        "positive_case_count": len(rows) - len(mutations),
        "mutation_count": len(mutations),
        "mutation_score": sum(row["safely_downgraded_or_rejected"] for row in mutations) / len(mutations),
        "false_accept_count": sum(row["false_accept"] for row in rows),
        "false_reject_count": sum(row["false_reject"] for row in rows),
        "path_accuracy": sum(row["path_correct"] for row in rows) / len(rows),
        "phase_accuracy": sum(row["phase_correct"] for row in rows) / len(rows),
        "diagnostic_field_accuracy": sum(row["field_correct"] for row in rows) / len(rows),
        "fault_injection_count": len(fault_rows),
        "faults_detected_by_reference": sum(row["wrong_result_detected"] for row in fault_rows),
        "claim_boundary": (
            "The static checker validates declared metadata. It cannot detect corruption of a packed "
            "buffer whose descriptor remains internally consistent; reference execution or memory "
            "protection is responsible for that failure class."
        )
    }
    write_csv(PROJECT / "processed" / "e1_mutation_results.csv", rows)
    write_csv(PROJECT / "processed" / "e1_fault_injection.csv", fault_rows)
    write_json(PROJECT / "processed" / "e1_summary.json", summary)
    return summary


def normalized_schedule_signature(space: str, row: dict[str, Any], contract_id: str) -> str:
    if space == "G0":
        signature = {
            "pipeline": "raw_generic_transform",
            "tile_sizes": [row["tile_m"], row["tile_n"], row["tile_k"]],
            "vectorize": bool(row["vectorize"])
        }
    elif row["predicted_path"] in {"direct", "adapt"}:
        checks = row["checks"]
        signature = {
            "pipeline": "contract_microkernel",
            "contract_id": contract_id,
            "path": row["predicted_path"],
            "tile_sizes": [row["tile_m"], row["tile_n"], row["tile_k"]],
            "mn_tail": checks.get("mn_tail"),
            "k_tail": checks.get("k_tail")
        }
    else:
        signature = {
            "pipeline": "generic_transform_fallback",
            "tile_sizes": [row["tile_m"], row["tile_n"], row["tile_k"]],
            "vectorize": bool(row["vectorize"])
        }
    canonical = json.dumps(signature, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def canonicalize_inactive_vectorize(
    space: str, members: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Collapse vectorize only where the selected microkernel path ignores it.

    G0 remains the declared raw Cartesian space. In G1 and C, direct/adapt
    candidates lower to the Contract microkernel path, where the generic
    vectorization toggle is not consumed. The canonical representative is the
    otherwise identical vectorize=false candidate.
    """
    if space == "G0":
        return list(members), {
            "scope": "not_applied_to_raw_cartesian_space",
            "inactive_groups": 0,
            "removed_candidates": 0
        }

    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in members:
        if row["predicted_path"] in {"direct", "adapt"}:
            key = (
                "microkernel",
                row["tile_m"], row["tile_n"], row["tile_k"], row["pack_mode"],
                row["predicted_path"],
                row["checks"].get("mn_tail"), row["checks"].get("k_tail")
            )
        else:
            key = ("vectorize_active", row["candidate_id"])
        groups[key].append(row)

    canonical: list[dict[str, Any]] = []
    inactive_groups = 0
    removed = 0
    for key, rows in groups.items():
        if key[0] != "microkernel":
            canonical.extend(rows)
            continue
        vector_values = {bool(row["vectorize"]) for row in rows}
        if vector_values != {False, True}:
            raise RuntimeError(f"incomplete inactive-vectorize pair in {space}: {key}")
        representative = next(row for row in rows if not row["vectorize"])
        canonical.append(representative)
        inactive_groups += 1
        removed += len(rows) - 1
    canonical.sort(key=lambda row: row["candidate_id"])
    return canonical, {
        "scope": "direct_and_adapt_microkernel_paths",
        "canonical_value": False,
        "inactive_groups": inactive_groups,
        "removed_candidates": removed
    }


def draws_to_first_success(total: int, successes: int, rng: random.Random) -> int | None:
    if successes <= 0:
        return None
    remaining_total, remaining_success, draws = total, successes, 0
    while remaining_total:
        draws += 1
        if rng.random() < remaining_success / remaining_total:
            return draws
        remaining_total -= 1
    return None


def run_e2() -> dict[str, Any]:
    experiment_config = load_json(PROJECT / "data" / "experiment_config.json")
    chapter6_config, workloads = load_config()
    inputs, state = build_space_state(workloads, chapter6_config)
    candidates = raw_candidates(inputs["space_config"]["raw_domain"])
    summary_rows: list[dict[str, Any]] = []
    first_rows: list[dict[str, Any]] = []
    checker_ns: list[int] = []

    for workload in workloads:
        item = state[workload["id"]]
        contract, _ = select_contract(item["task"], inputs["contracts"])
        for candidate in candidates:
            started = time.perf_counter_ns()
            check_candidate(candidate, item["task"], contract)
            checker_ns.append(time.perf_counter_ns() - started)

        all_rows = list(item["rows"].values())
        raw_spaces = {
            "G0": all_rows,
            "G1": item["spaces"]["generic"],
            "C": item["spaces"]["contract_only"]
        }
        for space, pre_members in raw_spaces.items():
            members, normalization = canonicalize_inactive_vectorize(space, pre_members)
            counts = Counter(row["predicted_path"] for row in members)
            pre_hashes = [
                normalized_schedule_signature(space, row, contract["id"])
                for row in pre_members
            ]
            hashes = [normalized_schedule_signature(space, row, contract["id"]) for row in members]
            hash_counts = Counter(hashes)
            callable_count = counts["direct"] + counts["adapt"]
            summary_rows.append({
                "workload_id": workload["id"],
                "family": workload["family"],
                "space": space,
                "raw_count": len(all_rows),
                "pre_normalization_retained_count": len(pre_members),
                "retained_count": len(members),
                "reduction_ratio": 1.0 - len(members) / len(all_rows),
                "inactive_vectorize_groups": normalization["inactive_groups"],
                "inactive_vectorize_removed_count": normalization["removed_candidates"],
                "inactive_vectorize_removed_ratio": (
                    normalization["removed_candidates"] / len(pre_members)
                ),
                "vectorize_normalization_scope": normalization["scope"],
                "direct_count": counts["direct"],
                "adapt_count": counts["adapt"],
                "fallback_count": counts["fallback"],
                "reject_count": counts["reject"],
                "direct_ratio": counts["direct"] / len(members),
                "adapt_ratio": counts["adapt"] / len(members),
                "fallback_ratio": counts["fallback"] / len(members),
                "reject_ratio": counts["reject"] / len(members),
                "callable_density": callable_count / len(members),
                "normalized_ir_unique": len(hash_counts),
                "pre_normalization_ir_duplicate_ratio": 1.0 - len(set(pre_hashes)) / len(pre_members),
                "normalized_ir_duplicate_ratio": 1.0 - len(hash_counts) / len(members),
            })
            draw_rng = random.Random(
                f"{experiment_config['seed']}:{workload['id']}:{space}:first_callable"
            )
            trial_draws = [
                draws_to_first_success(len(members), callable_count, draw_rng)
                for _ in range(int(experiment_config["random_order_trials"]))
            ]
            finite = [value for value in trial_draws if value is not None]
            first_rows.append({
                "workload_id": workload["id"],
                "space": space,
                "trials": len(trial_draws),
                "success_probability": len(finite) / len(trial_draws),
                "median_draws_to_first_callable": statistics.median(finite) if finite else None,
                "p95_draws_to_first_callable": percentile(finite, 0.95) if finite else None
            })

    manifest_data = load_json(CHAPTER6 / "processed" / "binary_manifests.json")
    manifest_ids = set(manifest_data) - {"B0_scalar", "B0_optimized", "B5_blis"}
    compile_failures = load_json(CHAPTER6 / "processed" / "compile_failures.json")
    if compile_failures:
        raise RuntimeError("the frozen compile failure manifest is no longer empty")
    representative = {row["id"]: row["role"] for row in experiment_config["representative_workloads"]}
    compile_rows: list[dict[str, Any]] = []
    sample_size = int(experiment_config["compile_replay_sample_per_workload_space"])
    for workload_id, role in representative.items():
        item = state[workload_id]
        raw_spaces = {
            "G0": list(item["rows"].values()),
            "G1": item["spaces"]["generic"],
            "C": item["spaces"]["contract_only"]
        }
        for space, pre_members in raw_spaces.items():
            eligible = [row for row in pre_members if row["candidate_id"] in manifest_ids]
            eligible.sort(key=lambda row: hashlib.sha256(
                f"{workload_id}:{space}:{row['candidate_id']}".encode()
            ).hexdigest())
            if len(eligible) < sample_size:
                raise RuntimeError(f"{workload_id}/{space} has only {len(eligible)} manifest-backed candidates")
            for row in eligible[:sample_size]:
                manifest = manifest_data[row["candidate_id"]]
                compile_rows.append({
                    "workload_id": workload_id,
                    "role": role,
                    "space": space,
                    "candidate_id": row["candidate_id"],
                    "predicted_path": row["predicted_path"],
                    "compile_status": "success",
                    "evidence_mode": "existing_real_binary_manifest_replay",
                    "normalization_status": "pre_normalization_historical_replay",
                    "executable_sha256": manifest["executable_sha256"],
                    "pipeline_ms": manifest["pipeline_ms"]
                })

    quality_rows = {row["method"]: row for row in read_csv(CHAPTER6 / "processed" / "space_quality_summary.csv")}
    chapter6_summary = load_json(CHAPTER6 / "processed" / "chapter6_summary.json")
    normalized_replay = load_json(PROJECT / "processed" / "e2_normalized_baco_summary.json")
    random_comparison = load_json(PROJECT / "processed" / "e2_baco_random_summary.json")
    if not normalized_replay["protocol_frozen_before_outcome"]:
        raise RuntimeError("normalized BaCO replay protocol was not frozen before outcome")
    if normalized_replay["compilation_performed"] or normalized_replay["hardware_measurement_performed"]:
        raise RuntimeError("normalized BaCO replay must remain data-only")
    if normalized_replay["run_count"] != 40 or normalized_replay["trace_count"] != 1000:
        raise RuntimeError("normalized BaCO replay does not match 8 workloads x 5 seeds x 25 budget")
    if not random_comparison["protocol_frozen_before_outcome"]:
        raise RuntimeError("same-pool random comparison protocol was not frozen before outcome")
    if random_comparison["compilation_performed"] or random_comparison["hardware_measurement_performed"]:
        raise RuntimeError("same-pool random comparison must remain data-only")
    if random_comparison["run_count_per_method"] != 40:
        raise RuntimeError("same-pool random comparison must contain 40 runs per method")
    if random_comparison["unique_query_budget"] != 25:
        raise RuntimeError("same-pool random comparison unique-query budget drifted")
    base_methods = {
        row["label"]: row
        for row in chapter6_summary["RQ4"]["fixed_budget"]
        if row["suite"] == "base"
    }
    quality = {
        "G0": {"D90": None, "time_to_90_pool_best": None, "measurement_status": "not_measured"},
        "G1": {
            "D90": float(quality_rows["B1"]["D90"]),
            "time_to_90_pool_best": base_methods["B1"]["median_time_to_90pct_iteration"],
            "reached_90_fraction": base_methods["B1"]["reached_90pct_pool_best_ratio"],
            "measurement_status": "historical_real_measurement_before_vectorize_normalization"
        },
        "C": {
            "D90": normalized_replay["normalized_final_method"]["D90"],
            "time_to_90_pool_best": normalized_replay["normalized_final_method"][
                "time_to_90pct_pool_best"
            ],
            "reached_90_fraction": normalized_replay["normalized_final_method"][
                "reached_90pct_pool_best_fraction"
            ],
            "measurement_status": "final_normalized_pool_offline_baco_replay",
            "performance_pool_size_per_workload": normalized_replay["pool_size_per_workload"],
            "pre_normalization_ablation": normalized_replay["pre_normalization_ablation"]
        }
    }
    checker_us = [value / 1000.0 for value in checker_ns]
    totals = {}
    for space in ("G0", "G1", "C"):
        subset = [row for row in summary_rows if row["space"] == space]
        first_subset = [row for row in first_rows if row["space"] == space]
        totals[space] = {
            "classifications": sum(row["retained_count"] for row in subset),
            "mean_pre_normalization_retained_count": statistics.mean(
                row["pre_normalization_retained_count"] for row in subset
            ),
            "mean_retained_count": statistics.mean(row["retained_count"] for row in subset),
            "mean_reduction_ratio": statistics.mean(row["reduction_ratio"] for row in subset),
            "mean_callable_density": statistics.mean(row["callable_density"] for row in subset),
            "mean_pre_normalization_ir_duplicate_ratio": statistics.mean(
                row["pre_normalization_ir_duplicate_ratio"] for row in subset
            ),
            "mean_ir_duplicate_ratio": statistics.mean(row["normalized_ir_duplicate_ratio"] for row in subset),
            "mean_inactive_vectorize_removed_ratio": statistics.mean(
                row["inactive_vectorize_removed_ratio"] for row in subset
            ),
            "inactive_vectorize_removed_count": sum(
                row["inactive_vectorize_removed_count"] for row in subset
            ),
            "median_of_workload_median_draws_to_first_callable": statistics.median(
                row["median_draws_to_first_callable"] for row in first_subset
            ),
            "p95_of_workload_p95_draws_to_first_callable": percentile(
                [row["p95_draws_to_first_callable"] for row in first_subset], 0.95
            ),
            "compile_replay_rows": sum(row["space"] == space for row in compile_rows),
            "compile_failure_rate_in_replay": 0.0,
            **quality[space]
        }
    summary = {
        "workload_count": len(workloads),
        "raw_candidates_per_workload": len(candidates),
        "static_classification_count": len(workloads) * len(candidates),
        "checker_single_candidate_median_us": statistics.median(checker_us),
        "checker_single_candidate_p95_us": percentile(checker_us, 0.95),
        "compile_replay_count": len(compile_rows),
        "compile_replay_expected": len(representative) * 3 * sample_size,
        "compile_replay_failure_count": 0,
        "compile_replay_boundary": (
            "The 768 rows replay pre-normalization existing real compiler manifests. They do not "
            "claim 768 fresh compilations, 32 unique canonical candidates per stratum, or "
            "extrapolate success to uncompiled G0 candidates."
        ),
        "vectorize_liveness_rule": (
            "vectorize remains active for the raw/generic transform path, but is canonicalized to "
            "false when a G1/C candidate dispatches to a direct or adapt Contract microkernel path"
        ),
        "normalization_boundary": (
            "Candidate counts, path ratios, callable density, IR hashes and first-callable draws "
            "are recomputed offline after canonicalization. Final C D90 and time-to-90% come from "
            "the frozen normalized-pool BaCO replay over existing objective measurements; the old "
            "11.5 result is retained only as the pre-normalization ablation. G1 remains historical."
        ),
        "normalized_baco_replay": normalized_replay,
        "same_pool_random_comparison": random_comparison,
        "spaces": totals
    }
    write_csv(PROJECT / "processed" / "e2_space_classification.csv", summary_rows)
    write_csv(PROJECT / "processed" / "e2_first_callable.csv", first_rows)
    write_csv(PROJECT / "processed" / "e2_compile_replay.csv", compile_rows)
    write_json(PROJECT / "processed" / "e2_summary.json", summary)
    return summary


def leaf_paths(value: Any, prefix: str = "") -> set[str]:
    if isinstance(value, dict):
        result: set[str] = set()
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else key
            result.update(leaf_paths(child, child_prefix))
        return result
    if isinstance(value, list):
        return {prefix}
    return {prefix}


def code_loc(path: Path) -> int:
    count = 0
    in_block = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        if in_block:
            if "*/" in line:
                in_block = False
            continue
        if line.startswith("/*"):
            in_block = "*/" not in line
            continue
        if line.startswith(("//", "#")):
            continue
        count += 1
    return count


def relevant_test_count(paths: list[Path], tokens: list[str]) -> int:
    count = 0
    lowered = [token.lower() for token in tokens]
    for root in paths:
        for path in root.rglob("test_*.py"):
            source = path.read_text(encoding="utf-8", errors="replace")
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                    segment = ast.get_source_segment(source, node) or ""
                    if any(token in segment.lower() for token in lowered):
                        count += 1
    return count


def run_e3() -> dict[str, Any]:
    packages = load_json(PROJECT / "data" / "package_contracts.json")["packages"]
    blis_facts = load_json(EXPERIMENTS / "chapter3_rules" / "data" / "facts.json")["facts"]
    multisource = load_yaml(EXPERIMENTS / "chapter3_multisource" / "data" / "multisource_facts.yaml")
    openblas_fact = next(
        row for row in multisource["facts"] if row["id"] == "openblas.riscv64_zvl128b.gemm.f32"
    )
    paths_by_package = {package["id"]: leaf_paths(package) for package in packages}
    shared = set.intersection(*paths_by_package.values())
    union = set.union(*paths_by_package.values())
    core_files = [
        CHAPTER4 / "scripts" / "chapter4lib.py",
        CHAPTER6 / "scripts" / "chapter6lib.py"
    ]
    package_ids = [package["id"] for package in packages]
    package_id_special_cases = sum(
        path.read_text(encoding="utf-8").count(package_id)
        for path in core_files for package_id in package_ids
    )
    f64_audit = load_json(TERMINATION / "processed" / "second_microkernel_audit.json")
    adapter_files = {
        "blis_haswell_f32_6x16": EXPERIMENTS / "chapter5_blis_adapter" / "runtime" / "blis_microkernel_adapter.cpp",
        "blis_haswell_f64_6x8": CGO / "runtime" / "blis_microkernel_adapter.cpp",
        "openblas_riscv64_zvl128b_f32_8x8": EXTERNAL / "runtime" / "k230_openblas_contract_bench.c"
    }
    test_roots = {
        "blis_haswell_f32_6x16": [EXPERIMENTS / "chapter5_blis_adapter" / "tests", CHAPTER6 / "tests"],
        "blis_haswell_f64_6x8": [CGO / "tests", TERMINATION / "tests"],
        "openblas_riscv64_zvl128b_f32_8x8": [EXTERNAL / "tests"]
    }
    test_tokens = {
        "blis_haswell_f32_6x16": ["6x16", "sgemm", "haswell_f32"],
        "blis_haswell_f64_6x8": ["6x8", "dgemm", "f64"],
        "openblas_riscv64_zvl128b_f32_8x8": ["openblas", "k230", "8x8"]
    }
    audit_rows = []
    for package in packages:
        package_id = package["id"]
        all_paths = paths_by_package[package_id]
        package_specific = {path for path in all_paths if path.startswith("package_specific.")}
        if package["library"] == "BLIS":
            source_facts = [
                row for row in blis_facts
                if row["library"] == "BLIS"
                and row["architecture"] == "haswell"
                and row["dtype"] == package["dtype"]
            ]
            acquisition = {
                "machine_parsed": sum(row["extraction_mode"] == "automatic" for row in source_facts),
                "machine_derived": sum(row["extraction_mode"] == "derived" for row in source_facts),
                "manual_cross_check": sum(row["verification_status"] == "source_cross_checked" for row in source_facts),
                "manual_only": sum(row["extraction_mode"] == "manual" for row in source_facts)
            }
        else:
            acquisition = {
                "machine_parsed": len(openblas_fact["evidence"]),
                "machine_derived": len(openblas_fact["performance_knowledge"]["runtime_derived"]),
                "manual_cross_check": 0,
                "manual_only": 0
            }
        if acquisition != package["fact_acquisition"]:
            raise RuntimeError(f"fact acquisition counts drifted for {package_id}: {acquisition}")
        if package_id == "blis_haswell_f32_6x16":
            core_modified_loc: int | None = None
            core_evidence = "baseline package; no onboarding delta"
            status = "BASELINE"
        elif package_id == "blis_haswell_f64_6x8":
            unchanged = f64_audit["conditions"]["core_generator_hash_unchanged"]
            core_modified_loc = 0 if unchanged else None
            core_evidence = "frozen before/after core-generator SHA-256 audit"
            status = "REUSED_SHARED_CORE"
        else:
            core_modified_loc = None
            core_evidence = "independent backend currently uses a package-local generator path"
            status = "PARTIAL_REUSE_SEPARATE_BACKEND_PATH"
        audit_rows.append({
            "package_id": package_id,
            "library": package["library"],
            "contract_total_leaf_fields": len(all_paths),
            "shared_semantic_leaf_fields": len(shared),
            "schema_union_leaf_fields": len(union),
            "schema_intersection_over_union_ratio": len(shared) / len(union),
            "package_shared_field_coverage_ratio": len(shared) / len(all_paths),
            "nonshared_leaf_fields": len(all_paths - shared),
            "package_specific_leaf_fields": len(package_specific),
            "core_generator_modified_loc": core_modified_loc,
            "core_change_evidence": core_evidence,
            "adapter_current_code_loc": code_loc(adapter_files[package_id]),
            "package_config_loc": len(json.dumps(package, indent=2).splitlines()),
            "package_id_special_cases_in_shared_core": sum(
                path.read_text(encoding="utf-8").count(package_id) for path in core_files
            ),
            "machine_parsed_facts": acquisition["machine_parsed"],
            "machine_derived_facts": acquisition["machine_derived"],
            "manual_cross_check_facts": acquisition["manual_cross_check"],
            "manual_only_facts": acquisition["manual_only"],
            "relevant_test_functions": relevant_test_count(test_roots[package_id], test_tokens[package_id]),
            "reuse_status": status
        })
    summary = {
        "package_count": len(packages),
        "shared_semantic_leaf_fields": len(shared),
        "schema_intersection_leaf_fields": len(shared),
        "schema_union_leaf_fields": len(union),
        "schema_intersection_over_union_ratio": len(shared) / len(union),
        "package_shared_field_coverage_ratios": {
            package_id: len(shared) / len(paths)
            for package_id, paths in paths_by_package.items()
        },
        "mean_package_shared_field_coverage_ratio": statistics.mean(
            len(shared) / len(paths) for paths in paths_by_package.values()
        ),
        "minimum_package_shared_field_coverage_ratio": min(
            len(shared) / len(paths) for paths in paths_by_package.values()
        ),
        "package_id_special_cases_in_shared_core": package_id_special_cases,
        "f64_core_generator_hash_unchanged": f64_audit["conditions"]["core_generator_hash_unchanged"],
        "openblas_uses_same_core_generator": False,
        "historical_onboarding_time_available": False,
        "historical_added_loc_available_for_all_packages": False,
        "strong_reuse_claim_supported": False,
        "supported_claim": (
            "The schema vocabulary is shared and the second BLIS dtype reuses the frozen core "
            "generator. OpenBLAS RVV validates a second library/ISA package and adapter, but its "
            "current package-local generation path prevents claiming zero core onboarding work."
        ),
        "audit_mode": (
            "Current-tree structural audit plus the existing f64 before/after hash audit; not a "
            "clean-room timed onboarding replay."
        )
    }
    write_csv(PROJECT / "processed" / "e3_reuse_audit.csv", audit_rows)
    write_json(PROJECT / "processed" / "e3_summary.json", summary)
    return summary


def bootstrap_ci(values: list[float], samples: int, seed: int) -> tuple[float, float, float]:
    rng = random.Random(seed)
    draws = [statistics.mean(rng.choice(values) for _ in values) for _ in range(samples)]
    return statistics.mean(values), percentile(draws, 0.025), percentile(draws, 0.975)


def run_e4() -> dict[str, Any]:
    config = load_json(PROJECT / "data" / "experiment_config.json")
    samples = int(config["bootstrap_samples"])
    calibration_rows = read_csv(TERMINATION / "processed" / "calibration_costs.csv")
    calibration = calibration_rows[0]
    model_cost_ms = float(calibration["model_fit_wall_ms"])
    measurement_cost_ms = float(calibration["observed_calibration_measurement_wall_ms"])
    compile_cost_ms = float(calibration["observed_unique_compile_pipeline_wall_ms"])
    search_cost_ms = measurement_cost_ms + compile_cost_ms
    total_cost_ms = model_cost_ms + search_cost_ms

    best_rows = read_csv(CGO / "processed" / "f64_best_by_workload.csv")
    winning = [row for row in best_rows if float(row["relative_to_blis"]) > 1.0]
    trial_rows = read_csv(CGO / "raw" / "f64_contract_trials.csv")
    trials_by_key: dict[tuple[str, str], list[float]] = defaultdict(list)
    winning_ids = {row["workload_id"]: row["best_candidate_id"] for row in winning}
    for row in trial_rows:
        workload_id = row["workload_id"]
        if workload_id not in winning_ids:
            continue
        if row["variant"] == "B5_blis":
            trials_by_key[(workload_id, "library")].append(float(row["median_ms"]))
        elif row["candidate_id"] == winning_ids[workload_id]:
            trials_by_key[(workload_id, "optimized")].append(float(row["median_ms"]))
    rng = random.Random(int(config["seed"]) + 4)
    i7_cycle_draws = []
    for _ in range(samples):
        saving = 0.0
        for row in winning:
            workload_id = row["workload_id"]
            saving += rng.choice(trials_by_key[(workload_id, "library")])
            saving -= rng.choice(trials_by_key[(workload_id, "optimized")])
        i7_cycle_draws.append(saving)
    i7_point = sum(float(row["blis_frontend_ms"]) - float(row["best_candidate_ms"]) for row in winning)
    i7_lcb = percentile(i7_cycle_draws, 0.025)
    i7_ucb = percentile(i7_cycle_draws, 0.975)
    i7_break_even = total_cost_ms / i7_point if i7_point > 0 else None
    i7_conservative = total_cost_ms / i7_lcb if i7_lcb > 0 else None

    trace_calls = {
        row["workload_id"]: int(row["call_count"])
        for row in read_csv(APPLICATION / "processed" / "qwen_trace_workloads.csv")
    }
    i9_rows = [
        row for row in read_csv(EXTERNAL / "processed" / "i9_external_summary.csv")
        if row["workload_id"] in trace_calls
    ]
    k230_rows = [
        row for row in read_csv(EXTERNAL / "processed" / "k230_external_summary.csv")
        if row["workload_id"] in trace_calls
    ]

    def inference_savings(rows: list[dict[str, str]], generated_key: str, library_key: str, scale: float) -> list[float]:
        return [
            trace_calls[row["workload_id"]]
            * (float(row[library_key]) - float(row[generated_key]))
            * scale
            for row in rows
        ]

    i9_values = inference_savings(i9_rows, "best_ms", "blis_ms", 1.0)
    k230_values = inference_savings(k230_rows, "best_adapter_seconds", "openblas_seconds", 1000.0)
    i9_mean, i9_lcb, i9_ucb = bootstrap_ci(i9_values, samples, int(config["seed"]) + 41)
    k230_mean, k230_lcb, k230_ucb = bootstrap_ci(k230_values, samples, int(config["seed"]) + 42)
    # bootstrap_ci returns a per-shape mean; multiply by shape count for an inference total.
    i9_point = sum(i9_values)
    i9_lcb *= len(i9_values)
    i9_ucb *= len(i9_values)
    k230_point = sum(k230_values)
    k230_lcb *= len(k230_values)
    k230_ucb *= len(k230_values)

    scenarios = [
        {
            "scenario": "i7_f64_posthoc_winning_shapes",
            "device": "i7 host",
            "horizon_unit": "deployment cycle containing one call to each selected winning shape",
            "deployment_cycle_definition": (
                "one synthetic equal-frequency cycle containing exactly one invocation of each "
                f"of the {len(winning)} post-hoc selected winning shapes; it is neither one model "
                "inference nor an observed production request distribution"
            ),
            "shape_count": len(winning),
            "model_calibration_cost_ms": model_cost_ms,
            "shape_search_compile_measure_cost_ms": search_cost_ms,
            "C_c_ms": model_cost_ms,
            "C_s_total_ms": search_cost_ms,
            "C_s_measurement_component_ms": measurement_cost_ms,
            "C_s_compile_component_ms": compile_cost_ms,
            "C_s_granularity": "aggregate_sum_only_not_per_shape",
            "total_cost_ms": total_cost_ms,
            "point_saving_per_horizon_unit_ms": i7_point,
            "saving_lcb95_ms": i7_lcb,
            "saving_ucb95_ms": i7_ucb,
            "finite_break_even": i7_point > 0,
            "point_break_even_horizon": i7_break_even,
            "lcb95_break_even_horizon": i7_conservative,
            "point_estimate_finite_break_even": i7_point > 0,
            "lcb95_finite_break_even": i7_lcb > 0,
            "search_worthwhile_under_lcb95": i7_lcb > 0,
            "posthoc_selection": True,
            "posthoc_marker": "POST_HOC_DESCRIPTIVE_UPPER_BOUND",
            "zero_search_cost_upper_bound": False,
            "selection_boundary": "winning shapes selected post hoc; descriptive upper-bound scenario"
        },
        {
            "scenario": "i9_qwen_exact_shapes",
            "device": "Intel Core i9-14900",
            "horizon_unit": "one frozen Qwen trace inference",
            "deployment_cycle_definition": None,
            "shape_count": len(i9_rows),
            "model_calibration_cost_ms": None,
            "shape_search_compile_measure_cost_ms": None,
            "C_c_ms": None,
            "C_s_total_ms": None,
            "C_s_measurement_component_ms": None,
            "C_s_compile_component_ms": None,
            "C_s_granularity": "not_needed_negative_savings_zero_cost_upper_bound",
            "total_cost_ms": None,
            "point_saving_per_horizon_unit_ms": i9_point,
            "saving_lcb95_ms": i9_lcb,
            "saving_ucb95_ms": i9_ucb,
            "finite_break_even": False,
            "point_break_even_horizon": None,
            "lcb95_break_even_horizon": None,
            "point_estimate_finite_break_even": False,
            "lcb95_finite_break_even": False,
            "search_worthwhile_under_lcb95": False,
            "posthoc_selection": False,
            "posthoc_marker": "FROZEN_EXACT_TRACE",
            "zero_search_cost_upper_bound": True,
            "selection_boundary": "denominator is negative even under zero search-cost assumption; choose BLIS"
        },
        {
            "scenario": "k230_qwen_exact_shapes",
            "device": "K230 C908",
            "horizon_unit": "one frozen Qwen trace inference",
            "deployment_cycle_definition": None,
            "shape_count": len(k230_rows),
            "model_calibration_cost_ms": None,
            "shape_search_compile_measure_cost_ms": None,
            "C_c_ms": None,
            "C_s_total_ms": None,
            "C_s_measurement_component_ms": None,
            "C_s_compile_component_ms": None,
            "C_s_granularity": "not_needed_negative_savings_zero_cost_upper_bound",
            "total_cost_ms": None,
            "point_saving_per_horizon_unit_ms": k230_point,
            "saving_lcb95_ms": k230_lcb,
            "saving_ucb95_ms": k230_ucb,
            "finite_break_even": False,
            "point_break_even_horizon": None,
            "lcb95_break_even_horizon": None,
            "point_estimate_finite_break_even": False,
            "lcb95_finite_break_even": False,
            "search_worthwhile_under_lcb95": False,
            "posthoc_selection": False,
            "posthoc_marker": "FROZEN_EXACT_TRACE",
            "zero_search_cost_upper_bound": True,
            "selection_boundary": "denominator is negative even under zero search-cost assumption; choose OpenBLAS"
        }
    ]
    curves = []
    for scenario in scenarios:
        for horizon in config["economic_horizons"]:
            cost = scenario["total_cost_ms"] or 0.0
            curves.append({
                "scenario": scenario["scenario"],
                "horizon": horizon,
                "horizon_unit": scenario["horizon_unit"],
                "net_value_point_ms": horizon * scenario["point_saving_per_horizon_unit_ms"] - cost,
                "net_value_lcb95_ms": horizon * scenario["saving_lcb95_ms"] - cost,
                "net_value_ucb95_ms": horizon * scenario["saving_ucb95_ms"] - cost,
                "search_cost_assumption": "observed" if scenario["total_cost_ms"] is not None else "zero_cost_upper_bound"
            })

    summary = {
        "scenarios": scenarios,
        "legacy_calibration_service_break_even_workloads": {
            row["method"]: float(row["wall_break_even_workloads_with_compile"])
            for row in calibration_rows
        },
        "legacy_metric_boundary": (
            "The legacy value is a future tuning-service workload horizon, not a matrix invocation "
            "count and not a model inference count."
        ),
        "decision_rule": "Search is worthwhile only when LCB95(V(H)) > 0.",
        "lcb95_break_even_definition": (
            "H_LCB = (C_c + sum_j C_s,j) / LCB95(sum_j f_j (t_b,j - t_o,j)); "
            "it is finite only when the denominator is strictly positive"
        ),
        "cost_symbol_definitions": {
            "C_c": "global calibration/model-fit wall time; observed as model_fit_wall_ms",
            "C_s_j": (
                "candidate generation, compilation, measurement and tuner cost attributable to "
                "shape j; current logs support only the aggregate sum over j"
            ),
            "C_s_total": "observed calibration measurement wall time plus unique compile pipeline wall time"
        },
        "i7_observed_cost_decomposition_ms": {
            "C_c": model_cost_ms,
            "C_s_measurement": measurement_cost_ms,
            "C_s_compile": compile_cost_ms,
            "C_s_total": search_cost_ms,
            "C_c_plus_C_s_total": total_cost_ms
        },
        "C_s_reporting_boundary": (
            "The source log records aggregate measurement and unique-compile wall times, not a "
            "clean per-shape C_s,j breakdown; no retrospective per-shape allocation is claimed."
        ),
        "deployment_cycle_definition": (
            "For the i7 post-hoc scenario, one deployment cycle is a synthetic equal-frequency "
            f"portfolio unit with one call to each of the {len(winning)} selected shapes. It is "
            "not a model inference and not an observed deployment frequency distribution."
        ),
        "posthoc_policy": (
            "The i7 winning set was selected after observing performance and is reported only as "
            "a descriptive upper bound. It is not evidence for a deployable pre-selection rule."
        ),
        "horizon_types": ["tuning task", "deployment call", "model inference"],
        "conclusion": (
            "A finite positive break-even exists only in the post-hoc i7 winning-shape scenario. "
            "The exact Transformer traces have negative denominators on i9 and K230, so no amount "
            "of reuse amortizes the generated path against the complete library."
        )
    }
    write_csv(PROJECT / "processed" / "e4_break_even_summary.csv", scenarios)
    write_csv(PROJECT / "processed" / "e4_value_curves.csv", curves)
    write_json(PROJECT / "processed" / "e4_summary.json", summary)
    return summary


def render_report(summaries: dict[str, Any]) -> None:
    e1, e2, e3, e4 = (summaries[key] for key in ("E1", "E2", "E3", "E4"))
    scenarios = {row["scenario"]: row for row in e4["scenarios"]}
    i7 = scenarios["i7_f64_posthoc_winning_shapes"]
    i9 = scenarios["i9_qwen_exact_shapes"]
    k230 = scenarios["k230_qwen_exact_shapes"]
    random_comparison = e2["same_pool_random_comparison"]
    baco_unique = random_comparison["baco"]
    random_unique = random_comparison["random"]
    lines = [
        "# Contract 与调度空间补充验证结果",
        "",
        "本报告由 `scripts/run_all.py` 生成。E1-E3 为本次静态/结构验证，E2 的编译项重放既有真实二进制清单，E4 只复用已经完成的 i7、i9 和 K230 测量。",
        "",
        "## E1 契约独立负例与单字段变异",
        "",
        f"- 3 个 package 共 {e1['case_count']} 个 gold case，其中 {e1['mutation_count']} 个单字段危险变异。",
        f"- Mutation Score = {e1['mutation_score']:.3f}；false accept = {e1['false_accept_count']}；false reject = {e1['false_reject_count']}。",
        f"- path/phase/diagnostic-field accuracy = {e1['path_accuracy']:.3f}/{e1['phase_accuracy']:.3f}/{e1['diagnostic_field_accuracy']:.3f}。",
        f"- 两个隔离故障注入均由 reference GEMM 检出错误结果：{e1['faults_detected_by_reference']}/{e1['fault_injection_count']}。",
        "- 能力边界：静态 checker 不能识别声明正确但物理内容已损坏的 packed buffer。",
        "",
        "## E2 调度空间内在价值",
        "",
        f"- 完成 {e2['workload_count']} x {e2['raw_candidates_per_workload']} = {e2['static_classification_count']} 次静态分类。",
        f"- checker 单候选耗时 median/p95 = {e2['checker_single_candidate_median_us']:.3f}/{e2['checker_single_candidate_p95_us']:.3f} us。",
        "- 三层空间汇总：",
        "",
        "| 空间 | 规范化前 | 规范化后 | 平均缩减率 | callable density | IR 重复率(前->后) | 首个 callable | D90 | time-to-90% |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for space in ("G0", "G1", "C"):
        row = e2["spaces"][space]
        d90 = "未测" if row["D90"] is None else f"{row['D90']:.4f}"
        t90 = "未测" if row["time_to_90_pool_best"] is None else f"{row['time_to_90_pool_best']:.1f}"
        lines.append(
            f"| {space} | {row['mean_pre_normalization_retained_count']:.1f} | "
            f"{row['mean_retained_count']:.1f} | {row['mean_reduction_ratio']:.3f} | "
            f"{row['mean_callable_density']:.3f} | "
            f"{row['mean_pre_normalization_ir_duplicate_ratio']:.3f}->{row['mean_ir_duplicate_ratio']:.3f} | "
            f"{row['median_of_workload_median_draws_to_first_callable']:.1f} | {d90} | {t90} |"
        )
    lines.extend([
        "",
        f"- 8 x 3 x 32 = {e2['compile_replay_count']} 条抽样项均能映射到既有真实成功编译 manifest；这不是 768 次新编译。",
        f"- 已将 direct/adapt 微内核路径上不活跃的 `vectorize` 规范为 false。C 的平均候选数由 {e2['spaces']['C']['mean_pre_normalization_retained_count']:.1f} 降至 {e2['spaces']['C']['mean_retained_count']:.1f}，IR 重复率由 {e2['spaces']['C']['mean_pre_normalization_ir_duplicate_ratio']:.3f} 降至 {e2['spaces']['C']['mean_ir_duplicate_ratio']:.3f}。",
        f"- 最终规范化方法使用 8 workload x 5 seed x 25 budget 的离线 BaCO replay：D90={e2['spaces']['C']['D90']:.4f}，time-to-90%-pool-best={e2['spaces']['C']['time_to_90_pool_best']:.1f}，达到阈值比例={e2['spaces']['C']['reached_90_fraction']:.3f}。replay 只读取冻结目标值，没有重新编译或硬件测量。",
        f"- 规范化前消融结果保留为 D90={e2['spaces']['C']['pre_normalization_ablation']['D90']:.4f}、time-to-90%-pool-best={e2['spaces']['C']['pre_normalization_ablation']['time_to_90pct_pool_best']:.1f}。最终 D90 下降 {abs(e2['normalized_baco_replay']['outcome_vs_pre_normalization']['D90_delta']):.4f}，time-to-90% 改善 {abs(e2['normalized_baco_replay']['outcome_vs_pre_normalization']['time_to_90pct_delta']):.1f} 次，均按冻结协议报告。",
        f"- 规范化 replay 共 {e2['normalized_baco_replay']['run_count']} 条运行、{e2['normalized_baco_replay']['trace_count']} 次 callback，其中 {e2['normalized_baco_replay']['duplicate_callbacks']} 次重复；224 个最终池项中 {e2['normalized_baco_replay']['normalization_evidence']['selected_schedules_with_paired_canonical_ir']} 个有成对 canonical IR，{e2['normalized_baco_replay']['normalization_evidence']['selected_schedules_without_paired_ir']} 个仅有单边历史 IR，后者依赖静态活性审计。",
        f"- 同一 28 点池和 25 个唯一候选查询预算下，BaCO/random 的达到率为 {baco_unique['reached_90pct_pool_best_fraction']:.3f}/{random_unique['reached_90pct_pool_best_fraction']:.3f}，中位 T90 为 {baco_unique['median_time_to_90pct_unique_query']:.1f}/{random_unique['median_time_to_90pct_unique_query']:.1f}。BaCO 为取得 1000 个唯一查询共消费 {baco_unique['callbacks_consumed_to_unique_budget']} 次 callback，其中 {baco_unique['duplicate_callbacks_before_unique_budget']} 次重复；random 无重复。",
        f"- budget 5 的 BaCO-random 平均 best-fraction 配对差为 {random_comparison['paired_comparison']['budget_5']['mean_best_fraction_difference']:.4f}，workload-cluster 95% CI=[{random_comparison['paired_comparison']['budget_5']['workload_cluster_bootstrap_95pct_ci'][0]:.4f}, {random_comparison['paired_comparison']['budget_5']['workload_cluster_bootstrap_95pct_ci'][1]:.4f}]；当前结果不支持 BaCO 优于均匀随机。",
        "- G1 的 D90/time-to-90% 仍是规范化前历史测量；G0 没有既有性能池。",
        "",
        "## E3 Contract package 复用审计",
        "",
        f"- 三个 package 的 schema 交集/并集为 {e3['schema_intersection_leaf_fields']}/{e3['schema_union_leaf_fields']} 个 leaf path，intersection-over-union 复用率为 {e3['schema_intersection_over_union_ratio']:.3f}。",
        f"- 逐 package 共享字段覆盖率为 {', '.join(f'{key}={value:.3f}' for key, value in e3['package_shared_field_coverage_ratios'].items())}；共享核心中的 package-ID 特判数为 {e3['package_id_special_cases_in_shared_core']}。",
        f"- BLIS f64 的既有 before/after 哈希审计显示核心 generator 不变：{e3['f64_core_generator_hash_unchanged']}。",
        "- OpenBLAS RVV 已证明第二库/第二 ISA 的 Contract、adapter 和合法执行，但当前使用 package-local 生成路径。",
        f"- 因而“任意新 package 均零核心修改”的强主张为 {e3['strong_reuse_claim_supported']}；可支持的是 schema 复用和 BLIS 内第二 dtype 的核心复用。",
        "- 无可靠 onboarding 工时日志，也无三个 package 的干净历史 LOC delta，报告不作事后估算。",
        "",
        "## E4 搜索经济性",
        "",
        "| 场景 | 单位 | 单位净节省点估计 | 95% CI | 点估计 break-even | LCB95 break-even |",
        "|---|---|---:|---:|---:|---:|",
        f"| i7 f64 事后 winning shapes | deployment cycle | {i7['point_saving_per_horizon_unit_ms']:.6f} ms | [{i7['saving_lcb95_ms']:.6f}, {i7['saving_ucb95_ms']:.6f}] | {i7['point_break_even_horizon']:.1f} cycles | {i7['lcb95_break_even_horizon']:.1f} cycles |",
        f"| i9 Qwen exact shapes | inference | {i9['point_saving_per_horizon_unit_ms']:.6f} ms | [{i9['saving_lcb95_ms']:.6f}, {i9['saving_ucb95_ms']:.6f}] | 无有限值 | 无有限值 |",
        f"| K230 Qwen exact shapes | inference | {k230['point_saving_per_horizon_unit_ms']:.6f} ms | [{k230['saving_lcb95_ms']:.6f}, {k230['saving_ucb95_ms']:.6f}] | 无有限值 | 无有限值 |",
        "",
        f"- i7 成本分解：`C_c={i7['C_c_ms']:.3f} ms`，`sum C_s,j={i7['C_s_total_ms']:.3f} ms`（测量 {i7['C_s_measurement_component_ms']:.3f} ms，唯一编译 {i7['C_s_compile_component_ms']:.3f} ms）。源日志只支持聚合 `sum C_s,j`，不报告虚构的逐 shape 分摊。",
        f"- `{i7['posthoc_marker']}`：i7 winning set 在观察性能后选择，只是描述性上界。deployment cycle 定义为对这 {i7['shape_count']} 个 shape 各调用一次的等频合成单位，不是一次模型 inference，也不是实测部署频率。",
        "既有 D0/D1 的 2293.6/2339.0 workloads 是后续调优服务任务数，不是单矩阵调用数，也不是模型 inference 数。只有 `LCB95(V(H)) > 0` 时才判定搜索值得。",
        "",
        "## 结论边界",
        "",
        "E1 支持 Contract 作为可诊断的安全门；E2 在消除微内核路径不活跃的 `vectorize` 后给出有效唯一空间指标；E3 量化了 schema 复用且只部分支持 package 化复用；E4 表明调优价值依赖设备、shape 分布和完整库基线，不能从局部候选胜出泛化为普遍收益。",
        "",
        "## 结果路径",
        "",
        "- `processed/e1_mutation_results.csv`、`e1_fault_injection.csv`、`e1_summary.json`",
        "- `processed/e2_space_classification.csv`、`e2_first_callable.csv`、`e2_compile_replay.csv`、`e2_summary.json`",
        "- `processed/e2_random_search_traces.csv`、`e2_baco_random_paired.csv`、`e2_baco_random_summary.json`",
        "- `processed/e3_reuse_audit.csv`、`e3_summary.json`",
        "- `processed/e4_break_even_summary.csv`、`e4_value_curves.csv`、`e4_summary.json`"
    ])
    report = PROJECT / "reports" / "contract_space_validation_results.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_provenance() -> None:
    inputs = [
        PROJECT / "data" / "package_contracts.json",
        PROJECT / "data" / "mutation_oracle.json",
        PROJECT / "data" / "experiment_config.json",
        PROJECT / "scripts" / "fault_worker.py",
        PROJECT / "scripts" / "audit_documentation.py",
        PROJECT / "scripts" / "run_normalized_baco_replay.py",
        PROJECT / "scripts" / "run_same_pool_random_baseline.py",
        PROJECT / "scripts" / "run_all.py",
        CHAPTER6 / "data" / "experiment_config.json",
        CHAPTER6 / "data" / "workloads.json",
        CHAPTER6 / "scripts" / "run_tuning.py",
        CHAPTER6 / "tuner" / "base_pools.json",
        CHAPTER6 / "processed" / "binary_manifests.json",
        CHAPTER6 / "processed" / "measurement_aggregates.csv",
        CHAPTER6 / "processed" / "space_quality_summary.csv",
        EXPERIMENTS / "chapter3_rules" / "data" / "facts.json",
        EXPERIMENTS / "chapter3_multisource" / "scripts" / "extract_multisource.py",
        TERMINATION / "processed" / "calibration_costs.csv",
        CGO / "processed" / "f64_best_by_workload.csv",
        EXTERNAL / "processed" / "i9_external_summary.csv",
        EXTERNAL / "processed" / "k230_external_summary.csv",
        APPLICATION / "processed" / "qwen_trace_workloads.csv"
    ]
    write_json(PROJECT / "provenance" / "manifest.json", {
        "schema_version": 1,
        "inputs": {str(path.relative_to(EXPERIMENTS)): sha256_file(path) for path in inputs},
        "python": sys.version,
        "generated_outputs": sorted(
            str(path.relative_to(PROJECT)) for path in (PROJECT / "processed").glob("e[1-4]_*")
        )
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=("E1", "E2", "E3", "E4"))
    args = parser.parse_args()
    runners = {"E1": run_e1, "E2": run_e2, "E3": run_e3, "E4": run_e4}
    if args.only:
        result = runners[args.only]()
        print(json.dumps({args.only: result}, indent=2, sort_keys=True))
        return
    summaries = {name: runner() for name, runner in runners.items()}
    render_report(summaries)
    write_provenance()
    write_json(PROJECT / "processed" / "summary.json", summaries)
    print(json.dumps({
        "status": "complete",
        "experiments": list(summaries),
        "report": str(PROJECT / "reports" / "contract_space_validation_results.md")
    }, indent=2))


if __name__ == "__main__":
    main()
