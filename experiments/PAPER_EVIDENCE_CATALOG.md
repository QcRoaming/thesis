# Thesis Paper Evidence Catalog

> Generated from `data/paper_evidence_selection.json`. The catalog screens evidence for writing; raw artifacts remain in their original experiment packages.

## Selection Rules

- Primary evidence must have a reproducible command, machine-readable results, correctness checks, and an explicit claim boundary.
- Supporting evidence may explain the pipeline, but it must not replace a newer frozen dataset for quantitative claims.
- Historical RVV and native-C++ artifacts are retained for traceability and appendices, not mixed into the x86 BLIS result set.
- Extracted Section 4.5 files are reference material, not a claimed local reproduction.

## Summary

| Tier | Count | Writing role |
|---|---:|---|
| `primary_main_text` | 11 | Main method and measured claims |
| `supporting_main_text` | 5 | Pipeline/background support |
| `appendix_only` | 5 | Historical or exploratory evidence |
| `reference_only` | 1 | External-paper interface reference |

## Main-text Evidence

| Experiment | Tier | Recommended sections | Decision |
|---|---|---|---|
| `historical.host_mlir_aot` | `supporting_main_text` | Chapter 2 baseline pipeline; Chapter 3 motivation | Use only to document the earlier generic Transform/AOT pipeline. Use Chapter 3 for frozen preliminary statistics. |
| `thesis.cgo_local_extension` | `primary_main_text` | Chapter 6 additional dtype and live tuning evaluation; Chapter 7 conclusions and limitations | Primary extension evidence for f64 Contract transfer, genuine online measurement, an equal-budget Optuna TPE baseline, and source-labelled BLIS/OpenBLAS prior ablation. Use the low-budget gains over random and naive source merging; do not claim statistically significant superiority over Optuna or cross-host generalization. |
| `thesis.chapter3_multisource` | `primary_main_text` | Chapter 3 multi-source knowledge model; Chapter 7 discussion | Primary evidence that hard compatibility knowledge and soft performance hints are separated across BLIS and OpenBLAS. Host OpenBLAS runtime validation supports extraction fidelity; backend-specific conflicts must not be collapsed into universal constants. |
| `thesis.chapter3_rules` | `primary_main_text` | Chapter 3; Chapter 6 RQ1 preliminary support | Primary evidence for Fact/Contract/Rule modeling and the eight-shape preliminary MLIR study. All 16 source-backed review cases have explicit thesis-author signoff. |
| `thesis.chapter4_5_integrated` | `primary_main_text` | Chapter 5 end-to-end implementation; Chapter 6 RQ2/RQ4 smoke evidence | Primary integration evidence that Chapter 4 candidates and BaCO callbacks now drive observed Chapter 5 direct/adapt/fallback execution. The six-point tuning data is not a formal convergence comparison. |
| `thesis.chapter4_space` | `primary_main_text` | Chapter 4; Chapter 6 RQ2-RQ3 method evidence | Primary method evidence for B1-B4 space construction, Checker decisions, provenance, complexity, and BaCO interface. Its old path examples remain observed fallback. |
| `thesis.chapter5_blis_adapter` | `primary_main_text` | Chapter 5; Chapter 6 implementation validation | Primary evidence for real packing, BLIS 6x16 invocation, fringe adaptation, and dynamic shape correctness. Performance remains preliminary because the dynamic baseline is scalar-loop. |
| `thesis.chapter6_application_validation` | `supporting_main_text` | Chapter 6 application trace and deployment closure; Chapter 7 limitations and external-validity boundary | Supporting evidence for model-code workload relevance, physical-K230 MLIR-to-RV64GCV library-adapter closure, and trace-weighted projection over completed K230 and i9-14900 exact-shape pools. The local WSL timing pool remains excluded, and all weighted values are measured-GEMM projections rather than end-to-end model latency. |
| `thesis.chapter6_contract_space_validation` | `primary_main_text` | Chapter 4 compatibility checker and schedule-space construction; Chapter 6 extensibility and economic analysis; Chapter 7 conclusions and limitations | Primary audit evidence for Contract mutation safety, canonicalized intrinsic schedule-space statistics, a frozen normalized-pool BaCO replay with a same-pool uniform-random control, quantified schema reuse boundaries and horizon-aware search economics. Separate the measured-subpool quality from the unsupported incremental advantage of BaCO, and report the pre-normalization ablation, partial cross-library generator reuse and complete-library no-break-even results. |
| `thesis.chapter6_evaluation` | `primary_main_text` | Chapter 6 formal evaluation; Chapter 7 conclusions and limitations | Primary formal evidence for RQ1-RQ6 within the single-host row-major f32 boundary. Use its B1-B4 comparison, complete-BLIS reference, ablations, holdout, overhead, and confidence intervals; do not extend the result to additional dtypes or hosts. |
| `thesis.chapter6_external_validation` | `supporting_main_text` | Chapter 6 independent-backend extensibility and target-library boundary; Appendix reproducibility and external validation protocol | The physical K230 and native i9-14900 exact-shape pools are complete. Use them as claim-eligible supporting evidence for independent OpenBLAS/RV64GCV backend integration, cross-host Contract legality, and negative complete-library performance boundaries; do not claim generated schedules outperform the complete libraries. |
| `thesis.chapter6_online_prior` | `primary_main_text` | Chapter 6 online calibration; Chapter 7 conclusions and limitations | Primary evidence for separating static source knowledge from target-calibrated soft priors. The same-host holdout shows strong offline calibration and no additional early-budget gain from online updating once the offline model is already trained; the misleading-prior control demonstrates recovery rather than guaranteed dominance. |
| `thesis.chapter6_same_pool_prior` | `primary_main_text` | Chapter 6 strict same-pool low-budget evaluation; Chapter 7 conclusions and limitations | Primary same-pool evidence that repairs the B2/B3/B4 comparison with a canonical common pool, active-parameter audit, unique-measurement budgets, holdout-safe calibration, and a shared oracle. The i7 result supports local calibrated-prior gains at budgets 5 and 10, while the completed i9 replication is inconclusive; the preregistered two-environment acceptance gate therefore fails. |
| `thesis.chapter6_termination_validation` | `primary_main_text` | Chapter 6 termination validation and calibration economics; Chapter 7 conclusions and limitations | Primary same-pool termination evidence separating target-data calibration from BLIS-derived soft performance features. Use the significant Data-only gain over no-prior, the absence of a significant Expert+Data increment, the measured non-amortization boundary, and the second f64 Contract extension. Do not call the f64 kernel an independent backend. |
| `thesis.k230_rvv_backend` | `supporting_main_text` | Cross-architecture K230 evaluation; Discussion: transferable compatibility knowledge and calibrated performance priors | Physical K230 RT-Smart measurements are available for scalar, explicit-RVV and full OpenBLAS paths across eight workloads. Use as supporting cross-architecture evidence under the recorded board configuration. |
| `thesis.x86_cross_host` | `supporting_main_text` | Chapter 6 cross-host evaluation; Chapter 7 conclusions and limitations | Supporting two-host x86 evidence under the same fixed f64 Contract, candidate domains and tuner budgets. Use the replicated compatibility checks, low-budget gains and host-dependent ranking reversal; do not claim universal x86 generalization or budget-25 tuner dominance. |

