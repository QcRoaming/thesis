# External validation artifact index

## i9-14900

- Status: `PASS`; the target run is complete (870 correct rows, 290 measurement groups).
- Returned archive: `returned/i9/chapter6-i9-result-20260722T085806Z.tar.gz`.
- Archive SHA-256: `4d3dc241b12e26bb7da20ee18b07613f8cf38ab449b219194196044d1f21b8c5`.
- Imported result: `raw/i9_external/i9_14900_20260722T085806Z/` (compiler build products removed).
- Summary: `processed/i9_external_summary.json` and `reports/i9_external_results.md`.
- The deployment package and target-side run script were removed after result import.

## K230 / RISC-V

- Package: `build/packages/chapter6-k230-openblas-external-validation.tar.gz`
- Size: 123,957 bytes
- SHA-256: `7a6fd7a754bbe07c7f513d998e8fe853e459166f1f4992ef32b41cc320301848`
- ELF: static RV64GCV, entry `0x200000000`
- Required symbols verified: `main`, `cblas_sgemm`, `sgemm_kernel`
- RVV instruction matches in disassembly: 368
- Frozen output: 399 candidate rows + 30 OpenBLAS rows = 429 correct rows

Place the extracted directory at
`CanMV\sdcard\chapter6-k230-openblas-external-validation`, then run from WSL:

```bash
python3 scripts/run_k230_external_via_serial.py \
  --port /dev/ttyACM1 \
  --board-root /sdcard/chapter6-k230-openblas-external-validation \
  --output-dir board_results
```

The serial runner rejects missing candidates, duplicate/missing trials, stale metadata,
incorrect paths, shape/tile mismatches, and any correctness failure.

### Physical result

- Status: `PASS`
- Correct rows: 429/429 across 10 workloads
- Paths selected by the per-workload pool oracle: 8 direct, 2 adapt
- Best generated adapter / complete OpenBLAS geometric relative performance:
  0.6730, workload-bootstrap 95% CI [0.6193, 0.7253]
- Exact eight Qwen shapes: 0.6653 geometric relative performance
- Adapter wins over complete OpenBLAS: 0/10
- Median trial CV across 143 groups: 0.158%; maximum best-adapter CV: 0.300%
- Maximum projection error: 5.99e-6
- Source CSV SHA-256:
  `56054ad3affd5c9d1a12ac903625b4a388f035811115aa49863541ccccce3d02`

Primary result artifacts:

- `processed/k230_external_summary.json`
- `processed/k230_external_summary.csv`
- `processed/k230_external_aggregates.csv`
- `reports/k230_external_results.md`
- `raw/k230_external/board_results_20260722T055157Z/`

## Status

Both targets completed physical measurement and strict import. The retained K230 package
remains an immutable measurement input. The i9 deployment package was removed; its verified
returned result and imported records remain. Neither target supports a claim that the
generated adapter outperforms the complete library on the measured workload set.
