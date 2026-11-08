#!/usr/bin/env python3
"""Core algorithms for the Chapter 4 kernel-aware schedule-space prototype."""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


PROJECT_DIR = Path(__file__).resolve().parent.parent
THESIS_DIR = PROJECT_DIR.parent.parent
CHAPTER3_DIR = PROJECT_DIR.parent / "chapter3_rules"

PATH_ORDER = {"direct": 0, "adapt": 1, "fallback": 2, "reject": 3}


@dataclass(frozen=True)
class Candidate:
    tile_m: int
    tile_n: int
    tile_k: int
    pack_mode: str
    vectorize: bool

    @property
    def id(self) -> str:
        return (
            f"m{self.tile_m}_n{self.tile_n}_k{self.tile_k}_"
            f"p{self.pack_mode}_v{int(self.vectorize)}"
        )


@dataclass
class Decision:
    path: str
    reason_codes: list[str]
    actions: list[str]
    checks: dict[str, str]
    score: float = 0.0
    is_core: bool = False


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_inputs(project: Path = PROJECT_DIR) -> dict[str, Any]:
    contract_path = CHAPTER3_DIR / "data" / "microkernel_contracts.yaml"
    rules_path = CHAPTER3_DIR / "data" / "expert_rules.yaml"
    return {
        "tasks": load_json(project / "data" / "task_contexts.json")["tasks"],
        "space_config": load_json(project / "data" / "space_configs.json"),
        "reason_codes": load_json(project / "data" / "reason_codes.json"),
        "contracts": load_yaml(contract_path)["contracts"],
        "rules": load_yaml(rules_path)["rules"],
        "source_files": {
            "contracts": {
                "path": str(contract_path),
                "sha256": file_sha256(contract_path),
            },
            "rules": {
                "path": str(rules_path),
                "sha256": file_sha256(rules_path),
            },
        },
    }


def raw_candidates(raw_domain: dict[str, list[Any]]) -> list[Candidate]:
    keys = ("tile_m", "tile_n", "tile_k", "pack_mode", "vectorize")
    return [Candidate(*values) for values in itertools.product(*(raw_domain[key] for key in keys))]


