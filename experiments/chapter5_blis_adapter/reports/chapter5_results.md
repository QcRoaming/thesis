# Chapter 5 BLIS adapter experiment

## Result

The aligned `192x256x256` f32 anchor completed both newly generated paths.
The Transform-driven BLIS path called the real `bli_sgemm_haswell_asm_6x16`
symbol and passed the full-matrix reference check.

| Variant | Observed path | Median ms | GFLOP/s | Max abs diff | BLIS symbol |
|---|---:|---:|---:|---:|---:|
| fallback_vectorized | fallback | 13.560975 | 1.856 | 1.19e-06 | no |
| direct_blis_6x16 | direct | 0.727804 | 34.578 | 1.07e-06 | yes |

For this run, the direct path was `18.633x` faster than the generated
fallback baseline. This ratio is host- and run-specific and is not a broad
performance claim.

## Evidence chain

1. `transform.apply_registered_pass` materializes BLIS-compatible A/B panels.
2. `transform.buddy.call_microkernel` only retargets the prepared placeholder.
3. LLVM IR contains `call void @buddy_blis_sgemm_6x16`.
4. The linked executable exports both the wrapper and
   `bli_sgemm_haswell_asm_6x16`.
5. Runtime output passes the scalar reference check.

## Boundary

Rank-2 row-major f32 GEMM on one x86-64 AVX2/FMA host. Static direct, M/N/K fringe adapt, and one-binary dynamic-shape execution are implemented for the fixed BLIS Haswell 6x16 microkernel; arbitrary layouts, additional dtypes/contracts, and cross-host statistics remain outside this experiment.
