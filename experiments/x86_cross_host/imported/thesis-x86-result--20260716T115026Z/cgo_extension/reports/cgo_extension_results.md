# CGO Extension Results

Overall status: `PASS`

## Additional dtype and Contract

The f64 dgemm 6x8 study covered 36 workloads and 3132 raw trial rows. Direct/adapt prediction agreement was `True`. The geometric best-candidate ratio relative to the full BLIS frontend was 0.804.

## Live tuner comparison

| Method | Budget | Relative to BLIS | Relative to posthoc pool best |
|---|---:|---:|---:|
| C0_random | 5 | 0.612 | 1.508 |
| C0_random | 10 | 0.640 | 1.579 |
| C0_random | 15 | 0.651 | 1.607 |
| C0_random | 25 | 0.657 | 1.621 |
| C1_static_blis | 5 | 0.621 | 1.532 |
| C1_static_blis | 10 | 0.644 | 1.589 |
| C1_static_blis | 15 | 0.654 | 1.612 |
| C1_static_blis | 25 | 0.656 | 1.619 |
| C2_offline_calibrated | 5 | 0.648 | 1.599 |
| C2_offline_calibrated | 10 | 0.651 | 1.605 |
| C2_offline_calibrated | 15 | 0.651 | 1.606 |
| C2_offline_calibrated | 25 | 0.651 | 1.606 |
| C3_online_calibrated | 5 | 0.648 | 1.599 |
| C3_online_calibrated | 10 | 0.651 | 1.606 |
| C3_online_calibrated | 15 | 0.652 | 1.607 |
| C3_online_calibrated | 25 | 0.652 | 1.607 |
| D1_optuna_tpe | 5 | 0.609 | 1.501 |
| D1_optuna_tpe | 10 | 0.636 | 1.568 |
| D1_optuna_tpe | 15 | 0.645 | 1.592 |
| D1_optuna_tpe | 25 | 0.655 | 1.615 |

## Source-labelled prior ablation

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

## Paired comparisons

A speedup above 1 favors the left method.

| Comparison | Pairs | Speedup | 95% CI | Left win rate | Tie rate |
|---|---:|---:|---:|---:|---:|
| offline_calibrated_vs_random_budget5 | 60 | 1.060 | [1.041, 1.082] | 0.833 | 0.000 |
| online_calibrated_vs_random_budget5 | 60 | 1.060 | [1.040, 1.082] | 0.817 | 0.000 |
| online_calibrated_vs_optuna_tpe_budget5 | 60 | 1.065 | [1.044, 1.089] | 0.767 | 0.000 |
| online_calibrated_vs_random_budget25 | 60 | 0.991 | [0.984, 0.999] | 0.333 | 0.000 |
| online_calibrated_vs_optuna_tpe_budget25 | 60 | 0.995 | [0.989, 1.000] | 0.383 | 0.017 |
| blis_only_vs_naive_merge_budget5 | 60 | 1.063 | [1.029, 1.103] | 0.167 | 0.833 |
| calibrated_source_prior_vs_naive_merge_budget5 | 60 | 1.067 | [1.018, 1.125] | 0.333 | 0.500 |
| calibrated_source_prior_vs_blis_only_budget5 | 60 | 1.003 | [0.986, 1.021] | 0.333 | 0.500 |
| calibrated_source_prior_vs_naive_merge_budget25 | 60 | 1.000 | [1.000, 1.000] | 0.000 | 1.000 |

## Boundaries

- Compatibility transfer is tested on f32 6x16 and f64 6x8 BLIS Haswell contracts.
- True-online and Optuna target objectives are fresh subprocess measurements.
- Multi-source ranking is an offline replay and never merges incompatible kernel ABIs.
- Cross-host generalization remains pending until a 14900-series archive is imported.
