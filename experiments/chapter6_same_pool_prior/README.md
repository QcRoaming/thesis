# Chapter 6 Same-pool Prior Correction

This package repairs the original B2/B3/B4 comparison without modifying the
frozen Chapter 6 artifacts. It uses the complete real f64 Contract corpora from
the i7-10750H and i9-14900 runs.

The corrected protocol has four invariants:

1. `tile_m`, `tile_n`, and `tile_k` are the only active schedule parameters.
   `vectorize` is removed because the current BLIS call adapter does not consume
   it; `pack_mode=ab`, MR, and NR are fixed by the Contract.
2. B2, B3, and B4 use the exact same canonical pool for every workload. The
   methods differ only in BaCO's categorical soft prior. B3/B4 use their top
   prior-ranked candidates as a no-replacement warm start, then PIBO; B2 uses a
   uniform no-replacement DOE and EI.
3. A budget counts unique candidate measurements. The adapter repairs BaCO
   3.0's categorical hash mismatch and masks observed tokens from exact
   finite-domain acquisition; the formal run fails on a duplicate callback.
4. The calibrated prior is fitted on design workloads, selected on validation
   workloads, and frozen before any holdout objective callback.

## Run

From this directory:

```bash
python3 scripts/run_experiment.py
python3 -m unittest discover -s tests -v
```

Use `--smoke` for one workload, one seed, and budget 5. Use `--force` to discard
cached BaCO run traces in this package only.

To complete only the development host while leaving cross-host acceptance
pending:

```bash
python3 scripts/run_experiment.py --environment i7_10750h_wsl2 --force
```

## Main outputs

- `processed/parameter_liveness.csv`: search-parameter liveness audit.
- `processed/same_pool_audit.csv`: per-method pool fingerprints and oracle.
- `processed/fixed_budget_results.csv`: B2/B3/B4 holdout outcomes.
- `processed/paired_comparisons.csv`: workload-clustered paired bootstrap CIs.
- `processed/acceptance_summary.json`: machine-readable verdict for all five
  requested conditions.
- `reports/acceptance_report.md`: concise human-readable result and boundary.
- `provenance/manifest.json`: input/output hashes and runtime metadata.

The full pool oracle is computed only after policy traces are complete and is
never passed to BaCO or to prior construction.
