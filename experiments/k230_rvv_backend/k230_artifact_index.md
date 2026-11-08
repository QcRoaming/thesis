# K230 RVV Backend Artifact Index

- Workloads: `data/workloads.json`
- Candidate schedules: `data/candidates.json`
- Runtime harness: `runtime/k230_gemm_bench.c`
- ELF build entry: `scripts/build_k230_elfs.py`
- Board execution entry: `board/run_k230_suite.sh`
- Direct serial execution entry: `scripts/run_board_via_serial.py`
- Board result importer: `scripts/import_board_results.py`
- Imported board CSV and raw logs: `raw/board_results_20260716_rtsmart_valid/`
- Board result summary: `processed/k230_board_summary.json`
- Static ELF files: `build/elf/`
- Disassembly evidence: `build/elf/*.disassembly.txt`
- K230 deployment archive: `build/k230_rvv_backend_deployment.tar.gz`
- Source/toolchain/ELF hashes: `provenance/elf_manifest.json`
- Deployment archive hash: `provenance/deployment_manifest.json`
- Build evidence report: `reports/k230_elf_results.md`
- Generated RVV API bridge: `build/rvv_intrinsic_compat/`
- Artifact tests: `tests/test_k230_artifacts.py`

Current status: `board_results_imported` (560 correct rows, 112 aggregates).
