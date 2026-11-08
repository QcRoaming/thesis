# Chapter 4 to Chapter 5 Integrated Artifact Index

- Configuration: `data/integration_config.json`
- Reproduction entry: `scripts/run_integrated_pipeline.py`
- Chapter 4 source space: `../chapter4_space/processed/spaces/`
- Chapter 5 evaluator implementation: `../chapter5_blis_adapter/`
- Path matrix: `raw/path_matrix.csv`
- BaCO callback log: `raw/baco_callback_log.jsonl`
- BaCO trace: `processed/baco_tuning_trace.csv`
- Machine-readable summary: `processed/integrated_summary.json`
- Human-readable result: `reports/integrated_results.md`
- Tests: `tests/test_integrated_pipeline.py`

This package does not rewrite the frozen Chapter 4 evidence. It imports the
Chapter 4 candidate generator and Compatibility Checker, then evaluates their
decisions through the Chapter 5 packing pass and real BLIS microkernel adapter.
