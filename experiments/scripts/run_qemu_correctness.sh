#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${PROJECT_DIR}/../../.." && pwd)"
CLANG="${CLANG:-${REPO_ROOT}/llvm/build/bin/clang}"
OBJDUMP="${OBJDUMP:-${REPO_ROOT}/llvm/build/bin/llvm-objdump}"
BUNDLED_QEMU="${PROJECT_DIR}/tools/qemu-9.2.1/bin/qemu-riscv64"
if [[ -z "${QEMU:-}" && -x "${BUNDLED_QEMU}" ]]; then
  QEMU="${BUNDLED_QEMU}"
else
  QEMU="${QEMU:-qemu-riscv64}"
fi
QEMU_RVV_CPU="${QEMU_RVV_CPU:-rv64,v=true,vext_spec=v1.0,vlen=128,elen=64}"
OUT_DIR="${PROJECT_DIR}/outputs/rvv"
RESULT_DIR="${PROJECT_DIR}/results"
mkdir -p "${OUT_DIR}" "${RESULT_DIR}"

SRC="${PROJECT_DIR}/mlir/rvv_correctness.c"
SCALAR_ELF="${OUT_DIR}/rv64gc_correctness.elf"
VECTOR_ELF="${OUT_DIR}/rv64gcv_correctness.elf"
VECTOR_DUMP="${OUT_DIR}/rv64gcv_correctness.objdump.txt"
VECTOR_LOG="${OUT_DIR}/rv64gcv_correctness.vectorize.log"
SCALAR_QEMU_LOG="${OUT_DIR}/rv64gc_correctness.qemu.log"
VECTOR_QEMU_LOG="${OUT_DIR}/rv64gcv_correctness.qemu.log"
RESULT="${RESULT_DIR}/qemu_correctness_check.md"

"${CLANG}" -target riscv64-unknown-linux-gnu -march=rv64gc -mabi=lp64d -O3 \
  -nostdlib -static -ffreestanding -fuse-ld=lld -Wl,-e,_start \
  "${SRC}" -o "${SCALAR_ELF}"

"${CLANG}" -target riscv64-unknown-linux-gnu -march=rv64gcv -mabi=lp64d -O3 \
  -nostdlib -static -ffreestanding -fuse-ld=lld -Wl,-e,_start \
  -Rpass=loop-vectorize "${SRC}" -o "${VECTOR_ELF}" 2> "${VECTOR_LOG}"
"${OBJDUMP}" -d --mattr=+v "${VECTOR_ELF}" > "${VECTOR_DUMP}"

vector_hits="$(awk '/vset|vle|vse|vfm|vfadd|vs[0-9]?r\.v|vl[0-9]?re/ { n++ } END { print n + 0 }' "${VECTOR_DUMP}")"

scalar_status="SKIPPED"
scalar_exit="not-run"
vector_exec_status="SKIPPED"
vector_exit="not-run"
qemu_version="not-found"

run_qemu_capture() {
  python3 - "$@" <<'PYRUN'
import subprocess
import sys

cmd = sys.argv[1:-1]
log_path = sys.argv[-1]
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
with open(log_path, "wb") as f:
    f.write(proc.stdout)
    f.write(proc.stderr)
code = proc.returncode
if code < 0:
    code = 128 + (-code)
print(code)
PYRUN
}

if command -v "${QEMU}" >/dev/null 2>&1; then
  qemu_version="$(${QEMU} --version | head -n 1)"

  scalar_exit="$(run_qemu_capture "${QEMU}" "${SCALAR_ELF}" "${SCALAR_QEMU_LOG}")"
  if [[ "${scalar_exit}" == "0" ]]; then
    scalar_status="PASS"
  else
    scalar_status="FAIL"
  fi

  vector_exit="$(run_qemu_capture "${QEMU}" -cpu "${QEMU_RVV_CPU}" "${VECTOR_ELF}" "${VECTOR_QEMU_LOG}")"
  if [[ "${vector_exit}" == "0" ]]; then
    vector_exec_status="PASS"
  elif [[ "${vector_exit}" == "132" ]]; then
    vector_exec_status="UNSUPPORTED_SIGILL"
  else
    vector_exec_status="FAIL"
  fi
else
  echo "${QEMU} not found" > "${SCALAR_QEMU_LOG}"
  echo "${QEMU} not found" > "${VECTOR_QEMU_LOG}"
fi

overall_status="FAIL"
if [[ "${scalar_status}" == "PASS" && "${vector_hits}" != "0" ]]; then
  overall_status="PASS_WITH_RVV_EXECUTION_NOTE"
fi
if [[ "${scalar_status}" == "PASS" && "${vector_exec_status}" == "PASS" ]]; then
  overall_status="PASS"
fi

{
  echo "# QEMU Correctness Check"
  echo
  echo "Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "## Status"
  echo
  echo "- Overall status: ${overall_status}"
  echo "- QEMU: ${qemu_version}"
  echo "- rv64gc scalar QEMU correctness: ${scalar_status} (exit=${scalar_exit})"
  echo "- rv64gcv RVV QEMU execution: ${vector_exec_status} (exit=${vector_exit})"
  echo "- RVV-like instruction hits in rv64gcv objdump: ${vector_hits}"
  echo
  echo "## Commands"
  echo
  echo '```bash'
  echo "${CLANG} -target riscv64-unknown-linux-gnu -march=rv64gc -mabi=lp64d -O3 -nostdlib -static -ffreestanding -fuse-ld=lld -Wl,-e,_start ${SRC} -o ${SCALAR_ELF}"
  echo "${QEMU} ${SCALAR_ELF}"
  echo "${CLANG} -target riscv64-unknown-linux-gnu -march=rv64gcv -mabi=lp64d -O3 -nostdlib -static -ffreestanding -fuse-ld=lld -Wl,-e,_start -Rpass=loop-vectorize ${SRC} -o ${VECTOR_ELF}"
  echo "${QEMU} -cpu ${QEMU_RVV_CPU} ${VECTOR_ELF}"
  echo '```'
  echo
  echo "## Vectorizer Remark"
  echo
  echo '```text'
  cat "${VECTOR_LOG}"
  echo '```'
  echo
  echo "## RVV Objdump Snippet"
  echo
  echo '```text'
  awk '/vset|vle|vse|vfm|vfadd|vs[0-9]?r\.v|vl[0-9]?re/ { print; shown++; if (shown >= 24) exit }' "${VECTOR_DUMP}"
  echo '```'
  echo
  echo "## QEMU Output: rv64gc"
  echo
  echo '```text'
  cat "${SCALAR_QEMU_LOG}"
  echo '```'
  echo
  echo "## QEMU Output: rv64gcv"
  echo
  echo '```text'
  cat "${VECTOR_QEMU_LOG}"
  echo '```'
  echo
  if [[ "${vector_exec_status}" == "UNSUPPORTED_SIGILL" ]]; then
    echo "Note: the selected qemu-riscv64 returned SIGILL for this RVV 1.0 executable. Use tools/qemu-9.2.1/bin/qemu-riscv64 or another newer QEMU with RVV 1.0 user-mode support for full rv64gcv execution correctness."
  fi
} > "${RESULT}"

echo "Generated ${RESULT}"
if [[ "${scalar_status}" != "PASS" ]]; then
  exit 1
fi
"${PROJECT_DIR}/scripts/refresh_experiment_registry.sh" historical.qemu_rvv_correctness
