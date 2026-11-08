# Sparse calibration external validation

- Environment: `i9_14900_sparse_external`
- Holdout workloads: 12
- Policy: finite-pool posterior Thompson ordering; every holdout target is read only after the ordering is frozen.

## Expert+Data vs Data-only

| Calibration rows | Search budget | Speedup | 95% CI | Significant |
|---:|---:|---:|---:|:---:|
| 5 | 5 | 0.9952x | [0.9831, 1.0073] | no |
| 5 | 10 | 0.9964x | [0.9868, 1.0049] | no |
| 10 | 5 | 1.0166x | [0.9926, 1.0410] | no |
| 10 | 10 | 1.0117x | [0.9997, 1.0236] | no |
| 20 | 5 | 0.9941x | [0.9762, 1.0104] | no |
| 20 | 10 | 0.9939x | [0.9800, 1.0073] | no |
| 40 | 5 | 0.9968x | [0.9815, 1.0097] | no |
| 40 | 10 | 0.9964x | [0.9889, 1.0024] | no |
| 80 | 5 | 0.9989x | [0.9977, 0.9999] | no |
| 80 | 10 | 0.9999x | [0.9999, 1.0000] | no |

## Cost boundary

Calibration cost includes measured benchmark-process wall time, model fitting, and unique candidate compilation where requested. Break-even is reported rather than assumed.

This report is a finite-pool replay over an independently measured target corpus. It is not a new live compilation run and it does not establish end-to-end model speedup.
