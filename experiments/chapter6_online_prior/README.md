# Chapter 6 Online Prior Calibration

This package extends the frozen Chapter 6 evidence without modifying it. It
uses the same real Transform/LLVM/AOT/BLIS evaluator and the same 28-candidate
Contract-only pools for every workload.

The protocol is leakage-separated:

- `design`: fit the global calibration posterior;
- `validation`: select prior precision and Thompson temperature;
- `holdout`: run the fixed policy once, with only observations selected by the
  policy revealed online.

Run the complete package with:

```bash
python3 jlq/thesis/experiments/chapter6_online_prior/scripts/run_online_prior.py
```

The original Chapter 6 files remain the source for the static-prior result.
This package is the V2 experiment for distinguishing transferable compatibility
knowledge from target-dependent performance knowledge.
