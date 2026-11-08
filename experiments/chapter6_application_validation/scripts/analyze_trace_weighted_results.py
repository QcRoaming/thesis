#!/usr/bin/env python3
"""Compute Qwen-trace-weighted target latency and tuning-cost boundaries."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
EXTERNAL = PROJECT.parent / "chapter6_external_validation"
WORKSPACE = PROJECT.parents[3]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def refresh_project_state(output_root: Path) -> None:
    if output_root != PROJECT:
        return
    subprocess.run(
        [sys.executable, str(PROJECT / "scripts" / "render_application_status.py")],
        cwd=PROJECT,
        check=True,
    )
    personal_os = Path(
        os.environ.get("PERSONAL_OS_ROOT", "/root/personal-os/PersonalOS")
    ).expanduser()
    registry = personal_os / "scripts" / "experiment_registry.py"
    if not registry.is_file():
        print(f"[registry] skipped; script not found: {registry}", flush=True)
        return
    subprocess.run(
        [
            sys.executable,
            str(registry),
            "refresh",
            "--root",
            str(personal_os),
            "--workspace-root",
            str(WORKSPACE),
        ],
        cwd=PROJECT,
        check=True,
    )


def stable_int(*parts: Any) -> int:
    return int.from_bytes(
        hashlib.sha256(":".join(map(str, parts)).encode()).digest()[:8], "big"
    )


def geometric_mean(values: list[float]) -> float:
    return math.exp(sum(math.log(max(value, 1.0e-300)) for value in values) / len(values))


def load_trace() -> list[dict[str, Any]]:
    path = PROJECT / "processed" / "qwen_trace_workloads.csv"
    if not path.is_file():
        raise FileNotFoundError(
            f"trace missing: run scripts/extract_qwen_shape_trace.py first: {path}"
        )
    rows: list[dict[str, Any]] = []
    for row in read_csv(path):
        rows.append({
            **row,
            "m": int(row["m"]), "k": int(row["k"]), "n": int(row["n"]),
            "call_count": int(row["call_count"]),
            "total_flops": int(row["total_flops"]),
        })
    return rows


def i9_measurements(root: Path) -> tuple[dict[str, Any], dict[str, float]]:
    path = root / "processed" / "i9_external_aggregates.csv"
    if not path.is_file():
        legacy_path = root / "processed" / "i9_transformer_aggregates.csv"
        if not legacy_path.is_file():
            raise FileNotFoundError(path)
        path = legacy_path
    by_workload: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"candidates": [], "library_ms": None}
    )
    for row in read_csv(path):
        workload = by_workload[row["workload_id"]]
        if row["variant"] == "B5_blis":
            workload["library_ms"] = float(row["median_ms"])
        elif row["variant"].startswith("candidate:"):
            workload["candidates"].append({
                "candidate_id": row["candidate_id"],
                "time_ms": float(row["median_ms"]),
                "score": float(row["static_score"]),
            })
    compile_costs: dict[str, float] = {}
    manifest = root / "provenance" / "i9_transformer_manifest.json"
    if manifest.is_file():
        document = json.loads(manifest.read_text(encoding="utf-8"))
        compile_costs = {
            candidate_id: float(values["pipeline_ms"])
            for candidate_id, values in document.get("candidate_manifests", {}).items()
        }
        baseline = document.get("baseline_manifest", {})
        if "pipeline_ms" in baseline:
            compile_costs["__library__"] = float(baseline["pipeline_ms"])
    return dict(by_workload), compile_costs


def local_x86_measurements(root: Path) -> tuple[dict[str, Any], dict[str, float]]:
    path = root / "processed" / "aggregates.csv"
    if not path.is_file():
        raise FileNotFoundError(path)
    by_workload: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"candidates": [], "library_ms": None}
    )
    for row in read_csv(path):
        workload = by_workload[row["workload_id"]]
        if row["variant"] == "B5_blis":
            workload["library_ms"] = float(row["median_ms"])
        elif row["variant"].startswith("candidate:"):
            workload["candidates"].append({
                "candidate_id": row["candidate_id"],
                "time_ms": float(row["median_ms"]),
                "score": float(row["static_score"]),
            })
    manifest = json.loads(
        (root / "provenance" / "manifest.json").read_text(encoding="utf-8")
    )
    compile_costs = {
        candidate_id: float(values["pipeline_ms"])
        for candidate_id, values in manifest.get("candidate_manifests", {}).items()
    }
    baseline = manifest.get("baseline_manifest", {})
    if "pipeline_ms" in baseline:
        compile_costs["__library__"] = float(baseline["pipeline_ms"])
    return dict(by_workload), compile_costs


def k230_measurements(root: Path) -> tuple[dict[str, Any], dict[str, float]]:
    path = root / "processed" / "k230_external_aggregates.csv"
    if not path.is_file():
        raise FileNotFoundError(path)
    matrix_path = EXTERNAL / "processed" / "k230_candidate_matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))["rows"]
    scores = {
        (row["workload_id"], row["candidate_id"]): float(row["score"])
        for row in matrix
    }
    by_workload: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"candidates": [], "library_ms": None}
    )
    for row in read_csv(path):
        workload = by_workload[row["workload_id"]]
        if row["variant"] == "openblas_full":
            workload["library_ms"] = float(row["median_seconds"]) * 1000.0
        elif row["variant"] == "contract_adapter":
            workload["candidates"].append({
                "candidate_id": row["candidate_id"],
                "time_ms": float(row["median_seconds"]) * 1000.0,
                "score": scores[(row["workload_id"], row["candidate_id"])],
            })
    return dict(by_workload), {}


def validate_measurements(
    target: str, measurements: dict[str, Any], trace: list[dict[str, Any]]
) -> None:
    required = {row["workload_id"] for row in trace}
    missing = required - set(measurements)
    if missing:
        raise ValueError(f"{target} is missing trace workloads: {sorted(missing)}")
    for workload_id in required:
        values = measurements[workload_id]
        if values["library_ms"] is None or not values["candidates"]:
            raise ValueError(f"{target} has incomplete measurements for {workload_id}")
        if any(row["time_ms"] <= 0.0 for row in values["candidates"]):
            raise ValueError(f"{target} has non-positive timing for {workload_id}")


def policy_orders(
    measurements: dict[str, Any], policy: str, seed: int
) -> dict[str, list[dict[str, Any]]]:
    base_policy = policy.removesuffix("_guarded")
    output: dict[str, list[dict[str, Any]]] = {}
    for workload_id, values in measurements.items():
        rows = list(values["candidates"])
        if base_policy == "static_expert":
            rows.sort(key=lambda row: (-row["score"], row["candidate_id"]))
        elif base_policy == "uniform_random":
            random.Random(stable_int(base_policy, workload_id, seed)).shuffle(rows)
        elif base_policy == "pool_oracle":
            rows.sort(key=lambda row: (row["time_ms"], row["candidate_id"]))
        else:
            raise ValueError(policy)
        output[workload_id] = rows
    return output


def evaluate_policy(
    target: str,
    trace: list[dict[str, Any]],
    measurements: dict[str, Any],
    compile_costs: dict[str, float],
    policy: str,
    seed: int,
    budget: int,
) -> list[dict[str, Any]]:
    guarded = policy.endswith("_guarded")
    if policy == "complete_library":
        orders: dict[str, list[dict[str, Any]]] = {}
    else:
        orders = policy_orders(measurements, policy, seed)
    rows: list[dict[str, Any]] = []
    for scenario_id in sorted({row["scenario_id"] for row in trace}):
        scenario_rows = [row for row in trace if row["scenario_id"] == scenario_id]
        weighted_ms = 0.0
        measurement_cost_ms = 0.0
        evaluated_candidates: set[str] = set()
        selected: list[str] = []
        for trace_row in scenario_rows:
            workload_id = trace_row["workload_id"]
            if policy == "complete_library":
                selected_ms = float(measurements[workload_id]["library_ms"])
                selected.append(f"{workload_id}:library")
            else:
                ordered = orders[workload_id]
                candidate_budget = budget - 1 if guarded else budget
                effective_budget = min(candidate_budget, len(ordered))
                if effective_budget <= 0:
                    raise ValueError(f"{policy} requires budget >= 2")
                evaluated = ordered[:effective_budget]
                best = min(evaluated, key=lambda row: (row["time_ms"], row["candidate_id"]))
                if guarded and float(measurements[workload_id]["library_ms"]) <= float(best["time_ms"]):
                    selected_ms = float(measurements[workload_id]["library_ms"])
                    selected.append(f"{workload_id}:library")
                else:
                    selected_ms = float(best["time_ms"])
                    selected.append(f"{workload_id}:{best['candidate_id']}")
                measurement_cost_ms += sum(float(row["time_ms"]) for row in evaluated)
                evaluated_candidates.update(row["candidate_id"] for row in evaluated)
                if guarded:
                    measurement_cost_ms += float(measurements[workload_id]["library_ms"])
                    evaluated_candidates.add("__library__")
            weighted_ms += selected_ms * int(trace_row["call_count"])
        compile_ms = sum(compile_costs.get(candidate_id, 0.0) for candidate_id in evaluated_candidates)
        rows.append({
            "target": target,
            "scenario_id": scenario_id,
            "policy": policy,
            "seed": seed,
            "budget": budget,
            "trace_weighted_projection_ms": weighted_ms,
            "kernel_measurement_cost_lower_bound_ms": measurement_cost_ms,
            "compile_pipeline_ms": compile_ms if compile_costs else "",
            "one_time_cost_lower_bound_ms": measurement_cost_ms + compile_ms,
            "selected_portfolio": ";".join(selected),
        })
    return rows


def analyze_target(
    target: str,
    trace: list[dict[str, Any]],
    measurements: dict[str, Any],
    compile_costs: dict[str, float],
    seeds: list[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    validate_measurements(target, measurements, trace)
    runs: list[dict[str, Any]] = []
    runs.extend(evaluate_policy(
        target, trace, measurements, compile_costs, "complete_library", 0, 0
    ))
    max_pool = max(len(values["candidates"]) for values in measurements.values())
    runs.extend(evaluate_policy(
        target, trace, measurements, compile_costs, "pool_oracle", 0, max_pool
    ))
    runs.extend(evaluate_policy(
        target, trace, measurements, compile_costs, "pool_oracle_guarded", 0,
        max_pool + 1,
    ))
    for budget in (5, 10):
        runs.extend(evaluate_policy(
            target, trace, measurements, compile_costs, "static_expert", 0, budget
        ))
        runs.extend(evaluate_policy(
            target, trace, measurements, compile_costs,
            "static_expert_guarded", 0, budget,
        ))
        for seed in seeds:
            runs.extend(evaluate_policy(
                target, trace, measurements, compile_costs, "uniform_random",
                seed, budget,
            ))
            runs.extend(evaluate_policy(
                target, trace, measurements, compile_costs,
                "uniform_random_guarded", seed, budget,
            ))

    groups: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in runs:
        groups[(row["scenario_id"], row["policy"], int(row["budget"]))].append(row)
    library = {
        row["scenario_id"]: float(row["trace_weighted_projection_ms"])
        for row in runs if row["policy"] == "complete_library"
    }
    summary: list[dict[str, Any]] = []
    for (scenario_id, policy, budget), values in sorted(groups.items()):
        latencies = [float(row["trace_weighted_projection_ms"]) for row in values]
        costs = [float(row["one_time_cost_lower_bound_ms"]) for row in values]
        latency = statistics.median(latencies)
        cost = statistics.median(costs)
        saving = library[scenario_id] - latency
        summary.append({
            "target": target,
            "scenario_id": scenario_id,
            "policy": policy,
            "budget": budget,
            "runs": len(values),
            "median_trace_weighted_projection_ms": latency,
            "min_trace_weighted_projection_ms": min(latencies),
            "max_trace_weighted_projection_ms": max(latencies),
            "relative_to_complete_library": library[scenario_id] / latency,
            "median_one_time_cost_lower_bound_ms": cost,
            "break_even_inferences_vs_complete_library": cost / saving
            if saving > 0.0 and cost > 0.0 else "",
            "compile_cost_available": bool(compile_costs),
        })
    return runs, summary


def guarded_prior_comparisons(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    targets = sorted({str(row["target"]) for row in runs})
    scenarios = sorted({str(row["scenario_id"]) for row in runs})
    for target in targets:
        for scenario_id in scenarios:
            for budget in (5, 10):
                static = [
                    float(row["trace_weighted_projection_ms"])
                    for row in runs
                    if row["target"] == target
                    and row["scenario_id"] == scenario_id
                    and row["policy"] == "static_expert_guarded"
                    and int(row["budget"]) == budget
                ]
                random_rows = [
                    float(row["trace_weighted_projection_ms"])
                    for row in runs
                    if row["target"] == target
                    and row["scenario_id"] == scenario_id
                    and row["policy"] == "uniform_random_guarded"
                    and int(row["budget"]) == budget
                ]
                if not static or not random_rows:
                    continue
                static_ms = static[0]
                random_median = statistics.median(random_rows)
                output.append({
                    "target": target,
                    "scenario_id": scenario_id,
                    "budget": budget,
                    "static_guarded_ms": static_ms,
                    "random_guarded_median_ms": random_median,
                    "static_speedup_vs_random_median": random_median / static_ms,
                    "static_wins_vs_random_seeds": sum(
                        static_ms < value for value in random_rows
                    ),
                    "random_seed_count": len(random_rows),
                    "random_guarded_min_ms": min(random_rows),
                    "random_guarded_max_ms": max(random_rows),
                    "inference_boundary": (
                        "five deterministic random seeds; no confidence interval "
                        "is claimed from four projection regions"
                    ),
                })
    return output


def write_report(
    output_root: Path,
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> None:
    lines = [
        "# Qwen trace-weighted target results",
        "",
        f"- Status: **{summary['status']}**",
        f"- Targets analyzed: {summary['targets_analyzed']}",
        f"- Trace workload rows: {summary['trace_workload_rows']}",
        "",
    ]
    if not rows:
        lines.extend([
            "Target result roots are not available yet. The Qwen shape trace and policy analysis are frozen; rerun this script after importing the i9 and K230 external measurements.",
            "",
        ])
    else:
        lines.extend([
            "| Target | Scenario | Policy | Budget | Weighted ms | / Library | Break-even inferences |",
            "|---|---|---|---:|---:|---:|---:|",
        ])
        for row in rows:
            break_even = row["break_even_inferences_vs_complete_library"]
            break_text = f"{float(break_even):.1f}" if break_even != "" else "not reached"
            lines.append(
                f"| {row['target']} | {row['scenario_id']} | {row['policy']} | "
                f"{row['budget']} | {row['median_trace_weighted_projection_ms']:.4f} | "
                f"{row['relative_to_complete_library']:.4f} | {break_text} |"
            )
        lines.extend([
            "",
            "Weighted latency covers the 24 Transformer blocks represented by the canonical trace and excludes lm_head. Tuning cost uses measured kernel time plus target-side compile-pipeline time when available; it is a lower bound because orchestration and process startup are not fully charged.",
            "",
        ])
        lines.extend([
            "## Guarded static prior versus guarded random",
            "",
            "| Target | Scenario | Budget | Static speedup / random median | Seed wins |",
            "|---|---|---:|---:|---:|",
        ])
        for row in comparisons:
            lines.append(
                f"| {row['target']} | {row['scenario_id']} | {row['budget']} | "
                f"{row['static_speedup_vs_random_median']:.4f} | "
                f"{row['static_wins_vs_random_seeds']}/{row['random_seed_count']} |"
            )
        lines.extend([
            "",
            "This comparison uses five deterministic random seeds. With only four projection regions per scenario, it is reported as a bounded application diagnostic rather than a new confidence-interval claim.",
            "",
        ])
    path = output_root / "reports" / "trace_weighted_results.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--i9-root", type=Path)
    parser.add_argument("--k230-root", type=Path)
    parser.add_argument("--local-x86-root", type=Path)
    parser.add_argument("--output-root", type=Path, default=PROJECT)
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    trace = load_trace()
    seeds = json.loads(
        (EXTERNAL / "data" / "experiment_config.json").read_text(encoding="utf-8")
    )["sparse_calibration"]["search_seeds"]
    runs: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    targets: list[str] = []
    if args.local_x86_root:
        root = args.local_x86_root.resolve()
        local_summary = json.loads(
            (root / "processed" / "summary.json").read_text(encoding="utf-8")
        )
        if local_summary.get("status") != "PASS":
            raise ValueError(
                f"local x86 measurement is not claim-eligible: "
                f"{local_summary.get('status')}"
            )
        target = str(local_summary["target"])
        measurements, compile_costs = local_x86_measurements(root)
        target_runs, target_summary = analyze_target(
            target, trace, measurements, compile_costs, seeds
        )
        runs.extend(target_runs)
        summaries.extend(target_summary)
        targets.append(target)
    if args.i9_root:
        measurements, compile_costs = i9_measurements(args.i9_root.resolve())
        target_runs, target_summary = analyze_target(
            "i9_14900", trace, measurements, compile_costs, seeds
        )
        runs.extend(target_runs)
        summaries.extend(target_summary)
        targets.append("i9_14900")
    if args.k230_root:
        measurements, compile_costs = k230_measurements(args.k230_root.resolve())
        target_runs, target_summary = analyze_target(
            "k230_c908", trace, measurements, compile_costs, seeds
        )
        runs.extend(target_runs)
        summaries.extend(target_summary)
        targets.append("k230_c908")
    status = "PASS" if targets else "AWAITING_TARGET_RESULTS"
    comparisons = guarded_prior_comparisons(runs)
    summary = {
        "schema_version": 1,
        "experiment_id": "thesis.chapter6_application_validation.trace_weighted",
        "status": status,
        "targets_analyzed": targets,
        "trace_workload_rows": len(trace),
        "policy_run_rows": len(runs),
        "policy_summary_rows": len(summaries),
        "guarded_prior_comparison_rows": len(comparisons),
        "lm_head_included": False,
        "cost_boundary": (
            "kernel measurement time plus compile-pipeline time when available; "
            "orchestration overhead is not fully charged"
        ),
    }
    write_csv(output_root / "processed" / "trace_weighted_policy_runs.csv", runs)
    write_csv(output_root / "processed" / "trace_weighted_policy_summary.csv", summaries)
    write_csv(
        output_root / "processed" / "guarded_prior_comparisons.csv", comparisons
    )
    write_json(output_root / "processed" / "trace_weighted_summary.json", summary)
    write_report(output_root, summary, summaries, comparisons)
    refresh_project_state(output_root)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
