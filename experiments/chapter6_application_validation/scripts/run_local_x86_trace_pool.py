#!/usr/bin/env python3
"""Measure the frozen Qwen GEMM pool on the current x86 host."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
EXTERNAL = EXPERIMENTS / "chapter6_external_validation"
sys.path.insert(0, str(EXTERNAL / "scripts"))

import run_i9_transformer_pool as pool  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def cpu_model() -> str:
    completed = subprocess.run(
        ["lscpu", "-J"], text=True, capture_output=True, check=True
    )
    document = json.loads(completed.stdout)
    fields = {
        row["field"].rstrip(":"): row["data"]
        for row in document["lscpu"]
    }
    return fields.get("Model name", platform.processor() or "unknown")


def measure_plan(
    state: dict[str, Any],
    manifests: dict[str, Any],
    baseline: dict[str, Any],
    measurement: dict[str, Any],
    output_root: Path,
    target_id: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    trials = int(measurement["process_trials_per_batch"])
    batches = int(measurement["batch_count"])
    total = sum(
        (len(item["active_pool"]) + 1) * trials * batches
        for item in state.values()
    )
    completed = 0
    for batch in range(batches):
        time.sleep(float(measurement["settle_seconds"]))
        for workload_id, item in sorted(state.items()):
            workload = item["workload"]
            operations = 2 * int(workload["m"]) * int(workload["k"]) * int(workload["n"])
            inner_iters = max(1, min(
                int(measurement["maximum_inner_iters"]),
                math.ceil(int(measurement["target_timed_flops_per_sample"]) / operations),
            ))
            live = {
                "warmups": int(measurement["warmups"]),
                "repeats": int(measurement["repeats_per_process"]),
                "inner_iters": inner_iters,
                "cpu_affinity": measurement.get("cpu_affinity"),
            }
            variants: list[tuple[str, dict[str, Any], dict[str, Any] | None]] = [
                (f"candidate:{row['candidate_id']}", manifests[row["candidate_id"]], row)
                for row in item["active_pool"]
            ]
            variants.append(("B5_blis", baseline, None))
            for batch_trial in range(trials):
                order = list(variants)
                random.Random(pool.stable_int(
                    target_id, batch, workload_id, batch_trial
                )).shuffle(order)
                for variant, manifest, candidate in order:
                    token = variant.replace(":", "_")
                    log = (
                        output_root / "reports" / "case_logs"
                        / f"batch_{batch}" / workload_id
                        / f"trial_{batch_trial}_{token}.log"
                    )
                    result = pool.cgo_common.measure_live(
                        manifest, workload, live, log, row=candidate
                    )
                    rows.append({
                        "target": target_id,
                        "dtype": "f32",
                        "batch": batch,
                        "batch_trial": batch_trial,
                        "trial": batch * trials + batch_trial,
                        "workload_id": workload_id,
                        "family": workload["family"],
                        "phase": workload["phase"],
                        "region": workload["region"],
                        "m": workload["m"],
                        "k": workload["k"],
                        "n": workload["n"],
                        "inner_iters": inner_iters,
                        "variant": variant,
                        "candidate_id": candidate["candidate_id"] if candidate else "",
                        "tile_m": candidate["tile_m"] if candidate else "",
                        "tile_n": candidate["tile_n"] if candidate else "",
                        "tile_k": candidate["tile_k"] if candidate else "",
                        "static_score": candidate["score"] if candidate else "",
                        "predicted_path": candidate["predicted_path"] if candidate else "library",
                        "observed_path": result.get("observed_path", "library"),
                        "median_ms": result["median_ms"],
                        "gflops": result["gflops"],
                        "projection_error": result["max_abs_diff"],
                        "fringe_calls": result.get("fringe_calls", 0),
                        "expected_fringe_calls": result.get("expected_fringe_calls", 0),
                        "benchmark_wall_ms": result["benchmark_wall_ms"],
                        "status": result["status"],
                        "executable_sha256": result["executable_sha256"],
                    })
                    completed += 1
                    print(
                        f"measure {completed}/{total}: batch={batch} {workload_id} "
                        f"{variant} trial={batch_trial}",
                        flush=True,
                    )
    return rows


def stability_audit(
    raw: list[dict[str, Any]],
    batch_rows: list[dict[str, Any]],
    acceptance: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[tuple[str, str], list[float]] = {}
    for row in raw:
        key = (str(row["workload_id"]), str(row["variant"]))
        groups.setdefault(key, []).append(float(row["median_ms"]))
    rows: list[dict[str, Any]] = []
    for (workload_id, variant), values in sorted(groups.items()):
        median = statistics.median(values)
        mad = statistics.median(abs(value - median) for value in values)
        robust_cv = 1.4826 * mad / median if median > 0.0 else math.inf
        passed = (
            len(values) >= int(acceptance["minimum_process_medians_per_variant"])
            and robust_cv <= float(acceptance["maximum_robust_cv"])
        )
        rows.append({
            "workload_id": workload_id,
            "variant": variant,
            "process_medians": len(values),
            "median_ms": median,
            "mad_ms": mad,
            "robust_cv": robust_cv,
            "stability_pass": passed,
        })
    ratios = [float(row["generated_relative_to_blis_geomean"]) for row in batch_rows]
    ratio_median = statistics.median(ratios)
    ratio_spread = (
        (max(ratios) - min(ratios)) / ratio_median if ratio_median > 0.0 else math.inf
    )
    variant_pass_fraction = sum(row["stability_pass"] for row in rows) / len(rows)
    summary = {
        "variant_rows": len(rows),
        "variant_pass_rows": sum(row["stability_pass"] for row in rows),
        "variant_pass_fraction": variant_pass_fraction,
        "batch_pool_to_blis_ratios": ratios,
        "batch_ratio_relative_spread": ratio_spread,
        "variant_stability_pass": variant_pass_fraction
        >= float(acceptance["minimum_variant_pass_fraction"]),
        "batch_stability_pass": ratio_spread
        <= float(acceptance["maximum_pool_to_library_batch_ratio_spread"]),
    }
    summary["stability_pass"] = (
        summary["variant_stability_pass"] and summary["batch_stability_pass"]
    )
    return rows, summary


def write_report(
    output_root: Path, target_id: str, rows: list[dict[str, Any]], overall: dict[str, Any]
) -> None:
    lines = [
        "# Local x86 Qwen-shape Contract pool results",
        "",
        f"- Target: `{target_id}`",
        f"- Status: **{overall['status']}**",
        f"- Exact trace workloads: {overall['workloads']}",
        f"- Candidate measurements: {overall['candidate_measurements']}",
        f"- Confirmatory batches: {overall['batch_count']}",
        f"- Process medians per variant: {overall['process_medians_per_variant']}",
        f"- Stability gate: **{'PASS' if overall['stability']['stability_pass'] else 'FAIL'}**",
        f"- Stable variant fraction: {overall['stability']['variant_pass_fraction']:.2%}",
        f"- Pool/BLIS batch-ratio relative spread: {overall['stability']['batch_ratio_relative_spread']:.2%}",
        (
            "- Pool oracle / complete BLIS geometric ratio: "
            f"{overall['generated_relative_to_blis_geomean']:.4f}"
        ),
        "",
        "| Workload | Shape MxKxN | Best tile | Path | Pool oracle / BLIS |",
        "|---|---:|---:|---|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['workload_id']} | {row['m']}x{row['k']}x{row['n']} | "
            f"{row['best_tile_m']}x{row['best_tile_n']}x{row['best_tile_k']} | "
            f"{row['best_predicted_path']} | {row['generated_relative_to_blis']:.4f} |"
        )
    lines.extend([
        "",
        "These are single-thread f32 GEMM measurements for the eight exact Qwen trace shapes. They are not end-to-end model latency measurements.",
        "",
    ])
    path = output_root / "reports" / "local_x86_trace_pool_results.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root", type=Path, default=PROJECT / "targets" / "i7_10750h"
    )
    parser.add_argument("--cpu", type=int)
    parser.add_argument("--force-build", action="store_true")
    args = parser.parse_args()

    config = json.loads(
        (PROJECT / "data" / "experiment_config.json").read_text(encoding="utf-8")
    )
    local = config["local_x86"]
    target_id = local["target_id"]
    cpu = int(local["cpu_affinity"] if args.cpu is None else args.cpu)
    for name, value in local["thread_environment"].items():
        os.environ[name] = str(value)
    output_root = args.output_root.resolve()
    trace_rows = pool.read_json(PROJECT / "processed" / "qwen_trace_summary.json")
    if trace_rows["status"] != "PASS":
        raise RuntimeError("Qwen trace must pass before target measurement")
    trace_ids = {
        row["workload_id"]
        for row in read_csv(PROJECT / "processed" / "qwen_trace_workloads.csv")
    }
    workloads = pool.read_json(EXTERNAL / "data" / "transformer_workloads.json")["workloads"]
    selected = [row for row in workloads if row["id"] in trace_ids]
    if {row["id"] for row in selected} != trace_ids:
        raise ValueError("frozen external workload set does not cover the Qwen trace")

    pool.configure_cgo(output_root)
    state = pool.build_plan(selected, int(local["candidate_pool_size_per_workload"]))
    plan_rows = []
    for workload_id, item in sorted(state.items()):
        for row in item["active_pool"]:
            plan_rows.append({
                "workload_id": workload_id,
                "contract_id": item["contract"]["id"],
                "candidate_id": row["candidate_id"],
                "tile_m": row["tile_m"],
                "tile_n": row["tile_n"],
                "tile_k": row["tile_k"],
                "predicted_path": row["predicted_path"],
                "score": row["score"],
            })
    pool.write_csv(output_root / "processed" / "candidate_plan.csv", plan_rows)

    pool.cgo_common.ensure_tools(build_buddy=False)
    manifests, baseline = pool.compile_plan(state, args.force_build)
    measurement = {
        "warmups": local["warmups"],
        "repeats_per_process": local["repeats_per_process"],
        "process_trials_per_batch": local["process_trials_per_batch"],
        "batch_count": local["batch_count"],
        "target_timed_flops_per_sample": local["target_timed_flops_per_sample"],
        "maximum_inner_iters": local["maximum_inner_iters"],
        "settle_seconds": local["settle_seconds"],
        "cpu_affinity": cpu,
    }
    raw = measure_plan(
        state, manifests, baseline, measurement, output_root, target_id
    )
    aggregates = pool.aggregate(raw)
    analysis_config = pool.read_json(EXTERNAL / "data" / "experiment_config.json")
    summary_rows, search_rows, overall = pool.analyze(
        state, aggregates, analysis_config
    )
    batch_rows: list[dict[str, Any]] = []
    for batch in range(int(local["batch_count"])):
        batch_raw = [row for row in raw if int(row["batch"]) == batch]
        batch_aggregates = pool.aggregate(batch_raw)
        _, _, batch_overall = pool.analyze(state, batch_aggregates, analysis_config)
        batch_rows.append({
            "batch": batch,
            "process_trials_per_variant": local["process_trials_per_batch"],
            "generated_relative_to_blis_geomean": batch_overall[
                "generated_relative_to_blis_geomean"
            ],
            "generated_wins": batch_overall["generated_wins"],
            "status": batch_overall["status"],
        })
    stability_rows, stability = stability_audit(
        raw, batch_rows, local["stability_acceptance"]
    )
    activity = pool.audit_parameter_activity(aggregates)
    active_audits = sum(
        row["activity_status"] == "active" for row in activity
    )
    eliminated_audits = sum(
        row["activity_status"] == "conditionally_eliminated" for row in activity
    )
    overall.update({
        "target": target_id,
        "cpu_model": cpu_model(),
        "trace_workloads_only": True,
        "all_expected_workloads_present": len(summary_rows) == len(trace_ids),
        "per_workload_parameter_audits": len(activity),
        "active_parameter_audits": active_audits,
        "conditionally_eliminated_parameter_audits": eliminated_audits,
        "all_parameters_audited": active_audits + eliminated_audits == len(activity),
        "confirmatory_protocol": True,
        "batch_count": local["batch_count"],
        "process_medians_per_variant": (
            int(local["batch_count"]) * int(local["process_trials_per_batch"])
        ),
        "stability": stability,
    })
    if overall["status"] == "PASS" and not stability["stability_pass"]:
        overall["status"] = "FAIL_UNSTABLE"

    pool.write_csv(output_root / "raw" / "trials.csv", raw)
    pool.write_csv(output_root / "processed" / "aggregates.csv", aggregates)
    pool.write_csv(output_root / "processed" / "summary.csv", summary_rows)
    pool.write_csv(output_root / "processed" / "search.csv", search_rows)
    pool.write_csv(output_root / "processed" / "parameter_activity.csv", activity)
    pool.write_csv(output_root / "processed" / "batch_summary.csv", batch_rows)
    pool.write_csv(output_root / "processed" / "stability_audit.csv", stability_rows)
    write_json(output_root / "processed" / "summary.json", overall)
    write_report(output_root, target_id, summary_rows, overall)

    outputs = [
        output_root / "raw" / "trials.csv",
        output_root / "processed" / "aggregates.csv",
        output_root / "processed" / "summary.csv",
        output_root / "processed" / "search.csv",
        output_root / "processed" / "parameter_activity.csv",
        output_root / "processed" / "batch_summary.csv",
        output_root / "processed" / "stability_audit.csv",
        output_root / "processed" / "summary.json",
        output_root / "reports" / "local_x86_trace_pool_results.md",
    ]
    write_json(output_root / "provenance" / "manifest.json", {
        "schema_version": 1,
        "experiment_id": "thesis.chapter6_application_validation.local_x86_trace_pool",
        "target": target_id,
        "host": {
            "cpu_model": cpu_model(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_affinity": cpu,
            "thread_environment": local["thread_environment"],
        },
        "protocol": {
            "config_sha256": sha256(PROJECT / "data" / "experiment_config.json"),
            "trace_sha256": sha256(PROJECT / "processed" / "qwen_trace_workloads.csv"),
            "external_workloads_sha256": sha256(
                EXTERNAL / "data" / "transformer_workloads.json"
            ),
            "runner_sha256": sha256(Path(__file__)),
        },
        "candidate_manifests": manifests,
        "baseline_manifest": baseline,
        "outputs": {
            str(path.relative_to(output_root)): sha256(path) for path in outputs
        },
        "claim_boundary": config["claim_boundary"],
    })
    print(json.dumps(overall, indent=2), flush=True)


if __name__ == "__main__":
    main()
