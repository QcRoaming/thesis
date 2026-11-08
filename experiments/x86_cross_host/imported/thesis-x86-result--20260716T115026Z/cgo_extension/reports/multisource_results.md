# Multi-source Prior Ablation

- status: `PASS`
- hard executable contract: `BLIS Haswell f32 6x16 for every executable`
- incompatible hard contracts merged: `False`

| Method | Budget | Relative to pool best |
|---|---:|---:|
| S0_conflict_aware_hard | 5 | 0.865 |
| S0_conflict_aware_hard | 10 | 0.943 |
| S0_conflict_aware_hard | 15 | 0.966 |
| S0_conflict_aware_hard | 25 | 0.996 |
| S1_blis_only | 5 | 0.971 |
| S1_blis_only | 10 | 0.986 |
| S1_blis_only | 15 | 0.993 |
| S1_blis_only | 25 | 1.000 |
| S2_openblas_only | 5 | 0.908 |
| S2_openblas_only | 10 | 0.978 |
| S2_openblas_only | 15 | 0.983 |
| S2_openblas_only | 25 | 1.000 |
| S3_naive_merge | 5 | 0.913 |
| S3_naive_merge | 10 | 0.983 |
| S3_naive_merge | 15 | 0.985 |
| S3_naive_merge | 25 | 1.000 |
| S4_calibrated | 5 | 0.974 |
| S4_calibrated | 10 | 1.000 |
| S4_calibrated | 15 | 1.000 |
| S4_calibrated | 25 | 1.000 |

OpenBLAS Haswell `R` is runtime-derived and is intentionally left missing rather than guessed.

## Claim boundary

This ablation compares source-labelled soft rankings on the same BLIS-hard-valid candidate pool. It does not claim that an OpenBLAS 8x4 internal kernel can be called through the BLIS 6x16 packing ABI. Outcomes are offline replays of real compiled runs.
