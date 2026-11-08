# Chapter 6 Artifact Index

## Protocol and Entry Points

- Frozen workloads: `data/workloads.json`
- Fairness and measurement protocol: `data/experiment_config.json`
- One-command reproduction: `scripts/run_chapter6.py`
- Space and compile/run implementation: `scripts/chapter6lib.py`, `scripts/run_measurements.py`
- Pinned BaCO replay with documented runtime compatibility shims: `scripts/run_tuning.py`
- Statistical analysis: `scripts/analyze_results.py`
- Python figure generation and QA: `scripts/plot_chapter6_figures.py`, `scripts/qa_figures.py`

## Primary Evidence

- Formal summary: `processed/chapter6_summary.json`
- Real trial rows: `raw/measurement_trials.csv`
- Aggregated real measurements: `processed/measurement_aggregates.csv`
- Dynamic scalar/vectorized and complete-BLIS references: `processed/baseline_comparison.csv`, `processed/baseline_summary.json`
- Space quality: `processed/space_quality_summary.csv`
- Tuning traces: `processed/tuning_traces.csv`
- Fixed-budget statistics: `processed/fixed_budget_summary.csv`
- Holdout results: `processed/holdout_zero_shot.csv`
- Overhead profile: `processed/overhead_profile.csv`
- Human-readable report: `reports/chapter6_results.md`
- Frozen source/tool/output hashes: `provenance/manifest.json`

## Manuscript Assets

- Figure contracts: `reports/figure_contracts.md`
- Figure 6-1 through Figure 6-11: `figures/`
- Figure QA and visual review: `reports/figure_qa.json`, `reports/figure_qa.md`, `reports/figure_visual_review.md`
- Table 6-1 through Table 6-4: `tables/`

## Inherited Evidence

- Fact quality and completed thesis-author signoff: `../chapter3_rules/verification/`
- Space generator and Checker definitions: `../chapter4_space/`
- Dynamic BLIS packing/fringe adapter: `../chapter5_blis_adapter/`
- Candidate-to-real-evaluator smoke evidence: `../chapter4_5_integrated/`

## Boundary

Single-thread row-major f32 on one x86-64 AVX2/FMA host. BaCO trajectories are
offline replays over real measurements. B5 is a mature-library performance
reference rather than a peer autotuning baseline. Cross-host and second-dtype
performance is not claimed. Chapter 3 machine checks and completed thesis-author
signoff remain separately recorded.
