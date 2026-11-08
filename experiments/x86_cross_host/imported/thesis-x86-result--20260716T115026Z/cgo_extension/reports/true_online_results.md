# True Online Calibration Results

- status: `PASS`
- workloads: 12
- trajectories: 240
- fresh objective processes: 6000
- objective cache hits: 0

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

The frozen full-pool value is used only for posthoc normalization; it is not visible to any policy.

## Claim boundary

Single-thread row-major x86-64 results. Target observations in true-online and Optuna trajectories are fresh benchmark subprocesses and are never read from the frozen corpus before selection. The f64 study uses the BLIS Haswell dgemm 6x8 contract. Cross-host evidence is tracked separately.
