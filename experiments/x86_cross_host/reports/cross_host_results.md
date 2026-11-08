# Intel Core i9-14900 Cross-host Results

Overall status: `PASS`.

## Reproducibility and host evidence

- Development host: `Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz` under `WSL2`.
- Imported CPU: `Intel(R) Core(TM) i9-14900`; pinned logical CPU: `0`.
- Returned archive SHA-256: `b63499c2209f08b41c0d834bd68e391a636d969c50fffd60c266e18b2970baee`.
- Both hosts used the same fixed Buddy, LLVM, BLIS and mimalloc revisions.
- Each host completed 3132 f64 Contract trials over 36 workloads with complete direct/adapt prediction agreement.
- Each host completed 6000 fresh true-online subprocess measurements with zero objective-cache hits and 1500 unique Optuna measurements.

## Cross-host metric comparison

| Metric | i7-10750H development host | i9-14900 |
|---|---:|---:|
| Best generated f64 candidate / complete BLIS, geometric mean | 1.064x | 0.804x |
| f64 Contract trial rows | 3132 | 3132 |
| True-online fresh subprocess rows | 6000 | 6000 |
| Optuna unique measurements | 1500 | 1500 |

The generated candidate pool was 1.064x relative to complete BLIS on the development host, but only 0.804x on the i9-14900. The direction change is direct evidence that source-derived or host-trained performance rankings must not be treated as host-independent constants.

## Paired fixed-budget comparisons

A speedup above one favors the left method. `better` means the 95% paired bootstrap interval is entirely above one; `worse` means it is entirely below one.

| Comparison | Development host | i9-14900 |
|---|---:|---:|
| `offline_calibrated_vs_random_budget5` | 1.192x [1.055, 1.343] (better) | 1.060x [1.041, 1.082] (better) |
| `online_calibrated_vs_random_budget5` | 1.155x [1.042, 1.277] (better) | 1.060x [1.040, 1.082] (better) |
| `online_calibrated_vs_optuna_tpe_budget5` | 1.038x [0.920, 1.159] (inconclusive) | 1.065x [1.044, 1.089] (better) |
| `online_calibrated_vs_random_budget25` | 1.018x [0.977, 1.068] (inconclusive) | 0.991x [0.984, 0.999] (worse) |
| `online_calibrated_vs_optuna_tpe_budget25` | 0.973x [0.936, 1.006] (inconclusive) | 0.995x [0.989, 1.000] (inconclusive) |

## Supported conclusions

1. Hard compatibility knowledge transfers more reliably than performance ranking: both hosts preserve complete Checker-to-runtime agreement over the f64 6x8 Contract.
2. Calibrated priors improve budget-5 sample efficiency over random on both hosts, with both paired bootstrap intervals above one.
3. The i9-14900 run shows a significant budget-5 gain over Optuna TPE, while the development-host interval crosses one. The defensible conclusion is host-dependent low-budget benefit, not universal tuner dominance.
4. At budget 25, the calibrated online policy does not consistently dominate random or Optuna. The method's strongest evidence is early-budget guidance.

The BLIS/OpenBLAS source-labelled ablation remains part of the local CGO extension. It is an offline replay over a shared real measurement corpus and is therefore not counted as an independent cross-host replication.

## Boundary

Two single-thread row-major x86-64 hosts using the same fixed revisions, f64 BLIS Haswell 6x8 Contract, candidate domains and tuner budgets. The result supports transfer of hard compatibility checks and low-budget sample-efficiency trends, but not host-independent absolute schedule ranking, asymptotic tuner superiority, multithreaded behavior or universal x86 generalization.
