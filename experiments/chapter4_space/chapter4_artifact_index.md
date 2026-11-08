# Chapter 4 Artifact Index

## Required Method Artifacts

| Requirement | Artifact | Status |
|---|---|---|
| Generic / Contract-only / Expert-core / Expert+Shell | `data/space_configs.json`, `processed/spaces/`, `processed/space_summary.csv` | complete |
| Task Context | `data/task_contexts.json` | complete |
| Contract Registry and selection log | `processed/contract_registry.json`, `processed/contract_selection.csv` | complete |
| Compatibility Checker and reason codes | `scripts/chapter4lib.py`, `data/reason_codes.json`, `raw/candidate_decisions.csv` | complete |
| Conditional domains | `conditional_parameters`, candidate CSV fields | complete |
| Candidate provenance | `provenance/candidate_provenance.csv` | complete |
| Algorithms 4-1 to 4-3 | `reports/algorithms.md` and corresponding functions | complete |
| direct/adapt/fallback Transform templates | `build/transform_paths/`, `raw/transform_paths.csv` | complete |
| Tuner export and full log | `tuner/`, `raw/baco_callback_log.jsonl`, `processed/baco_tuning_trace.csv` | complete |
| Properties, boundaries, complexity | `tests/test_chapter4.py`, `reports/invariants.md`, `reports/complexity.md` | 53/53 pass |

## Figures And Tables

- Figure 4-1: `figures/figure4_1_framework.*`
- Figure 4-2: `figures/figure4_2_spaces_and_paths.*`
- Figure 4-3: `figures/figure4_3_checker.*`
- Figure 4-4: `figures/figure4_4_transform_instantiation.*`
- Figure 4-5: `figures/figure4_5_provenance.*`
- Table 4-1: `tables/table4_1_symbols.{csv,tex}`
- Table 4-2: `tables/table4_2_checker_rules.{csv,tex}`
- Table 4-3: `tables/table4_3_paths.{csv,tex}`
- Figure contracts and QA: `reports/figure_contracts.md`, `reports/figure_qa.{md,json}`

## Empirical Evidence

- Six Task Contexts, 15,600 raw candidate decisions in total.
- Three real Transform-to-AOT policy examples; 3/3 compile and correctness pass.
- One real unmodified-BaCO run with six evaluations; 6/6 valid.
- Complete per-stage commands, IR, binaries, callback records, and source hashes.
- Measured generation time and peak memory for each Task Context.

## Claim Boundary

The method and tuner closed loop are complete. A real BLIS packing/library-call adapter is not implemented: predicted `direct`/`adapt` candidates are observed as fallback in LLVM IR. The artifacts are suitable for Chapter 4 method writing but must not be cited as evidence of observed BLIS microkernel replacement.

## Reproduction

```bash
python3 /buddy-mlir/jlq/thesis/experiments/chapter4_space/scripts/run_chapter4.py
```
