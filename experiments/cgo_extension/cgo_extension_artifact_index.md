# CGO Extension Artifact Index

## Reproduce

```bash
python3 scripts/run_local_extension.py
```

## Primary evidence

- `processed/cgo_extension_summary.json`: combined machine-readable status and paired comparisons.
- `processed/f64_contract_summary.json`: 36-shape f64 dgemm 6x8 Contract study.
- `raw/f64_contract_trials.csv`: all independent f64 trial measurements.
- `raw/true_online_traces.csv`: fresh-process select/execute/update trajectories.
- `raw/optuna_traces.csv`: equal-budget Optuna TPE unique evaluations.
- `raw/optuna_callbacks.csv`: complete and pruned-duplicate TPE callbacks.
- `processed/multisource_fixed_budget.csv`: source-labelled prior ablation.
- `reports/cgo_extension_results.md`: consolidated interpretation and boundaries.
- `provenance/cgo_extension_manifest.json`: hashes of formal summaries and report.

## Boundary

These files support additional-dtype/Contract, true-online, tuner-baseline, and
multi-source soft-prior claims on the local x86 host. Cross-host performance is
tracked by `../x86_cross_host` and remains pending until its returned archive is
imported.
