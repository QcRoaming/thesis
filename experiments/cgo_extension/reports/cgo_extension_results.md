# CGO Extension Results

Overall status: `PASS`

## Additional dtype and Contract

The f64 dgemm 6x8 study covered 36 workloads and 3132 raw trial rows. Direct/adapt prediction agreement was `True`. The geometric best-candidate ratio relative to the full BLIS frontend was 1.064.

## Live tuner comparison

| Method | Budget | Relative to BLIS | Relative to posthoc pool best |
|---|---:|---:|---:|
| C0_random | 5 | 0.445 | 0.818 |
| C0_random | 10 | 0.503 | 0.924 |
| C0_random | 15 | 0.532 | 0.977 |
| C0_random | 25 | 0.548 | 1.006 |
| C1_static_blis | 5 | 0.464 | 0.852 |
| C1_static_blis | 10 | 0.512 | 0.942 |
| C1_static_blis | 15 | 0.546 | 1.003 |
| C1_static_blis | 25 | 0.577 | 1.061 |
| C2_offline_calibrated | 5 | 0.530 | 0.975 |
| C2_offline_calibrated | 10 | 0.552 | 1.015 |
| C2_offline_calibrated | 15 | 0.555 | 1.019 |
| C2_offline_calibrated | 25 | 0.557 | 1.023 |
| C3_online_calibrated | 5 | 0.514 | 0.944 |
| C3_online_calibrated | 10 | 0.525 | 0.965 |
| C3_online_calibrated | 15 | 0.531 | 0.977 |
| C3_online_calibrated | 25 | 0.558 | 1.025 |
| D1_optuna_tpe | 5 | 0.495 | 0.910 |
| D1_optuna_tpe | 10 | 0.531 | 0.976 |
| D1_optuna_tpe | 15 | 0.560 | 1.029 |
| D1_optuna_tpe | 25 | 0.573 | 1.053 |

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
| offline_calibrated_vs_random_budget5 | 60 | 1.192 | [1.055, 1.343] | 0.733 | 0.000 |
| online_calibrated_vs_random_budget5 | 60 | 1.155 | [1.042, 1.277] | 0.800 | 0.000 |
| online_calibrated_vs_optuna_tpe_budget5 | 60 | 1.038 | [0.920, 1.159] | 0.667 | 0.000 |
| online_calibrated_vs_random_budget25 | 60 | 1.018 | [0.977, 1.068] | 0.550 | 0.000 |
| online_calibrated_vs_optuna_tpe_budget25 | 60 | 0.973 | [0.936, 1.006] | 0.467 | 0.000 |
| blis_only_vs_naive_merge_budget5 | 60 | 1.063 | [1.029, 1.103] | 0.167 | 0.833 |
| calibrated_source_prior_vs_naive_merge_budget5 | 60 | 1.067 | [1.018, 1.125] | 0.333 | 0.500 |
| calibrated_source_prior_vs_blis_only_budget5 | 60 | 1.003 | [0.986, 1.021] | 0.333 | 0.500 |
| calibrated_source_prior_vs_naive_merge_budget25 | 60 | 1.000 | [1.000, 1.000] | 0.000 | 1.000 |

## Boundaries

- Compatibility transfer is tested on f32 6x16 and f64 6x8 BLIS Haswell contracts.
- True-online and Optuna target objectives are fresh subprocess measurements.
- Multi-source ranking is an offline replay and never merges incompatible kernel ABIs.
- Cross-host generalization remains pending until a 14900K/KF archive is imported.
