#!/usr/bin/env python3
"""Generate chapter 3 tables, quality report, provenance, and artifact index."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter
from pathlib import Path

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent


FACT_DESCRIPTIONS = {
    "fact_id": "Globally unique field-level fact identifier",
    "operator": "Source operator semantic category",
    "dtype": "Element data type",
    "architecture": "Knowledge-source architecture",
    "library": "Source library",
    "version": "Immutable source revision",
    "source_file": "Source path relative to the library root",
    "source_line": "One-based source line",
    "source_symbol": "Owning source symbol",
    "raw_value": "Value as extracted or deterministically decoded",
    "normalized_field": "Canonical field name",
    "normalized_value": "Canonical typed value",
    "applicability": "Operation, machine, feature, and thread scope",
    "evidence_level": "E1-E5 evidence grade",
    "extraction_mode": "Automatic, derived, manual, or empirical",
    "verification_status": "Machine/human verification state",
    "notes": "Ambiguity or derivation note",
}

CONTRACT_DESCRIPTIONS = {
    "kernel_id": "Unique target-kernel Contract identifier",
    "dtype": "Kernel element data type",
    "isa": "Required instruction-set features",
    "mr": "Fixed microkernel row extent",
    "nr": "Fixed microkernel column extent",
    "k_constraint": "K minimum, step, and remainder behavior",
    "input_layout": "A/B layout expected at the kernel boundary",
    "output_layout": "Preferred output storage",
    "stride": "Stride requirements carried by the ABI",
    "alignment": "Known alignment requirements and uncertainty state",
    "packing": "Packing requirements for direct invocation",
    "tail_policy": "Kernel behavior versus adapter compensation",
    "call_convention": "Callable ABI",
    "fallback_path": "Execution path when direct/adapt is unavailable",
    "kernel_requirements": "Conditions intrinsic to the kernel",
    "adapter_capabilities": "Conditions compensable outside the kernel",
    "verification_status": "Source review status",
}


def write_table(base: Path, headers: list[str], rows: list[list[object]]) -> None:
    base.parent.mkdir(parents=True, exist_ok=True)
    with base.with_suffix(".csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    base.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def find_observed_anchor(project: Path) -> dict | None:
    raw = project / "raw" / "preliminary_aot.csv"
    if not raw.exists():
        return None
    with raw.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["case_id"] == "anchor_192x256x256_anchor":
                return row
    return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project = args.project.resolve()
    facts_doc = json.loads((project / "data" / "facts.json").read_text())
    facts = facts_doc["facts"]
    contracts = yaml.safe_load((project / "data" / "microkernel_contracts.yaml").read_text())["contracts"]
    rules = yaml.safe_load((project / "data" / "expert_rules.yaml").read_text())["rules"]

    write_table(
        project / "tables" / "table3-1_fact_schema",
        ["Field", "Type", "Definition"],
        [[field, "required", description] for field, description in FACT_DESCRIPTIONS.items()],
    )
    write_table(
        project / "tables" / "table3-2_contract_schema",
        ["Field", "Type", "Definition"],
        [[field, "required", description] for field, description in CONTRACT_DESCRIPTIONS.items()],
    )
    write_table(
        project / "tables" / "table3-3_rule_schema_examples",
        ["Rule ID", "Category", "Strength", "Priority", "Evidence", "Action"],
        [
            [
                rule["rule_id"],
                rule["category"],
                rule["strength"],
                rule["priority"],
                rule["evidence_level"],
                rule["action"],
            ]
            for rule in rules
        ],
    )

    required_fields = set(FACT_DESCRIPTIONS)
    complete = sum(required_fields <= set(fact) for fact in facts)
    verification = read_csv(project / "verification" / "manual_verification.csv")
    ambiguities = read_csv(project / "data" / "ambiguities.csv")
    quality = {
        "fact_count": len(facts),
        "schema_complete_records": complete,
        "field_coverage_ratio": complete / len(facts),
        "source_traceability_ratio": sum(bool(f["source_file"] and f["source_line"]) for f in facts) / len(facts),
        "evidence_levels": dict(Counter(f["evidence_level"] for f in facts)),
        "extraction_modes": dict(Counter(f["extraction_mode"] for f in facts)),
        "verification_cases": len(verification),
        "machine_check_pass_ratio": sum(row["machine_check"] == "pass" for row in verification) / len(verification),
        "human_signoff_ratio": sum(row["human_status"] == "verified" for row in verification) / len(verification),
        "open_ambiguities": len(ambiguities),
    }
    reports = project / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (project / "verification" / "extraction_coverage.json").write_text(
        json.dumps(quality, indent=2) + "\n", encoding="utf-8"
    )
    quality_lines = [
        "# Fact Extraction Quality and Verification Status",
        "",
        f"- Atomic Fact records: **{quality['fact_count']}**",
        f"- Required-field coverage: **{quality['field_coverage_ratio']:.1%}**",
        f"- Source traceability: **{quality['source_traceability_ratio']:.1%}**",
        f"- Machine verification pass ratio: **{quality['machine_check_pass_ratio']:.1%}**",
        f"- Human signoff ratio: **{quality['human_signoff_ratio']:.1%}**",
        f"- Open ambiguities: **{quality['open_ambiguities']}**",
        "",
        "Machine checks verify extraction consistency and source locations. They do not replace",
        (
            "the human review requested by the thesis protocol. All source-backed review rows are "
            "marked `verified` following explicit thesis-author confirmation."
            if quality["human_signoff_ratio"] == 1.0
            else "the human review requested by the thesis protocol; unsigned rows remain explicitly `pending_signoff`."
        ),
        "",
    ]
    (reports / "extraction_quality.md").write_text("\n".join(quality_lines), encoding="utf-8")

    f32 = next(item for item in contracts if item["dtype"] == "f32")
    source_facts = {
        fact["normalized_field"]: fact
        for fact in facts
        if fact["dtype"] == "f32"
    }
    observed = find_observed_anchor(project)
    provenance = {
        "case_id": "anchor_192x256x256_f32",
        "source": {
            "file": source_facts["kernel_symbol"]["source_file"],
            "line": source_facts["kernel_symbol"]["source_line"],
            "symbol": source_facts["kernel_symbol"]["normalized_value"],
        },
        "raw_facts": {
            field: source_facts[field]["raw_value"]
            for field in ("kernel_symbol", "mr", "nr", "mc", "kc", "nc", "pack_kernel")
        },
        "normalized_fact_ids": [source_facts[field]["fact_id"] for field in ("mr", "nr", "mc", "kc", "nc")],
        "contract_id": f32["kernel_id"],
        "rule_ids": [rule["rule_id"] for rule in rules],
        "task": {"operation": "linalg.matmul", "dtype": "f32", "m": 192, "k": 256, "n": 256},
        "candidate_domain": {"tile_m": "multiples of 6", "tile_n": "multiples of 16", "tile_k": "bounded by 256"},
        "transform_parameters": {"tile_m": 24, "tile_n": 32, "tile_k": 64, "vectorize": True, "packing_required_for_direct": True},
        "predicted_contract_path": "direct",
        "observed_preliminary_path": observed["execution_path"] if observed else "not_yet_measured",
        "observed_microkernel_replaced": observed["microkernel_replaced"] if observed else "not_yet_measured",
        "boundary_note": "The preliminary Transform template does not implement packing or BLIS replacement, so a contract-direct candidate is observed as fallback.",
    }
    provenance_dir = project / "provenance"
    provenance_dir.mkdir(parents=True, exist_ok=True)
    (provenance_dir / "anchor_192x256x256.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    provenance_lines = [
        "# End-to-End Provenance Case",
        "",
        "`Source Line -> Raw Fact -> Normalized Fact -> Contract -> Rule -> Candidate Domain -> Transform Parameters`",
        "",
        f"- Source: `{provenance['source']['file']}:{provenance['source']['line']}`",
        f"- Kernel: `{provenance['source']['symbol']}`",
        f"- Contract: `{provenance['contract_id']}`",
        "- Task: `linalg.matmul`, f32, M=192, K=256, N=256",
        "- Parameters: `tile_m=24, tile_n=32, tile_k=64, vectorize=true`",
        f"- Contract prediction: `{provenance['predicted_contract_path']}`",
        f"- Observed preliminary path: `{provenance['observed_preliminary_path']}`",
        f"- Observed BLIS replacement: `{provenance['observed_microkernel_replaced']}`",
        "",
        provenance["boundary_note"],
        "",
        "## Alignment with CGO 2025 Section 4.5",
        "",
        "The alignment is at the parameter interface, evaluator pipeline, and evidence",
        "schema; it is not an assertion that the two workloads or measured speedups are",
        "equivalent. Section 4.5 evaluates a fixed-shape `linalg.batch_matmul` with",
        "`B=6, M=196, N=256, K=2304`, whereas this provenance case evaluates a",
        "non-batched `linalg.matmul` with `M=192, N=256, K=256`.",
        "",
        "| Section 4.5 parameter | Chapter 3 projection |",
        "|---|---|",
        "| `tile0` (batch) | omitted because the payload has no batch dimension |",
        "| `tile1` (M) | `tile_m=24` |",
        "| `tile2` (N) | `tile_n=32` |",
        "| `tile3` (K) | `tile_k=64` |",
        "| `do_vect` | `vectorize=true` |",
        "",
        "The resulting aligned evaluator chain is:",
        "",
        "```text",
        "expert-space config -> Transform instance -> LLVM IR -> clang AOT",
        "-> compile status -> correctness status -> observed execution path",
        "-> runtime/GFLOP/s feedback",
        "```",
        "",
        "Section 4.5's `Valid` field only indicates evaluator/build feasibility. This",
        "case therefore does not map `Valid=1` to correctness or replacement. It records",
        "`compile_status=pass`, `correctness_status=pass`, `predicted_path=direct`,",
        "`observed_path=fallback`, and `microkernel_replaced=false` independently. The",
        "paper's fixed four-lane vectorization condition is also not imported: the lane",
        "width is derived from the Haswell f32 contract and is eight here.",
        "",
        "The current seeded-random sampler and a future BaCO adapter can consume the same",
        "evaluator contract. Replacing the tuner does not change this frozen anchor or",
        "retroactively alter its raw measurements.",
        "",
    ]
    (reports / "provenance_case.md").write_text("\n".join(provenance_lines), encoding="utf-8")

    raw_path = project / "raw" / "preliminary_aot.csv"
    if raw_path.exists():
        raw_rows = read_csv(raw_path)
        samples = [row for row in raw_rows if row["candidate_kind"] != "baseline"]
        attempted = [row for row in raw_rows if row["candidate_kind"] == "sample"]
        passed = [row for row in attempted if row["correctness_status"] == "pass"]
        normalized = [float(row["normalized_to_shape_best"]) for row in passed]
        speedups = [float(row["speedup_vs_default"]) for row in passed]
        compile_ms = [float(row["native_compile_ms"]) for row in passed]
        spaces = read_csv(project / "processed" / "preliminary_space_sizes.csv")
        reductions = [float(row["reduction_ratio"]) for row in spaces]
        status_counts = Counter(row["status"] for row in samples)
        results_lines = [
            "# 第3章预备实证结果摘要",
            "",
            "> 本报告只用于证明研究问题值得研究，不替代第6章正式实验。",
            "",
            "## 实验范围",
            "",
            f"- 工作负载：{len(spaces)} 个 `linalg.matmul` f32 shape。",
            f"- 通用参数空间：每个 shape 原始空间 {spaces[0]['raw_space_size']} 个候选。",
            f"- 实际测量：{len(attempted)} 个 Transform/AOT 候选；另有 {status_counts['STATIC_REJECT']} 个策略拒绝。",
            "- 流程：Transform Dialect → LLVM IR → clang AOT → 正确性与性能测量。",
            "",
            "## 可直接引用的预备结果",
            "",
            f"- 合法空间缩减比例为 {min(reductions):.1%}—{max(reductions):.1%}；小 K shape 的缩减最大。",
            f"- 已尝试候选编译成功率为 {sum(row['compile_status'] == 'pass' for row in attempted) / len(attempted):.1%}。",
            f"- 已编译候选数值正确率为 {sum(row['correctness_status'] == 'pass' for row in attempted) / len(attempted):.1%}。",
            f"- 实际 BLIS microkernel 替换率为 {sum(row['microkernel_replaced'] == 'true' for row in passed) / len(passed):.1%}。",
            f"- 正确候选 fallback 比例为 {sum(row['execution_path'] == 'fallback' for row in passed) / len(passed):.1%}。",
            f"- 相对各 shape 最优样本的归一化性能中位数为 {statistics.median(normalized):.3f}，范围为 {min(normalized):.3f}—{max(normalized):.3f}。",
            f"- 相对未分块默认路径的 speedup 中位数为 {statistics.median(speedups):.3f}×。",
            f"- native 编译时间中位数为 {statistics.median(compile_ms):.1f} ms/候选。",
            "",
            "## 解释边界",
            "",
            "当前 Transform 模板仅实例化 tiling 与可选 vectorization，尚未实现 BLIS packing/replacement adapter。",
            "因此 0% replacement 和 100% fallback 是实际系统边界，不是 checker 模拟值，也不能用于断言专家空间",
            "的最终性能。预备实验能够支持的结论仅是：通用空间存在策略不兼容候选、性能密度较低，且现有",
            "Transform 后端尚不能利用已建模的 direct microkernel Contract。",
            "",
        ]
        (reports / "chapter3_preliminary_results.md").write_text("\n".join(results_lines), encoding="utf-8")

    required = [
        "research-scope.md",
        "data/facts.json",
        "data/facts.csv",
        "data/microkernel_contracts.yaml",
        "data/expert_rules.yaml",
        "verification/human_signoffs.json",
        "verification/manual_verification.csv",
        "verification/validation_report.md",
        "reports/extraction_quality.md",
        "reports/provenance_case.md",
        "reports/chapter3_preliminary_results.md",
        "tables/table3-1_fact_schema.md",
        "tables/table3-2_contract_schema.md",
        "tables/table3-3_rule_schema_examples.md",
        "figures/fig3-1_preliminary_distribution.pdf",
        "figures/fig3-2_fact_contract_rule_boundary.pdf",
        "figures/fig3-3_evidence_normalization_flow.pdf",
        "figures/fig3-4_provenance_case.pdf",
        "figures/legends.md",
        "figures/qa_report.md",
    ]
    index_lines = ["# Chapter 3 Artifact Index", "", "| Artifact | Status |", "|---|---|"]
    for relative in required:
        index_lines.append(f"| `{relative}` | {'ready' if (project / relative).exists() else 'pending'} |")
    index_lines.extend(
        [
            "",
            (
                "Human signoff is complete for all source-backed review rows; the durable author confirmation is stored "
                "in `verification/human_signoffs.json`. Machine and human checks remain separate fields."
                if quality["human_signoff_ratio"] == 1.0
                else "Unsigned review rows remain explicit in `verification/manual_verification.csv`; machine checks must not be relabeled as human review."
            ),
            "",
        ]
    )
    (project / "chapter3_artifact_index.md").write_text("\n".join(index_lines), encoding="utf-8")
    print("generated chapter 3 tables, quality report, provenance, and artifact index")


if __name__ == "__main__":
    main()
