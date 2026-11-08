# f64 BLIS Contract Results

- mode: `smoke`
- status: `PASS`
- contract: `haswell_f64_gemm_6x8`
- workloads: 2
- candidate binaries: 2
- trial rows: 4
- observed paths: `{"adapt": 1, "direct": 1}`
- all checker predictions matched: `True`
- best-candidate/BLIS geometric ratio: 0.348

The ratio is `BLIS frontend time / best generated-candidate time`; values below 1 mean the full BLIS frontend is faster.

## Claim boundary

Single-thread row-major x86-64 results. Target observations in true-online and Optuna trajectories are fresh benchmark subprocesses and are never read from the frozen corpus before selection. The f64 study uses the BLIS Haswell dgemm 6x8 contract. Cross-host evidence is tracked separately.
