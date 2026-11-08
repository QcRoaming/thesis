#!/usr/bin/env python3
"""Check registry coverage, evidence paths, and E1-E4 numbers in the guide."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
WORKSPACE = EXPERIMENTS.parents[2]
DEFAULT_REGISTRY = Path("/root/personal-os/PersonalOS/registries/experiments.json")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(registry_path: Path) -> dict[str, object]:
    guide_path = EXPERIMENTS / "EXPERIMENTS_DETAILED_GUIDE.md"
    guide = guide_path.read_text(encoding="utf-8")
    registry = load_json(registry_path)
    guide_ids = re.findall(r"^### 5\.\d+ `([^`]+)`", guide, flags=re.MULTILINE)
    registry_ids = [entry["id"] for entry in registry["entries"]]

    tokens = set(re.findall(r"`(jlq/thesis/[^`]+)`", guide))
    evidence_paths = sorted(
        token for token in tokens
        if " " not in token
        and "..." not in token
        and not any(mark in token for mark in ("*", "{", "}", "<", ">"))
    )
    missing_paths = [path for path in evidence_paths if not (WORKSPACE / path).exists()]

    e1 = load_json(PROJECT / "processed" / "e1_summary.json")
    e2 = load_json(PROJECT / "processed" / "e2_summary.json")
    e3 = load_json(PROJECT / "processed" / "e3_summary.json")
    e4 = load_json(PROJECT / "processed" / "e4_summary.json")
    scenarios = {row["scenario"]: row for row in e4["scenarios"]}
    replay = e2["normalized_baco_replay"]
    final_replay = replay["normalized_final_method"]
    old_replay = replay["pre_normalization_ablation"]
    random_comparison = e2["same_pool_random_comparison"]
    baco_unique = random_comparison["baco"]
    random_unique = random_comparison["random"]
    expected_fragments = [
        f"{e1['mutation_count']}/{e1['mutation_count']}",
        f"{e2['static_classification_count']:,}",
        f"{e2['spaces']['C']['mean_pre_normalization_retained_count']:.1f}",
        f"{e2['spaces']['C']['mean_retained_count']:.1f}",
        f"最终 D90 为 {final_replay['D90']:.4f}",
        f"time-to-90%-pool-best 中位数为 {final_replay['time_to_90pct_pool_best']:.1f} 次",
        f"D90={old_replay['D90']:.4f}",
        f"time-to-90%-pool-best={old_replay['time_to_90pct_pool_best']:.1f}",
        f"共 {replay['run_count']} 条 run 和 {replay['trace_count']} 次 callback",
        (
            "BaCO/random 的达到率为 "
            f"{baco_unique['reached_90pct_pool_best_fraction']:.3f}/"
            f"{random_unique['reached_90pct_pool_best_fraction']:.3f}"
        ),
        (
            "中位 T90 为 "
            f"{baco_unique['median_time_to_90pct_unique_query']:.1f}/"
            f"{random_unique['median_time_to_90pct_unique_query']:.1f}"
        ),
        (
            f"共消费 {baco_unique['callbacks_consumed_to_unique_budget']} 次 callback，"
            f"其中 {baco_unique['duplicate_callbacks_before_unique_budget']} 次重复"
        ),
        (
            f"交集/并集为 {e3['schema_intersection_leaf_fields']}/"
            f"{e3['schema_union_leaf_fields']}"
        ),
        f"{scenarios['i7_f64_posthoc_winning_shapes']['point_break_even_horizon']:,.0f} cycles",
        f"{scenarios['i7_f64_posthoc_winning_shapes']['lcb95_break_even_horizon']:,.0f} cycles",
        f"C_c={scenarios['i7_f64_posthoc_winning_shapes']['C_c_ms']:.3f} ms",
        scenarios['i7_f64_posthoc_winning_shapes']['posthoc_marker'],
        f"{scenarios['i9_qwen_exact_shapes']['point_saving_per_horizon_unit_ms']:.2f} ms",
        f"{scenarios['k230_qwen_exact_shapes']['point_saving_per_horizon_unit_ms']:.2f} ms"
    ]
    missing_fragments = [fragment for fragment in expected_fragments if fragment not in guide]
    failures = {
        "registry_ids_missing_from_guide": sorted(set(registry_ids) - set(guide_ids)),
        "guide_ids_missing_from_registry": sorted(set(guide_ids) - set(registry_ids)),
        "duplicate_guide_ids": sorted(key for key in set(guide_ids) if guide_ids.count(key) > 1),
        "missing_evidence_paths": missing_paths,
        "missing_metric_fragments": missing_fragments
    }
    passed = all(not values for values in failures.values())
    return {
        "status": "PASS" if passed else "FAIL",
        "guide": str(guide_path),
        "registry": str(registry_path),
        "registry_id_count": len(registry_ids),
        "guide_id_count": len(guide_ids),
        "checked_workspace_evidence_paths": len(evidence_paths),
        "checked_metric_fragments": len(expected_fragments),
        "failures": failures
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args()
    result = audit(args.registry.resolve())
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
