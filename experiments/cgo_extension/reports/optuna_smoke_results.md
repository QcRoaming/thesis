# Optuna TPE Results

- status: `PASS`
- Optuna: `4.9.0`
- unique measurements: 5
- pruned duplicate callbacks: 2

| Budget | Relative to BLIS | Relative to posthoc pool best |
|---:|---:|---:|
| 5 | 0.674 | 0.741 |

Duplicate suggestions are pruned without execution and do not consume the unique-candidate budget.

## Claim boundary

Single-thread row-major x86-64 results. Target observations in true-online and Optuna trajectories are fresh benchmark subprocesses and are never read from the frozen corpus before selection. The f64 study uses the BLIS Haswell dgemm 6x8 contract. Cross-host evidence is tracked separately.
