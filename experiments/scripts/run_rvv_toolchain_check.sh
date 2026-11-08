#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${PROJECT_DIR}/../../.." && pwd)"
CLANG="${CLANG:-${REPO_ROOT}/llvm/build/bin/clang}"
LLC="${LLC:-${REPO_ROOT}/llvm/build/bin/llc}"
OBJDUMP="${OBJDUMP:-${REPO_ROOT}/llvm/build/bin/llvm-objdump}"
OUT_DIR="${PROJECT_DIR}/outputs/rvv"
RESULT_DIR="${PROJECT_DIR}/results"
mkdir -p "${OUT_DIR}" "${RESULT_DIR}"

SRC="${PROJECT_DIR}/mlir/rvv_saxpy.c"
OBJ="${OUT_DIR}/rvv_saxpy.o"
DUMP="${OUT_DIR}/rvv_saxpy.objdump.txt"
LOG="${OUT_DIR}/rvv_saxpy.vectorize.log"

"${CLANG}" -target riscv64-unknown-elf -march=rv64gcv -mabi=lp64d -O3 \
  -c "${SRC}" -o "${OBJ}" -Rpass=loop-vectorize 2> "${LOG}"
"${OBJDUMP}" -d --mattr=+v "${OBJ}" > "${DUMP}"

vector_hits="$(awk '/vset|vle|vse|vfm|vfadd|vs[0-9]?r\.v|vl[0-9]?re/ { n++ } END { print n + 0 }' "${DUMP}")"

{
  echo "# RVV Toolchain Check"
  echo
  echo "Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "## Tool Versions"
  echo
  echo '```text'
  "${CLANG}" --version
  "${LLC}" --version | sed -n '1,12p'
  echo '```'
  echo
  echo "## Command"
  echo
  echo '```bash'
  echo "${CLANG} -target riscv64-unknown-elf -march=rv64gcv -mabi=lp64d -O3 -c ${SRC} -o ${OBJ} -Rpass=loop-vectorize"
  echo "${OBJDUMP} -d --mattr=+v ${OBJ}"
  echo '```'
  echo
  echo "## Result"
  echo
  echo "- Object file: ${OBJ}"
  echo "- RVV-like instruction hits in objdump: ${vector_hits}"
  echo "- Vectorizer remark:"
  echo
  echo '```text'
  cat "${LOG}"
  echo '```'
  echo
  echo "## Objdump RVV Snippet"
  echo
  echo '```text'
  awk '/vset|vle|vse|vfm|vfadd|vs[0-9]?r\.v|vl[0-9]?re/ { print; shown++; if (shown >= 20) exit }' "${DUMP}"
  echo '```'
  echo
  echo "QEMU/real-board correctness was not executed in this check. For the 2026-06-30 midterm, this is toolchain and instruction-generation evidence while Milk-V Jupiter is not yet available."
} > "${RESULT_DIR}/rvv_toolchain_check.md"

echo "Generated ${RESULT_DIR}/rvv_toolchain_check.md"
"${PROJECT_DIR}/scripts/refresh_experiment_registry.sh" historical.rvv_toolchain
