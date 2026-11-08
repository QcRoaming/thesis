# Application-validation artifact index

## K230 deployment package

- Package: `build/packages/chapter6-k230-mlir-closure-validation.tar.gz`
- Size: 402305 bytes
- SHA-256: `642272d2ebc564ce2689757f0fdf600734a39a1bb6990022e8f67410acc9d0d9`
- ELF SHA-256: `916fde1f63815f5c796e010bcee58b4ffa717dbbd0444862a7f2aa8d5dabab0a`
- ELF entry: `0x200000000`
- Board command: `K230_MLIR_REPS=5 K230_MLIR_WARMUPS=1 sh board/run_k230_mlir_closure.sh`

## Primary evidence

- `processed/qwen_trace_summary.json`
- `raw/qwen_linear_trace.csv`
- `processed/qwen_canonical_trace.csv`
- `processed/qwen_trace_workloads.csv`
- `provenance/k230_mlir_closure_manifest.json`
- `build/k230_mlir_closure/cases/*/input.mlir`
- `build/k230_mlir_closure/cases/*/transformed.mlir`
- `build/k230_mlir_closure/cases/*/kernel.ll`
- `processed/k230_mlir_closure_summary.json`
- `processed/k230_mlir_closure_summary.csv`
- `processed/k230_mlir_closure_aggregates.csv`
- `reports/k230_mlir_closure_results.md`
- `raw/k230_mlir_closure/board_results_*`
- `../chapter6_external_validation/processed/k230_external_summary.json`
- `../chapter6_external_validation/processed/k230_external_summary.csv`
- `../chapter6_external_validation/processed/k230_external_aggregates.csv`
- `../chapter6_external_validation/reports/k230_external_results.md`
- `processed/trace_weighted_summary.json`
- `processed/trace_weighted_policy_summary.csv`
- `reports/trace_weighted_results.md`
- `../chapter6_external_validation/processed/i9_external_summary.json`
- `../chapter6_external_validation/processed/i9_external_summary.csv`
- `../chapter6_external_validation/processed/i9_external_aggregates.csv`
- `../chapter6_external_validation/reports/i9_external_results.md`
- `../chapter6_external_validation/provenance/i9_external_import_manifest.json`

## Diagnostic evidence excluded from performance claims

- `targets/i7_10750h/raw/trials.csv`
- `targets/i7_10750h/processed/summary.json`
- `targets/i7_10750h/processed/stability_audit.csv`
- `targets/i7_10750h/qualification/raw/trials.csv`
- `targets/i7_10750h/qualification/processed/summary.json`
- `targets/i7_10750h/qualification/processed/stability_audit.csv`
- `targets/i7_10750h/qualification/provenance/manifest.json`

## Status boundary

- Qwen trace: `PASS`
- Local exact-shape pool: `FAIL_UNSTABLE`
- Local WSL qualification: `FAIL_UNQUALIFIED`
- K230 closure: `PASS`
- K230 complete candidate pool: `PASS`
- i9 exact-shape candidate pool: `PASS`
- Trace-weighted target analysis: `PASS`
