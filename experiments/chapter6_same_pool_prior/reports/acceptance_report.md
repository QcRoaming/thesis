# Same-pool Calibrated-prior Acceptance Report

Overall status: `FAIL`.

## Requested conditions

| Condition | Status |
|---|---|
| All search parameters completed liveness audit | `PASS` |
| B2/B3/B4 are strict same-pool controls | `PASS` |
| Unique budget and leakage safeguards pass | `PASS` |
| B4 beats no-prior BaCO with CI > 1 on two environments | `FAIL` |
| Common-pool oracle is invariant | `PASS` |

## Protocol

- Canonical pool size range: 23-26.
- Unique-candidate budget: 10; checkpoints: [5, 10].
- Seeds: [11, 29, 41, 73, 101]; no-replacement warm-start samples: 4.
- Active parameters: `tile_m`, `tile_n`, `tile_k`.
- `vectorize` is removed as inactive; `pack_mode=ab`, MR=6, and NR=8 are fixed.
- Holdout pool oracles are added only after policy replay.

## Selected calibration

- `i7_10750h_wsl2`: validation-selected PI model weight `0.25`.
- `i9_14900_linux`: validation-selected PI model weight `0.25`.

## Fixed-budget pool efficiency

| Environment | Method | Budget | Relative to oracle | Oracle hit rate |
|---|---|---:|---:|---:|
| i7_10750h_wsl2 | B2_no_prior_baco | 5 | 0.923 | 33.3% |
| i7_10750h_wsl2 | B2_no_prior_baco | 10 | 0.963 | 40.0% |
| i7_10750h_wsl2 | B3_static_prior_baco | 5 | 0.910 | 50.0% |
| i7_10750h_wsl2 | B3_static_prior_baco | 10 | 0.974 | 75.0% |
| i7_10750h_wsl2 | B4_calibrated_prior_baco | 5 | 0.976 | 66.7% |
| i7_10750h_wsl2 | B4_calibrated_prior_baco | 10 | 0.997 | 83.3% |
| i9_14900_linux | B2_no_prior_baco | 5 | 0.982 | 56.7% |
| i9_14900_linux | B2_no_prior_baco | 10 | 0.993 | 71.7% |
| i9_14900_linux | B3_static_prior_baco | 5 | 0.942 | 38.3% |
| i9_14900_linux | B3_static_prior_baco | 10 | 0.988 | 76.7% |
| i9_14900_linux | B4_calibrated_prior_baco | 5 | 0.975 | 63.3% |
| i9_14900_linux | B4_calibrated_prior_baco | 10 | 0.992 | 70.0% |

## Paired B4 versus B2

A speedup above one favors the calibrated prior. Confidence intervals resample workload clusters.

| Environment | Budget | Speedup | 95% CI | Verdict |
|---|---:|---:|---:|---|
| i7_10750h_wsl2 | 5 | 1.058x | [1.027, 1.092] | better |
| i7_10750h_wsl2 | 10 | 1.035x | [1.011, 1.064] | better |
| i9_14900_linux | 5 | 0.992x | [0.977, 1.007] | inconclusive |
| i9_14900_linux | 10 | 0.999x | [0.990, 1.006] | inconclusive |

## Leakage boundary

B2 samples the DOE uniformly; B3/B4 warm-start from the highest-ranked candidates under their declared soft prior over the same pool. The calibration target vector contains design and validation observations only; holdout entries are `NaN`. During replay, a holdout runtime is read only inside the objective callback after BaCO returns a selected token. The run fails on a duplicate callback, so every formal callback consumes exactly one unique measurement.

## Claim boundary

Offline policy replay over two independently measured, complete f64 Contract corpora. Every method uses the same canonical finite pool and the same unique-candidate budget. Design workloads fit the calibrated prior, validation workloads select hyperparameters, and holdout runtimes are revealed only after BaCO selects a candidate. Results do not establish multithreaded, non-row-major, non-x86, or end-to-end application generalization.
