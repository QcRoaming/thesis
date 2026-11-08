# Chapter 3 Multi-source Artifact Index

- Reproduction entry: `scripts/run_multisource.py`
- Source extractor: `scripts/extract_multisource.py`
- Multi-source facts: `data/multisource_facts.yaml`
- Backend contracts: `data/multisource_contracts.yaml`
- Conflict audit: `data/conflicts.yaml`
- Machine-readable summary: `processed/summary.json`
- OpenBLAS build/runtime validation: `raw/openblas_validation.csv`
- Human-readable result: `reports/multisource_results.md`
- Provenance and hashes: `provenance/manifest.json`
- Tests: `tests/test_multisource.py`

Compatibility facts are hard and backend-specific. Performance facts are soft
priors and are not treated as universal constraints.
