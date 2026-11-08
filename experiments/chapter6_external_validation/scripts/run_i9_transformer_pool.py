#!/usr/bin/env python3
"""Compile and measure the f32 BLIS Contract pool on frozen Transformer shapes."""

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
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
REPO = EXPERIMENTS.parents[2]
CGO_SCRIPTS = EXPERIMENTS / "cgo_extension" / "scripts"
if str(CGO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(CGO_SCRIPTS))

import cgo_common  # noqa: E402


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_int(*parts: Any) -> int:
    return int.from_bytes(
        hashlib.sha256(":".join(map(str, parts)).encode()).digest()[:8], "big"
    )


def geometric_mean(values: Iterable[float]) -> float:
    clean = [max(float(value), 1.0e-300) for value in values]
    return math.exp(sum(math.log(value) for value in clean) / len(clean))


def canonical_pool(rows: list[dict[str, Any]], size: int) -> list[dict[str, Any]]:
    aliases: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        aliases[(int(row["tile_m"]), int(row["tile_n"]), int(row["tile_k"]))].append(row)
    representatives: list[dict[str, Any]] = []
    for values in aliases.values():
        values.sort(key=lambda row: (bool(row["vectorize"]), row["candidate_id"]))
        representatives.append(values[0])
    representatives.sort(key=lambda row: (
        -float(row["score"]),
        0 if row["predicted_path"] == "direct" else 1,
        row["candidate_id"],
    ))
    if len(representatives) < size:
        raise ValueError(f"only {len(representatives)} active schedules, need {size}")
    selected: list[dict[str, Any]] = []
    used_m: set[int] = set()
    used_n: set[int] = set()
    used_k: set[int] = set()
    while len(selected) < size:
        remaining = [row for row in representatives if row not in selected]
        choice = max(
            remaining,
            key=lambda row: (
                int(row["tile_m"] not in used_m)
                + int(row["tile_n"] not in used_n)
                + int(row["tile_k"] not in used_k),
                float(row["score"]),
                row["candidate_id"],
            ),
        )
        selected.append(choice)
        used_m.add(int(choice["tile_m"]))
        used_n.add(int(choice["tile_n"]))
        used_k.add(int(choice["tile_k"]))
    return selected


def configure_cgo(output_root: Path) -> None:
    cgo_common.BUILD = output_root / "build" / "i9_transformer"
    cgo_common.REPORTS = output_root / "reports"
    cgo_common.DRIVER = PROJECT / "runtime" / "projection_candidate_bench.cpp"
    cgo_common.BLIS_DRIVER = PROJECT / "runtime" / "projection_blis_bench.cpp"


def build_plan(workloads: list[dict[str, Any]], pool_size: int) -> dict[str, Any]:
    state = cgo_common.build_contract_state("f32", workloads, pool_size=pool_size)
    for item in state.values():
        item["active_pool"] = canonical_pool(item["contract_rows"], pool_size)
    return state


