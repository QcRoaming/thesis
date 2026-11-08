# Chapter 6 Formal Evaluation Results

## Protocol

- Frozen workloads: **36**, including **8** core tuning shapes and **12** holdout shapes.
- B1-B4 use the same **25**-candidate budget and seeds `[11, 29, 41, 73, 101]`.
- Every candidate value in the offline replay comes from a real Transform/LLVM/clang execution with three independent process trials. BaCO source files, finite domains, seeds, and objective values are unchanged; replay avoids re-compiling identical candidates across seeds.
- BaCO 3.0.0 uses categorical schedule IDs and a GPy surrogate. Runtime compatibility imports `warnings`, maps scikit-learn's retired `sparse` keyword to `sparse_output`, and applies deterministic wider diagonal jitter only after GPy exhausts its native Cholesky retry; no third-party source is edited.
- BaCO observed 370 repeated callbacks across 680 runs despite `allow_duplicate_samples=false`; callback and unique counts are both retained.
- The wider numerical-jitter fallback triggered 1292 times; trigger counts are retained per run.
- B5 calls the complete `bli_sgemm` frontend. It is a mature-library reference, not a peer autotuning method.

## RQ1-RQ2

- Extracted facts: 22; field coverage and source traceability: 100.0%/100.0%.
- Machine checks pass at 100.0%; human signoff is 100.0% (16/16 verified; 0 pending). Machine and human states remain separate.
- Candidate path agreement: 100.0% over 1256 measured candidate/workload cases.

## RQ3-RQ4

- B1: D80/D90/D95 = 4.0%/2.7%/2.7%; normalized-performance geometric mean = 0.082.
- B2: D80/D90/D95 = 28.1%/19.6%/16.5%; normalized-performance geometric mean = 0.571.
- B3: D80/D90/D95 = 10.3%/4.5%/4.5%; normalized-performance geometric mean = 0.466.
- B4: D80/D90/D95 = 12.1%/6.7%/6.7%; normalized-performance geometric mean = 0.445.
- B1 best-at-25 relative-to-B5 geometric mean = 0.781 (bootstrap 95% CI [0.688, 0.887]); 90%-of-pool-best reached in 90.0% of runs; median time = 10.5 evaluations (26 denotes right censoring).
- B2 best-at-25 relative-to-B5 geometric mean = 0.948 (bootstrap 95% CI [0.858, 1.043]); 90%-of-pool-best reached in 87.5% of runs; median time = 11.5 evaluations (26 denotes right censoring).
- B3 best-at-25 relative-to-B5 geometric mean = 0.791 (bootstrap 95% CI [0.702, 0.889]); 90%-of-pool-best reached in 100.0% of runs; median time = 6.0 evaluations (26 denotes right censoring).
- B4 best-at-25 relative-to-B5 geometric mean = 0.800 (bootstrap 95% CI [0.713, 0.895]); 90%-of-pool-best reached in 90.0% of runs; median time = 7.0 evaluations (26 denotes right censoring).

## RQ5-RQ6

- The vectorized dynamic MLIR reference beats the scalar dynamic loop on 36/36 shapes, with a geometric-mean speedup of 7.710x. Its geometric-mean performance is 0.184 of complete BLIS `bli_sgemm` (scalar: 0.024).
- Component ablations and shell-ratio sensitivity are reported in `processed/fixed_budget_summary.csv`; the misleading-prior variant reverses B4's declared order without changing membership.
- Holdout is zero-shot: each method uses its pre-measurement default candidate without retraining on holdout performance. If a local expert space is empty, selection follows the declared conservative B4->B3->B2->B1 fallback chain and records the source method.
- Empty-space fallback was required in 2/48 holdout method/shape cases.
- B1 holdout relative-to-B5 geometric mean: 0.224.
- B2 holdout relative-to-B5 geometric mean: 0.474.
- B3 holdout relative-to-B5 geometric mean: 0.282.
- B4 holdout relative-to-B5 geometric mean: 0.364.

## Claim Boundary

Single-thread row-major f32 results on one x86-64 AVX2/FMA host. Tuning trajectories are offline BaCO replays over a frozen corpus of real compiled-and-executed candidates. Confidence intervals resample workloads or seeds, not machines. Cross-host and additional-dtype performance generalization are outside this package.

The second-dtype and cross-host performance enhancements were not run. This is an explicit scope limit, not missing rows silently treated as success. All 16 Chapter 3 source-backed review items have explicit thesis-author signoff; that state is recorded separately from machine checks.
