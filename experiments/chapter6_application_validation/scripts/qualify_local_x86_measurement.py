#!/usr/bin/env python3
"""Qualify WSL CPU affinity and timing windows before a second formal run."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import random
import statistics
import sys
import time
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
TARGET = PROJECT / "targets" / "i7_10750h"
OUTPUT = TARGET / "qualification"
sys.path.insert(0, str(PROJECT / "scripts"))

import run_local_x86_trace_pool as local_pool  # noqa: E402


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def robust_cv(values: list[float]) -> float:
    median = statistics.median(values)
    mad = statistics.median(abs(value - median) for value in values)
    return 1.4826 * mad / median if median > 0.0 else math.inf


def main() -> None:
    config_path = PROJECT / "data" / "experiment_config.json"
    config = read_json(config_path)
    local = config["local_x86"]
    qualification = config["local_x86_measurement_qualification"]
    manifest_path = TARGET / "provenance" / "manifest.json"
    manifest = read_json(manifest_path)
    candidate_plan = read_csv(TARGET / "processed" / "candidate_plan.csv")
    workloads = {
        row["id"]: row
        for row in local_pool.pool.read_json(
            local_pool.EXTERNAL / "data" / "transformer_workloads.json"
        )["workloads"]
    }
    for name, value in local["thread_environment"].items():
        os.environ[name] = str(value)

    case_rows: list[tuple[dict[str, Any], dict[str, str]]] = []
    for case in qualification["cases"]:
        matches = [
            row for row in candidate_plan
            if row["workload_id"] == case["workload_id"]
            and row["candidate_id"] == case["candidate_id"]
        ]
        if len(matches) != 1:
            raise RuntimeError(f"qualification case is not unique: {case}")
        case_rows.append((case, matches[0]))

    jobs = []
    for trial in range(int(qualification["process_trials_per_variant"])):
        for cpu in qualification["cpu_candidates"]:
            for case, candidate in case_rows:
                for variant in qualification["variants"]:
                    jobs.append((trial, int(cpu), case, candidate, variant))
    random.Random(20260722).shuffle(jobs)

    rows: list[dict[str, Any]] = []
    for index, (trial, cpu, case, candidate, variant) in enumerate(jobs, 1):
        workload = workloads[case["workload_id"]]
        operations = 2 * int(workload["m"]) * int(workload["k"]) * int(workload["n"])
        inner_iters = max(1, min(
            int(qualification["maximum_inner_iters"]),
            math.ceil(int(qualification["target_timed_flops_per_sample"]) / operations),
        ))
        generated = variant == "generated_candidate"
        selected_manifest = (
            manifest["candidate_manifests"][case["candidate_id"]]
            if generated else manifest["baseline_manifest"]
        )
        measurement = {
            "warmups": int(qualification["warmups"]),
            "repeats": int(qualification["repeats_per_process"]),
            "inner_iters": inner_iters,
            "cpu_affinity": cpu,
        }
        log = (
            OUTPUT / "reports" / "case_logs" / f"cpu_{cpu}"
            / case["workload_id"] / f"trial_{trial}_{variant}.log"
        )
        result = local_pool.pool.cgo_common.measure_live(
            selected_manifest,
            workload,
            measurement,
            log,
            row=candidate if generated else None,
        )
        rows.append({
            "cpu": cpu,
            "trial": trial,
            "workload_id": case["workload_id"],
            "variant": variant,
            "candidate_id": case["candidate_id"] if generated else "",
            "inner_iters": inner_iters,
            "median_ms": result["median_ms"],
            "min_ms": result["min_ms"],
            "max_ms": result["max_ms"],
            "stddev_ms": result["stddev_ms"],
            "gflops": result["gflops"],
            "status": result["status"],
        })
        print(
            f"qualification {index}/{len(jobs)}: cpu={cpu} "
            f"{case['workload_id']} {variant} trial={trial}",
            flush=True,
        )
        time.sleep(float(qualification["settle_seconds"]))

    grouped: dict[tuple[int, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (int(row["cpu"]), str(row["workload_id"]), str(row["variant"]))
        grouped.setdefault(key, []).append(row)
    audit_rows: list[dict[str, Any]] = []
    threshold = float(qualification["acceptance"]["maximum_robust_cv"])
    for (cpu, workload_id, variant), values in sorted(grouped.items()):
        medians = [float(row["median_ms"]) for row in values]
        value_cv = robust_cv(medians)
        audit_rows.append({
            "cpu": cpu,
            "workload_id": workload_id,
            "variant": variant,
            "process_medians": len(medians),
            "median_ms": statistics.median(medians),
            "robust_cv": value_cv,
            "all_correct": all(row["status"] == "PASS" for row in values),
            "qualification_pass": value_cv <= threshold
            and all(row["status"] == "PASS" for row in values),
        })

    cpu_rows: list[dict[str, Any]] = []
    required_fraction = float(
        qualification["acceptance"]["required_case_variant_pass_fraction"]
    )
    for cpu in qualification["cpu_candidates"]:
        values = [row for row in audit_rows if int(row["cpu"]) == int(cpu)]
        pass_fraction = sum(row["qualification_pass"] for row in values) / len(values)
        cpu_rows.append({
            "cpu": int(cpu),
            "case_variant_groups": len(values),
            "passing_groups": sum(row["qualification_pass"] for row in values),
            "pass_fraction": pass_fraction,
            "qualification_pass": pass_fraction >= required_fraction,
        })
    qualifying = [row["cpu"] for row in cpu_rows if row["qualification_pass"]]
    selected_cpu = min(qualifying) if qualifying else None
    summary = {
        "status": "PASS" if selected_cpu is not None else "FAIL_UNQUALIFIED",
        "protocol_id": qualification["protocol_id"],
        "qualification_only": True,
        "performance_claims_allowed": False,
        "jobs": len(rows),
        "cpu_candidates": qualification["cpu_candidates"],
        "qualifying_cpus": qualifying,
        "selected_cpu": selected_cpu,
        "selection_rule": qualification["acceptance"]["selection_rule"],
        "maximum_robust_cv": threshold,
        "required_case_variant_pass_fraction": required_fraction,
        "next_decision": (
            qualification["decision"]["if_pass"]
            if selected_cpu is not None else qualification["decision"]["if_fail"]
        ),
    }
    raw_path = OUTPUT / "raw" / "trials.csv"
    audit_path = OUTPUT / "processed" / "stability_audit.csv"
    cpu_path = OUTPUT / "processed" / "cpu_summary.csv"
    summary_path = OUTPUT / "processed" / "summary.json"
    write_csv(raw_path, rows)
    write_csv(audit_path, audit_rows)
    write_csv(cpu_path, cpu_rows)
    write_json(summary_path, summary)
    report_path = OUTPUT / "reports" / "measurement_qualification.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join([
            "# Local x86 measurement qualification",
            "",
            f"- Status: **{summary['status']}**",
            "- Scope: diagnostic only; timings are excluded from performance claims.",
            f"- Jobs: {summary['jobs']}",
            f"- Qualifying CPUs: {qualifying or 'none'}",
            f"- Selected CPU: {selected_cpu if selected_cpu is not None else 'none'}",
            f"- Selection rule: {summary['selection_rule']}",
            f"- Next decision: {summary['next_decision']}",
            "",
            "| CPU | Passing groups | Pass fraction | Qualified |",
            "|---:|---:|---:|---|",
            *[
                f"| {row['cpu']} | {row['passing_groups']}/{row['case_variant_groups']} | "
                f"{row['pass_fraction']:.2%} | {'yes' if row['qualification_pass'] else 'no'} |"
                for row in cpu_rows
            ],
            "",
        ]),
        encoding="utf-8",
    )
    provenance_path = OUTPUT / "provenance" / "manifest.json"
    write_json(provenance_path, {
        "schema_version": 1,
        "experiment_id": "thesis.chapter6_application_validation.measurement_qualification",
        "config_sha256": sha256(config_path),
        "input_manifest_sha256": sha256(manifest_path),
        "runner_sha256": sha256(Path(__file__)),
        "outputs": {
            str(path.relative_to(OUTPUT)): sha256(path)
            for path in (raw_path, audit_path, cpu_path, summary_path, report_path)
        },
        "claim_boundary": qualification["purpose"],
    })
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
