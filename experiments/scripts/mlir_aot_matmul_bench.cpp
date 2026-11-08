#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

#ifndef KERNEL_SYMBOL
#error "KERNEL_SYMBOL must name the MLIR-generated function"
#endif
#ifndef MATMUL_M
#error "MATMUL_M must be defined"
#endif
#ifndef MATMUL_K
#error "MATMUL_K must be defined"
#endif
#ifndef MATMUL_N
#error "MATMUL_N must be defined"
#endif

#define CONCAT_IMPL(a, b) a##b
#define CONCAT(a, b) CONCAT_IMPL(a, b)
#define C_INTERFACE(symbol) CONCAT(_mlir_ciface_, symbol)

namespace {

using Clock = std::chrono::steady_clock;

struct MemRef2D {
  float *allocated;
  float *aligned;
  int64_t offset;
  int64_t sizes[2];
  int64_t strides[2];
};

extern "C" void C_INTERFACE(KERNEL_SYMBOL)(MemRef2D *result, MemRef2D *a,
                                            MemRef2D *b, MemRef2D *c);

MemRef2D makeMemRef(float *data, int64_t rows, int64_t cols) {
  return {data, data, 0, {rows, cols}, {cols, 1}};
}

void fillInputs(std::vector<float> &a, std::vector<float> &b) {
  for (int64_t i = 0; i < MATMUL_M; ++i) {
    for (int64_t k = 0; k < MATMUL_K; ++k) {
      a[i * MATMUL_K + k] =
          static_cast<float>(((i * 17 + k * 13) % 101) - 50) / 101.0f;
    }
  }
  for (int64_t k = 0; k < MATMUL_K; ++k) {
    for (int64_t j = 0; j < MATMUL_N; ++j) {
      b[k * MATMUL_N + j] =
          static_cast<float>(((k * 19 + j * 7) % 97) - 48) / 97.0f;
    }
  }
}

void computeReference(const std::vector<float> &a,
                      const std::vector<float> &b,
                      std::vector<float> &reference) {
  for (int64_t i = 0; i < MATMUL_M; ++i) {
    for (int64_t j = 0; j < MATMUL_N; ++j) {
      float acc = 0.0f;
      for (int64_t k = 0; k < MATMUL_K; ++k)
        acc += a[i * MATMUL_K + k] * b[k * MATMUL_N + j];
      reference[i * MATMUL_N + j] = acc;
    }
  }
}

float element(const MemRef2D &memref, int64_t i, int64_t j) {
  return memref.aligned[memref.offset + i * memref.strides[0] +
                        j * memref.strides[1]];
}

int parsePositive(const char *value, const char *name) {
  const long parsed = std::strtol(value, nullptr, 10);
  if (parsed <= 0) {
    std::cerr << name << " must be positive\n";
    std::exit(2);
  }
  return static_cast<int>(parsed);
}

} // namespace

int main(int argc, char **argv) {
  const int warmups = argc > 1 ? parsePositive(argv[1], "warmups") : 3;
  const int repeats = argc > 2 ? parsePositive(argv[2], "repeats") : 11;
  const int innerIters = argc > 3 ? parsePositive(argv[3], "inner_iters") : 1;

  std::vector<float> a(static_cast<size_t>(MATMUL_M) * MATMUL_K);
  std::vector<float> b(static_cast<size_t>(MATMUL_K) * MATMUL_N);
  std::vector<float> c(static_cast<size_t>(MATMUL_M) * MATMUL_N, 0.0f);
  std::vector<float> reference(static_cast<size_t>(MATMUL_M) * MATMUL_N);
  fillInputs(a, b);
  computeReference(a, b, reference);

  MemRef2D aDesc = makeMemRef(a.data(), MATMUL_M, MATMUL_K);
  MemRef2D bDesc = makeMemRef(b.data(), MATMUL_K, MATMUL_N);
  MemRef2D cDesc = makeMemRef(c.data(), MATMUL_M, MATMUL_N);
  MemRef2D resultDesc{};

  std::vector<double> samples;
  samples.reserve(repeats);
  for (int sample = 0; sample < warmups + repeats; ++sample) {
    double elapsedMs = 0.0;
    for (int iteration = 0; iteration < innerIters; ++iteration) {
      std::fill(c.begin(), c.end(), 0.0f);
      const auto start = Clock::now();
      C_INTERFACE(KERNEL_SYMBOL)(&resultDesc, &aDesc, &bDesc, &cDesc);
      const auto end = Clock::now();
      elapsedMs +=
          std::chrono::duration<double, std::milli>(end - start).count();
    }
    if (sample >= warmups)
      samples.push_back(elapsedMs / innerIters);
  }

  std::sort(samples.begin(), samples.end());
  const double medianMs = samples[samples.size() / 2];
  const double minMs = samples.front();
  const double maxMs = samples.back();
  double meanMs = 0.0;
  for (double sample : samples)
    meanMs += sample;
  meanMs /= samples.size();
  double variance = 0.0;
  for (double sample : samples) {
    const double delta = sample - meanMs;
    variance += delta * delta;
  }
  variance /= samples.size();
  const size_t p90Index =
      std::min(samples.size() - 1,
               static_cast<size_t>(std::ceil(samples.size() * 0.9)) - 1);

  float maxAbsDiff = 0.0f;
  float maxRelDiff = 0.0f;
  double checksum = 0.0;
  bool correct = resultDesc.aligned != nullptr;
  if (correct) {
    for (int64_t i = 0; i < MATMUL_M; ++i) {
      for (int64_t j = 0; j < MATMUL_N; ++j) {
        const float actual = element(resultDesc, i, j);
        const float expected = reference[i * MATMUL_N + j];
        const float absDiff = std::fabs(actual - expected);
        const float relDiff = absDiff / std::max(std::fabs(expected), 1.0e-6f);
        maxAbsDiff = std::max(maxAbsDiff, absDiff);
        maxRelDiff = std::max(maxRelDiff, relDiff);
        checksum += actual;
        if (absDiff > 1.0e-3f + 1.0e-4f * std::fabs(expected))
          correct = false;
      }
    }
  }

  const double operations =
      2.0 * static_cast<double>(MATMUL_M) * MATMUL_K * MATMUL_N;
  const double gflops = operations / (medianMs * 1.0e6);
  const bool aliasesC = resultDesc.aligned == cDesc.aligned;

  std::cout << "median_ms,min_ms,max_ms,mean_ms,stddev_ms,p90_ms,gflops,"
               "max_abs_diff,max_rel_diff,checksum,output_aliases_c,status\n";
  std::cout << std::fixed << std::setprecision(6) << medianMs << ',' << minMs
            << ',' << maxMs << ',' << meanMs << ',' << std::sqrt(variance)
            << ',' << samples[p90Index] << ',' << std::setprecision(3)
            << gflops << ',' << std::setprecision(8) << maxAbsDiff << ','
            << maxRelDiff << ',' << checksum << ',' << (aliasesC ? 1 : 0)
            << ',' << (correct ? "PASS" : "FAIL") << '\n';
  return correct ? 0 : 1;
}
