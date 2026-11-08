#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${PROJECT_DIR}/../../.." && pwd)"
MLIR_OPT="${MLIR_OPT:-${REPO_ROOT}/llvm/build/bin/mlir-opt}"
MLIR_TRANSLATE="${MLIR_TRANSLATE:-${REPO_ROOT}/llvm/build/bin/mlir-translate}"
CXX="${CXX:-${REPO_ROOT}/llvm/build/bin/clang++}"
CASE_FILE="${AOT_CASE_FILE:-${PROJECT_DIR}/config/aot_cases.csv}"
CASE_FILTER="${AOT_CASE_FILTER:-.*}"
WARMUPS="${AOT_WARMUPS:-3}"
REPEATS="${AOT_REPEATS:-11}"
INNER_ITERS="${AOT_INNER_ITERS:-5}"
STACK_KB="${AOT_STACK_KB:-65536}"
OUT_DIR="${PROJECT_DIR}/outputs/mlir_aot"
RESULT_DIR="${PROJECT_DIR}/results"
RESULT_CSV="${RESULT_DIR}/mlir_aot_benchmark.csv"
RESULT_MD="${RESULT_DIR}/mlir_aot_benchmark_summary.md"
GENERATOR="${PROJECT_DIR}/scripts/generate_matmul_mlir.py"
DRIVER="${PROJECT_DIR}/scripts/mlir_aot_matmul_bench.cpp"
mkdir -p "${OUT_DIR}" "${RESULT_DIR}"

for tool in "${MLIR_OPT}" "${MLIR_TRANSLATE}" "${CXX}" "${GENERATOR}"; do
  if [[ ! -x "${tool}" ]]; then
    echo "error: required tool is not executable: ${tool}" >&2
    exit 1
  fi
done

now_ns() {
  date +%s%N
}

elapsed_ms() {
  local start_ns="$1"
  local end_ns="$2"
  echo $(( (end_ns - start_ns) / 1000000 ))
}

printf '%s\n' \
  "case,shape,schedule,tile_m,tile_n,tile_k,warmups,repeats,inner_iters,stack_limit_kb,median_ms,min_ms,max_ms,mean_ms,stddev_ms,p90_ms,gflops,max_abs_diff,max_rel_diff,checksum,output_aliases_c,status,lowering_ms,native_compile_ms,llvm_ir_bytes,executable_bytes" \
  > "${RESULT_CSV}"

failures=0

