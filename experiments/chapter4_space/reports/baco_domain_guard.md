# BaCO Broad-domain Diagnostic And Guard

The first live BaCO attempt exposed a compiler-cost hazard that was not visible from static candidate legality alone.

- `m48_n32_k128_pab_v1` emitted approximately 1.1 MiB LLVM IR and required about 159 s for native `clang -O3` compilation, while still compiling and passing correctness.
- `m96_n64_k128_pab_v1` emitted approximately 3.2 MiB LLVM IR; the broad-domain smoke run was stopped during its multi-minute compilation.
- These candidates remain executable and are not relabeled as `reject`. Compile-cost control is an experiment-runtime policy, not a correctness rule.

The full Expert+Shell lookup therefore remains 249 candidates, while the Chapter 4 live BaCO smoke run declares a six-candidate subset satisfying `tile_m=168`, `tile_n>=128`, and `tile_k>=128`. The retained M fringe prevents the observed full static vector expansion in this toolchain. This guard is recorded in `tuner/baco_tuning_pool.json` and does not alter the Compatibility Checker.

Diagnostic IR and logs are retained under `build/diagnostics/broad_domain_attempt/`.
