# Transform Dialect GEMM Experiment Pack

This directory contains the reproducible Transform Dialect and CPU/RVV GEMM
experiments for the thesis.

The writing-oriented evidence selection is generated at
`PAPER_EVIDENCE_CATALOG.md`. It separates primary main-text evidence from
supporting, appendix-only, and reference-only material without moving or
duplicating raw experiment artifacts.

`FINAL_EXPERIMENT_AUDIT.md` is the consolidated conclusion and boundary report
for all frozen experiments. Regenerate both views with:

```bash
python3 scripts/build_paper_evidence_catalog.py
python3 scripts/build_final_experiment_audit.py
```

`EXPERIMENTS_DETAILED_GUIDE.md` is the human-readable inventory for all 21
registered experiments. It records each experiment's execution chain, device,
protocol, primary result paths, reproduction command, and claim boundary.

## Contents

- `mlir/`: payload MLIR, Transform Dialect schedules, and a small RVV C kernel.
- `config/aot_cases.csv`: source of truth for host AOT benchmark shapes and schedules.
- `scripts/generate_matmul_mlir.py`: generates a static f32 GEMM payload and optional Transform schedule.
- `scripts/run_transform_demo.sh`: runs Transform Dialect tiling/vectorization, lowers to LLVM dialect, translates to LLVM IR, and compiles the transformed kernel to a riscv64 object with RVV enabled.
- `scripts/run_mlir_aot_benchmark.sh`: AOT-compiles generated MLIR kernels, executes them on the host CPU, checks correctness, and records latency, GFLOP/s, compilation time, and code size.
- `scripts/run_cpu_benchmark.sh`: legacy native C++ tile sanity check; it is not used for the primary performance claim.
- `scripts/run_rvv_toolchain_check.sh`: compiles a small C loop to `rv64gcv` and records RVV instruction evidence.
- `scripts/run_qemu_correctness.sh`: builds a freestanding RISC-V ELF and runs it with `qemu-riscv64` when QEMU is installed.
- `results/`: generated CSV/TSV/Markdown summaries for the report.
- `chapter3_rules/`: frozen expert-fact, Contract, Rule, and preliminary MLIR evidence.
- `chapter3_multisource/`: BLIS/OpenBLAS fact extraction, conflict modeling, and pinned OpenBLAS runtime validation.
- `chapter4_space/`: frozen schedule-space generation and BaCO interface evidence.
- `chapter5_blis_adapter/`: real BLIS packing, microkernel, fringe, and dynamic-shape evidence.
- `chapter4_5_integrated/`: live Chapter 4 candidate/BaCO to Chapter 5 evaluator integration.
- `chapter6_evaluation/`: formal 36-shape B0-B5 evaluation, five-seed BaCO,
  ablations, holdout, overhead, and manuscript figures/tables.
- `chapter6_online_prior/`: target-calibrated soft-prior study over the extended 1008-case real corpus.
- `chapter6_same_pool_prior/`: strict canonical-pool B2/B3/B4 repair with active-parameter, unique-budget, and leakage audits.
- `chapter6_termination_validation/`: Data-only/Expert+Data termination ablation, time-to-95%-oracle calibration economics, and second-microkernel Contract extension audit.
- `chapter6_external_validation/`: completed native i9-14900 and physical K230
  exact-shape pools, strict return-archive import, independent OpenBLAS RV64GCV
  Contract validation, and complete-library performance boundaries.
- `chapter6_application_validation/`: real Qwen projection-shape trace, representative
  MLIR-to-RV64GCV adapter closure, trace-weighted i9/K230 projection, and a
  disclosed i7 WSL measurement-qualification failure; local WSL timing data
  remain diagnostic-only.
- `cgo_extension/`: f64 6x8 Contract transfer, true-online measurement, equal-budget Optuna TPE, and multi-source prior ablation.
- `x86_cross_host/`: completed fixed-revision i9-14900 cross-host evaluation,
  including verified return archive, f64 Contract checks, true-online tuning,
  Optuna TPE, and a local-versus-target comparison report.
- `k230_rvv_backend/`: completed physical K230 RT-Smart evaluation for scalar,
  explicit-RVV schedules, and complete OpenBLAS SGEMM across eight workloads.
- `transformer_region_go_nogo/`: appendix-only Transformer fan-out shared-packing mechanism probe.
- `data/paper_evidence_selection.json`: machine-readable paper-use classification.
- `scripts/build_paper_evidence_catalog.py`: validates and renders the writing catalog.
- `scripts/build_final_experiment_audit.py`: rebuilds the final quantitative
  conclusion, necessity assessment, claim boundaries, and paper-use map.

## MatMul Input Coverage

The Transform Dialect matmul inputs include both a square-size ladder and transformer-style rectangular GEMMs:

- `128/256/512/1024/2048 x same x same`: square scaling cases, useful for observing how the same schedule behaves as the matrix footprint moves from toy size to cache-stressing sizes.
- `M=256, K=4096, N=4096`: batched token hidden-to-hidden projection, representative of attention Q/K/V/O projection shapes.
- `M=256, K=4096, N=11008`: feed-forward up/gate projection shape.
- `M=256, K=11008, N=4096`: feed-forward down projection shape.
- `M=1, K=4096, N=11008`: single-token decode projection, where the weight matrix is large but the row count is tiny.

The larger MLIR cases are static-shape transform inputs. They exercise tiling,
vectorization, lowering, and RVV instruction generation without executing every
large-model workload by default.

## Experiment Modes

`run_transform_demo.sh` defaults to a bounded smoke set. Use the extended set
when regenerating all square and Transformer-shaped IR snapshots:

```bash
TRANSFORM_CASE_SET=extended jlq/thesis/experiments/scripts/run_transform_demo.sh
```

The host AOT runner reads `config/aot_cases.csv`. A regular expression can select
a subset while developing:

```bash
AOT_CASE_FILTER='matmul_128_.*' \
  jlq/thesis/experiments/scripts/run_mlir_aot_benchmark.sh
```

The AOT CSV records the configured stack limit. It defaults to 64 MiB because
the current generic multi-dimensional vector-to-LLVM lowering emits loop-local
stack temporaries. This is a measured pipeline limitation, not a performance
optimization, and must remain visible in reported results.

## Run

```bash
jlq/thesis/experiments/scripts/setup_qemu_9_2_1.sh
jlq/thesis/experiments/scripts/run_all.sh
```

Set `RUN_LEGACY_CPP_BENCHMARK=1` to include the old C++ tile sanity check in
`run_all.sh`. RVV instruction counts and QEMU runs are code-generation and
correctness evidence; they are not real-board performance measurements.

The formal thesis evaluation is intentionally separate from the historical
`run_all.sh` bundle:

```bash
python3 jlq/thesis/experiments/chapter6_evaluation/scripts/run_chapter6.py
```
