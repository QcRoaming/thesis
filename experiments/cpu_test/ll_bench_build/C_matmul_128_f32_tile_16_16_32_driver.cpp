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

extern "C" void _mlir_ciface_matmul_128_f32(MemRef2D *Result, MemRef2D *A, MemRef2D *B, MemRef2D *C);

static void call_kernel(MemRef2D &A, MemRef2D &B, MemRef2D &C) {
  MemRef2D Result{};
  _mlir_ciface_matmul_128_f32(&Result, &A, &B, &C);
}

int main() {
  constexpr int N = 128;
  constexpr int warmups = 3;
  constexpr int repeats = 11;
  std::string func_name = "matmul_128_f32";

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

