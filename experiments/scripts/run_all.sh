#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"${PROJECT_DIR}/scripts/run_transform_demo.sh"
"${PROJECT_DIR}/scripts/run_mlir_aot_benchmark.sh"
if [[ "${RUN_LEGACY_CPP_BENCHMARK:-0}" == "1" ]]; then
  "${PROJECT_DIR}/scripts/run_cpu_benchmark.sh"
fi
"${PROJECT_DIR}/scripts/run_rvv_toolchain_check.sh"
"${PROJECT_DIR}/scripts/run_qemu_correctness.sh"
"${PROJECT_DIR}/scripts/write_summary.py"
echo "All thesis experiments completed."