while IFS=, read -r case_name m k n schedule tile_m tile_n tile_k; do
  if [[ "${case_name}" == "case" || -z "${case_name}" || "${case_name}" == \#* ]]; then
    continue
  fi
  if [[ ! "${case_name}" =~ ${CASE_FILTER} ]]; then
    continue
  fi
  if [[ "${schedule}" != "default" && "${schedule}" != "tile" ]]; then
    echo "error: unsupported schedule '${schedule}' in ${CASE_FILE}" >&2
    exit 1
  fi

  symbol="matmul_m${m}_k${k}_n${n}_f32"
  input_mlir="${OUT_DIR}/${case_name}.mlir"
  transformed_mlir="${OUT_DIR}/${case_name}_transformed.mlir"
  llvm_mlir="${OUT_DIR}/${case_name}_llvm.mlir"
  llvm_ir="${OUT_DIR}/${case_name}.ll"
  executable="${OUT_DIR}/${case_name}_bench"

  generator_args=(
    --m "${m}" --k "${k}" --n "${n}"
    --symbol "${symbol}" --output "${input_mlir}"
  )
  if [[ "${schedule}" == "tile" ]]; then
    generator_args+=(--tile-m "${tile_m}" --tile-n "${tile_n}" --tile-k "${tile_k}")
  fi
  "${GENERATOR}" "${generator_args[@]}"

  lower_start="$(now_ns)"
  if [[ "${schedule}" == "tile" ]]; then
    "${MLIR_OPT}" "${input_mlir}" \
      --transform-interpreter \
      -test-transform-dialect-erase-schedule \
      --canonicalize --cse \
      -o "${transformed_mlir}"
  else
    "${MLIR_OPT}" "${input_mlir}" \
      --one-shot-bufferize="bufferize-function-boundaries" \
      --convert-linalg-to-loops \
      --canonicalize --cse \
      -o "${transformed_mlir}"
  fi
  "${MLIR_OPT}" "${transformed_mlir}" --test-lower-to-llvm -o "${llvm_mlir}"
  "${MLIR_TRANSLATE}" --mlir-to-llvmir "${llvm_mlir}" -o "${llvm_ir}"
  lower_end="$(now_ns)"
  lowering_ms="$(elapsed_ms "${lower_start}" "${lower_end}")"

  compile_start="$(now_ns)"
  "${CXX}" -O3 -march=native -std=c++17 \
    -DKERNEL_SYMBOL="${symbol}" \
    -DMATMUL_M="${m}" -DMATMUL_K="${k}" -DMATMUL_N="${n}" \
    "${DRIVER}" "${llvm_ir}" -o "${executable}"
  compile_end="$(now_ns)"
  native_compile_ms="$(elapsed_ms "${compile_start}" "${compile_end}")"

  set +e
  benchmark_output="$(bash -c 'ulimit -s "$1"; exec "$2" "$3" "$4" "$5"' \
    benchmark "${STACK_KB}" "${executable}" "${WARMUPS}" "${REPEATS}" \
    "${INNER_ITERS}" 2>&1)"
  benchmark_exit=$?
  set -e
  if [[ "${benchmark_exit}" == "0" ]]; then
    benchmark_row="$(printf '%s\n' "${benchmark_output}" | tail -n 1)"
  else
    failures=$((failures + 1))
    if [[ "${benchmark_output}" == *","* ]]; then
      benchmark_row="$(printf '%s\n' "${benchmark_output}" | tail -n 1)"
    else
      benchmark_row=",,,,,,,,,,0,RUNTIME_ERROR_${benchmark_exit}"
    fi
    echo "warning: ${case_name} failed at runtime (exit=${benchmark_exit})" >&2
  fi
  llvm_ir_bytes="$(stat -c '%s' "${llvm_ir}")"
  executable_bytes="$(stat -c '%s' "${executable}")"
  shape="${m}x${k}x${n}"
  printf '%s\n' \
    "${case_name},${shape},${schedule},${tile_m},${tile_n},${tile_k},${WARMUPS},${REPEATS},${INNER_ITERS},${STACK_KB},${benchmark_row},${lowering_ms},${native_compile_ms},${llvm_ir_bytes},${executable_bytes}" \
    >> "${RESULT_CSV}"
  echo "completed ${case_name}"
done < "${CASE_FILE}"

cpu_model="$(sed -n 's/^model name[[:space:]]*: //p' /proc/cpuinfo | head -n 1)"
{
  echo "# MLIR AOT MatMul Benchmark"
  echo
  echo "Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "- CPU: ${cpu_model:-unknown}"
  echo "- Compiler: $("${CXX}" --version | head -n 1)"
  echo "- Cases: ${CASE_FILE}"
  echo "- Case filter: ${CASE_FILTER}"
  echo "- Stack limit: ${STACK_KB} KiB"
  echo
  echo '```csv'
  cat "${RESULT_CSV}"
  echo '```'
  echo
  echo "The timed region calls the AOT-compiled MLIR kernel only. Input filling,"
  echo "reference computation, output clearing, and correctness checks are excluded."
  echo "The explicit stack limit is recorded because the generic multi-dimensional"
  echo "vector-to-LLVM lowering currently emits loop-local stack temporaries."
} > "${RESULT_MD}"

echo "Generated ${RESULT_CSV}"
echo "Generated ${RESULT_MD}"
if [[ "${failures}" != "0" ]]; then
  echo "error: ${failures} AOT benchmark case(s) failed" >&2
  exit 1
fi
"${PROJECT_DIR}/scripts/refresh_experiment_registry.sh" historical.host_mlir_aot
