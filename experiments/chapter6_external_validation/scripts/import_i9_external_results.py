#!/usr/bin/env python3
"""Audit and import the formal i9-14900 external-validation result bundle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import shutil
import statistics
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parents[3]
EXPECTED_ROOT_PREFIX = "i9_14900_"
EXPECTED_TRIALS = {0, 1, 2}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def geometric_mean(values: list[float]) -> float:
    if not values:
        raise ValueError("geometric mean requires at least one value")
    return math.exp(sum(math.log(max(value, 1.0e-300)) for value in values) / len(values))


def cluster_bootstrap(
    values: dict[str, float], replicates: int = 20000
) -> tuple[float, float]:
    keys = sorted(values)
    if not keys:
        raise ValueError("bootstrap requires at least one workload")
    rng = random.Random(20260722)
    samples: list[float] = []
    for _ in range(replicates):
        draw = [values[rng.choice(keys)] for _ in keys]
        samples.append(geometric_mean(draw))
    samples.sort()
    return samples[int(0.025 * replicates)], samples[int(0.975 * replicates)]


def verify_external_checksum(archive: Path, checksum_path: Path | None) -> str:
    actual = sha256(archive)
    if checksum_path is None:
        checksum_path = Path(str(archive) + ".sha256")
    if not checksum_path.is_file():
        raise FileNotFoundError(f"missing external checksum: {checksum_path}")
    fields = checksum_path.read_text(encoding="utf-8").strip().split()
    if not fields or len(fields[0]) != 64:
        raise ValueError(f"invalid checksum file: {checksum_path}")
    if fields[0].lower() != actual:
        raise ValueError(
            f"external checksum mismatch: expected={fields[0].lower()} actual={actual}"
        )
    return actual


def safe_extract(archive: Path, destination: Path) -> Path:
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        if not members:
            raise ValueError("empty i9 result archive")
        roots: set[str] = set()
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError(f"unsafe archive member: {member.name}")
            if not member.isdir() and not member.isfile():
                raise ValueError(f"unsupported archive member type: {member.name}")
            roots.add(path.parts[0])
        if len(roots) != 1:
            raise ValueError(f"archive must contain one result root, observed={sorted(roots)}")
        root_name = next(iter(roots))
        if not root_name.startswith(EXPECTED_ROOT_PREFIX):
            raise ValueError(f"unexpected result root: {root_name}")
        bundle.extractall(destination, members=members)
    return destination / root_name


def require_files(root: Path, relative_paths: list[str]) -> None:
    missing = [relative for relative in relative_paths if not (root / relative).is_file()]
    if missing:
        raise FileNotFoundError(f"i9 result bundle is incomplete: {missing}")


def verify_manifest_outputs(root: Path, manifest_path: Path) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    outputs = manifest.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        raise ValueError(f"manifest has no outputs: {manifest_path}")
    for relative, expected in outputs.items():
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256(path)
        if actual != expected:
            raise ValueError(
                f"internal output hash mismatch for {relative}: expected={expected} actual={actual}"
            )
    return len(outputs)


def verify_candidate_binaries(root: Path, manifest: dict[str, Any]) -> int:
    candidates = manifest.get("candidate_manifests", {})
    if len(candidates) != 86:
        raise ValueError(f"expected 86 unique i9 candidate binaries, observed={len(candidates)}")
    for candidate_id, record in candidates.items():
        if record.get("candidate_id") != candidate_id:
            raise ValueError(f"candidate manifest ID mismatch: {candidate_id}")
        for flag in (
            "wrapper_call_present",
            "fringe_wrapper_call_present",
            "blis_kernel_symbol_present",
        ):
            if record.get(flag) is not True:
                raise ValueError(f"{candidate_id} failed binary audit: {flag}")
        executable = root / "build" / "i9_transformer" / "binaries" / "f32" / candidate_id / "benchmark"
        if sha256(executable) != record["executable_sha256"]:
            raise ValueError(f"candidate executable hash mismatch: {candidate_id}")
    baseline = manifest.get("baseline_manifest", {})
    for flag in ("blis_frontend_symbol_present", "blis_kernel_symbol_present"):
        if baseline.get(flag) is not True:
            raise ValueError(f"BLIS baseline failed binary audit: {flag}")
    executable = root / "build" / "i9_transformer" / "binaries" / "f32" / "B5_blis" / "benchmark"
    if sha256(executable) != baseline.get("executable_sha256"):
        raise ValueError("BLIS baseline executable hash mismatch")
    return len(candidates) + 1


def parse_protocol(root: Path) -> dict[str, str]:
    protocol: dict[str, str] = {}
    for line in (root / "reports" / "run_protocol.txt").read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            protocol[key.strip()] = value.strip()
    required = {
        "target": "i9_14900_linux",
        "smoke": "0",
        "skip_perf": "0",
        "threads": "1",
    }
    for key, expected in required.items():
        if protocol.get(key) != expected:
            raise ValueError(
                f"formal run protocol mismatch for {key}: expected={expected}, "
                f"observed={protocol.get(key)}"
            )
    if not protocol.get("cpu", "").isdigit():
        raise ValueError("formal run protocol has no valid CPU affinity")
    return protocol


def frozen_workloads() -> dict[str, dict[str, Any]]:
    value = json.loads(
        (PROJECT / "data" / "transformer_workloads.json").read_text(encoding="utf-8")
    )
    return {row["id"]: row for row in value["workloads"]}


def frozen_plan() -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["workload_id"], row["candidate_id"]): row
        for row in read_csv(PROJECT / "processed" / "i9_candidate_plan.csv")
    }


def validate_measurements(root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    plan_path = root / "processed" / "i9_candidate_plan.csv"
    if sha256(plan_path) != sha256(PROJECT / "processed" / "i9_candidate_plan.csv"):
        raise ValueError("returned i9 candidate plan differs from the frozen local plan")
    expected_workloads = frozen_workloads()
    expected_plan = frozen_plan()
    if len(expected_workloads) != 10 or len(expected_plan) != 280:
        raise ValueError("local frozen i9 workload or candidate plan is incomplete")

    rows = read_csv(root / "raw" / "i9_transformer_trials.csv")
    required = {
        "target", "dtype", "workload_id", "m", "k", "n", "trial", "variant",
        "candidate_id", "tile_m", "tile_n", "tile_k", "predicted_path",
        "observed_path", "median_ms", "gflops", "projection_error", "status",
        "executable_sha256",
    }
    if len(rows) != 870 or not rows or not required.issubset(rows[0]):
        raise ValueError(f"expected 870 complete i9 rows with the frozen schema, observed={len(rows)}")
    if any(row["status"] != "PASS" for row in rows):
        raise ValueError("i9 result contains a failed correctness row")

    observed_keys: set[tuple[str, str, int]] = set()
    grouped_trials: dict[tuple[str, str], set[int]] = defaultdict(set)
    candidate_groups: Counter[str] = Counter()
    baseline_groups: Counter[str] = Counter()
    for row in rows:
        workload_id = row["workload_id"]
        if workload_id not in expected_workloads:
            raise ValueError(f"unexpected i9 workload: {workload_id}")
        workload = expected_workloads[workload_id]
        for dimension in ("m", "k", "n"):
            if int(row[dimension]) != int(workload[dimension]):
                raise ValueError(f"shape mismatch for {workload_id}: {dimension}")
        if row["target"] != "i9_14900_linux" or row["dtype"] != "f32":
            raise ValueError(f"target or dtype mismatch for {workload_id}")
        trial = int(row["trial"])
        key = (workload_id, row["variant"], trial)
        if key in observed_keys:
            raise ValueError(f"duplicate i9 trial key: {key}")
        observed_keys.add(key)
        grouped_trials[(workload_id, row["variant"])].add(trial)
        if row["variant"] == "B5_blis":
            baseline_groups[workload_id] += 1
            if row["candidate_id"] or row["predicted_path"] != "library" or row["observed_path"] != "library":
                raise ValueError(f"invalid BLIS baseline row for {workload_id}")
            continue
        if not row["variant"].startswith("candidate:"):
            raise ValueError(f"unexpected i9 variant: {row['variant']}")
        candidate_id = row["candidate_id"]
        if row["variant"] != f"candidate:{candidate_id}":
            raise ValueError(f"candidate variant mismatch: {row['variant']}")
        expected = expected_plan.get((workload_id, candidate_id))
        if expected is None:
            raise ValueError(f"candidate is outside the frozen pool: {workload_id}/{candidate_id}")
        for parameter in ("tile_m", "tile_n", "tile_k", "predicted_path"):
            if row[parameter] != expected[parameter]:
                raise ValueError(f"candidate parameter mismatch: {workload_id}/{candidate_id}/{parameter}")
        if row["observed_path"] != row["predicted_path"]:
            raise ValueError(f"predicted/observed path mismatch: {workload_id}/{candidate_id}")
        candidate_groups[workload_id] += 1

    if any(trials != EXPECTED_TRIALS for trials in grouped_trials.values()):
        raise ValueError("at least one i9 measurement group does not contain trials 0, 1, and 2")
    if any(candidate_groups[workload_id] != 84 for workload_id in expected_workloads):
        raise ValueError(f"candidate trial matrix is incomplete: {candidate_groups}")
    if any(baseline_groups[workload_id] != 3 for workload_id in expected_workloads):
        raise ValueError(f"BLIS trial matrix is incomplete: {baseline_groups}")

    aggregates = read_csv(root / "processed" / "i9_transformer_aggregates.csv")
    if len(aggregates) != 290:
        raise ValueError(f"expected 290 aggregate groups, observed={len(aggregates)}")
    return rows, aggregates


def analyze_results(
    root: Path,
    archive: Path,
    archive_hash: str,
    rows: list[dict[str, str]],
    aggregates: list[dict[str, str]],
    protocol: dict[str, str],
    verified_outputs: int,
    verified_binaries: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    original = json.loads(
        (root / "processed" / "i9_transformer_summary.json").read_text(encoding="utf-8")
    )
    summary_rows: list[dict[str, Any]] = read_csv(
        root / "processed" / "i9_transformer_summary.csv"
    )
    if original.get("status") != "PASS" or len(summary_rows) != 10:
        raise ValueError("returned i9 summary is incomplete or failed")
    by_group = {(row["workload_id"], row["variant"]): row for row in aggregates}
    ratios: dict[str, float] = {}
    noisy_workloads: list[str] = []
    selected_cvs: list[float] = []
    baseline_cvs: list[float] = []
    for row in summary_rows:
        workload_id = str(row["workload_id"])
        ratio = float(row["generated_relative_to_blis"])
        ratios[workload_id] = ratio
        candidate = by_group[(workload_id, f"candidate:{row['best_candidate_id']}")]
        baseline = by_group[(workload_id, "B5_blis")]
        candidate_cv = float(candidate["trial_cv"])
        baseline_cv = float(baseline["trial_cv"])
        selected_cvs.append(candidate_cv)
        baseline_cvs.append(baseline_cv)
        row["best_candidate_trial_cv"] = candidate_cv
        row["blis_trial_cv"] = baseline_cv
        if candidate_cv > 0.05 or baseline_cv > 0.05:
            noisy_workloads.append(workload_id)

    ratio_gmean = geometric_mean(list(ratios.values()))
    if not math.isclose(
        ratio_gmean,
        float(original["generated_relative_to_blis_geomean"]),
        rel_tol=1.0e-12,
    ):
        raise ValueError("returned i9 geometric mean is internally inconsistent")
    ci_lower, ci_upper = cluster_bootstrap(ratios)
    sensitivity_ratios = {
        key: value for key, value in ratios.items() if key not in noisy_workloads
    }
    sensitivity_lower, sensitivity_upper = cluster_bootstrap(sensitivity_ratios)

    sparse = json.loads(
        (root / "processed" / "sparse_summary.json").read_text(encoding="utf-8")
    )
    expert_increment = [
        row for row in sparse["comparisons"]
        if row["test_method"] == "D1_expert_plus_data_thompson"
        and row["reference_method"] == "D0_data_only_thompson"
    ]
    if len(expert_increment) != 10:
        raise ValueError("sparse Data-only versus Expert+Data matrix is incomplete")
    significant_benefit = sum(float(row["ci95_lower"]) > 1.0 for row in expert_increment)
    significant_harm = sum(float(row["ci95_upper"]) < 1.0 for row in expert_increment)

    group_cvs = [float(row["trial_cv"]) for row in aggregates]
    perf_status = original.get("perf_status", [])
    perf_available = sum(row.get("status") == "PASS" for row in perf_status)
    host_text = (root / "reports" / "host_metadata.txt").read_text(encoding="utf-8")
    if "Intel(R) Core(TM) i9-14900" not in host_text:
        raise ValueError("host metadata does not identify the expected Intel Core i9-14900")

    summary: dict[str, Any] = {
        "schema_version": 2,
        "experiment_id": "thesis.chapter6_external_validation.i9_14900",
        "status": "PASS",
        "status_meaning": "formal protocol, integrity, completeness, and correctness passed",
        "target": "i9_14900_linux",
        "cpu_affinity": int(protocol["cpu"]),
        "threads": 1,
        "workloads": len(summary_rows),
        "correctness_rows": len(rows),
        "candidate_measurements": 280,
        "measurement_groups": len(aggregates),
        "unique_candidate_binaries": verified_binaries - 1,
        "generated_relative_to_blis_geomean": ratio_gmean,
        "generated_relative_to_blis_ci95": [ci_lower, ci_upper],
        "generated_wins": sum(value > 1.0 for value in ratios.values()),
        "max_workload_ratio": max(ratios.values()),
        "median_trial_cv": statistics.median(group_cvs),
        "max_trial_cv": max(group_cvs),
        "groups_trial_cv_over_5pct": sum(value > 0.05 for value in group_cvs),
        "best_candidate_median_trial_cv": statistics.median(selected_cvs),
        "best_candidate_max_trial_cv": max(selected_cvs),
        "blis_median_trial_cv": statistics.median(baseline_cvs),
        "blis_max_trial_cv": max(baseline_cvs),
        "pre_registered_i9_cv_gate": None,
        "sensitivity_cv_threshold": 0.05,
        "sensitivity_excluded_workloads": noisy_workloads,
        "sensitivity_remaining_workloads": len(sensitivity_ratios),
        "sensitivity_generated_relative_to_blis_geomean": geometric_mean(
            list(sensitivity_ratios.values())
        ),
        "sensitivity_generated_relative_to_blis_ci95": [
            sensitivity_lower,
            sensitivity_upper,
        ],
        "max_projection_error": max(float(row["projection_error"]) for row in rows),
        "parameter_liveness": original["parameter_liveness"],
        "per_workload_parameter_activity_audited": original[
            "per_workload_parameter_activity_audited"
        ],
        "conditionally_eliminated_dimensions": original[
            "conditionally_eliminated_dimensions"
        ],
        "common_pool_oracle_invariant": original["common_pool_oracle_invariant"],
        "perf_measurements": len(perf_status),
        "perf_measurements_available": perf_available,
        "perf_status": "UNAVAILABLE" if perf_status and perf_available == 0 else "PARTIAL",
        "sparse_holdout_workloads": sparse["holdout_workloads"],
        "sparse_trajectory_rows": sparse["trajectory_rows"],
        "expert_plus_data_vs_data_only_comparisons": len(expert_increment),
        "expert_plus_data_significant_benefits": significant_benefit,
        "expert_plus_data_significant_harms": significant_harm,
        "expert_performance_increment_claim": "STOP",
        "archive_sha256": archive_hash,
        "archive_path": str(archive.resolve()),
        "internal_manifest_outputs_verified": verified_outputs,
        "executables_verified": verified_binaries,
        "claim_boundary": original["claim_boundary"],
    }
    return summary, summary_rows


def audit_extracted(root: Path, archive: Path, archive_hash: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    require_files(root, [
        "reports/run_protocol.txt",
        "reports/host_metadata.txt",
        "raw/i9_transformer_trials.csv",
        "processed/i9_candidate_plan.csv",
        "processed/i9_transformer_aggregates.csv",
        "processed/i9_transformer_summary.csv",
        "processed/i9_transformer_summary.json",
        "processed/i9_parameter_activity.csv",
        "processed/i9_perf_status.csv",
        "processed/sparse_summary.json",
        "provenance/i9_transformer_manifest.json",
        "provenance/sparse_manifest.json",
    ])
    protocol = parse_protocol(root)
    transformer_manifest_path = root / "provenance" / "i9_transformer_manifest.json"
    sparse_manifest_path = root / "provenance" / "sparse_manifest.json"
    verified_outputs = verify_manifest_outputs(root, transformer_manifest_path)
    verified_outputs += verify_manifest_outputs(root, sparse_manifest_path)
    transformer_manifest = json.loads(transformer_manifest_path.read_text(encoding="utf-8"))
    verified_binaries = verify_candidate_binaries(root, transformer_manifest)
    rows, aggregates = validate_measurements(root)
    return analyze_results(
        root,
        archive,
        archive_hash,
        rows,
        aggregates,
        protocol,
        verified_outputs,
        verified_binaries,
    )


def audit_archive(
    archive: Path, checksum_path: Path | None = None
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    archive = archive.resolve()
    archive_hash = verify_external_checksum(archive, checksum_path)
    with tempfile.TemporaryDirectory(prefix="i9-external-audit-") as temporary:
        root = safe_extract(archive, Path(temporary))
        return audit_extracted(root, archive, archive_hash)


def refresh_registry(output_root: Path) -> None:
    if output_root != PROJECT:
        return
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


def copy_processed_outputs(root: Path, output_root: Path) -> None:
    mappings = {
        "processed/i9_transformer_aggregates.csv": "processed/i9_external_aggregates.csv",
        "processed/i9_transformer_summary.csv": "processed/i9_external_summary.csv",
        "processed/i9_transformer_search.csv": "processed/i9_external_search.csv",
        "processed/i9_parameter_activity.csv": "processed/i9_external_parameter_activity.csv",
        "processed/i9_perf_status.csv": "processed/i9_external_perf_status.csv",
        "processed/sparse_calibration_costs.csv": "processed/i9_sparse_calibration_costs.csv",
        "processed/sparse_paired_comparisons.csv": "processed/i9_sparse_paired_comparisons.csv",
        "processed/sparse_fixed_budget.csv": "processed/i9_sparse_fixed_budget.csv",
        "processed/sparse_time_to95.csv": "processed/i9_sparse_time_to95.csv",
        "processed/sparse_summary.json": "processed/i9_sparse_summary.json",
    }
    for source, destination in mappings.items():
        target = output_root / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / source, target)


def write_report(
    output_root: Path, summary: dict[str, Any], summary_rows: list[dict[str, Any]]
) -> None:
    lower, upper = summary["generated_relative_to_blis_ci95"]
    sensitivity_lower, sensitivity_upper = summary[
        "sensitivity_generated_relative_to_blis_ci95"
    ]
    report = [
        "# i9-14900 external-validation results",
        "",
        f"- Formal import status: **{summary['status']}** ({summary['status_meaning']}).",
        f"- Correct rows / measurement groups: {summary['correctness_rows']} / "
        f"{summary['measurement_groups']}.",
        "- Generated Contract pool / complete BLIS geometric relative performance: "
        f"{summary['generated_relative_to_blis_geomean']:.4f} "
        f"(workload bootstrap 95% CI [{lower:.4f}, {upper:.4f}]); "
        f"wins: {summary['generated_wins']}/{summary['workloads']}.",
        f"- Median/max group trial CV: {summary['median_trial_cv']:.2%} / "
        f"{summary['max_trial_cv']:.2%}; groups above 5%: "
        f"{summary['groups_trial_cv_over_5pct']}.",
        "- Selected-candidate/BLIS max trial CV: "
        f"{summary['best_candidate_max_trial_cv']:.2%} / "
        f"{summary['blis_max_trial_cv']:.2%}.",
        "- No i9 CV acceptance threshold was frozen before measurement. The 5% analysis is "
        "therefore reported only as a sensitivity check, not as a retrospective pass gate.",
        f"- Sensitivity check excludes {summary['sensitivity_excluded_workloads']}; "
        f"remaining ratio {summary['sensitivity_generated_relative_to_blis_geomean']:.4f} "
        f"(95% CI [{sensitivity_lower:.4f}, {sensitivity_upper:.4f}]).",
        f"- perf stat availability: {summary['perf_measurements_available']}/"
        f"{summary['perf_measurements']}; this does not affect the primary wall-time result.",
        "- Sparse Data-only vs Expert+Data: "
        f"{summary['expert_plus_data_significant_benefits']}/"
        f"{summary['expert_plus_data_vs_data_only_comparisons']} significant benefits and "
        f"{summary['expert_plus_data_significant_harms']} significant harms; the incremental "
        "expert performance-feature claim remains **STOP**.",
        "",
        "| Workload | Shape MxKxN | Best tile | Path | Generated / BLIS | Candidate CV | BLIS CV |",
        "|---|---:|---:|---|---:|---:|---:|",
    ]
    for row in summary_rows:
        report.append(
            f"| {row['workload_id']} | {row['m']}x{row['k']}x{row['n']} | "
            f"{row['best_tile_m']}x{row['best_tile_n']}x{row['best_tile_k']} | "
            f"{row['best_predicted_path']} | "
            f"{float(row['generated_relative_to_blis']):.4f} | "
            f"{float(row['best_candidate_trial_cv']):.2%} | "
            f"{float(row['blis_trial_cv']):.2%} |"
        )
    report.extend([
        "",
        "A ratio above 1 means that the generated Contract schedule is faster. These are "
        "single-threaded f32 GEMM kernel-package measurements, not end-to-end model latency. "
        "The negative library-boundary result does not invalidate legality transfer, parameter "
        "liveness, or independent backend integration evidence.",
        "",
    ])
    path = output_root / "reports" / "i9_external_results.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(report), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--checksum", type=Path)
    parser.add_argument("--output-root", type=Path, default=PROJECT)
    args = parser.parse_args()
    archive = args.archive.resolve()
    output_root = args.output_root.resolve()
    archive_hash = verify_external_checksum(archive, args.checksum)

    with tempfile.TemporaryDirectory(prefix="i9-external-import-") as temporary:
        root = safe_extract(archive, Path(temporary))
        summary, summary_rows = audit_extracted(root, archive, archive_hash)
        archive_root = output_root / "raw" / "i9_external" / root.name
        if archive_root.exists():
            shutil.rmtree(archive_root)
        archive_root.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(root, archive_root)
        summary["archived_result_dir"] = str(archive_root)
        copy_processed_outputs(root, output_root)

    write_csv(output_root / "processed" / "i9_external_summary.csv", summary_rows)
    write_json(output_root / "processed" / "i9_external_summary.json", summary)
    write_json(
        output_root / "provenance" / "i9_external_import_manifest.json",
        {
            "schema_version": 1,
            "archive": str(archive),
            "archive_sha256": archive_hash,
            "archived_result_dir": summary["archived_result_dir"],
            "internal_manifest_outputs_verified": summary[
                "internal_manifest_outputs_verified"
            ],
            "executables_verified": summary["executables_verified"],
            "formal_protocol_verified": True,
            "measurement_matrix_verified": True,
        },
    )
    write_report(output_root, summary, summary_rows)
    refresh_registry(output_root)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
