# Sparse calibration external validation

- Environment: `i7_local_sparse_smoke`
- Holdout workloads: 12
- Policy: finite-pool posterior Thompson ordering; every holdout target is read only after the ordering is frozen.

## Expert+Data vs Data-only

| Calibration rows | Search budget | Speedup | 95% CI | Significant |
|---:|---:|---:|---:|:---:|
| 5 | 5 | 1.0462x | [0.9482, 1.1664] | no |
| 5 | 10 | 1.0181x | [0.9483, 1.0986] | no |
| 10 | 5 | 0.9714x | [0.8748, 1.0729] | no |
| 10 | 10 | 0.9869x | [0.9300, 1.0525] | no |

## Cost boundary

Calibration cost includes measured benchmark-process wall time, model fitting, and unique candidate compilation where requested. Break-even is reported rather than assumed.

This report is a finite-pool replay over an independently measured target corpus. It is not a new live compilation run and it does not establish end-to-end model speedup.
