#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${PROJECT_DIR}/../../.." && pwd)"
CXX="${CXX:-${REPO_ROOT}/llvm/build/bin/clang++}"
RESULT_DIR="${PROJECT_DIR}/results"
OUT_DIR="${PROJECT_DIR}/outputs"
mkdir -p "${RESULT_DIR}" "${OUT_DIR}"

BIN="${OUT_DIR}/cpu_matmul_bench"
"${CXX}" -O3 -march=native -std=c++17 "${PROJECT_DIR}/scripts/cpu_matmul_bench.cpp" -o "${BIN}"
"${BIN}" > "${RESULT_DIR}/cpu_initial_results.csv"

{
  echo "# CPU MatMul Benchmark"
  echo
  echo "Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "## Platform"
  echo
  echo "- CPU: Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz"
  echo "- Compiler: $(${CXX} --version | head -n 1)"
  echo "- Flags: -O3 -march=native -std=c++17"
  echo
  echo "## Results"
  echo
  echo '```csv'
  cat "${RESULT_DIR}/cpu_initial_results.csv"
  echo '```'
  echo
  echo "Note: this is a native C++ schedule benchmark mirroring the tile sizes used by the Transform Dialect scripts. It is an initial latency sanity check, not the final MLIR AOT performance result."
} > "${RESULT_DIR}/cpu_benchmark_summary.md"

echo "Generated ${RESULT_DIR}/cpu_initial_results.csv"
echo "Generated ${RESULT_DIR}/cpu_benchmark_summary.md"
"${PROJECT_DIR}/scripts/refresh_experiment_registry.sh" historical.native_cpp_tile_sanity
