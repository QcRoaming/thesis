# Transformer region shared-packing go/no-go

## Decision

**NO_GO_STRONG_BASELINE_NOT_BEATEN**

All 160 measured rows passed correctness.

## Paired results

| Comparison | Geomean | 95% case-bootstrap CI | Wins |
|---|---:|---:|---:|
| shared A vs repacked A microkernel | 1.006x | [0.906, 1.121] | 4/8 |
| shared A microkernel vs concatenated BLIS | 0.720x | [0.510, 0.972] | 1/8 |
| shared A microkernel vs best complete-BLIS path | 0.665x | [0.472, 0.894] | 1/8 |
| concatenated BLIS vs independent BLIS | 0.956x | [0.865, 1.051] | 1/8 |

## Case matrix

| Case | Independent BLIS ms | Concatenated BLIS ms | Repacked A ms | Shared A ms | Shared/best BLIS |
|---|---:|---:|---:|---:|---:|
| gate_up_decode_m1 | 13.502811 | 13.300705 | 10.410634 | 9.866779 | 1.263x |
| gate_up_decode_m8 | 18.506144 | 18.766954 | 19.739652 | 21.313933 | 0.879x |
| gate_up_prefill_m256 | 132.535178 | 145.672149 | 566.277369 | 515.608569 | 0.263x |
| gate_up_prefill_m64 | 53.413843 | 56.175236 | 132.521781 | 112.491480 | 0.465x |
| qkv_decode_m1 | 0.618715 | 0.643196 | 0.744759 | 0.741967 | 0.739x |
| qkv_decode_m8 | 1.612804 | 1.563121 | 1.308333 | 1.640379 | 0.875x |
| qkv_prefill_m256 | 14.065136 | 14.511290 | 25.364879 | 25.601116 | 0.557x |
| qkv_prefill_m64 | 4.818978 | 5.069670 | 6.888123 | 6.379363 | 0.780x |

## Mechanism bound

Shared packing reduced the activation-pack count from the branch count to one, but the measured saved packing time was at most 3.08% of the repacked-path latency.

Holding microkernel compute time fixed, the packing-only ideal speedup is 1.010x geomean and at most 1.032x. Thus activation packing reuse alone does not reach the frozen 1.05x target.

## Measurement audit

- BLIS threads: 1; pinned CPU: 10.
- Variant schedule: `per_repeat_rotating_order`.
- Trial CV across case/variant cells: median 0.104, maximum 0.352. The WSL2 maximum is retained as a residual-noise limitation.

## Interpretation contract

- `shared A vs repacked A` isolates activation-packing reuse; both use persistent B and the same real BLIS 6x16 microkernel.
- `shared A vs concatenated BLIS` is the strong-baseline test; offline weight concatenation is algebraically equivalent for these fan-out linear layers.
- `shared A vs best complete-BLIS path` selects the faster independent or concatenated complete-BLIS path within each paired trial; it is a stricter diagnostic and does not relax the frozen decision criteria.
- A local pass remains provisional until the frozen experiment reproduces on the i9-14900.
- A local failure stops expansion unless profiling identifies a separately testable implementation defect.

## Boundary

This is a native mechanism probe using real BLIS frontend calls and the real BLIS Haswell 6x16 microkernel. It tests whether compiler-visible shared activation packing can beat both repeated packing and a concatenated-weight single-BLIS strong baseline. It does not yet implement an MLIR graph planner, low-precision kernels, a complete Transformer block, or an end-to-end model.