## Claim Map

### `historical.host_mlir_aot`

- The host MLIR Transform-to-AOT path compiled, ran, and checked correctness.
- Evidence: `jlq/thesis/experiments/results/mlir_aot_benchmark.csv`, `jlq/thesis/experiments/results/mlir_aot_benchmark_summary.md`

### `thesis.cgo_local_extension`

- The f64 Haswell dgemm 6x8 path passed 3132 trials over 36 shapes, with all direct/adapt predictions matching runtime observations.
- At budget 5, offline and online calibrated policies were 1.192x and 1.155x faster than random in paired geometric comparisons, with both 95% bootstrap intervals above one.
- Online calibration did not significantly outperform Optuna TPE at budget 5 or 25; all 7500 tuner objectives were fresh subprocess measurements with zero objective-cache hits.
- BLIS-only and calibrated source priors both outperformed naive BLIS/OpenBLAS merging at budget 5, while calibrated and BLIS-only performance were statistically indistinguishable.
- Evidence: `jlq/thesis/experiments/cgo_extension/processed/cgo_extension_summary.json`, `jlq/thesis/experiments/cgo_extension/processed/f64_contract_summary.json`, `jlq/thesis/experiments/cgo_extension/raw/true_online_traces.csv`, `jlq/thesis/experiments/cgo_extension/raw/optuna_traces.csv`, `jlq/thesis/experiments/cgo_extension/processed/multisource_fixed_budget.csv`, `jlq/thesis/experiments/cgo_extension/processed/paired_bootstrap_comparisons.csv`, `jlq/thesis/experiments/cgo_extension/reports/cgo_extension_results.md`, `jlq/thesis/experiments/cgo_extension/provenance/cgo_extension_manifest.json`

