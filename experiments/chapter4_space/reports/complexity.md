# Chapter 4 Complexity And Memory

Let `N=|U|`, `C` be the number of Contracts, `D` the fixed checker dimensions, and `E=|S_exec|`.

- Contract selection: `O(C)` per Task Context.
- Candidate construction and compatibility checking: `O(ND)`; `D` is 11 in the current checker.
- Ranking: `O(E log E)` time.
- Deterministic stratified shell construction: `O(E)` time.
- Materialized artifact memory: `O(N)`; checker working state per candidate is `O(D)`.

## Measured Generation Cost

Each of the six frozen Task Contexts enumerates 2,600 raw candidates. Measurements use `time.perf_counter` and `tracemalloc` in the same generation process.

- Elapsed range: **154.896-238.025 ms**; median **209.269 ms**.
- Per-candidate range: **59.575-91.548 us**.
- Peak traced memory range: **3.815-5.143 MiB**.

These values characterize this bounded implementation and host only; they are not a global optimum or asymptotic proof by measurement.

Source data: `processed/generation_complexity.csv`.
