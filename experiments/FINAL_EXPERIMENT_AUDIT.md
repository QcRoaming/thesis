# Final Experiment Audit

> Generated from frozen machine-readable summaries. This is the single entry point for deciding which experiments support the thesis argument.

## Overall status

- Audit status: `PASS`.
- Registered evidence entries: 22; main-text eligible: 16.
- Evidence tiers: 11 primary, 5 supporting, 5 appendix-only, 1 reference-only.
- Completed external targets: Intel Core i9-14900 and physical K230 C908.
- No pending hardware run remains for the current thesis experiment boundary.

## End-to-end evidence chain

1. **Knowledge representation:** 22 source-linked facts have full machine-check, traceability and author-signoff coverage; BLIS/OpenBLAS extraction records four explicit source conflicts.
2. **Compatibility and space construction:** 1256 measured candidate cases achieve complete prediction-to-runtime agreement. Contract-only, expert-core and expert-shell spaces remain separately measurable.
3. **Compiler execution:** the integrated path observes direct, adapt and fallback exactly as predicted, with real BLIS packing and 6x16 invocation for eligible f32 cases.
4. **Dynamic shapes:** seven direct/adapt shapes are correct and fringe counts match; the geometric mean is 15.90x over the declared scalar-loop dynamic fallback.
5. **Formal evaluation:** 36 workloads, fixed budgets, five seeds, complete BLIS and optimized dynamic MLIR references, ablations, holdout and overhead are frozen.
6. **External validity:** f64 6x8, a second x86 host, and a physical RISC-V board are now measured.
7. **Termination validation:** Data-only, Expert+Data, calibration economics and second-Contract extensibility are tested under pre-registered stop conditions.
8. **Application relevance:** the real Qwen model control flow maps all core projection calls and FLOPs to eight frozen workload rows, while three representative MLIR/RV64GCV closure cases pass static and host-ABI checks; the local WSL timing pool is explicitly ineligible.

## Core quantitative findings

- The Checker is reliable within the tested Contracts: prediction-observation agreement is 1.000.
- Packing is indispensable to the callable microkernel path: removing its rule drops normalized performance from 0.800 to 0.046.
- In the frozen 28-candidate measured subpools, BaCO/uniform-random reached 90% of pool-best in 0.925/1.000 of runs, with median unique-query T90 7.5/7.0; the paired result does not support a BaCO advantage over uniform random.
- On the development host at budget 5, offline calibration is 1.192x and online calibration is 1.155x faster than random; both 95% intervals are above one.
- On the i9-14900 at budget 5, online calibration is 1.065x faster than Optuna TPE with 95% interval [1.044, 1.089].
- In the strict termination ablation at budget 5, Data-only is 1.049x over no-prior with interval [1.024, 1.075], but Expert+Data over Data-only is only 1.009x with interval [0.999, 1.027].
- Mean time-to-95%-oracle falls from 7.90 to 3.08 evaluations, but the 591-row calibration does not amortize within the 12-workload horizon.
- The second f64 6x8 microkernel Contract passes with an unchanged core generator across 36 workloads; this is not an independent-backend result.
- Absolute ranking is host dependent: the generated f64 pool changes from 1.064x relative to complete BLIS locally to 0.804x on the i9-14900.
- K230 produced 560 correct rows; the best measured explicit-RVV schedule is 2.29x and complete OpenBLAS is 13.47x relative to their in-process scalar controls.

## Is expert prior necessary?

- **Hard compatibility knowledge: yes.** It defines legal packing, kernel ABI and direct/adapt/fallback behavior, and its predictions transfer across the tested hosts.
- **Packing/call Contract: yes.** The no-packing ablation collapses performance and cannot represent the real accelerated path.
- **Fixed BLIS performance constants: no.** MR/NR and blocking values are useful seeds, but the ablations and host reversal reject treating them as universal hard constraints.
- **Target-data calibration: conditionally useful.** It improves low-budget sample efficiency, but the measured setup cost is not recovered in 12 holdouts.
- **Current BLIS soft performance rules: no demonstrated incremental value.** Expert+Data does not significantly beat Data-only at the registered checkpoints, so these features are retained only as historical transfer or feedback-calibration inputs.

## Final thesis claim

The defensible contribution is a compiler workflow that turns transferable hard compatibility knowledge into callable direct/adapt schedules and extends to a second BLIS microkernel Contract without changing the core space generator. Within the frozen 28-candidate measured subpools, BaCO does not outperform uniform random search without replacement. Target data can improve low-budget search in the separate calibrated-prior experiments, but the current BLIS-derived soft performance rules add no demonstrated value beyond that data and their measured calibration cost is not practically amortized in the frozen horizon.

## Claim boundaries

- Single-thread row-major GEMM remains the main x86 evaluation boundary.
- Arbitrary layouts, strides, transposes and batched operators are not covered.
- K230 evidence is limited to one physical C908 RT-Smart board and toolchain.
- The two-host x86 result does not establish universal host-independent ranking.
- Chapter 5 speedups use a scalar-loop dynamic fallback; complete-library comparisons are reported separately.
- No end-to-end model or application-level speedup is claimed.
- The Qwen trace is model-code coverage evidence; the i7 WSL exact-shape timing pool failed qualification and is excluded from performance claims.
- The second microkernel is on the same BLIS Haswell backend; independent-backend extensibility is not established.

## Paper-use map

- Chapter 3: `thesis.chapter3_rules` and `thesis.chapter3_multisource`.
- Chapter 4: `thesis.chapter4_space`.
- Chapter 5: `thesis.chapter5_blis_adapter` and `thesis.chapter4_5_integrated`.
- Chapter 6: `thesis.chapter6_evaluation`, `thesis.chapter6_online_prior`, `thesis.chapter6_same_pool_prior`, `thesis.chapter6_termination_validation`, `thesis.chapter6_application_validation`, `thesis.cgo_local_extension`, `thesis.x86_cross_host`, and `thesis.k230_rvv_backend`.
- Historical native C++, QEMU and code-generation-only RVV artifacts stay in the appendix.

## Optional publication extensions

- Add another independent x86 or RISC-V target and preserve the same fixed-budget protocol.
- Evaluate multithreaded execution and hardware counters for packing, cache and memory effects.
- Extend Contracts to layout/stride/transpose/batched GEMM cases.
- Evaluate one end-to-end operator or model workload without weakening the current baselines.
- Replace the explicit two-entry runtime registry with a descriptor-driven independent-backend package and test it on a distinct library or ISA.