### `thesis.chapter3_multisource`

- BLIS and OpenBLAS expose source-linked but backend-specific microkernel, packing, layout and blocking facts.
- Cross-source conflicts motivate hard compatibility contracts plus calibratable soft performance priors.
- The pinned OpenBLAS Haswell CBLAS probe passed all four shapes and 28 real trials.
- Evidence: `jlq/thesis/experiments/chapter3_multisource/data/multisource_facts.yaml`, `jlq/thesis/experiments/chapter3_multisource/data/conflicts.yaml`, `jlq/thesis/experiments/chapter3_multisource/processed/summary.json`, `jlq/thesis/experiments/chapter3_multisource/reports/multisource_results.md`, `jlq/thesis/experiments/chapter3_multisource/reports/openblas_runtime_validation.md`

### `thesis.chapter3_rules`

- The extractor produced source-linked facts and contracts with explicit evidence and review state.
- The eight-shape preliminary MLIR/AOT dataset quantifies legal-space reduction, fallback, correctness, and compile cost.
- Evidence: `jlq/thesis/experiments/chapter3_rules/processed/preliminary_summary.json`, `jlq/thesis/experiments/chapter3_rules/reports/chapter3_preliminary_results.md`, `jlq/thesis/experiments/chapter3_rules/verification/validation_report.json`

### `thesis.chapter4_5_integrated`

- Checker-predicted direct, adapt, and fallback cases match observed runtime paths.
- The integrated BaCO callback reaches real BLIS microkernel evaluations with candidate-level correctness and path evidence.
- Evidence: `jlq/thesis/experiments/chapter4_5_integrated/raw/path_matrix.csv`, `jlq/thesis/experiments/chapter4_5_integrated/processed/baco_tuning_trace.csv`, `jlq/thesis/experiments/chapter4_5_integrated/processed/integrated_summary.json`, `jlq/thesis/experiments/chapter4_5_integrated/reports/integrated_results.md`

### `thesis.chapter4_space`

- The implementation generates Generic, Contract-only, Expert-core, and Expert+Shell spaces with explicit provenance.
- The six-task filtering funnel and generation-overhead measurements are reproducible.
- Unmodified BaCO consumed the exported finite lookup in a bounded smoke run.
- Evidence: `jlq/thesis/experiments/chapter4_space/processed/space_summary.json`, `jlq/thesis/experiments/chapter4_space/processed/baco_tuning_summary.json`, `jlq/thesis/experiments/chapter4_space/reports/chapter4_results.md`

### `thesis.chapter5_blis_adapter`

