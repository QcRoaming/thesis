# Transformer region go/no-go artifact index

- Configuration and frozen criteria: `data/experiment_config.json`
- Real BLIS mechanism probe: `runtime/region_fanout_bench.cpp`
- One-command runner: `scripts/run_go_nogo.py`
- Raw paired trials: `raw/region_trials.csv`
- Per-case aggregates: `processed/case_summary.csv`
- Machine-readable decision: `processed/go_nogo_summary.json`
- Human-readable report: `reports/go_nogo_results.md`
- Build and symbol logs: `reports/compile.log`, `reports/symbols.log`
- Host and input hashes: `provenance/manifest.json`
- Artifact tests: `tests/test_go_nogo.py`

The probe intentionally includes concatenated-weight complete BLIS as a strong
baseline. The C++ microkernel paths are mechanism evidence for deciding whether
to implement a later MLIR region planner; they are not presented as that
planner.
