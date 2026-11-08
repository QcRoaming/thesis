# Chapter 3 Research Scope and Fixed Versions

This file freezes the scope of the preliminary study. Results outside this
boundary must not be generalized without additional experiments.

## Research boundary

| Item | Frozen value |
|---|---|
| Operator | Static-shape `linalg.matmul` / GEMM |
| Main dtype | `f32` |
| Secondary knowledge entry | `f64` Contract only; not part of the preliminary performance plot |
| Expert source | BLIS Haswell configuration and kernels |
| Knowledge-source architecture | Intel Haswell, AVX2/FMA |
| Measurement host | Intel Core i7-10750H, Comet Lake, AVX2/FMA |
| Execution backend | MLIR Transform Dialect to LLVM IR to native executable |
| Thread mode | Single process, single benchmark thread, CPU affinity core 0 |
| Transform coverage | Outer tiling and optional vectorization |
| BLIS replacement coverage | Not implemented; observed replacement is recorded as false |
| Preliminary workload size | Eight representative f32 shapes |
| Tuner | Seeded random sampling, seed 17 |

The source and measurement microarchitectures are not identical. The
preliminary performance results therefore demonstrate an ISA-compatible
transfer experiment and pipeline behavior, not native Haswell performance.

## Fixed versions

| Component | Version/commit |
|---|---|
| Workspace | `d7bb40cbac731175dc507f06f0655d81508f2ca2` |
| BLIS | `36df51a81cc732eeadbf2e6732941dd5400db47d` |
| LLVM/MLIR | `09b849a2ac83dbf4be1b2f01c767339e46cc34ae` |
| MLIR tools | LLVM 21.0.0git, optimized assertions build |
| Native compiler | clang 21.0.0git |
| Python | 3.10.12 |
| Figure backend | R 4.1.2 with ggplot2, patchwork, svglite and ragg |
| Operating environment | x86_64 Linux under WSL2 |

## Compilation and measurement protocol

- Transform application: `mlir-opt --transform-interpreter`.
- Lowering: bufferization/loop conversion, `--test-lower-to-llvm`, then
  `mlir-translate --mlir-to-llvmir`.
- Native compilation: `clang++ -O3 -march=native -std=c++17`.
- Correctness tolerance: `1e-3 + 1e-4 * abs(reference)`.
- Timing excludes input generation, reference computation, and correctness
  checking.
- Warmups, repeats, inner iterations, stack limit, seed, and affinity are
  recorded in `data/preliminary_shapes.yaml` and every raw result row.

## Claim boundary

Chapter 3 uses these data only to establish research motivation and validate
the knowledge representation. Full-scale comparisons, confidence intervals,
hold-out generalization, and final performance claims belong to Chapter 5.
