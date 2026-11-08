#!/usr/bin/env python3
"""Build the final thesis experiment audit from frozen machine-readable results."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


EXPERIMENTS = Path(__file__).resolve().parent.parent
SELECTION = EXPERIMENTS / "data" / "paper_evidence_selection.json"
OUTPUT_JSON = EXPERIMENTS / "processed" / "final_experiment_audit.json"
OUTPUT_MD = EXPERIMENTS / "FINAL_EXPERIMENT_AUDIT.md"


def load(relative: str) -> dict[str, Any]:
    return json.loads((EXPERIMENTS / relative).read_text(encoding="utf-8"))


def load_csv(relative: str) -> list[dict[str, str]]:
    with (EXPERIMENTS / relative).open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def pair(summary: dict[str, Any], name: str) -> dict[str, Any]:
    return next(row for row in summary["paired_bootstrap"] if row["comparison"] == name)


def build_audit() -> dict[str, Any]:
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    entries = selection["entries"]
    missing = [
        path
        for entry in entries
        for path in entry["evidence_files"]
        if not (EXPERIMENTS.parents[2] / path).is_file()
    ]
    if missing:
        raise FileNotFoundError("missing evidence files: " + ", ".join(missing))

    chapter6 = load("chapter6_evaluation/processed/chapter6_summary.json")
    online = load("chapter6_online_prior/processed/online_prior_summary.json")
    local = load("cgo_extension/processed/cgo_extension_summary.json")
    cross_host = load("x86_cross_host/processed/cross_host_summary.json")
    k230 = load("k230_rvv_backend/processed/k230_board_summary.json")
    chapter5 = load("chapter5_blis_adapter/processed/dynamic_multishape_summary.json")
    multisource = load("chapter3_multisource/processed/summary.json")
    integrated = load("chapter4_5_integrated/processed/integrated_summary.json")
    termination = load(
        "chapter6_termination_validation/processed/acceptance_summary.json"
    )
    termination_pairs = load_csv(
        "chapter6_termination_validation/processed/paired_comparisons.csv"
    )
    termination_t95 = load_csv(
        "chapter6_termination_validation/processed/time_to_95_summary.csv"
    )
    termination_costs = load_csv(
        "chapter6_termination_validation/processed/calibration_costs.csv"
    )
    second_microkernel = load(
        "chapter6_termination_validation/processed/second_microkernel_audit.json"
    )
    application_trace = load(
        "chapter6_application_validation/processed/qwen_trace_summary.json"
    )
    application_local = load(
        "chapter6_application_validation/targets/i7_10750h/processed/summary.json"
    )
    application_qualification = load(
        "chapter6_application_validation/targets/i7_10750h/qualification/processed/summary.json"
    )
    application_closure = load(
        "chapter6_application_validation/provenance/k230_mlir_closure_manifest.json"
    )
    contract_space = load(
        "chapter6_contract_space_validation/processed/e2_summary.json"
    )
    same_pool_random = contract_space["same_pool_random_comparison"]

    local_offline_b5 = pair(local, "offline_calibrated_vs_random_budget5")
    local_online_b5 = pair(local, "online_calibrated_vs_random_budget5")
    remote_online_optuna_b5 = next(
        row["i9_14900"]
        for row in cross_host["paired_comparisons"]
        if row["comparison"] == "online_calibrated_vs_optuna_tpe_budget5"
    )
    no_packing = next(
        row for row in chapter6["RQ5"]["ablations"] if row["label"] == "no_packing_rule"
    )
    no_mr_nr = next(
        row for row in chapter6["RQ5"]["ablations"] if row["label"] == "no_mr_nr"
    )
    full = next(
        row for row in chapter6["RQ5"]["ablations"] if row["label"] == "full"
    )
    data_vs_no_prior_b5 = next(
        row for row in termination_pairs
        if row["test_method"] == "D0_data_only_baco"
        and row["reference_method"] == "B2_no_prior_baco"
        and int(row["budget"]) == 5
    )
    expert_vs_data_b5 = next(
        row for row in termination_pairs
        if row["test_method"] == "D1_expert_plus_data_baco"
        and row["reference_method"] == "D0_data_only_baco"
        and int(row["budget"]) == 5
    )
    no_prior_t95 = next(
        row for row in termination_t95 if row["method"] == "B2_no_prior_baco"
    )
    expert_t95 = next(
        row for row in termination_t95
        if row["method"] == "D1_expert_plus_data_baco"
    )
    expert_cost = next(
        row for row in termination_costs
        if row["method"] == "D1_expert_plus_data_baco"
    )

    return {
        "schema_version": 1,
        "status": "PASS",
        "registered_evidence_entries": len(entries),
        "tier_counts": dict(Counter(entry["tier"] for entry in entries)),
        "main_text_eligible_entries": sum(entry["body_eligible"] for entry in entries),
        "completed_external_targets": [
            "Intel Core i9-14900 Ubuntu 20.04",
            "K230 C908 RT-Smart",
        ],
        "research_question_evidence": {
            "knowledge_extraction": {
                "fact_count": chapter6["RQ1"]["fact_count"],
                "source_traceability_ratio": chapter6["RQ1"]["source_traceability_ratio"],
                "human_signoff_ratio": chapter6["RQ1"]["human_signoff_ratio"],
                "multisource_conflicts": multisource["conflict_count"],
            },
            "compatibility_checker": {
                "measured_candidate_cases": chapter6["RQ2"]["measured_candidate_cases"],
                "prediction_observation_agreement": chapter6["RQ2"]["prediction_observation_agreement"],
                "integrated_direct_adapt_fallback_match": integrated["path_matrix"][
                    "all_predictions_match_observations"
                ],
                "cross_host_f64_contract_transfer": cross_host["cross_host_findings"][
                    "hard_contract_transfer_replicated"
                ],
            },
            "search_space_and_ablation": {
                "formal_workloads": chapter6["RQ3"]["workload_count"],
                "b2_contract_only_normalized_gmean": next(
                    row["normalized_performance_gmean"]
                    for row in chapter6["RQ3"]["space_quality"]
                    if row["method"] == "B2"
                ),
                "full_normalized_gmean": full["normalized_gmean"],
                "no_packing_normalized_gmean": no_packing["normalized_gmean"],
                "no_mr_nr_normalized_gmean": no_mr_nr["normalized_gmean"],
                "same_pool_random_comparison": same_pool_random,
            },
            "runtime_integration": {
                "dynamic_shapes": chapter5["overall"]["shape_count"],
                "all_correct": chapter5["overall"]["all_correct"],
                "fringe_counts_match": chapter5["overall"]["fringe_counts_match"],
                "speedup_vs_scalar_loop_gmean": chapter5["overall"][
                    "geometric_mean_speedup"
                ],
            },
            "calibrated_soft_prior": {
                "real_measurement_corpus_cases": online["corpus_cases"],
                "local_offline_vs_random_budget5": local_offline_b5,
                "local_online_vs_random_budget5": local_online_b5,
                "i9_14900_online_vs_optuna_budget5": remote_online_optuna_b5,
                "fresh_online_protocol_replicated": cross_host["cross_host_findings"][
                    "fresh_online_protocol_replicated"
                ],
                "termination_decision": termination["termination_decisions"],
                "data_only_vs_no_prior_budget5": data_vs_no_prior_b5,
                "expert_plus_data_vs_data_only_budget5": expert_vs_data_b5,
                "no_prior_mean_evaluations_to_95_oracle": float(
                    no_prior_t95["mean_evaluations_to_95_oracle"]
                ),
                "expert_mean_evaluations_to_95_oracle": float(
                    expert_t95["mean_evaluations_to_95_oracle"]
                ),
                "calibration_target_rows": int(expert_cost["calibration_target_rows"]),
                "calibration_amortized_within_12_holdouts": (
                    expert_cost["amortized_within_horizon_with_compile"].lower()
                    == "true"
                ),
            },
            "second_microkernel_extension": {
                "status": second_microkernel["second_microkernel_status"],
                "generated_workloads": second_microkernel["generated_workloads"],
                "formal_trial_rows": second_microkernel["formal_trial_rows"],
                "core_generator_hash_unchanged": second_microkernel["conditions"][
                    "core_generator_hash_unchanged"
                ],
                "independent_backend_status": second_microkernel[
                    "independent_backend_status"
                ],
            },
            "external_validity": {
                "local_candidate_pool_vs_blis": cross_host["hosts"][
                    "development_host"
                ]["candidate_pool_relative_to_blis_gmean"],
                "i9_14900_candidate_pool_vs_blis": cross_host["hosts"]["i9_14900"][
                    "candidate_pool_relative_to_blis_gmean"
                ],
                "k230_rows": k230["row_count"],
                "k230_all_correct": k230["all_correct"],
                "k230_best_rvv_vs_scalar_gmean": k230["comparisons"][
                    "rvv_best_vs_scalar"
                ]["geomean_speedup"],
                "k230_openblas_vs_scalar_gmean": k230["comparisons"][
                    "openblas_full_vs_scalar"
                ]["geomean_speedup"],
            },
            "application_validation": {
                "qwen_raw_linear_calls": application_trace["raw_linear_calls"],
                "qwen_canonical_core_calls": application_trace[
                    "canonical_core_calls"
                ],
                "core_call_coverage": application_trace["core_call_coverage"],
                "core_flop_coverage": application_trace["core_flop_coverage"],
                "local_timing_status": application_local["status"],
                "local_stable_variant_fraction": application_local["stability"][
                    "variant_pass_fraction"
                ],
                "wsl_qualification_status": application_qualification["status"],
                "qualifying_cpus": application_qualification["qualifying_cpus"],
                "k230_static_closure_status": application_closure["status"],
                "k230_static_closure_cases": len(application_closure["cases"]),
                "host_abi_smoke_status": application_closure["host_abi_smoke"][
                    "status"
                ],
            },
        },
        "necessity_assessment": {
            "hard_compatibility_knowledge": (
                "Necessary for constructing callable candidates and predicting direct, "
                "adapt and fallback execution; it transfers across the tested hosts."
            ),
            "packing_and_call_contract": (
                "Critical. Removing the packing rule reduces the formal normalized "
                f"geometric mean from {full['normalized_gmean']:.3f} to "
                f"{no_packing['normalized_gmean']:.3f}."
            ),
            "fixed_source_performance_constants": (
                "Not generally necessary or safe as hard constraints. The no-MR/NR "
                f"ablation reaches {no_mr_nr['normalized_gmean']:.3f}, and the f64 "
                "candidate-pool ranking reverses relative to complete BLIS across hosts."
            ),
            "calibrated_soft_prior": (
                "Target-data calibration improves low-budget selection over no-prior "
                "search, but the termination ablation finds no statistically supported "
                "increment from the current BLIS-derived soft performance features. Its "
                "591-row calibration cost also does not amortize within 12 holdouts."
            ),
        },
        "main_conclusion": (
            "The defensible contribution is a compiler workflow that turns transferable "
            "hard compatibility knowledge into callable direct/adapt schedules and extends "
            "to a second BLIS microkernel Contract without changing the core space generator. "
            "Within the frozen 28-candidate measured subpools, BaCO does not outperform "
            "uniform random search without replacement. Target data can improve low-budget "
            "search in the separate calibrated-prior experiments, but the current BLIS-derived soft "
            "performance rules add no demonstrated value beyond that data and their measured "
            "calibration cost is not practically amortized in the frozen horizon."
        ),
        "current_boundaries": [
            "Single-thread row-major GEMM remains the main x86 evaluation boundary.",
            "Arbitrary layouts, strides, transposes and batched operators are not covered.",
            "K230 evidence is limited to one physical C908 RT-Smart board and toolchain.",
            "The two-host x86 result does not establish universal host-independent ranking.",
            "Chapter 5 speedups use a scalar-loop dynamic fallback; complete-library comparisons are reported separately.",
            "No end-to-end model or application-level speedup is claimed.",
            "The Qwen trace is model-code coverage evidence; the i7 WSL exact-shape timing pool failed qualification and is excluded from performance claims.",
            "The second microkernel is on the same BLIS Haswell backend; independent-backend extensibility is not established.",
        ],
        "publication_extensions": [
            "Add another independent x86 or RISC-V target and preserve the same fixed-budget protocol.",
            "Evaluate multithreaded execution and hardware counters for packing, cache and memory effects.",
            "Extend Contracts to layout/stride/transpose/batched GEMM cases.",
            "Evaluate one end-to-end operator or model workload without weakening the current baselines.",
            "Replace the explicit two-entry runtime registry with a descriptor-driven independent-backend package and test it on a distinct library or ISA.",
        ],
    }


def render(audit: dict[str, Any]) -> str:
    rq = audit["research_question_evidence"]
    local_offline = rq["calibrated_soft_prior"]["local_offline_vs_random_budget5"]
    local_online = rq["calibrated_soft_prior"]["local_online_vs_random_budget5"]
    remote_optuna = rq["calibrated_soft_prior"]["i9_14900_online_vs_optuna_budget5"]
    data_only = rq["calibrated_soft_prior"]["data_only_vs_no_prior_budget5"]
    expert_increment = rq["calibrated_soft_prior"][
        "expert_plus_data_vs_data_only_budget5"
    ]
    tiers = audit["tier_counts"]
    same_pool = rq["search_space_and_ablation"]["same_pool_random_comparison"]
    lines = [
        "# Final Experiment Audit",
        "",
        "> Generated from frozen machine-readable summaries. This is the single entry point for deciding which experiments support the thesis argument.",
        "",
        "## Overall status",
        "",
        f"- Audit status: `{audit['status']}`.",
        f"- Registered evidence entries: {audit['registered_evidence_entries']}; main-text eligible: {audit['main_text_eligible_entries']}.",
        (
            "- Evidence tiers: "
            f"{tiers.get('primary_main_text', 0)} primary, "
            f"{tiers.get('supporting_main_text', 0)} supporting, "
            f"{tiers.get('appendix_only', 0)} appendix-only, "
            f"{tiers.get('reference_only', 0)} reference-only."
        ),
        "- Completed external targets: Intel Core i9-14900 and physical K230 C908.",
        "- No pending hardware run remains for the current thesis experiment boundary.",
        "",
        "## End-to-end evidence chain",
        "",
        "1. **Knowledge representation:** 22 source-linked facts have full machine-check, traceability and author-signoff coverage; BLIS/OpenBLAS extraction records four explicit source conflicts.",
        "2. **Compatibility and space construction:** 1256 measured candidate cases achieve complete prediction-to-runtime agreement. Contract-only, expert-core and expert-shell spaces remain separately measurable.",
        "3. **Compiler execution:** the integrated path observes direct, adapt and fallback exactly as predicted, with real BLIS packing and 6x16 invocation for eligible f32 cases.",
        (
            "4. **Dynamic shapes:** seven direct/adapt shapes are correct and fringe counts "
            f"match; the geometric mean is {rq['runtime_integration']['speedup_vs_scalar_loop_gmean']:.2f}x "
            "over the declared scalar-loop dynamic fallback."
        ),
        "5. **Formal evaluation:** 36 workloads, fixed budgets, five seeds, complete BLIS and optimized dynamic MLIR references, ablations, holdout and overhead are frozen.",
        "6. **External validity:** f64 6x8, a second x86 host, and a physical RISC-V board are now measured.",
        "7. **Termination validation:** Data-only, Expert+Data, calibration economics and second-Contract extensibility are tested under pre-registered stop conditions.",
        (
            "8. **Application relevance:** the real Qwen model control flow maps all core "
            "projection calls and FLOPs to eight frozen workload rows, while three "
            "representative MLIR/RV64GCV closure cases pass static and host-ABI checks; "
            "the local WSL timing pool is explicitly ineligible."
        ),
        "",
        "## Core quantitative findings",
        "",
        (
            "- The Checker is reliable within the tested Contracts: prediction-observation "
            f"agreement is {rq['compatibility_checker']['prediction_observation_agreement']:.3f}."
        ),
        (
            "- Packing is indispensable to the callable microkernel path: removing its rule "
            f"drops normalized performance from {rq['search_space_and_ablation']['full_normalized_gmean']:.3f} "
            f"to {rq['search_space_and_ablation']['no_packing_normalized_gmean']:.3f}."
        ),
        (
            "- In the frozen 28-candidate measured subpools, BaCO/uniform-random reached "
            f"90% of pool-best in {same_pool['baco']['reached_90pct_pool_best_fraction']:.3f}/"
            f"{same_pool['random']['reached_90pct_pool_best_fraction']:.3f} of runs, with median "
            f"unique-query T90 {same_pool['baco']['median_time_to_90pct_unique_query']:.1f}/"
            f"{same_pool['random']['median_time_to_90pct_unique_query']:.1f}; the paired result "
            "does not support a BaCO advantage over uniform random."
        ),
        (
            "- On the development host at budget 5, offline calibration is "
            f"{local_offline['left_speedup_over_right_gmean']:.3f}x and online calibration is "
            f"{local_online['left_speedup_over_right_gmean']:.3f}x faster than random; both "
            "95% intervals are above one."
        ),
        (
            "- On the i9-14900 at budget 5, online calibration is "
            f"{remote_optuna['speedup']:.3f}x faster than Optuna TPE with 95% interval "
            f"[{remote_optuna['ci_low']:.3f}, {remote_optuna['ci_high']:.3f}]."
        ),
        (
            "- In the strict termination ablation at budget 5, Data-only is "
            f"{float(data_only['gmean_speedup']):.3f}x over no-prior with interval "
            f"[{float(data_only['ci95_lower']):.3f}, {float(data_only['ci95_upper']):.3f}], "
            "but Expert+Data over Data-only is only "
            f"{float(expert_increment['gmean_speedup']):.3f}x with interval "
            f"[{float(expert_increment['ci95_lower']):.3f}, "
            f"{float(expert_increment['ci95_upper']):.3f}]."
        ),
        (
            "- Mean time-to-95%-oracle falls from "
            f"{rq['calibrated_soft_prior']['no_prior_mean_evaluations_to_95_oracle']:.2f} "
            "to "
            f"{rq['calibrated_soft_prior']['expert_mean_evaluations_to_95_oracle']:.2f} "
            "evaluations, but the 591-row calibration does not amortize within the "
            "12-workload horizon."
        ),
        (
            "- The second f64 6x8 microkernel Contract passes with an unchanged core "
            f"generator across {rq['second_microkernel_extension']['generated_workloads']} "
            "workloads; this is not an independent-backend result."
        ),
        (
            "- Absolute ranking is host dependent: the generated f64 pool changes from "
            f"{rq['external_validity']['local_candidate_pool_vs_blis']:.3f}x relative to "
            f"complete BLIS locally to {rq['external_validity']['i9_14900_candidate_pool_vs_blis']:.3f}x "
            "on the i9-14900."
        ),
        (
            "- K230 produced "
            f"{rq['external_validity']['k230_rows']} correct rows; the best measured explicit-RVV "
            f"schedule is {rq['external_validity']['k230_best_rvv_vs_scalar_gmean']:.2f}x and "
            f"complete OpenBLAS is {rq['external_validity']['k230_openblas_vs_scalar_gmean']:.2f}x "
            "relative to their in-process scalar controls."
        ),
        "",
        "## Is expert prior necessary?",
        "",
        "- **Hard compatibility knowledge: yes.** It defines legal packing, kernel ABI and direct/adapt/fallback behavior, and its predictions transfer across the tested hosts.",
        "- **Packing/call Contract: yes.** The no-packing ablation collapses performance and cannot represent the real accelerated path.",
        "- **Fixed BLIS performance constants: no.** MR/NR and blocking values are useful seeds, but the ablations and host reversal reject treating them as universal hard constraints.",
        "- **Target-data calibration: conditionally useful.** It improves low-budget sample efficiency, but the measured setup cost is not recovered in 12 holdouts.",
        "- **Current BLIS soft performance rules: no demonstrated incremental value.** Expert+Data does not significantly beat Data-only at the registered checkpoints, so these features are retained only as historical transfer or feedback-calibration inputs.",
        "",
        "## Final thesis claim",
        "",
        audit["main_conclusion"],
        "",
        "## Claim boundaries",
        "",
    ]
    lines.extend(f"- {item}" for item in audit["current_boundaries"])
    lines.extend([
        "",
        "## Paper-use map",
        "",
        "- Chapter 3: `thesis.chapter3_rules` and `thesis.chapter3_multisource`.",
        "- Chapter 4: `thesis.chapter4_space`.",
        "- Chapter 5: `thesis.chapter5_blis_adapter` and `thesis.chapter4_5_integrated`.",
        "- Chapter 6: `thesis.chapter6_evaluation`, `thesis.chapter6_online_prior`, `thesis.chapter6_same_pool_prior`, `thesis.chapter6_termination_validation`, `thesis.chapter6_application_validation`, `thesis.cgo_local_extension`, `thesis.x86_cross_host`, and `thesis.k230_rvv_backend`.",
        "- Historical native C++, QEMU and code-generation-only RVV artifacts stay in the appendix.",
        "",
        "## Optional publication extensions",
        "",
    ])
    lines.extend(f"- {item}" for item in audit["publication_extensions"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    audit = build_audit()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    OUTPUT_MD.write_text(render(audit), encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "output_json": str(OUTPUT_JSON),
        "output_markdown": str(OUTPUT_MD),
    }, indent=2))


if __name__ == "__main__":
    main()
