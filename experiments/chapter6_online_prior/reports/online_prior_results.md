# Online Prior Calibration Results

## Protocol

- Design cases fit the global posterior; validation cases select hyperparameters.
- Holdout outcomes are not used during fitting or hyperparameter selection.
- During each holdout trajectory, a candidate outcome is revealed only after selection.
- Every objective value comes from the real Chapter 6 Transform/LLVM/AOT/BLIS evaluator.

## Selected Hyperparameters

- prior precision: 10.0
- Thompson temperature: 0.25
- validation mean log simple-regret AUC: 0.009025

## Holdout Best-at-5

| Method | Relative to B5 gmean | Relative to pool best |
|---|---:|---:|
| C0_random | 0.493 | 0.845 |
| C1_static_blis | 0.503 | 0.863 |
| C2_offline_calibrated | 0.568 | 0.974 |
| C3_online_calibrated | 0.563 | 0.966 |
| C4_misleading_online | 0.357 | 0.613 |

## Holdout Best-at-25

| Method | Relative to B5 gmean | 95% workload bootstrap CI | Relative to pool best |
|---|---:|---:|---:|
| C0_random | 0.578 | [0.453, 0.743] | 0.993 |
| C1_static_blis | 0.583 | [0.460, 0.748] | 1.000 |
| C2_offline_calibrated | 0.583 | [0.458, 0.752] | 1.000 |
| C3_online_calibrated | 0.583 | [0.457, 0.749] | 1.000 |
| C4_misleading_online | 0.573 | [0.453, 0.734] | 0.983 |

- design mean Spearman: static=0.080, calibrated=0.635

- validation mean Spearman: static=0.034, calibrated=0.633

- holdout mean Spearman: static=0.167, calibrated=0.685

## Interpretation

- Offline calibration improves low-budget ranking over both random and the static BLIS score.
- On this same-host holdout, per-target online updates do not surpass the already trained offline posterior.
- The misleading-prior negative control is poor at budget 5 but recovers by budget 25, showing that measured feedback can correct a bad soft prior without weakening hard compatibility checks.

## Claim Boundary

Offline sequential replay over real x86 candidate measurements. Design workloads fit the model, validation workloads select hyperparameters, and holdout workloads are used once with fixed settings. Target-workload observations are revealed only after the policy selects that candidate. Cross-host results are not part of this package.
