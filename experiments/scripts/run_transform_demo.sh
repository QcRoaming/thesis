#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${PROJECT_DIR}/../../.." && pwd)"
MLIR_OPT="${MLIR_OPT:-${REPO_ROOT}/llvm/build/bin/mlir-opt}"
MLIR_TRANSLATE="${MLIR_TRANSLATE:-${REPO_ROOT}/llvm/build/bin/mlir-translate}"
LLC="${LLC:-${REPO_ROOT}/llvm/build/bin/llc}"
OBJDUMP="${OBJDUMP:-${REPO_ROOT}/llvm/build/bin/llvm-objdump}"
OUT_DIR="${PROJECT_DIR}/outputs/transform_ir_snapshots"
RESULT_DIR="${PROJECT_DIR}/results"
CASE_SET="${TRANSFORM_CASE_SET:-smoke}"
mkdir -p "${OUT_DIR}" "${RESULT_DIR}"

count_pattern() {
  local file="$1"
  local pattern="$2"
  awk -v pat="${pattern}" 'BEGIN { n = 0 } $0 ~ pat { n++ } END { print n }' "${file}"
}

SMOKE_CASES=(
  matmul_128_f32_tile_16_16_32
  matmul_128_f32_tile_32_32_32
  matmul_256_f32_tile_32_32_32
  matmul_m1_k4096_n11008_f32_tile_1_32_32
)

EXTENDED_CASES=(
  "${SMOKE_CASES[@]}"
  matmul_512_f32_tile_32_32_32
  matmul_1024_f32_tile_32_32_32
  matmul_2048_f32_tile_32_32_32
  matmul_m256_k4096_n4096_f32_tile_32_32_32
  matmul_m256_k4096_n11008_f32_tile_32_32_32
  matmul_m256_k11008_n4096_f32_tile_32_32_32
)

case "${CASE_SET}" in
  smoke)
    CASES=("${SMOKE_CASES[@]}")
    ;;
  extended)
    CASES=("${EXTENDED_CASES[@]}")
    ;;
  *)
    echo "error: TRANSFORM_CASE_SET must be 'smoke' or 'extended'" >&2
    exit 1
    ;;
esac

printf "case\ttransformed_lines\tlinalg_matmul\tscf_for\tvector_contract\tvector_transfer_read\tvector_transfer_write\tscalable_vector_ops\tllvm_lines\tllvm_ir_bytes\trvv_object_bytes\trvv_vsetvli_hits\trvv_vector_hits\n" > "${RESULT_DIR}/transform_metrics.tsv"

for case_name in "${CASES[@]}"; do
  input="${PROJECT_DIR}/mlir/${case_name}.mlir"
  transformed="${OUT_DIR}/${case_name}_transformed.mlir"
  lowered="${OUT_DIR}/${case_name}_llvm.mlir"
  llvm_ir="${OUT_DIR}/${case_name}.ll"
  rvv_obj="${OUT_DIR}/${case_name}_rv64gcv.o"
  rvv_dump="${OUT_DIR}/${case_name}_rv64gcv.objdump.txt"

  if [[ ! -f "${input}" ]]; then
    echo "error: missing Transform input: ${input}" >&2
    exit 1
  fi

  "${MLIR_OPT}" "${input}" \
    --transform-interpreter \
    -test-transform-dialect-erase-schedule \
    --canonicalize --cse \
    -o "${transformed}"

  "${MLIR_OPT}" "${input}" \
    --transform-interpreter \
    -test-transform-dialect-erase-schedule \
    --test-lower-to-llvm \
    -o "${lowered}"

  "${MLIR_TRANSLATE}" --mlir-to-llvmir "${lowered}" -o "${llvm_ir}"
  "${LLC}" -mtriple=riscv64-unknown-elf -mattr=+m,+a,+f,+d,+c,+v -filetype=obj "${llvm_ir}" -o "${rvv_obj}"
  "${OBJDUMP}" -d --mattr=+v "${rvv_obj}" > "${rvv_dump}"

  lines="$(wc -l < "${transformed}" | tr -d ' ')"
  llvm_lines="$(wc -l < "${lowered}" | tr -d ' ')"
  llvm_ir_bytes="$(stat -c '%s' "${llvm_ir}")"
  rvv_object_bytes="$(stat -c '%s' "${rvv_obj}")"
  rvv_vsetvli_hits="$(awk '/vsetvli/ { n++ } END { print n + 0 }' "${rvv_dump}")"
  rvv_hits="$(awk '/vset|vle|vse|vfm|vfadd|vs[0-9]?r\.v|vl[0-9]?re/ { n++ } END { print n + 0 }' "${rvv_dump}")"
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
    "${case_name}" "${lines}" \
    "$(count_pattern "${transformed}" "linalg\\.matmul")" \
    "$(count_pattern "${transformed}" "scf\\.for")" \
    "$(count_pattern "${transformed}" "vector\\.contract")" \
    "$(count_pattern "${transformed}" "vector\\.transfer_read")" \
    "$(count_pattern "${transformed}" "vector\\.transfer_write")" \
    "$(count_pattern "${transformed}" "vector<[^>]*\\[")" \
    "${llvm_lines}" "${llvm_ir_bytes}" "${rvv_object_bytes}" \
    "${rvv_vsetvli_hits}" "${rvv_hits}" >> "${RESULT_DIR}/transform_metrics.tsv"
  echo "completed ${case_name}"
done

{
  echo "# Transform Demo Check"
  echo
  echo "Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "- Case set: ${CASE_SET}"
  echo "- Case count: ${#CASES[@]}"
  echo
  echo "## Tool Versions"
  echo
  echo '```text'
  "${MLIR_OPT}" --version
  "${MLIR_TRANSLATE}" --version | head -n 3
  "${LLC}" --version | sed -n '1,8p'
  echo '```'
  echo
  echo "## Metrics"
  echo
  echo '```text'
  cat "${RESULT_DIR}/transform_metrics.tsv"
  echo '```'
  echo
  echo "## RVV Evidence"
  echo
  echo "The generated LLVM IR was compiled with llc for riscv64 +v. Instruction"
  echo "counts establish code-generation evidence only; they are not performance metrics."
  echo "A zero scalable_vector_ops value means this Transform pipeline still uses"
  echo "fixed-size MLIR vectors even though LLVM may legalize them to RVV instructions."
} > "${RESULT_DIR}/transform_demo_check.md"

echo "Generated ${RESULT_DIR}/transform_metrics.tsv"
echo "Generated ${RESULT_DIR}/transform_demo_check.md"
"${PROJECT_DIR}/scripts/refresh_experiment_registry.sh" historical.transform_rvv_codegen
