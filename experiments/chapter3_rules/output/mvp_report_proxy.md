# BLIS Expert-Space MVP Report

## Extracted fact

- Kernel: `bli_sgemm_haswell_asm_6x16`
- Register tile: `6x16`
- Cache blocking: `MC=168, KC=256, NC=4080`
- Packing kernel: `bli_spackm_haswell_asm_6x16`
- ISA: `avx2, fma`; vector lanes for f32: `8`
- Source revision: `36df51a81cc732eeadbf2e6732941dd5400db47d`

## Search-space size and contract outcomes

`Eligible` is the number sent to the tuner under that variant's policy.
The four outcome columns are pre-measurement contract classifications.

| Task | Space | Generated | Eligible | Direct | Adapt | Fallback | Reject |
|---|---|---:|---:|---:|---:|---:|---:|
| matmul_aligned_192x256x256_f32 | expert | 1176 | 336 | 175 | 161 | 504 | 336 |
| matmul_aligned_192x256x256_f32 | expert_remove_cache_blocking | 1176 | 392 | 210 | 182 | 588 | 196 |
| matmul_aligned_192x256x256_f32 | expert_remove_compatibility_checker | 1176 | 1176 | 175 | 161 | 504 | 336 |
| matmul_aligned_192x256x256_f32 | expert_remove_mr_nr | 1176 | 840 | 175 | 161 | 504 | 336 |
| matmul_aligned_192x256x256_f32 | expert_remove_packing | 1176 | 840 | 0 | 0 | 840 | 336 |
| matmul_aligned_192x256x256_f32 | generic | 4704 | 3696 | 350 | 994 | 2352 | 1008 |
| matmul_edge_128x128x128_f32 | expert | 1176 | 392 | 0 | 392 | 588 | 196 |
| matmul_edge_128x128x128_f32 | expert_remove_cache_blocking | 1176 | 392 | 0 | 392 | 588 | 196 |
| matmul_edge_128x128x128_f32 | expert_remove_compatibility_checker | 1176 | 1176 | 0 | 392 | 588 | 196 |
| matmul_edge_128x128x128_f32 | expert_remove_mr_nr | 1176 | 980 | 0 | 392 | 588 | 196 |
| matmul_edge_128x128x128_f32 | expert_remove_packing | 1176 | 980 | 0 | 0 | 980 | 196 |
| matmul_edge_128x128x128_f32 | generic | 4704 | 4312 | 0 | 1568 | 2744 | 392 |

## Generic vs expert

- `matmul_aligned_192x256x256_f32`: `3696` generic candidates vs `336` expert candidates, a `90.9%` reduction.
- `matmul_edge_128x128x128_f32`: `4312` generic candidates vs `392` expert candidates, a `90.9%` reduction.

## Equal-budget search

Metric: `proxy_score` (higher is better).

| Task | Space | Final best | Best candidate action |
|---|---|---:|---|
| matmul_aligned_192x256x256_f32 | expert | 2.2512 | direct |
| matmul_aligned_192x256x256_f32 | expert_remove_cache_blocking | 1.8343 | direct |
| matmul_aligned_192x256x256_f32 | expert_remove_compatibility_checker | 2.1216 | adapt |
| matmul_aligned_192x256x256_f32 | expert_remove_mr_nr | 1.3200 | direct |
| matmul_aligned_192x256x256_f32 | expert_remove_packing | 1.1623 | fallback |
| matmul_aligned_192x256x256_f32 | generic | 0.8593 | direct |
| matmul_edge_128x128x128_f32 | expert | 2.2241 | adapt |
| matmul_edge_128x128x128_f32 | expert_remove_cache_blocking | 1.2878 | adapt |
| matmul_edge_128x128x128_f32 | expert_remove_compatibility_checker | 1.5343 | adapt |
| matmul_edge_128x128x128_f32 | expert_remove_mr_nr | 2.2555 | adapt |
| matmul_edge_128x128x128_f32 | expert_remove_packing | 1.1324 | fallback |
| matmul_edge_128x128x128_f32 | generic | 1.0507 | adapt |

> These scores only validate the pipeline and convergence accounting; they are not measured performance.

## Interpretation boundary

This MVP validates source-backed fact extraction, contract classification, space generation, equal-budget sampling, native measurement plumbing, and ablation bookkeeping. `direct/adapt/fallback/reject` are checker decisions, not observed MLIR library-replacement success rates. A final thesis experiment must compile each retained Transform Dialect candidate and record the actual replacement/lowering outcome.
