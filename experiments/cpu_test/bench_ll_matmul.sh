#!/usr/bin/env bash
set -euo pipefail

LL_FILE="${1:?usage: ./bench_ll_matmul.sh path/to/matmul.ll [N]}"
USER_N="${2:-}"

CXX="/buddy-mlir/llvm/build/bin/clang++"
CXXFLAGS="${CXXFLAGS:--O3}"
WARMUPS="${WARMUPS:-3}"
REPEATS="${REPEATS:-11}"

OUT_DIR="${OUT_DIR:-./cpu_test/ll_bench_build}"
mkdir -p "${OUT_DIR}"

BASE_NAME="$(basename "${LL_FILE}" .ll)"
DRIVER_CPP="${OUT_DIR}/${BASE_NAME}_driver.cpp"
EXE="${OUT_DIR}/${BASE_NAME}_bench"

# 1. 找普通 MLIR lowered 函数，比如 @matmul_128_f32
BASE_FUNC="$(
  grep -nE '^[[:space:]]*define[[:space:]].*@.*matmul' "${LL_FILE}" \
    | grep -v '_mlir_ciface_' \
    | sed -nE 's/.*@([^ (]+).*/\1/p' \
    | head -n 1 || true
)"

CIFACE_FUNC="$(
  grep -nE '^[[:space:]]*define[[:space:]].*@_mlir_ciface_.*matmul' "${LL_FILE}" \
    | sed -nE 's/.*@([^ (]+).*/\1/p' \
    | head -n 1 || true
)"

if [[ -z "${BASE_FUNC}" && -z "${CIFACE_FUNC}" ]]; then
  echo "error: cannot find matmul function in ${LL_FILE}" >&2
  grep -n "define" "${LL_FILE}" | head -20 >&2
  exit 1
fi

if [[ -z "${BASE_FUNC}" ]]; then
  BASE_FUNC="${CIFACE_FUNC#_mlir_ciface_}"
fi

CALL_MODE="expanded"
CALL_FUNC="${BASE_FUNC}"

