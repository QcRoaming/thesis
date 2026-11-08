# CGO Extension Experiments

This package strengthens the thesis evaluation along four axes without changing
the frozen Chapter 6 corpus:

1. a real online `select -> execute -> update` loop where target observations
   are obtained from a fresh benchmark process after selection;
2. an additional `f64` BLIS Haswell contract using
   `bli_dgemm_haswell_asm_6x8`, including dynamic shapes and fringe adaptation;
3. an Optuna TPE baseline with the same finite pool, unique-evaluation budget,
   seeds, compiler pipeline and benchmark protocol;
4. a source-labelled BLIS/OpenBLAS prior ablation that keeps incompatible hard
   contracts separate and treats blocking values as soft ranking features.

Run the local closed loop with:

```bash
python3 scripts/run_local_extension.py
```

Development smoke tests use `--smoke`. Formal outputs are written to `raw/`,
`processed/`, `reports/`, and `provenance/`; build products and per-invocation
logs are under `build/`.

The driver sets `CGO_EXTENSION_TEST_MODE` so a clean formal run validates only
formal artifacts and a clean smoke run validates only smoke artifacts. Running
the tests directly without that variable retains the combined artifact audit.

The 14900/14900K/14900KF deployment package is maintained separately in
`../x86_cross_host` so an external-host result cannot be confused with a result
measured on the development host.

## Claim boundary

The local package measures one single-threaded x86-64 host. It demonstrates
that compatibility knowledge transfers across `f32` and `f64` BLIS contracts,
and that soft performance knowledge can be calibrated from online feedback.
It does not by itself establish cross-machine generalization; that claim remains
pending until the external-host archive is imported and validated.
