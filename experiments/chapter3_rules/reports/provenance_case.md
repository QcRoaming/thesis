# End-to-End Provenance Case

`Source Line -> Raw Fact -> Normalized Fact -> Contract -> Rule -> Candidate Domain -> Transform Parameters`

- Source: `config/haswell/bli_cntx_init_haswell.c:54`
- Kernel: `bli_sgemm_haswell_asm_6x16`
- Contract: `haswell_f32_gemm_6x16`
- Task: `linalg.matmul`, f32, M=192, K=256, N=256
- Parameters: `tile_m=24, tile_n=32, tile_k=64, vectorize=true`
- Contract prediction: `direct`
- Observed preliminary path: `fallback`
- Observed BLIS replacement: `false`

The preliminary Transform template does not implement packing or BLIS replacement, so a contract-direct candidate is observed as fallback.

## Alignment with CGO 2025 Section 4.5

The alignment is at the parameter interface, evaluator pipeline, and evidence
schema; it is not an assertion that the two workloads or measured speedups are
equivalent. Section 4.5 evaluates a fixed-shape `linalg.batch_matmul` with
`B=6, M=196, N=256, K=2304`, whereas this provenance case evaluates a
non-batched `linalg.matmul` with `M=192, N=256, K=256`.

| Section 4.5 parameter | Chapter 3 projection |
|---|---|
| `tile0` (batch) | omitted because the payload has no batch dimension |
| `tile1` (M) | `tile_m=24` |
| `tile2` (N) | `tile_n=32` |
| `tile3` (K) | `tile_k=64` |
| `do_vect` | `vectorize=true` |

The resulting aligned evaluator chain is:

```text
expert-space config -> Transform instance -> LLVM IR -> clang AOT
-> compile status -> correctness status -> observed execution path
-> runtime/GFLOP/s feedback
```

Section 4.5's `Valid` field only indicates evaluator/build feasibility. This
case therefore does not map `Valid=1` to correctness or replacement. It records
`compile_status=pass`, `correctness_status=pass`, `predicted_path=direct`,
`observed_path=fallback`, and `microkernel_replaced=false` independently. The
paper's fixed four-lane vectorization condition is also not imported: the lane
width is derived from the Haswell f32 contract and is eight here.

The current seeded-random sampler and a future BaCO adapter can consume the same
evaluator contract. Replacing the tuner does not change this frozen anchor or
retroactively alter its raw measurements.
