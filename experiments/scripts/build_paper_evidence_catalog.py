#!/usr/bin/env python3
"""Validate and render the thesis paper-evidence selection catalog."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENTS = Path(__file__).resolve().parent.parent
REPO = EXPERIMENTS.parents[2]
SOURCE = EXPERIMENTS / "data" / "paper_evidence_selection.json"
OUTPUT = EXPERIMENTS / "PAPER_EVIDENCE_CATALOG.md"
ALLOWED_TIERS = {
    "primary_main_text",
    "supporting_main_text",
    "appendix_only",
    "reference_only",
}


def load_and_validate() -> dict[str, Any]:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("paper evidence schema_version must be 1")
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("paper evidence entries must be a non-empty list")
    ids = [entry.get("id") for entry in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("paper evidence ids must be unique")
    missing_files = []
    for entry in entries:
        if entry.get("tier") not in ALLOWED_TIERS:
            raise ValueError(f"unsupported paper tier for {entry.get('id')}")
        if not isinstance(entry.get("body_eligible"), bool):
            raise ValueError(f"body_eligible must be boolean for {entry.get('id')}")
        if not entry.get("decision") or not entry.get("usable_claims"):
            raise ValueError(f"decision and usable_claims are required for {entry.get('id')}")
        for relative in entry.get("evidence_files", []):
            path = (REPO / relative).resolve()
            if REPO.resolve() not in path.parents:
                raise ValueError(f"evidence path escapes workspace: {relative}")
            if not path.is_file():
                missing_files.append(relative)
    if missing_files:
        raise FileNotFoundError("missing selected evidence:\n- " + "\n- ".join(missing_files))
    return data


def render(data: dict[str, Any]) -> str:
    entries = sorted(data["entries"], key=lambda entry: entry["id"])
    counts = Counter(entry["tier"] for entry in entries)
    k230 = next(entry for entry in entries if entry["id"] == "thesis.k230_rvv_backend")
    x86 = next(entry for entry in entries if entry["id"] == "thesis.x86_cross_host")
    same_pool = next(
        entry for entry in entries if entry["id"] == "thesis.chapter6_same_pool_prior"
    )
    external = next(
        entry for entry in entries
        if entry["id"] == "thesis.chapter6_external_validation"
    )
    termination = next(
        entry for entry in entries
        if entry["id"] == "thesis.chapter6_termination_validation"
    )
    if k230["body_eligible"] and x86["body_eligible"]:
        remaining_gap = (
            "The completed evidence matrix now includes the formal B1-B4 evaluation, "
            "optimized dynamic MLIR and complete-library references, component ablations, "
            "shape holdout, overhead decomposition, multi-source conflicts, online soft-prior "
            "calibration, f32/f64 Contracts, a physical K230 run, and an imported i9-14900 "
            "cross-host run. No pending hardware run remains for the current thesis boundary. "
            "A broader publication claim would still benefit from additional independent "
            "hosts or backends, arbitrary layout/stride coverage, multithreaded evaluation, "
            "and larger end-to-end workloads."
        )
    elif k230["body_eligible"]:
        remaining_gap = (
            "The primary packages now include the Chapter 6 formal B1-B4 evaluation, "
            "optimized dynamic MLIR and complete-BLIS references, component ablations, "
            "shape holdout, overhead decomposition, multi-source fact conflicts, online "
            "soft-prior calibration, completed Chapter 3 author signoff, and physical K230 "
            "cross-architecture measurements. A returned 14900-series cross-host run remains "
            "the main optional extension for a broader publication claim."
        )
    else:
        remaining_gap = (
            "The primary packages now include the Chapter 6 formal B1-B4 evaluation, "
            "optimized dynamic MLIR and complete-BLIS references, component ablations, "
            "shape holdout, overhead decomposition, multi-source fact conflicts, online "
            "soft-prior calibration, and completed Chapter 3 author signoff. The K230 static "
            "ELF package is ready, but physical-board execution and CSV import are still "
            "required before any cross-architecture performance or transfer claim. "
            "Second-dtype and additional-host studies remain optional extensions."
        )
    if same_pool["body_eligible"]:
        remaining_gap += (
            " The strict same-pool calibrated-prior protocol is complete on both the "
            "i7-10750H and i9-14900. The i7 gain does not replicate significantly on "
            "the i9, so the separately declared two-environment acceptance gate fails."
        )
    if termination["body_eligible"]:
        remaining_gap += (
            " The termination ablation shows no statistically supported increment from "
            "the current BLIS-derived soft performance features beyond target-data "
            "calibration, and the measured calibration cost does not amortize in the "
            "12-workload horizon. A second BLIS Haswell microkernel Contract is validated, "
            "but that same-library result is not itself an independent backend."
        )
    if external["body_eligible"]:
        remaining_gap += (
            " The OpenBLAS/RV64GCV package supplies one independent library/ISA backend "
            "integration on K230; broader backend generality still requires another "
            "independent package or device."
        )
    lines = [
        "# Thesis Paper Evidence Catalog",
        "",
        "> Generated from `data/paper_evidence_selection.json`. The catalog screens evidence for writing; raw artifacts remain in their original experiment packages.",
        "",
        "## Selection Rules",
        "",
        "- Primary evidence must have a reproducible command, machine-readable results, correctness checks, and an explicit claim boundary.",
        "- Supporting evidence may explain the pipeline, but it must not replace a newer frozen dataset for quantitative claims.",
        "- Historical RVV and native-C++ artifacts are retained for traceability and appendices, not mixed into the x86 BLIS result set.",
        "- Extracted Section 4.5 files are reference material, not a claimed local reproduction.",
        "",
        "## Summary",
        "",
        "| Tier | Count | Writing role |",
        "|---|---:|---|",
        f"| `primary_main_text` | {counts['primary_main_text']} | Main method and measured claims |",
        f"| `supporting_main_text` | {counts['supporting_main_text']} | Pipeline/background support |",
        f"| `appendix_only` | {counts['appendix_only']} | Historical or exploratory evidence |",
        f"| `reference_only` | {counts['reference_only']} | External-paper interface reference |",
        "",
        "## Main-text Evidence",
        "",
        "| Experiment | Tier | Recommended sections | Decision |",
        "|---|---|---|---|",
    ]
    for entry in entries:
        if not entry["body_eligible"]:
            continue
        sections = "; ".join(entry["recommended_sections"])
        lines.append(
            f"| `{entry['id']}` | `{entry['tier']}` | {sections} | {entry['decision']} |"
        )
    lines.extend(["", "## Claim Map", ""])
    for entry in entries:
        if not entry["body_eligible"]:
            continue
        lines.extend([f"### `{entry['id']}`", ""])
        lines.extend(f"- {claim}" for claim in entry["usable_claims"])
        lines.append("- Evidence: " + ", ".join(f"`{path}`" for path in entry["evidence_files"]))
        lines.append("")
    lines.extend([
        "## Excluded From Main Empirical Argument",
        "",
        "| Experiment | Tier | Reason |",
        "|---|---|---|",
    ])
    for entry in entries:
        if entry["body_eligible"]:
            continue
        lines.append(f"| `{entry['id']}` | `{entry['tier']}` | {entry['decision']} |")
    lines.extend([
        "", "## Remaining Formal Evidence Gap", "",
        remaining_gap,
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    data = load_and_validate()
    OUTPUT.write_text(render(data), encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "entries": len(data["entries"]),
        "output": str(OUTPUT),
    }, indent=2))


if __name__ == "__main__":
    main()
