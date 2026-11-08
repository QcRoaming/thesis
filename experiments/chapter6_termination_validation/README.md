# Chapter 6 Termination Validation

This package runs three pre-registered go/no-go checks on the i7-10750H f64
corpus without changing the frozen Chapter 6 artifacts:

1. Data-only versus Expert+Data under an exact same-pool BaCO protocol.
2. Time-to-95%-oracle and calibration-cost amortization.
3. A second BLIS microkernel Contract (`dgemm 6x8`) extension audit.

The hard compatibility Contract is shared by all methods. The ablation tests
only whether BLIS-derived *soft performance* features add value beyond target
measurements and schedule geometry.

## Run

```bash
python3 scripts/run_termination_validation.py
python3 -m unittest discover -s tests -v
```

Use `--force` to discard this package's cached BaCO trajectories. Generated
results are written to `raw/`, `processed/`, `reports/`, and `provenance/`.

The second package is a second real microkernel on the same BLIS Haswell
backend. It is deliberately not reported as an independent backend result.
