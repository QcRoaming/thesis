# True Online Calibration Results

- status: `PASS`
- workloads: 1
- trajectories: 4
- fresh objective processes: 20
- objective cache hits: 0

| Method | Budget | Relative to BLIS | Relative to posthoc pool best |
|---|---:|---:|---:|
| C0_random | 5 | 0.481 | 0.914 |
| C1_static_blis | 5 | 0.533 | 1.013 |
| C2_offline_calibrated | 5 | 0.571 | 1.086 |
| C3_online_calibrated | 5 | 0.857 | 1.629 |

The frozen full-pool value is used only for posthoc normalization; it is not visible to any policy.

## Claim boundary

Single-thread row-major x86-64 results. Target observations in true-online and Optuna trajectories are fresh benchmark subprocesses and are never read from the frozen corpus before selection. The f64 study uses the BLIS Haswell dgemm 6x8 contract. Cross-host evidence is tracked separately.