if [[ -n "${CIFACE_FUNC}" ]]; then
  CIFACE_LINE="$(grep -E "^[[:space:]]*define[[:space:]].*@${CIFACE_FUNC}\\(" "${LL_FILE}" | head -n 1 || true)"
  PTR_COUNT="$(echo "${CIFACE_LINE}" | grep -o 'ptr' | wc -l || true)"

  if [[ "${PTR_COUNT}" == "3" ]]; then
    CALL_MODE="ciface_3ptr"
    CALL_FUNC="${CIFACE_FUNC}"
  elif [[ "${PTR_COUNT}" == "4" ]]; then
    CALL_MODE="ciface_4ptr_return"
    CALL_FUNC="${CIFACE_FUNC}"
  else
    CALL_MODE="expanded"
    CALL_FUNC="${BASE_FUNC}"
  fi
fi

# 3. 解析矩阵大小 N
# 优先从用户参数取；否则从函数名 matmul_128_f32 中解析 128。
if [[ -n "${USER_N}" ]]; then
  N="${USER_N}"
else
  N="$(echo "${BASE_FUNC}" | sed -nE 's/.*matmul_([0-9]+)_f32.*/\1/p')"
fi

if [[ -z "${N}" ]]; then
  echo "error: cannot infer N from function name: ${BASE_FUNC}" >&2
  echo "please pass N manually, e.g.:" >&2
  echo "  ./bench_ll_matmul.sh ${LL_FILE} 128" >&2
  exit 1
fi

echo "LL_FILE   = ${LL_FILE}"
echo "BASE_FUNC = ${BASE_FUNC}"
echo "CALL_MODE = ${CALL_MODE}"
echo "CALL_FUNC = ${CALL_FUNC}"
echo "N         = ${N}"
echo "CXX       = ${CXX}"
echo "CXXFLAGS  = ${CXXFLAGS}"
echo

# 4. 生成 C++ driver

cat > "${DRIVER_CPP}" <<EOF
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <vector>

using Clock = std::chrono::steady_clock;

struct MemRef2D {
  float *allocated;
  float *aligned;
  int64_t offset;
  int64_t sizes[2];
  int64_t strides[2];
};

static MemRef2D make_memref_2d(float *data, int64_t n) {
  MemRef2D m;
  m.allocated = data;
  m.aligned = data;
  m.offset = 0;
  m.sizes[0] = n;
  m.sizes[1] = n;
  m.strides[0] = n;
  m.strides[1] = 1;
  return m;
}

static void fill_inputs(int n, std::vector<float> &A, std::vector<float> &B) {
  for (int i = 0; i < n; ++i) {
    for (int k = 0; k < n; ++k) {
      A[i * n + k] =
          static_cast<float>(((i * 17 + k * 13) % 101) - 50) / 101.0f;
    }
  }

  for (int k = 0; k < n; ++k) {
    for (int j = 0; j < n; ++j) {
      B[k * n + j] =
          static_cast<float>(((k * 19 + j * 7) % 97) - 48) / 97.0f;
    }
  }
}

static void matmul_ref(int n, const float *A, const float *B, float *C) {
  for (int i = 0; i < n; ++i) {
    for (int j = 0; j < n; ++j) {
      float acc = 0.0f;
      for (int k = 0; k < n; ++k) {
        acc += A[i * n + k] * B[k * n + j];
      }
      C[i * n + j] = acc;
    }
  }
}

static float max_abs_diff(const std::vector<float> &X,
                          const std::vector<float> &Y) {
  float max_diff = 0.0f;
  for (std::size_t i = 0; i < X.size(); ++i) {
    max_diff = std::max(max_diff, std::fabs(X[i] - Y[i]));
  }
  return max_diff;
}

static float checksum(const std::vector<float> &X) {
  volatile float sink = 0.0f;
  for (float v : X) {
    sink += v;
  }
  return sink;
}

EOF

if [[ "${CALL_MODE}" == "ciface_3ptr" ]]; then
cat >> "${DRIVER_CPP}" <<EOF
extern "C" void ${CALL_FUNC}(MemRef2D *A, MemRef2D *B, MemRef2D *C);

static void call_kernel(MemRef2D &A, MemRef2D &B, MemRef2D &C) {
  ${CALL_FUNC}(&A, &B, &C);
}

EOF

elif [[ "${CALL_MODE}" == "ciface_4ptr_return" ]]; then
cat >> "${DRIVER_CPP}" <<EOF
extern "C" void ${CALL_FUNC}(MemRef2D *Result, MemRef2D *A, MemRef2D *B, MemRef2D *C);

static void call_kernel(MemRef2D &A, MemRef2D &B, MemRef2D &C) {
  MemRef2D Result{};
  ${CALL_FUNC}(&Result, &A, &B, &C);
}

EOF
else
cat >> "${DRIVER_CPP}" <<EOF
extern "C" MemRef2D ${CALL_FUNC}(
    float *A_alloc, float *A_aligned, int64_t A_offset,
    int64_t A_size0, int64_t A_size1,
    int64_t A_stride0, int64_t A_stride1,

    float *B_alloc, float *B_aligned, int64_t B_offset,
    int64_t B_size0, int64_t B_size1,
    int64_t B_stride0, int64_t B_stride1,

    float *C_alloc, float *C_aligned, int64_t C_offset,
    int64_t C_size0, int64_t C_size1,
    int64_t C_stride0, int64_t C_stride1);

static void call_kernel(MemRef2D &A, MemRef2D &B, MemRef2D &C) {
  (void)${CALL_FUNC}(
      A.allocated, A.aligned, A.offset,
      A.sizes[0], A.sizes[1],
      A.strides[0], A.strides[1],

      B.allocated, B.aligned, B.offset,
      B.sizes[0], B.sizes[1],
      B.strides[0], B.strides[1],

      C.allocated, C.aligned, C.offset,
      C.sizes[0], C.sizes[1],
      C.strides[0], C.strides[1]);
}

EOF
fi

cat >> "${DRIVER_CPP}" <<EOF
int main() {
  constexpr int N = ${N};
  constexpr int warmups = ${WARMUPS};
  constexpr int repeats = ${REPEATS};
  std::string func_name = "${BASE_FUNC}";

  std::vector<float> A(static_cast<std::size_t>(N) * N);
  std::vector<float> B(static_cast<std::size_t>(N) * N);
  std::vector<float> C(static_cast<std::size_t>(N) * N, 0.0f);
  std::vector<float> Ref(static_cast<std::size_t>(N) * N, 0.0f);

  fill_inputs(N, A, B);
  matmul_ref(N, A.data(), B.data(), Ref.data());

  MemRef2D A_desc = make_memref_2d(A.data(), N);
  MemRef2D B_desc = make_memref_2d(B.data(), N);
  MemRef2D C_desc = make_memref_2d(C.data(), N);

  constexpr int inner_iters = 20;

std::vector<double> samples;
samples.reserve(repeats);

for (int r = 0; r < warmups + repeats; ++r) {
  double total_ms = 0.0;

  for (int it = 0; it < inner_iters; ++it) {
    std::fill(C.begin(), C.end(), 0.0f);

    auto start = Clock::now();
    call_kernel(A_desc, B_desc, C_desc);
    auto end = Clock::now();

    total_ms +=
        std::chrono::duration<double, std::milli>(end - start).count();
  }

  double avg_ms = total_ms / inner_iters;

  if (r >= warmups) {
    samples.push_back(avg_ms);
  }
}

std::sort(samples.begin(), samples.end());

const double median_ms = samples[samples.size() / 2];
const double min_ms = samples.front();
const double max_ms = samples.back();

double mean_ms = 0.0;
for (double v : samples) {
  mean_ms += v;
}
mean_ms /= static_cast<double>(samples.size());

double var_ms = 0.0;
for (double v : samples) {
  const double d = v - mean_ms;
  var_ms += d * d;
}
var_ms /= static_cast<double>(samples.size());

const double stddev_ms = std::sqrt(var_ms);
const double p90_ms = samples[static_cast<std::size_t>(samples.size() * 0.9)];

const double flops = 2.0 * N * N * N;
const double gflops = flops / (median_ms / 1000.0) / 1.0e9;

const float diff = max_abs_diff(C, Ref);
const float sum = checksum(C);

std::cout
    << "function,N,warmups,repeats,inner_iters,"
    << "median_ms,min_ms,max_ms,mean_ms,stddev_ms,p90_ms,gflops,"
    << "max_abs_diff,checksum\n";

std::cout
    << func_name << ","
    << N << ","
    << warmups << ","
    << repeats << ","
    << inner_iters << ","
    << std::fixed << std::setprecision(4)
    << median_ms << ","
    << min_ms << ","
    << max_ms << ","
    << mean_ms << ","
    << stddev_ms << ","
    << p90_ms << ","
    << std::setprecision(3)
    << gflops << ","
    << std::setprecision(6)
    << diff << ","
    << sum << "\n";

  return diff < 1e-3f ? 0 : 1;
}

EOF

echo "generated driver: ${DRIVER_CPP}"

# 5. 编译 driver.cpp + matmul.ll
"${CXX}" ${CXXFLAGS} "${DRIVER_CPP}" "${LL_FILE}" -o "${EXE}"

echo "built executable: ${EXE}"
echo

# 6. 运行
"${EXE}"