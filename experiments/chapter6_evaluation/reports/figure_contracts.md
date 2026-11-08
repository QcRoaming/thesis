# Chapter 6 Figure Contracts

All figures use the Python backend, editable SVG as the primary format, PDF as
the print vector format, and 600 dpi TIFF plus PNG for raster QA. Quantitative
figures use the frozen CSV files under `processed/`; no values are copied from
the prose draft.

## Figure 6-1

- Core conclusion: BLIS facts are schema-complete and source-traceable, and all 16 source-backed review cases have explicit thesis-author signoff.
- Figure archetype: quantitative grid; target size 183 x 82 mm.
- Panel map: a, fact/evidence counts; b, coverage, machine review, and human signoff ratios.
- Evidence hierarchy: extraction coverage is primary; ambiguity count and separate machine/human review ratios are controls.
- Statistics/source: descriptive counts and proportions from `extraction_coverage.json`; no inferential test.
- Reviewer risk: machine checks must not be presented as human validation.

## Figure 6-2

- Core conclusion: Compatibility Checker predictions agree with observed direct, adapt, and fallback paths in the measured corpus.
- Figure archetype: quantitative grid; target size 120 x 82 mm.
- Panel map: one annotated confusion matrix.
- Evidence hierarchy: diagonal counts are primary; absent off-diagonal cells are validation.
- Statistics/source: candidate/workload cases from `checker_confusion.csv`; descriptive agreement ratio.
- Reviewer risk: policy rejects are not executable runtime classes and must stay outside this matrix.

## Figure 6-3

- Core conclusion: Contract and expert rules progressively reduce the raw schedule space before the equal-cost tuning pool is formed.
- Figure archetype: quantitative grid; target size 183 x 88 mm.
- Panel map: a, aggregate full-space funnel; b, per-family retained ratio.
- Evidence hierarchy: raw-to-core reduction is primary; compile guard and 25-point pool are controls.
- Statistics/source: all 36 workloads from `space_summary.csv`; median and interquartile range where aggregated.
- Reviewer risk: correctness filtering and compile-cost guarding must remain distinct.

## Figure 6-4

- Core conclusion: Expert spaces shift the empirical normalized-performance distribution relative to Generic search.
- Figure archetype: quantitative grid; target size 120 x 88 mm.
- Panel map: empirical CDF for B1-B4 with B5-normalized x-axis.
- Evidence hierarchy: full measured tuning pools are primary; D80/D90/D95 guides are validation thresholds.
- Statistics/source: 8 shapes x 25 candidates per method from `candidate_space_quality.csv`.
- Reviewer risk: B5 is a mature-library reference, not a peer search method.

## Figure 6-5

- Core conclusion: Under equal budgets, expert-space BaCO reaches its best region in fewer evaluations and lower evaluator-equivalent time.
- Figure archetype: quantitative grid; target size 183 x 88 mm.
- Panel map: a, best-so-far versus evaluations; b, best-so-far versus equivalent wall time.
- Evidence hierarchy: median over 8 shapes x 5 seeds is primary; 25th-75th percentile bands show robustness.
- Statistics/source: `convergence_normalized.csv`; offline replay over real measurements.
- Reviewer risk: equivalent time must not be mislabeled as observed end-to-end replay wall time.

## Figure 6-6

- Core conclusion: The fixed-budget performance of B1-B4 differs despite identical seeds, budget, compiler, and measurement corpus.
- Figure archetype: quantitative grid; target size 120 x 82 mm.
- Panel map: geometric mean relative to B5 with workload/seed bootstrap intervals.
- Evidence hierarchy: best-at-25 is primary; interval and individual run points are validation.
- Statistics/source: `fixed_budget_summary.csv` and `fixed_budget_results.csv`, 10,000 bootstrap replicates.
- Reviewer risk: intervals resample workload/seed runs, not machines.

## Figure 6-7

- Core conclusion: Removing compatibility, packing, expert priors, or shell components changes fixed-budget search quality.
- Figure archetype: quantitative grid; target size 183 x 88 mm.
- Panel map: ablation forest/bar plot relative to full B4.
- Evidence hierarchy: normalized best-at-25 is primary; bootstrap intervals are validation.
- Statistics/source: ablation rows in `fixed_budget_summary.csv`.
- Reviewer risk: each ablation must name its operational pool change; it is not source-code deletion evidence.

## Figure 6-8

- Core conclusion: A bounded exploration shell trades expert concentration for robustness, and excessive shell mass can dilute the budget.
- Figure archetype: quantitative grid; target size 120 x 82 mm.
- Panel map: shell ratio versus fixed-budget normalized performance and time-to-target.
- Evidence hierarchy: performance is primary; time-to-target is validation.
- Statistics/source: shell suite in `fixed_budget_summary.csv`.
- Reviewer risk: only tested ratios 0, 5, 10, 20, and 30 percent may be interpreted.

## Figure 6-9

- Core conclusion: Zero-shot defaults remain correct on holdout shapes, but relative performance varies by method and shape family.
- Figure archetype: quantitative grid; target size 183 x 100 mm.
- Panel map: method-by-holdout heatmap grouped by family.
- Evidence hierarchy: B5-normalized performance is primary; path labels are supporting metadata.
- Statistics/source: `holdout_zero_shot.csv`; no holdout retuning.
- Reviewer risk: this supports shape holdout only, not dtype, architecture, or host generalization.

## Figure 6-10

- Core conclusion: Native compile/link dominates one-time candidate construction, while checker and tuning replay overheads are smaller.
- Figure archetype: quantitative grid; target size 120 x 82 mm.
- Panel map: log-scale stage-time bars with explicit unit labels.
- Evidence hierarchy: measured stage timings are primary; units prevent invalid direct totals.
- Statistics/source: `overhead_profile.csv` and extraction profile.
- Reviewer risk: stages with different amortization units must not be summed into a fictitious single latency.

## Figure 6-11

- Core conclusion: Vectorized dynamic MLIR improves substantially over the scalar loop but remains below complete BLIS on average; candidate path and construction cost explain representative residual gaps.
- Figure archetype: two-panel quantitative grid; target size 183 x 84 mm.
- Panel map: (a) scalar and vectorized dynamic references relative to complete BLIS across 36 shapes; (b) normalized candidate performance versus construction cost, colored by observed path.
- Evidence hierarchy: complete-BLIS-normalized baseline and candidate measurements are primary; labeled extrema are supporting cases.
- Statistics/source: `baseline_comparison.csv`, `candidate_space_quality.csv`, and `measurement_aggregates.csv`.
- Reviewer risk: B5 is a mature-library reference rather than a peer tuner, and slow but correct fallback is not a checker false positive.

## Integrity Notes

These are generated charts rather than microscopy or photographic panels. There
is no crop, contrast, gamma, pseudo-color, stitching, or reused raster source.
All plotted data remain traceable to CSV/JSON outputs generated by the same
experiment package.
