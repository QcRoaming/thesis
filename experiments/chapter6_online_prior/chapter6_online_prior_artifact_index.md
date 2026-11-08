# Chapter 6 Online Prior Artifact Index

- Configuration: `data/online_prior_config.json`
- Complete 36 x 28 real candidate corpus: `processed/calibration_corpus.csv`
- Added real measurements: `raw/extended_measurement_trials.csv`
- Online trajectories: `raw/online_prior_traces.csv`
- Rank correlations: `processed/rank_correlations.csv`
- Fixed-budget results: `processed/fixed_budget_summary.csv`
- Machine-readable summary: `processed/online_prior_summary.json`
- Human-readable report: `reports/online_prior_results.md`
- Reproduction entry: `scripts/run_online_prior.py`
- Provenance and hashes: `provenance/manifest.json`
- Leakage and trajectory tests: `tests/test_online_prior.py`

This package extends rather than rewrites the frozen Chapter 6 evaluation.
