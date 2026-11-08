# Chapter 6 Formal Evaluation

This package is the formal evaluation layer over the frozen Chapter 3 fact
model, Chapter 4 schedule spaces, Chapter 5 BLIS adapter, and the Chapter 4-5
integration smoke test. It does not rewrite those packages.

## What It Runs

- 36 predeclared row-major f32 GEMM shapes in design, validation, and holdout splits.
- Eight core tuning shapes, five seeds, and a 25-candidate budget.
- B0 scalar dynamic MLIR, B1 Generic, B2 Contract-only, B3 Expert-core,
  B4 Expert+Shell, and B5 complete BLIS `bli_sgemm`.
- Real Transform Dialect, MLIR-to-LLVM lowering, clang AOT, execution, numerical
  checking, direct/adapt/fallback path checking, and runtime fringe counting.
- Component ablations, shell-ratio sensitivity, misleading-prior robustness,
  zero-shot holdout, and extraction/checker/compile/benchmark/tuner overhead.
- Figure 6-1 through Figure 6-11 and Table 6-1 through Table 6-4.

BaCO trajectories are offline replays over a frozen corpus of real measured
candidates. This avoids recompiling the same candidate for every seed while
keeping the pinned BaCO GP configuration, seed, finite domain, and objective
values.
Both replay wall time and evaluator-equivalent compile-and-measure time are
recorded separately.

BaCO 3.0.0 may repeat a categorical point even when
`allow_duplicate_samples=false`. The formal budget therefore means tuner
callbacks; every run records both callback count and unique-candidate count.

The pinned BaCO 3.0.0 categorical preprocessor references Python's `warnings`
module without importing it and uses scikit-learn's retired `sparse` keyword.
The runner injects the standard-library module and maps `sparse` to
`sparse_output` at runtime. If GPy exhausts its native Cholesky jitter retries,
the runner performs a deterministic wider diagonal-jitter retry and records the
trigger count in the run summary. No third-party source file, candidate pool,
observation, or random seed is modified; the numerical fallback is reported as
an execution-compatibility intervention rather than an algorithmic contribution.

## Reproduction

```bash
python3 jlq/thesis/experiments/chapter6_evaluation/scripts/run_chapter6.py
```

The first run compiles the candidate corpus and is intentionally much slower
than subsequent checkpointed runs. Use `--force-measurements` or
`--force-tuning` only when the corresponding frozen evidence must be replaced.

## Main Outputs

- `processed/chapter6_summary.json`: RQ1-RQ6 machine-readable summary.
- `reports/chapter6_results.md`: writing-oriented result report.
- `processed/measurement_aggregates.csv`: real candidate and baseline measurements.
- `processed/tuning_traces.csv`: all BaCO trajectories.
- `processed/fixed_budget_summary.csv`: baseline, ablation, and shell statistics.
- `figures/`: editable and raster exports for Figure 6-1 through Figure 6-11.
- `tables/`: CSV and LaTeX exports for Table 6-1 through Table 6-4.
- `reports/figure_qa.json`: export QA.

## Claim Boundary

The package supports single-thread, row-major f32 conclusions on one x86-64
AVX2/FMA host. Bootstrap intervals resample workloads or workload/seed runs;
they are not cross-machine confidence intervals. Additional-dtype and
cross-host performance experiments are not represented as completed. Chapter 3
human-review rows remain pending author signoff.
