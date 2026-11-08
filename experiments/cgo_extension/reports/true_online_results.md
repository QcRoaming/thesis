# True Online Calibration Results

- status: `PASS`
- workloads: 12
- trajectories: 240
- fresh objective processes: 6000
- objective cache hits: 0

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

The frozen full-pool value is used only for posthoc normalization; it is not visible to any policy.

## Claim boundary

Single-thread row-major x86-64 results. Target observations in true-online and Optuna trajectories are fresh benchmark subprocesses and are never read from the frozen corpus before selection. The f64 study uses the BLIS Haswell dgemm 6x8 contract. Cross-host evidence is tracked separately.
