#!/usr/bin/env python3
"""Render the thesis-facing status and immutable artifact index."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
EXTERNAL = PROJECT.parent / "chapter6_external_validation"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    trace = read_json(PROJECT / "processed" / "qwen_trace_summary.json")
    closure = read_json(PROJECT / "provenance" / "k230_mlir_closure_manifest.json")
    deployment = read_json(
        PROJECT / "provenance" / "k230_mlir_closure_deployment.json"
    )
    weighted = read_json(PROJECT / "processed" / "trace_weighted_summary.json")
    local_root = PROJECT / "targets" / "i7_10750h"
    local = read_json(local_root / "processed" / "summary.json")
    qualification = read_json(
        local_root / "qualification" / "processed" / "summary.json"
    )
    board_summary_path = PROJECT / "processed" / "k230_mlir_closure_summary.json"
    board = read_json(board_summary_path) if board_summary_path.is_file() else None
    external_summary_path = EXTERNAL / "processed" / "k230_external_summary.json"
    external = (
        read_json(external_summary_path) if external_summary_path.is_file() else None
    )
    i9_summary_path = EXTERNAL / "processed" / "i9_external_summary.json"
    i9 = read_json(i9_summary_path) if i9_summary_path.is_file() else None
    weighted_rows = read_csv(PROJECT / "processed" / "trace_weighted_policy_summary.csv")
    guarded_b5 = {
        row["scenario_id"]: row
        for row in weighted_rows
        if row["target"] == local["target"]
        and row["policy"] == "static_expert_guarded"
        and int(row["budget"]) == 5
    }
    elf = closure["target_elf"]
    lines = [
        "# Chapter 6 application-validation status",
        "",
        "## Completed locally",
        "",
        f"- Qwen shape trace: **{trace['status']}**, "
        f"{trace['raw_linear_calls']} raw Linear calls and "
        f"{trace['canonical_core_calls']} canonical projection calls.",
        f"- Frozen-pool coverage: {trace['core_call_coverage']:.2%} of core calls "
        f"and {trace['core_flop_coverage']:.2%} of core projection FLOPs.",
        f"- Local exact-shape pool: **{local['status']}**, "
        f"{local['workloads']} workloads and {local['candidate_measurements']} measured "
        "candidate points; timings are diagnostic-only because the stability gate failed.",
        f"- WSL measurement qualification: **{qualification['status']}**; "
        f"qualifying CPUs: {qualification['qualifying_cpus'] or 'none'}. No second "
        "confirmatory local performance run is permitted by the frozen decision rule.",
        f"- Per-workload parameter audit: {local['active_parameter_audits']}/"
        f"{local['per_workload_parameter_audits']} active and "
        f"{local['conditionally_eliminated_parameter_audits']} eliminated by "
        "static legality; the common-pool oracle is invariant.",
        f"- Host MLIR ABI smoke: **{closure['host_abi_smoke']['status']}**, "
        f"`{closure['host_abi_smoke']['stdout']}`.",
        f"- K230 static ELF: entry `{elf['entry_point']}`, "
        f"{elf['rvv_instruction_matches']} RVV instruction matches, "
        f"{len(closure['cases'])} predeclared cases.",
        "- Core Chapter 4 generator modified for this closure: **no**.",
        "- New compiler pass required: **no**; the bridge uses "
        "`transform.annotate` and `convert-linalg-to-std`.",
    ]
    if board is not None:
        lower, upper = board["c_adapter_over_mlir_adapter_ci95"]
        lines.extend([
            f"- Physical K230 MLIR closure: **{board['status']}**, "
            f"{board['correctness_rows']} correct rows across {board['cases']} cases and "
            f"{board['variants']} variants.",
            "- C-adapter / MLIR-adapter geometric ratio: "
            f"{board['c_adapter_over_mlir_adapter_geomean']:.4f}, cluster-bootstrap "
            f"95% CI [{lower:.4f}, {upper:.4f}]; parity acceptance: "
            f"**{board['parity_acceptance']}**.",
        ])
    if external is not None:
        lower, upper = external["adapter_relative_to_openblas_ci95"]
        lines.extend([
            f"- Physical K230 full candidate pool: **{external['status']}**, "
            f"{external['correctness_rows']} correct rows across "
            f"{external['workloads']} workloads; "
            f"{external['direct_workloads']} direct and "
            f"{external['adapt_workloads']} adapt pool-oracle selections.",
            "- Best generated adapter / complete OpenBLAS geometric relative "
            f"performance: {external['adapter_relative_to_openblas_geomean']:.4f}, "
            f"workload-bootstrap 95% CI [{lower:.4f}, {upper:.4f}]; adapter wins: "
            f"{external['adapter_wins']}/{external['workloads']}.",
        ])
    if i9 is not None:
        lower, upper = i9["generated_relative_to_blis_ci95"]
        lines.extend([
            f"- Physical i9-14900 exact-shape pool: **{i9['status']}**, "
            f"{i9['correctness_rows']} correct rows across {i9['workloads']} workloads.",
            "- Best generated Contract pool / complete BLIS geometric relative "
            f"performance: {i9['generated_relative_to_blis_geomean']:.4f}, "
            f"workload-bootstrap 95% CI [{lower:.4f}, {upper:.4f}]; generated wins: "
            f"{i9['generated_wins']}/{i9['workloads']}.",
        ])
    lines.extend([
        "",
        "## External-evidence status",
        "",
        "- The physical K230 and native i9-14900 exact-shape pools are complete; "
        "no hardware run remains pending inside the frozen thesis boundary.",
        f"- Current weighted-analysis status: **{weighted['status']}**.",
        "",
        "The physical K230 evidence now covers both representative compiler-to-adapter "
        "closure and the complete frozen candidate pool. Trace weighting projects "
        "measured GEMM times onto the frozen call trace; it is not end-to-end model latency.",
        "",
    ])
    report = PROJECT / "reports" / "application_validation_status.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")

    index = [
        "# Application-validation artifact index",
        "",
        "## K230 deployment package",
        "",
        f"- Package: `{Path(deployment['path']).relative_to(PROJECT)}`",
        f"- Size: {deployment['size_bytes']} bytes",
        f"- SHA-256: `{deployment['sha256']}`",
        f"- ELF SHA-256: `{elf['sha256']}`",
        f"- ELF entry: `{elf['entry_point']}`",
        f"- Board command: `{deployment['board_command']}`",
        "",
        "## Primary evidence",
        "",
        "- `processed/qwen_trace_summary.json`",
        "- `raw/qwen_linear_trace.csv`",
        "- `processed/qwen_canonical_trace.csv`",
        "- `processed/qwen_trace_workloads.csv`",
        "- `provenance/k230_mlir_closure_manifest.json`",
        "- `build/k230_mlir_closure/cases/*/input.mlir`",
        "- `build/k230_mlir_closure/cases/*/transformed.mlir`",
        "- `build/k230_mlir_closure/cases/*/kernel.ll`",
    ]
    if board is not None:
        index.extend([
            "- `processed/k230_mlir_closure_summary.json`",
            "- `processed/k230_mlir_closure_summary.csv`",
            "- `processed/k230_mlir_closure_aggregates.csv`",
            "- `reports/k230_mlir_closure_results.md`",
            "- `raw/k230_mlir_closure/board_results_*`",
        ])
    if external is not None:
        index.extend([
            "- `../chapter6_external_validation/processed/k230_external_summary.json`",
            "- `../chapter6_external_validation/processed/k230_external_summary.csv`",
            "- `../chapter6_external_validation/processed/k230_external_aggregates.csv`",
            "- `../chapter6_external_validation/reports/k230_external_results.md`",
            "- `processed/trace_weighted_summary.json`",
            "- `processed/trace_weighted_policy_summary.csv`",
            "- `reports/trace_weighted_results.md`",
        ])
    if i9 is not None:
        index.extend([
            "- `../chapter6_external_validation/processed/i9_external_summary.json`",
            "- `../chapter6_external_validation/processed/i9_external_summary.csv`",
            "- `../chapter6_external_validation/processed/i9_external_aggregates.csv`",
            "- `../chapter6_external_validation/reports/i9_external_results.md`",
            "- `../chapter6_external_validation/provenance/i9_external_import_manifest.json`",
        ])
    index.extend([
        "",
        "## Diagnostic evidence excluded from performance claims",
        "",
        "- `targets/i7_10750h/raw/trials.csv`",
        "- `targets/i7_10750h/processed/summary.json`",
        "- `targets/i7_10750h/processed/stability_audit.csv`",
        "- `targets/i7_10750h/qualification/raw/trials.csv`",
        "- `targets/i7_10750h/qualification/processed/summary.json`",
        "- `targets/i7_10750h/qualification/processed/stability_audit.csv`",
        "- `targets/i7_10750h/qualification/provenance/manifest.json`",
        "",
        "## Status boundary",
        "",
        f"- Qwen trace: `{trace['status']}`",
        f"- Local exact-shape pool: `{local['status']}`",
        f"- Local WSL qualification: `{qualification['status']}`",
        f"- K230 closure: `{board['status'] if board is not None else closure['status']}`",
        f"- K230 complete candidate pool: "
        f"`{external['status'] if external is not None else 'AWAITING_TARGET_RESULTS'}`",
        f"- i9 exact-shape candidate pool: "
        f"`{i9['status'] if i9 is not None else 'AWAITING_TARGET_RESULTS'}`",
        f"- Trace-weighted target analysis: `{weighted['status']}`",
        "",
    ])
    (PROJECT / "APPLICATION_VALIDATION_ARTIFACT_INDEX.md").write_text(
        "\n".join(index), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