def select_contract(task: dict[str, Any], contracts: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Select a Contract by compatibility, directness, and adaptation cost."""
    log: list[dict[str, Any]] = []
    target = task["target"]
    features = set(target["features"])
    for contract in contracts:
        required = set(contract["target"]["required_features"])
        failures = []
        if contract["operation"] != task["operation"]:
            failures.append("operation")
        if contract["dtype"] != task["dtype"]:
            failures.append("dtype")
        if contract["target"]["machine"] != target["machine"]:
            failures.append("machine")
        if not required.issubset(features):
            failures.append("features")
        architecture_match = contract["target"]["architecture"] == target["architecture"]
        directness = 100 - 30 * len(failures) + (15 if architecture_match else 0)
        adaptation_cost = 0
        shape = task["shape"]
        if shape["m"] % contract["mr"] or shape["n"] % contract["nr"]:
            adaptation_cost += 2
        if shape["k"] % int(contract["k_constraint"].get("main_loop_step", 1)):
            adaptation_cost += 1
        score = directness - 5 * adaptation_cost
        log.append(
            {
                "task_id": task["id"],
                "contract_id": contract["id"],
                "eligible": not failures,
                "architecture_match": architecture_match,
                "adaptation_cost": adaptation_cost,
                "selection_score": score,
                "failure_dimensions": failures,
            }
        )
    eligible = [row for row in log if row["eligible"]]
    if not eligible:
        return None, log
    selected_row = max(eligible, key=lambda row: (row["selection_score"], row["contract_id"]))
    selected_row["selected"] = True
    selected = next(contract for contract in contracts if contract["id"] == selected_row["contract_id"])
    for row in log:
        row.setdefault("selected", False)
    return selected, log


def conditional_parameters(candidate: Candidate, task: dict[str, Any], contract: dict[str, Any] | None) -> dict[str, Any]:
    """Algorithm 4-2: instantiate only parameters enabled by current choices."""
    result = asdict(candidate)
    result["pack_a"] = candidate.pack_mode == "ab"
    result["pack_b"] = candidate.pack_mode == "ab"
    if candidate.pack_mode == "ab":
        packing = contract.get("packing", {}) if contract is not None else {}
        result["pack_layout"] = packing.get("layout", "blis_panel")
        result["call_convention"] = (
            contract.get("call_convention", "BLIS GEMM_UKR ABI")
            if contract is not None
            else "BLIS GEMM_UKR ABI"
        )
    else:
        result["call_convention"] = "generic_mlir_memref"
    if contract is not None:
        shape = task["shape"]
        step = int(contract["k_constraint"].get("main_loop_step", 1))
        needs_mn_tail = bool(shape["m"] % contract["mr"] or shape["n"] % contract["nr"])
        needs_k_tail = bool(shape["k"] % step)
        if needs_mn_tail:
            result["mn_tail_strategy"] = "finite_fringe_adapter"
        if needs_k_tail:
            result["k_remainder_strategy"] = "scalar_cleanup_adapter"
        if candidate.vectorize:
            result["vector_lanes"] = contract["vectorization"]["lanes"]
    return result


def _fallback_or_reject(task: dict[str, Any]) -> tuple[str, str]:
    if task.get("fallback_available", False):
        return "fallback", "generic_mlir_tiled_loop"
    return "reject", "no_executable_action"


def check_candidate(candidate: Candidate, task: dict[str, Any], contract: dict[str, Any] | None) -> Decision:
    """Compatibility Checker with explicit dimensions, reasons, and actions."""
    checks: dict[str, str] = {}
    reasons: list[str] = []
    actions: list[str] = []
    shape = task["shape"]

    checks["payload"] = "pass" if task["operation"] == "linalg.matmul" else "fail"
    if checks["payload"] == "fail":
        return Decision("reject", ["UNSUPPORTED_OPERATION"], ["discard_candidate"], checks)

    positive = candidate.tile_m > 0 and candidate.tile_n > 0 and candidate.tile_k > 0
    checks["positive_tiles"] = "pass" if positive else "fail"
    if not positive:
        return Decision("reject", ["NON_POSITIVE_TILE"], ["discard_candidate"], checks)

    within_extent = (
        candidate.tile_m <= shape["m"]
        and candidate.tile_n <= shape["n"]
        and candidate.tile_k <= shape["k"]
    )
    checks["static_extent"] = "pass" if within_extent else "fail"
    checks["transform_precondition"] = "pass" if within_extent else "fail"
    if not within_extent:
        return Decision(
            "reject",
            ["TILE_EXCEEDS_EXTENT", "TRANSFORM_PRECONDITION_FAILED"],
            ["discard_candidate"],
            checks,
        )

    if contract is None:
        checks["contract_selection"] = "fail"
        path, action = _fallback_or_reject(task)
        reason = "NO_MATCHING_CONTRACT" if path == "fallback" else "NO_EXECUTABLE_FALLBACK"
        return Decision(path, [reason], [action], checks)

    checks["contract_selection"] = "pass"
    checks["dtype"] = "pass" if task["dtype"] == contract["dtype"] else "fail"
    required_features = set(contract["target"]["required_features"])
    checks["isa"] = "pass" if required_features.issubset(set(task["target"]["features"])) else "fail"
    checks["mr_nr"] = (
        "pass"
        if candidate.tile_m % int(contract["mr"]) == 0 and candidate.tile_n % int(contract["nr"]) == 0
        else "fail"
    )
    step = int(contract["k_constraint"].get("main_loop_step", 1))
    checks["k_constraint"] = "pass" if candidate.tile_k % step == 0 else "adaptable"
    lanes = int(contract["vectorization"]["lanes"])
    checks["vectorization"] = (
        "pass" if not candidate.vectorize or candidate.tile_n % lanes == 0 else "fail"
    )
    pack_required = bool(contract["packing"]["required_for_direct"])
    packed = candidate.pack_mode == "ab"
    checks["packing"] = "pass" if packed or not pack_required else "fail"
    checks["pack_layout"] = "pass" if packed else ("not_applicable" if not pack_required else "fail")
    row_major_output = task["layout"]["c"] == "row_major"
    checks["output_layout"] = "pass" if row_major_output else "fail"
    unit_inner_strides = all(int(value) == 1 for value in task["stride"].values())
    checks["stride"] = "pass" if unit_inner_strides else "fail"
    required_alignment = [
        contract["alignment"].get("a_bytes"),
        contract["alignment"].get("b_bytes"),
        contract["alignment"].get("c_bytes"),
    ]
    checks["alignment"] = "pass" if not any(required_alignment) else "unproven"
    checks["call_convention"] = "pass" if packed else "fail"

    hard_failures = {
        "dtype": "DTYPE_MISMATCH",
        "isa": "ISA_FEATURE_MISSING",
        "mr_nr": "MR_NR_MISMATCH",
        "vectorization": "VECTOR_LANE_MISMATCH",
        "packing": "PACKING_REQUIRED",
        "pack_layout": "PACK_LAYOUT_MISMATCH",
        "output_layout": "OUTPUT_LAYOUT_MISMATCH",
        "stride": "STRIDE_MISMATCH",
        "alignment": "ALIGNMENT_UNAVAILABLE",
        "call_convention": "CALL_CONVENTION_MISMATCH",
    }
    for dimension, reason in hard_failures.items():
        if checks[dimension] in {"fail", "unproven"}:
            reasons.append(reason)

    if reasons:
        path, action = _fallback_or_reject(task)
        if path == "reject":
            reasons.append("NO_EXECUTABLE_FALLBACK")
        return Decision(path, list(dict.fromkeys(reasons)), [action], checks)

    adapters = task["available_adapters"]
    shape_mn_tail = bool(shape["m"] % int(contract["mr"]) or shape["n"] % int(contract["nr"]))
    shape_k_tail = bool(shape["k"] % step)
    if checks["k_constraint"] == "adaptable" or shape_k_tail:
        checks["k_tail"] = "adaptable" if adapters.get("k_remainder") else "fail"
        if adapters.get("k_remainder") and contract["k_constraint"].get("remainder_supported", False):
            reasons.append("K_REMAINDER_ADAPTER")
            actions.append("insert_k_remainder_cleanup")
        else:
            path, action = _fallback_or_reject(task)
            return Decision(path, ["K_REMAINDER_ADAPTER"], [action], checks)
    else:
        checks["k_tail"] = "pass"

    if shape_mn_tail:
        checks["mn_tail"] = "adaptable" if adapters.get("mn_tail") else "fail"
        if adapters.get("mn_tail"):
            reasons.append("MN_TAIL_ADAPTER")
            actions.append("insert_finite_mn_fringe")
        else:
            path, action = _fallback_or_reject(task)
            return Decision(path, ["MN_TAIL_ADAPTER"], [action], checks)
    else:
        checks["mn_tail"] = "pass"

    if reasons:
        actions.insert(0, "insert_ab_panel_packing")
        return Decision("adapt", reasons, list(dict.fromkeys(actions)), checks)
    return Decision(
        "direct",
        ["DIRECT_CONTRACT_MATCH"],
        ["insert_ab_panel_packing", "invoke_contract_kernel"],
        checks,
    )


def score_candidate(candidate: Candidate, task: dict[str, Any], contract: dict[str, Any] | None, decision: Decision) -> float:
    """Score only prioritizes legal candidates; it never changes correctness."""
    if decision.path == "reject":
        return -math.inf
    score = {"direct": 60.0, "adapt": 52.0, "fallback": 10.0}[decision.path]
    if contract is None:
        return score
    shape = task["shape"]
    bounds = {
        "tile_m": min(shape["m"], int(contract["cache_blocking"]["mc"])),
        "tile_n": min(shape["n"], int(contract["cache_blocking"]["nc"])),
        "tile_k": min(shape["k"], int(contract["cache_blocking"]["kc"])),
    }
    for key, value in (("tile_m", candidate.tile_m), ("tile_n", candidate.tile_n), ("tile_k", candidate.tile_k)):
        bound = bounds[key]
        if bound % value == 0:
            score += 6.0
        score += 4.0 * min(value, bound) / max(value, bound)
    if candidate.pack_mode == "ab":
        score += 6.0
    if candidate.vectorize:
        score += 5.0
    if candidate.tile_m == bounds["tile_m"]:
        score += 3.0
    if candidate.tile_k == bounds["tile_k"]:
        score += 3.0
    return round(score, 6)


def is_expert_core(candidate: Candidate, task: dict[str, Any], contract: dict[str, Any] | None, decision: Decision) -> bool:
    if contract is None or decision.path not in {"direct", "adapt"}:
        return False
    shape = task["shape"]
    bounds = (
        min(shape["m"], int(contract["cache_blocking"]["mc"])),
        min(shape["n"], int(contract["cache_blocking"]["nc"])),
        min(shape["k"], int(contract["cache_blocking"]["kc"])),
    )
    values = (candidate.tile_m, candidate.tile_n, candidate.tile_k)
    divisor_hits = sum(bound % value == 0 for bound, value in zip(bounds, values))
    cache_friendly = divisor_hits >= (2 if decision.path == "direct" else 1)
    score_threshold = 85.0 if decision.path == "direct" else 75.0
    return (
        candidate.pack_mode == "ab"
        and candidate.vectorize
        and cache_friendly
        and decision.score >= score_threshold
    )


def evaluate_candidates(candidates: Iterable[Candidate], task: dict[str, Any], contract: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = []
    for candidate in candidates:
        decision = check_candidate(candidate, task, contract)
        decision.score = score_candidate(candidate, task, contract, decision)
        decision.is_core = is_expert_core(candidate, task, contract, decision)
        params = conditional_parameters(candidate, task, contract)
        rows.append(
            {
                "task_id": task["id"],
                "candidate_id": candidate.id,
                **asdict(candidate),
                "conditional_parameters": params,
                "contract_id": contract["id"] if contract else None,
                "predicted_path": decision.path,
                "reason_codes": decision.reason_codes,
                "actions": decision.actions,
                "checks": decision.checks,
                "score": decision.score,
                "is_core": decision.is_core,
            }
        )
    return rows


def select_shell(rows: list[dict[str, Any]], ratio: float, seed: int, task_id: str) -> list[dict[str, Any]]:
    core = [row for row in rows if row["is_core"]]
    pool = [row for row in rows if row["predicted_path"] != "reject" and not row["is_core"]]
    if not core or not pool or ratio <= 0:
        return []
    count = min(len(pool), math.ceil(len(core) * ratio / (1.0 - ratio)))
    strata: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pool:
        reason = row["reason_codes"][0] if row["reason_codes"] else "NONE"
        strata[f"{row['predicted_path']}:{reason}"].append(row)
    rng = random.Random(f"{seed}:{task_id}:shell")
    for values in strata.values():
        values.sort(key=lambda row: row["candidate_id"])
        rng.shuffle(values)
    selected: list[dict[str, Any]] = []
    keys = sorted(strata)
    while len(selected) < count and keys:
        next_keys = []
        for key in keys:
            if strata[key] and len(selected) < count:
                selected.append(strata[key].pop())
            if strata[key]:
                next_keys.append(key)
        keys = next_keys
    return selected


def rank_and_select_initial(rows: list[dict[str, Any]], size: int) -> list[dict[str, Any]]:
    """Algorithm 4-3: deterministic score ranking with parameter diversity."""
    ranked = sorted(
        rows,
        key=lambda row: (
            -float(row["score"]),
            PATH_ORDER[row["predicted_path"]],
            row["candidate_id"],
        ),
    )
    selected: list[dict[str, Any]] = []
    used_tiles: set[tuple[int, int, int]] = set()
    for row in ranked:
        tile = (row["tile_m"], row["tile_n"], row["tile_k"])
        if tile not in used_tiles:
            selected.append(row)
            used_tiles.add(tile)
        if len(selected) == size:
            return selected
    for row in ranked:
        if row not in selected:
            selected.append(row)
        if len(selected) == size:
            break
    return selected


def generate_spaces_for_task(
    task: dict[str, Any],
    candidates: list[Candidate],
    contracts: list[dict[str, Any]],
    config: dict[str, Any],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Algorithm 4-1: generate legal, contract, core, and core+shell spaces."""
    contract, selection_log = select_contract(task, contracts)
    rows = evaluate_candidates(candidates, task, contract)
    executable = [row for row in rows if row["predicted_path"] != "reject"]
    contract_only = [row for row in executable if row["predicted_path"] in {"direct", "adapt"}]
    core = [row for row in contract_only if row["is_core"]]
    shell_ratio = next(item["exploration_ratio"] for item in config["configs"] if item["id"] == "expert_shell")
    shell = select_shell(rows, float(shell_ratio), int(config["seed"]), task["id"])
    shell_ids = {row["candidate_id"] for row in shell}
    spaces = {
        "generic": executable,
        "contract_only": contract_only,
        "expert_core": core,
        "expert_shell": core + shell,
    }
    for space_id, members in spaces.items():
        initial_size = next(item["initial_design_size"] for item in config["configs"] if item["id"] == space_id)
        initial_ids = {row["candidate_id"] for row in rank_and_select_initial(members, min(initial_size, len(members)))}
        for row in members:
            row.setdefault("space_memberships", []).append(space_id)
            if row["candidate_id"] in initial_ids:
                row.setdefault("initial_design_memberships", []).append(space_id)
            if row["candidate_id"] in shell_ids:
                row["is_shell"] = True
    return spaces, rows, selection_log


def provenance_record(row: dict[str, Any], task: dict[str, Any], contract: dict[str, Any] | None, rules: list[dict[str, Any]], source_files: dict[str, Any]) -> dict[str, Any]:
    applied_rule_ids = []
    for rule in rules:
        category = rule["category"]
        if category == "register_blocking" and contract:
            applied_rule_ids.append(rule["rule_id"])
        elif category == "cache_blocking" and contract:
            applied_rule_ids.append(rule["rule_id"])
        elif category == "packing" and row["pack_mode"] == "ab":
            applied_rule_ids.append(rule["rule_id"])
        elif category == "vectorization" and row["vectorize"]:
            applied_rule_ids.append(rule["rule_id"])
        elif category == "tail_and_fallback" and row["predicted_path"] != "direct":
            applied_rule_ids.append(rule["rule_id"])
    fact_ids = sorted(
        {
            fact_id
            for rule in rules
            if rule["rule_id"] in applied_rule_ids
            for fact_id in rule.get("source_fact_ids", [])
            if contract is None or f".{contract['dtype']}." in f".{fact_id}."
        }
    )
    return {
        "task_id": task["id"],
        "candidate_id": row["candidate_id"],
        "contract_id": contract["id"] if contract else None,
        "fact_ids": fact_ids,
        "rule_ids": applied_rule_ids,
        "reason_codes": row["reason_codes"],
        "predicted_path": row["predicted_path"],
        "conditional_parameters": row["conditional_parameters"],
        "source_files": source_files,
    }


def flatten_row(row: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key, value in row.items():
        result[key] = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value
    return result


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    flattened = [flatten_row(row) for row in rows]
    fields = list(dict.fromkeys(key for row in flattened for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(flattened)


def summarize_task(task: dict[str, Any], rows: list[dict[str, Any]], spaces: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    path_counts = Counter(row["predicted_path"] for row in rows)
    core = len(spaces["expert_core"])
    shell = sum(bool(row.get("is_shell")) for row in spaces["expert_shell"])
    return {
        "task_id": task["id"],
        "role": task["role"],
        "dtype": task["dtype"],
        "m": task["shape"]["m"],
        "k": task["shape"]["k"],
        "n": task["shape"]["n"],
        "raw_count": len(rows),
        "legal_count": len(rows) - path_counts["reject"],
        "direct_count": path_counts["direct"],
        "adapt_count": path_counts["adapt"],
        "fallback_count": path_counts["fallback"],
        "reject_count": path_counts["reject"],
        "generic_count": len(spaces["generic"]),
        "contract_only_count": len(spaces["contract_only"]),
        "expert_core_count": core,
        "shell_count": shell,
        "expert_shell_count": len(spaces["expert_shell"]),
        "shell_ratio_observed": shell / max(1, core + shell),
        "generic_reduction_ratio": 1.0 - len(spaces["generic"]) / len(rows),
        "contract_reduction_ratio": 1.0 - len(spaces["contract_only"]) / len(rows),
        "core_reduction_ratio": 1.0 - core / len(rows),
        "expert_shell_reduction_ratio": 1.0 - len(spaces["expert_shell"]) / len(rows),
    }