- The generated binary contains and executes the real BLIS Haswell f32 6x16 microkernel path.
- Seven dynamic shapes validate direct/adapt execution, nonzero-C accumulation, and runtime fringe counts.
- Reported speedups are only relative to the declared scalar-loop dynamic fallback.
- Evidence: `jlq/thesis/experiments/chapter5_blis_adapter/processed/chapter5_summary.json`, `jlq/thesis/experiments/chapter5_blis_adapter/processed/dynamic_multishape_summary.json`, `jlq/thesis/experiments/chapter5_blis_adapter/reports/dynamic_multishape_results.md`

### `thesis.chapter6_application_validation`

- Executing the Hugging Face Qwen2ForCausalLM control flow with stateless shape-preserving modules records 338 raw Linear calls, 336 core projection calls and 192 canonical fused projection calls across two frozen scenarios.
- The eight frozen Qwen workload rows cover 100 percent of the 24-block core projection calls and FLOPs represented by the canonical trace; lm_head is explicitly excluded.
- All 24 per-workload tile-parameter audits are accounted for: 20 are active and four decode tile_m dimensions are conditionally eliminated by static legality.
- Three predeclared direct/fringe cases lower from linalg and Transform parameters to LLVM IR, link the existing OpenBLAS packing/sgemm_kernel adapter into a static RV64GCV ELF, and pass both the host ABI smoke and a 45-row physical K230 correctness/path run without modifying the frozen Chapter 4 generator or adding a compiler pass.
- On the physical K230, the C-adapter/MLIR-adapter geometric time ratio is 0.9887 with a cluster-bootstrap 95 percent interval of [0.9765, 1.0009], satisfying the preregistered wrapper-parity criterion.
- The eight exact Qwen shapes complete their physical K230 candidate pools; the best generated adapter reaches 0.6653 geometric relative performance versus complete OpenBLAS on those shapes.
- For both frozen trace scenarios, a library guard restores projected GEMM latency to the complete-OpenBLAS baseline, but no generated candidate beats the library and the one-time tuning cost therefore has no positive break-even point.
- The 2088-process i7 confirmation and 120-process WSL qualification are retained as negative measurement-quality evidence; neither supports a local performance or search-benefit claim.
- The trace-weighted analysis consumes both the completed native i9-14900 and physical K230 exact-shape pools; no hardware run remains pending within the frozen thesis boundary.
- Evidence: `jlq/thesis/experiments/chapter6_application_validation/processed/qwen_trace_summary.json`, `jlq/thesis/experiments/chapter6_application_validation/processed/qwen_trace_workloads.csv`, `jlq/thesis/experiments/chapter6_application_validation/provenance/k230_mlir_closure_manifest.json`, `jlq/thesis/experiments/chapter6_application_validation/processed/k230_mlir_closure_summary.json`, `jlq/thesis/experiments/chapter6_application_validation/processed/k230_mlir_closure_summary.csv`, `jlq/thesis/experiments/chapter6_application_validation/processed/k230_mlir_closure_aggregates.csv`, `jlq/thesis/experiments/chapter6_application_validation/reports/k230_mlir_closure_results.md`, `jlq/thesis/experiments/chapter6_application_validation/processed/trace_weighted_summary.json`, `jlq/thesis/experiments/chapter6_application_validation/processed/trace_weighted_policy_summary.csv`, `jlq/thesis/experiments/chapter6_application_validation/processed/guarded_prior_comparisons.csv`, `jlq/thesis/experiments/chapter6_application_validation/reports/trace_weighted_results.md`, `jlq/thesis/experiments/chapter6_application_validation/targets/i7_10750h/processed/summary.json`, `jlq/thesis/experiments/chapter6_application_validation/targets/i7_10750h/qualification/processed/summary.json`, `jlq/thesis/experiments/chapter6_application_validation/reports/application_validation_status.md`, `jlq/thesis/experiments/chapter6_application_validation/APPLICATION_VALIDATION_ARTIFACT_INDEX.md`

### `thesis.chapter6_contract_space_validation`

