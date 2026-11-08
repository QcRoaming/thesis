# Multi-source Prior Ablation

- status: `PASS`
- hard executable contract: `BLIS Haswell f32 6x16 for every executable`
- incompatible hard contracts merged: `False`

| Method | Budget | Relative to pool best |
|---|---:|---:|
| S0_conflict_aware_hard | 5 | 0.945 |
| S1_blis_only | 5 | 1.000 |
| S2_openblas_only | 5 | 1.000 |
| S3_naive_merge | 5 | 1.000 |
| S4_calibrated | 5 | 1.000 |

OpenBLAS Haswell `R` is runtime-derived and is intentionally left missing rather than guessed.

## Claim boundary

This ablation compares source-labelled soft rankings on the same BLIS-hard-valid candidate pool. It does not claim that an OpenBLAS 8x4 internal kernel can be called through the BLIS 6x16 packing ABI. Outcomes are offline replays of real compiled runs.
