# Chapter 5 artifact index

- Configuration: `data/experiment_config.json`
- Reproduction entry: `scripts/run_chapter5.py`
- Runtime adapter: `runtime/blis_microkernel_adapter.cpp`
- Packing ABI smoke test: `runtime/wrapper_smoke.cpp`
- Dynamic benchmark driver: `runtime/dynamic_matmul_bench.cpp`
- Transform op definition: `../../../../midend/include/Dialect/Microkernel/TransformOps.td`
- Transform op implementation: `../../../../midend/lib/Dialect/Microkernel/TransformOps.cpp`
- Packing pass: `../../../../midend/lib/Conversion/MatMulOptimization/MatMulBlisMicrokernel.cpp`
- Raw path measurements: `raw/path_results.csv`
- Raw wrapper result: `raw/wrapper_smoke.csv`
- Machine-readable summary: `processed/chapter5_summary.json`
- Result report: `reports/chapter5_results.md`
- Direct-path IR and executable: `build/direct_blis_6x16/`
- Fallback control IR and executable: `build/fallback_vectorized/`
- Dynamic multi-shape trials: `raw/dynamic_multishape_trials.csv`
- Dynamic multi-shape summary: `processed/dynamic_multishape_summary.json`
- Dynamic multi-shape report: `reports/dynamic_multishape_results.md`
- Full reproduction entry: `scripts/run_chapter5_full.py`

The custom Transform op only selects the external callee. Packing and loop
materialization belong to the registered transformation pass; the C++ adapter
only bridges the lowered integer-address ABI to the BLIS microkernel ABI.