- Across three independently frozen package manifests, all 24 dangerous single-field mutations were rejected or safely downgraded, with zero false accepts and zero false rejects over 30 gold cases.
- Across 36 workloads and 2600 raw candidates per workload, canonicalizing inactive vectorize on direct/adapt microkernel paths reduced the mean Contract-only set from 208.7 to 104.4 unique schedules, with callable density 1.000 and zero residual normalized-IR duplication in C.
- Under the frozen normalized-pool protocol, 40 offline BaCO runs (8 workloads, 5 seeds, budget 25) produced final D90 0.1875, median time-to-90%-pool-best 8.0 and a 0.925 reached fraction without compilation or hardware remeasurement; the pre-normalization D90 0.1964 and time 11.5 are retained only as ablation results.
- The frozen replay worsened D90 by 0.0089 while improving time-to-90% by 3.5 callbacks; both directions are reported regardless of outcome. Of 224 selected schedules, 166 have paired existing canonical-IR evidence and 58 rely only on the audited inactive-parameter rule because no compiled vectorize=false counterpart exists.
- The 28-candidate measured subpools cover 14.3% to 46.7% of their workloads' full normalized Contract spaces; their performance results must not be extrapolated to the complete mean 104.4-candidate static spaces.
- Under the same frozen subpools and 25 unique-query budget, BaCO and uniform random without replacement reached 90% of pool-best in 0.925 and 1.000 of runs, with median T90 values 7.5 and 7.0. The budget-5 paired best-fraction difference was 0.0032 with workload-cluster 95% interval [-0.0636, 0.0643], so the experiment does not support a BaCO advantage over uniform random.
- The three package schemas have 31 intersection and 34 union leaf paths (IoU 0.912), but the OpenBLAS RVV package currently uses a package-local generation path; universal zero-core-change onboarding is not established.
- A finite positive break-even exists only for an explicitly post-hoc i7 upper-bound scenario: point and LCB95 break-even are 165865 and 741587 synthetic deployment cycles; the frozen i9 and K230 exact traces have negative savings denominators against complete BLIS/OpenBLAS.
- Evidence: `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e1_summary.json`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e2_summary.json`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e3_summary.json`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e4_summary.json`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e1_mutation_results.csv`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e2_space_classification.csv`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e2_normalized_pool.csv`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e2_normalized_baco_traces.csv`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e2_normalized_convergence.csv`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e2_normalized_baco_summary.json`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e2_random_search_traces.csv`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e2_same_pool_baco_unique_traces.csv`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e2_baco_random_paired.csv`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e2_baco_random_summary.json`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e2_vectorize_equivalence_audit.csv`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e3_reuse_audit.csv`, `jlq/thesis/experiments/chapter6_contract_space_validation/processed/e4_break_even_summary.csv`, `jlq/thesis/experiments/chapter6_contract_space_validation/reports/contract_space_validation_results.md`, `jlq/thesis/experiments/chapter6_contract_space_validation/provenance/manifest.json`

### `thesis.chapter6_evaluation`

- Thirty-six predeclared shapes and eight core tuning shapes provide the formal space-quality and baseline matrix.
- B1-B4 use equal 25-candidate budgets, five seeds, one real measurement corpus, and pinned BaCO 3.0; finite domains, seeds, and objective values are unchanged, while runtime compatibility interventions are disclosed separately.
- The evaluation includes a genuinely vectorized dynamic MLIR reference, complete BLIS bli_sgemm, component ablations, shell sensitivity, zero-shot holdout, and system overhead.
- Evidence: `jlq/thesis/experiments/chapter6_evaluation/processed/chapter6_summary.json`, `jlq/thesis/experiments/chapter6_evaluation/processed/baseline_summary.json`, `jlq/thesis/experiments/chapter6_evaluation/processed/measurement_aggregates.csv`, `jlq/thesis/experiments/chapter6_evaluation/processed/fixed_budget_summary.csv`, `jlq/thesis/experiments/chapter6_evaluation/reports/chapter6_results.md`, `jlq/thesis/experiments/chapter6_evaluation/reports/figure_qa.json`, `jlq/thesis/experiments/chapter6_evaluation/reports/figure_visual_review.md`

### `thesis.chapter6_external_validation`

- The i9 and K230 measurement protocols and immutable deployment archives were frozen before external execution.
- The OpenBLAS RV64GCV extension preserves the frozen core generator hash and adds a Contract, candidate data, explicit packing/call adapter, and deployment code.
- The static K230 ELF contains the real cblas_sgemm and sgemm_kernel symbols, and 429 of 429 physical-board rows pass strict candidate-coverage, path and correctness checks over ten workloads.
- The per-workload pool oracle selects eight direct and two adapt schedules, demonstrating automatic legal scheduling and fringe handling without changing the frozen core generator.
- The best generated adapter reaches 0.6730 geometric relative performance versus complete OpenBLAS with a workload-bootstrap 95 percent interval of [0.6193, 0.7253] and wins zero of ten workloads; this is a measured negative performance boundary rather than a library-speedup claim.
- Across 143 timing groups, median trial CV is 0.158 percent; the maximum CV among selected best adapters is 0.300 percent and maximum numerical projection error is 5.99e-6.
- The native i9-14900 import passes archive integrity, executable and manifest verification, candidate completeness, path agreement and correctness checks for 870 rows over ten workloads.
- On the i9-14900, the best generated Contract pool reaches 0.5448 geometric relative performance versus complete BLIS with workload-bootstrap 95 percent interval [0.4833, 0.6104] and wins zero of ten workloads.
- The i9 sparse Data-only versus Expert+Data ablation finds zero significant benefits and two significant harms, so the incremental BLIS-derived soft performance-feature claim remains stopped.
- Evidence: `jlq/thesis/experiments/chapter6_external_validation/EXTERNAL_VALIDATION_ARTIFACT_INDEX.md`, `jlq/thesis/experiments/chapter6_external_validation/data/experiment_config.json`, `jlq/thesis/experiments/chapter6_external_validation/processed/k230_candidate_matrix.csv`, `jlq/thesis/experiments/chapter6_external_validation/processed/k230_external_summary.json`, `jlq/thesis/experiments/chapter6_external_validation/processed/k230_external_summary.csv`, `jlq/thesis/experiments/chapter6_external_validation/processed/k230_external_aggregates.csv`, `jlq/thesis/experiments/chapter6_external_validation/reports/k230_external_results.md`, `jlq/thesis/experiments/chapter6_external_validation/provenance/generator_freeze.json`, `jlq/thesis/experiments/chapter6_external_validation/provenance/k230_external_manifest.json`, `jlq/thesis/experiments/chapter6_external_validation/provenance/i9_deployment_manifest.json`, `jlq/thesis/experiments/chapter6_external_validation/processed/i9_external_summary.json`, `jlq/thesis/experiments/chapter6_external_validation/processed/i9_external_summary.csv`, `jlq/thesis/experiments/chapter6_external_validation/processed/i9_external_aggregates.csv`, `jlq/thesis/experiments/chapter6_external_validation/processed/i9_sparse_summary.json`, `jlq/thesis/experiments/chapter6_external_validation/reports/i9_external_results.md`, `jlq/thesis/experiments/chapter6_external_validation/provenance/i9_external_import_manifest.json`

### `thesis.chapter6_online_prior`

- A 1008-case real measurement corpus supports design, validation and held-out online-prior comparisons without synthetic objective values.
- Static BLIS ranking is weakly correlated with target performance, while calibrated ranking is substantially stronger on all splits.
- Online feedback can recover from a deliberately misleading prior, but does not automatically outperform a well-trained offline prior on the same host.
- Evidence: `jlq/thesis/experiments/chapter6_online_prior/processed/online_prior_summary.json`, `jlq/thesis/experiments/chapter6_online_prior/raw/online_prior_traces.csv`, `jlq/thesis/experiments/chapter6_online_prior/reports/online_prior_results.md`, `jlq/thesis/experiments/chapter6_online_prior/provenance/manifest.json`

### `thesis.chapter6_same_pool_prior`

- The canonical pool contains 23-26 unique active schedules per workload after removing the inactive vectorize alias; tile_m, tile_n, and tile_k pass measured liveness checks.
- B2, B3, and B4 replay the same complete candidate pool with no-replacement budgets, zero duplicate objective callbacks, no holdout target reads, and an invariant common-pool oracle.
- On the i7-10750H holdout, calibrated B4 improves over no-prior B2 by 1.058x at budget 5 and 1.035x at budget 10, with workload-cluster bootstrap intervals wholly above one.
- The static B3 prior is inconclusive against B2 at both checkpoints, separating source-derived ranking from target-calibrated performance knowledge.
- On the i9-14900 holdout, calibrated B4 versus no-prior B2 is 0.992x at budget 5 and 0.999x at budget 10, with both confidence intervals crossing one; the requested two-environment significance condition is not satisfied.
- Evidence: `jlq/thesis/experiments/chapter6_same_pool_prior/processed/acceptance_summary.json`, `jlq/thesis/experiments/chapter6_same_pool_prior/processed/parameter_liveness.csv`, `jlq/thesis/experiments/chapter6_same_pool_prior/processed/same_pool_audit.csv`, `jlq/thesis/experiments/chapter6_same_pool_prior/processed/paired_comparisons.csv`, `jlq/thesis/experiments/chapter6_same_pool_prior/reports/acceptance_report.md`, `jlq/thesis/experiments/chapter6_same_pool_prior/provenance/manifest.json`

### `thesis.chapter6_termination_validation`

- Under identical pools, seeds and unique budgets, Data-only improves over no-prior BaCO by 1.049x at budget 5 and 1.035x at budget 10, with workload-cluster confidence intervals above one.
- Expert+Data does not significantly improve over Data-only: the budget-5 interval crosses one and the budget-10 result is effectively identical.
- The calibrated methods reduce mean time-to-95%-oracle from 7.90 to 3.08 candidate evaluations, but the 591-row calibration cost does not amortize within the 12 frozen holdout workloads.
- The unchanged core space generator selects the f64 6x8 Contract for all 36 workloads, creates direct/adapt schedules, and passes fresh direct/fringe runtime checks plus full-pool search without duplicate objectives.
- The extension result establishes a second BLIS Haswell microkernel Contract, not an independent library, ISA, or backend.
- Evidence: `jlq/thesis/experiments/chapter6_termination_validation/processed/acceptance_summary.json`, `jlq/thesis/experiments/chapter6_termination_validation/processed/paired_comparisons.csv`, `jlq/thesis/experiments/chapter6_termination_validation/processed/time_to_95_summary.csv`, `jlq/thesis/experiments/chapter6_termination_validation/processed/calibration_costs.csv`, `jlq/thesis/experiments/chapter6_termination_validation/processed/second_microkernel_audit.json`, `jlq/thesis/experiments/chapter6_termination_validation/reports/termination_validation_report.md`, `jlq/thesis/experiments/chapter6_termination_validation/provenance/manifest.json`

### `thesis.k230_rvv_backend`

- The physical K230 run produced 560 correct timing rows across eight workloads, including non-divisible fringe shapes.
- Selecting the best measured explicit-RVV candidate per workload achieved a 2.29x geometric-mean speedup over its in-process scalar control.
- The complete OpenBLAS RISCV64_ZVL128B SGEMM path achieved a 13.47x geometric-mean speedup over the in-process scalar control.
- No fixed source-derived schedule dominated all workloads; generic, OpenBLAS-derived and cross-source candidates won different shapes, while the BLIS-derived fixed candidate was not a reliable performance prior.
- Evidence: `jlq/thesis/experiments/k230_rvv_backend/processed/k230_board_summary.json`, `jlq/thesis/experiments/k230_rvv_backend/provenance/elf_manifest.json`, `jlq/thesis/experiments/k230_rvv_backend/provenance/deployment_manifest.json`, `jlq/thesis/experiments/k230_rvv_backend/reports/k230_elf_results.md`

### `thesis.x86_cross_host`

- The returned Intel Core i9-14900 archive passed SHA-256, revision, CPU-family and formal-status validation.
- Both x86 hosts completed 3132 f64 Contract trials with complete direct/adapt prediction agreement, 6000 fresh true-online subprocess measurements with zero objective-cache hits, and 1500 unique Optuna measurements.
- At budget 5, offline and online calibrated policies were both about 1.060x faster than random on the i9-14900 with 95% intervals above one; online calibration was 1.065x faster than Optuna TPE with interval [1.044, 1.089].
- The generated f64 candidate pool changed from 1.064x relative to complete BLIS on the development host to 0.804x on the i9-14900, showing that absolute performance ranking is not host invariant.
- At budget 25 the online policy did not consistently dominate random or Optuna, so the supported benefit is low-budget guidance rather than asymptotic superiority.
- Evidence: `jlq/thesis/experiments/x86_cross_host/processed/latest_import.json`, `jlq/thesis/experiments/x86_cross_host/processed/cross_host_summary.json`, `jlq/thesis/experiments/x86_cross_host/reports/cross_host_results.md`, `jlq/thesis/experiments/x86_cross_host/imported/thesis-x86-result--20260716T115026Z/host_metadata.json`, `jlq/thesis/experiments/x86_cross_host/imported/thesis-x86-result--20260716T115026Z/cgo_extension/processed/cgo_extension_summary.json`

## Excluded From Main Empirical Argument

| Experiment | Tier | Reason |
|---|---|---|
| `historical.native_cpp_tile_sanity` | `appendix_only` | Retain as a native C++ sanity check; do not use for the MLIR method's primary performance claim. |
| `historical.qemu_rvv_correctness` | `appendix_only` | Correctness-only emulator evidence is outside the current x86 BLIS thesis evaluation. |
| `historical.rvv_toolchain` | `appendix_only` | Toolchain evidence only; it does not support runtime performance conclusions. |
| `historical.transform_rvv_codegen` | `appendix_only` | Keep as code-generation evidence; fixed vectors and RVV instructions do not establish target speedup. |
| `paper.transform_dialect_section_4_5` | `reference_only` | Use as a source-grounded interface reference, not as a local reproduction or local measurement. |
| `thesis.transformer_region_go_nogo` | `appendix_only` | Local go/no-go evidence rejects shared activation packing as a standalone main contribution under the measured f32 BLIS Contract. Preserve it as a negative-result boundary; future region planning must obtain value from additional mechanisms such as fusion, heterogeneous layouts/dtypes, or phase-specific kernel portfolios. |

## Remaining Formal Evidence Gap

The completed evidence matrix now includes the formal B1-B4 evaluation, optimized dynamic MLIR and complete-library references, component ablations, shape holdout, overhead decomposition, multi-source conflicts, online soft-prior calibration, f32/f64 Contracts, a physical K230 run, and an imported i9-14900 cross-host run. No pending hardware run remains for the current thesis boundary. A broader publication claim would still benefit from additional independent hosts or backends, arbitrary layout/stride coverage, multithreaded evaluation, and larger end-to-end workloads. The strict same-pool calibrated-prior protocol is complete on both the i7-10750H and i9-14900. The i7 gain does not replicate significantly on the i9, so the separately declared two-environment acceptance gate fails. The termination ablation shows no statistically supported increment from the current BLIS-derived soft performance features beyond target-data calibration, and the measured calibration cost does not amortize in the 12-workload horizon. A second BLIS Haswell microkernel Contract is validated, but that same-library result is not itself an independent backend. The OpenBLAS/RV64GCV package supplies one independent library/ISA backend integration on K230; broader backend generality still requires another independent package or device.