def compile_plan(state: dict[str, Any], force: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for item in state.values():
        for row in item["active_pool"]:
            rows.setdefault(row["candidate_id"], row)
    manifests: dict[str, Any] = {}
    for number, (candidate_id, row) in enumerate(sorted(rows.items()), start=1):
        print(f"compile {number}/{len(rows)}: {candidate_id}", flush=True)
        manifests[candidate_id] = cgo_common.compile_candidate(row, "f32", force=force)
    baseline = cgo_common.compile_blis_frontend("f32", force=force)
    return manifests, baseline


def measure_plan(
    state: dict[str, Any],
    manifests: dict[str, Any],
    baseline: dict[str, Any],
    measurement: dict[str, Any],
    output_root: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    trials = int(measurement["process_trials"])
    live = {
        "warmups": int(measurement["warmups"]),
        "repeats": int(measurement["repeats_per_process"]),
        "inner_iters": 1,
        "cpu_affinity": measurement.get("cpu_affinity"),
    }
    total = sum((len(item["active_pool"]) + 1) * trials for item in state.values())
    completed = 0
    for workload_id, item in sorted(state.items()):
        workload = item["workload"]
        variants: list[tuple[str, dict[str, Any], dict[str, Any] | None]] = [
            (f"candidate:{row['candidate_id']}", manifests[row["candidate_id"]], row)
            for row in item["active_pool"]
        ]
        variants.append(("B5_blis", baseline, None))
        for trial in range(trials):
            order = list(variants)
            random.Random(stable_int("i9", workload_id, trial)).shuffle(order)
            for variant, manifest, candidate in order:
                token = variant.replace(":", "_")
                log = output_root / "reports" / "i9_case_logs" / workload_id / f"trial_{trial}_{token}.log"
                result = cgo_common.measure_live(
                    manifest, workload, live, log, row=candidate
                )
                rows.append({
                    "target": "i9_14900_linux",
                    "dtype": "f32",
                    "workload_id": workload_id,
                    "family": workload["family"],
                    "phase": workload["phase"],
                    "region": workload["region"],
                    "m": workload["m"],
                    "k": workload["k"],
                    "n": workload["n"],
                    "trial": trial,
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
                print(f"measure {completed}/{total}: {workload_id} {variant} trial={trial}", flush=True)
    return rows


def aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["workload_id"], row["variant"])].append(row)
    output: list[dict[str, Any]] = []
    for _, values in sorted(groups.items()):
        first = values[0]
        trial_times = [float(row["median_ms"]) for row in values]
        trial_mean = statistics.fmean(trial_times)
        trial_cv = (
            statistics.stdev(trial_times) / trial_mean
            if len(trial_times) > 1 and trial_mean > 0.0
            else 0.0
        )
        output.append({
            **{key: first[key] for key in (
                "target", "dtype", "workload_id", "family", "phase", "region",
                "m", "k", "n", "variant", "candidate_id", "tile_m", "tile_n",
                "tile_k", "static_score", "predicted_path", "observed_path",
            )},
            "trial_count": len(values),
            "all_pass": all(row["status"] == "PASS" for row in values),
            "median_ms": statistics.median(trial_times),
            "median_gflops": statistics.median(float(row["gflops"]) for row in values),
            "max_projection_error": max(float(row["projection_error"]) for row in values),
            "trial_cv": trial_cv,
        })
    return output


def analyze(
    state: dict[str, Any], aggregates: list[dict[str, Any]], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    by_workload: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in aggregates:
        by_workload[row["workload_id"]].append(row)
    summary_rows: list[dict[str, Any]] = []
    search_rows: list[dict[str, Any]] = []
    checkpoints = config["transformer_pool"]["search_checkpoints"]
    search_seeds = config["sparse_calibration"]["search_seeds"]
    for workload_id, values in sorted(by_workload.items()):
        candidates = [row for row in values if row["variant"].startswith("candidate:")]
        baseline = next(row for row in values if row["variant"] == "B5_blis")
        best = min(candidates, key=lambda row: (float(row["median_ms"]), row["candidate_id"]))
        oracle = float(best["median_ms"])
        summary_rows.append({
            "workload_id": workload_id,
            "m": best["m"], "k": best["k"], "n": best["n"],
            "pool_size": len(candidates),
            "best_candidate_id": best["candidate_id"],
            "best_tile_m": best["tile_m"],
            "best_tile_n": best["tile_n"],
            "best_tile_k": best["tile_k"],
            "best_predicted_path": best["predicted_path"],
            "best_ms": oracle,
            "blis_ms": baseline["median_ms"],
            "generated_relative_to_blis": float(baseline["median_ms"]) / oracle,
            "all_candidates_pass": all(bool(row["all_pass"]) for row in candidates),
        })
        orders: list[tuple[str, int, list[dict[str, Any]]]] = []
        orders.append((
            "static_expert_order", 0,
            sorted(candidates, key=lambda row: (-float(row["static_score"]), row["candidate_id"])),
        ))
        for seed in search_seeds:
            shuffled = list(candidates)
            random.Random(stable_int("random", workload_id, seed)).shuffle(shuffled)
            orders.append(("uniform_random", int(seed), shuffled))
        for policy, seed, ordered in orders:
            best_so_far = math.inf
            for iteration, row in enumerate(ordered, start=1):
                best_so_far = min(best_so_far, float(row["median_ms"]))
                if iteration in checkpoints:
                    search_rows.append({
                        "workload_id": workload_id,
                        "policy": policy,
                        "seed": seed,
                        "budget": iteration,
                        "best_ms": best_so_far,
                        "pool_oracle_ms": oracle,
                        "oracle_fraction": oracle / best_so_far,
                    })
    ratios = [row["generated_relative_to_blis"] for row in summary_rows]
    liveness: dict[str, Any] = {}
    for parameter in ("tile_m", "tile_n", "tile_k"):
        values = sorted({
            int(row[parameter]) for row in aggregates
            if row["variant"].startswith("candidate:")
        })
        liveness[parameter] = {"distinct_values": values, "active": len(values) > 1}
    overall = {
        "status": "PASS" if all(row["all_candidates_pass"] for row in summary_rows) else "FAIL",
        "workloads": len(summary_rows),
        "candidate_measurements": sum(row["pool_size"] for row in summary_rows),
        "generated_relative_to_blis_geomean": geometric_mean(ratios),
        "generated_wins": sum(float(value) > 1.0 for value in ratios),
        "parameter_liveness": liveness,
        "common_pool_oracle_invariant": True,
    }
    return summary_rows, search_rows, overall


def audit_parameter_activity(aggregates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_workload: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in aggregates:
        if row["variant"].startswith("candidate:"):
            by_workload[row["workload_id"]].append(row)
    output: list[dict[str, Any]] = []
    for workload_id, rows in sorted(by_workload.items()):
        for parameter in ("tile_m", "tile_n", "tile_k"):
            values = sorted({int(row[parameter]) for row in rows})
            active = len(values) > 1
            output.append({
                "workload_id": workload_id,
                "parameter": parameter,
                "distinct_values": ";".join(map(str, values)),
                "distinct_count": len(values),
                "activity_status": "active" if active else "conditionally_eliminated",
                "included_in_workload_search": active,
                "elimination_reason": (
                    "Contract and static-extent legality leave one value"
                    if not active else ""
                ),
            })
    return output


def run_perf(
    summary_rows: list[dict[str, Any]],
    state: dict[str, Any],
    manifests: dict[str, Any],
    baseline: dict[str, Any],
    cpu: int | None,
    output_root: Path,
) -> list[dict[str, Any]]:
    if not shutil_which("perf"):
        return [{"status": "UNAVAILABLE", "reason": "perf executable not found"}]
    selected_ids = {"qkv_decode_m8", "gate_up_prefill_m32", "qkv_fringe_m17"}
    rows: list[dict[str, Any]] = []
    events = "cycles,instructions,cache-references,cache-misses,branches,branch-misses"
    for summary in summary_rows:
        if summary["workload_id"] not in selected_ids:
            continue
        workload = state[summary["workload_id"]]["workload"]
        variants = (
            ("pool_best", manifests[summary["best_candidate_id"]]),
            ("B5_blis", baseline),
        )
        for variant, manifest in variants:
            command = ["perf", "stat", "-x,", "-e", events, "--"]
            if cpu is not None:
                command.extend(["taskset", "-c", str(cpu)])
            command.extend([
                manifest["executable"], str(workload["m"]), str(workload["k"]),
                str(workload["n"]), "1", "3", "1",
            ])
            completed = subprocess.run(command, text=True, capture_output=True)
            log = output_root / "reports" / "perf" / f"{workload['id']}_{variant}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(
                "$ " + " ".join(command) + "\n\nSTDOUT\n" + completed.stdout
                + "\nSTDERR\n" + completed.stderr,
                encoding="utf-8",
            )
            counters: dict[str, Any] = {}
            for line in completed.stderr.splitlines():
                fields = line.split(",")
                if len(fields) < 3:
                    continue
                value_text, event = fields[0].strip(), fields[2].strip()
                if event not in {
                    "cycles", "instructions", "cache-references", "cache-misses",
                    "branches", "branch-misses",
                }:
                    continue
                try:
                    counters[event.replace("-", "_")] = float(value_text)
                except ValueError:
                    counters[event.replace("-", "_")] = value_text
            rows.append({
                "workload_id": workload["id"],
                "variant": variant,
                "status": "PASS" if completed.returncode == 0 else "UNAVAILABLE",
                "returncode": completed.returncode,
                "log": str(log),
                **counters,
            })
    return rows


def shutil_which(name: str) -> str | None:
    from shutil import which
    return which(name)


def write_report(output_root: Path, summary_rows: list[dict[str, Any]], overall: dict[str, Any]) -> None:
    lines = [
        "# i9 Transformer-shape Contract pool results",
        "",
        f"- Status: **{overall['status']}**",
        f"- Workloads: {overall['workloads']}",
        f"- Generated-pool/complete-BLIS geometric ratio: {overall['generated_relative_to_blis_geomean']:.4f}",
        "",
        "| Workload | Shape MxKxN | Best tile | Path | Generated / BLIS |",
        "|---|---:|---:|---|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['workload_id']} | {row['m']}x{row['k']}x{row['n']} | "
            f"{row['best_tile_m']}x{row['best_tile_n']}x{row['best_tile_k']} | "
            f"{row['best_predicted_path']} | {row['generated_relative_to_blis']:.4f} |"
        )
    lines.extend([
        "",
        "Correctness uses a deterministic projection outside the timed region. Results are single-threaded f32 GEMM kernel evidence, not full-model latency.",
        "",
    ])
    path = output_root / "reports" / "i9_transformer_pool_results.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=PROJECT)
    parser.add_argument("--cpu", type=int)
    parser.add_argument("--force-build", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--skip-perf", action="store_true")
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    config = read_json(PROJECT / "data" / "experiment_config.json")
    workloads_document = read_json(PROJECT / "data" / "transformer_workloads.json")
    workloads = workloads_document["workloads"][:2] if args.smoke else workloads_document["workloads"]
    pool_size = 10 if args.smoke else int(config["transformer_pool"]["i9_pool_size"])
    configure_cgo(output_root)
    state = build_plan(workloads, pool_size)
    plan_rows = []
    for workload_id, item in sorted(state.items()):
        for row in item["active_pool"]:
            plan_rows.append({
                "workload_id": workload_id,
                "contract_id": item["contract"]["id"],
                "candidate_id": row["candidate_id"],
                "tile_m": row["tile_m"], "tile_n": row["tile_n"], "tile_k": row["tile_k"],
                "predicted_path": row["predicted_path"], "score": row["score"],
            })
    write_csv(output_root / "processed" / "i9_candidate_plan.csv", plan_rows)
    if args.plan_only:
        print(json.dumps({"status": "PLAN_PASS", "workloads": len(state), "rows": len(plan_rows)}, indent=2))
        return
    cgo_common.ensure_tools(build_buddy=False)
    manifests, baseline = compile_plan(state, args.force_build)
    measurement = dict(config["transformer_pool"])
    if args.smoke:
        measurement.update({"process_trials": 1, "warmups": 1, "repeats_per_process": 1})
    measurement["cpu_affinity"] = args.cpu
    rows = measure_plan(state, manifests, baseline, measurement, output_root)
    aggregates = aggregate(rows)
    summary_rows, search_rows, overall = analyze(state, aggregates, config)
    activity_rows = audit_parameter_activity(aggregates)
    overall["per_workload_parameter_activity_audited"] = True
    overall["conditionally_eliminated_dimensions"] = sum(
        row["activity_status"] == "conditionally_eliminated" for row in activity_rows
    )
    perf_rows = [] if args.skip_perf else run_perf(
        summary_rows, state, manifests, baseline, args.cpu, output_root
    )
    write_csv(output_root / "raw" / "i9_transformer_trials.csv", rows)
    write_csv(output_root / "processed" / "i9_transformer_aggregates.csv", aggregates)
    write_csv(output_root / "processed" / "i9_transformer_summary.csv", summary_rows)
    write_csv(output_root / "processed" / "i9_transformer_search.csv", search_rows)
    write_csv(output_root / "processed" / "i9_parameter_activity.csv", activity_rows)
    write_csv(output_root / "processed" / "i9_perf_status.csv", perf_rows)
    write_json(output_root / "processed" / "i9_transformer_summary.json", {
        "schema_version": 1,
        "experiment_id": config["experiment_id"],
        "target": "i9_14900_linux",
        **overall,
        "host": {"platform": platform.platform(), "python": platform.python_version(), "cpu_affinity": args.cpu},
        "perf_status": perf_rows,
        "claim_boundary": config["claim_boundary"],
    })
    write_report(output_root, summary_rows, overall)
    outputs = [
        output_root / "raw" / "i9_transformer_trials.csv",
        output_root / "processed" / "i9_transformer_summary.csv",
        output_root / "processed" / "i9_parameter_activity.csv",
        output_root / "processed" / "i9_transformer_summary.json",
        output_root / "reports" / "i9_transformer_pool_results.md",
    ]
    write_json(output_root / "provenance" / "i9_transformer_manifest.json", {
        "schema_version": 1,
        "generator": {
            "path": str(EXPERIMENTS / "chapter4_space" / "scripts" / "chapter4lib.py"),
            "sha256": sha256(EXPERIMENTS / "chapter4_space" / "scripts" / "chapter4lib.py"),
        },
        "inputs": {
            "config": sha256(PROJECT / "data" / "experiment_config.json"),
            "workloads": sha256(PROJECT / "data" / "transformer_workloads.json"),
            "candidate_driver": sha256(PROJECT / "runtime" / "projection_candidate_bench.cpp"),
            "blis_driver": sha256(PROJECT / "runtime" / "projection_blis_bench.cpp"),
        },
        "outputs": {str(path.relative_to(output_root)): sha256(path) for path in outputs},
        "candidate_manifests": manifests,
        "baseline_manifest": baseline,
    })
    print(json.dumps(overall, indent=2), flush=True)


if __name__ == "__main__":
    main()
