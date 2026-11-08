#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <vector>

#ifndef KERNEL_SYMBOL
#error "KERNEL_SYMBOL must name the MLIR-generated function"
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

#ifdef BLIS_ADAPTER_ENABLED
extern "C" void buddy_blis_reset_fringe_calls();
extern "C" uint64_t buddy_blis_get_fringe_calls();
#endif

MemRef2D makeMemRef(float *data, int64_t rows, int64_t cols) {
  return {data, data, 0, {rows, cols}, {cols, 1}};
}

int64_t parsePositive(const char *value, const char *name) {
  const long long parsed = std::strtoll(value, nullptr, 10);
  if (parsed <= 0) {
    std::cerr << name << " must be positive\n";
    std::exit(2);
  }
  return static_cast<int64_t>(parsed);
}

void fillInputs(std::vector<float> &a, std::vector<float> &b,
                std::vector<float> &initialC, int64_t m, int64_t k, int64_t n) {
  for (int64_t i = 0; i < m; ++i)
    for (int64_t p = 0; p < k; ++p)
      a[i * k + p] =
          static_cast<float>(((i * 17 + p * 13) % 101) - 50) / 101.0f;
  for (int64_t p = 0; p < k; ++p)
    for (int64_t j = 0; j < n; ++j)
      b[p * n + j] = static_cast<float>(((p * 19 + j * 7) % 97) - 48) / 97.0f;
  for (int64_t i = 0; i < m; ++i)
    for (int64_t j = 0; j < n; ++j)
      initialC[i * n + j] =
          static_cast<float>(((i * 3 + j * 5) % 23) - 11) / 113.0f;
}

void computeReference(const std::vector<float> &a, const std::vector<float> &b,
                      const std::vector<float> &initialC,
                      std::vector<float> &reference, int64_t m, int64_t k,
                      int64_t n) {
  reference = initialC;
  for (int64_t i = 0; i < m; ++i)
    for (int64_t j = 0; j < n; ++j)
      for (int64_t p = 0; p < k; ++p)
        reference[i * n + j] += a[i * k + p] * b[p * n + j];
}

float element(const MemRef2D &memref, int64_t i, int64_t j) {
  return memref
      .aligned[memref.offset + i * memref.strides[0] + j * memref.strides[1]];
}

} // namespace

int main(int argc, char **argv) {
  if (argc < 4) {
    std::cerr << "usage: benchmark M K N [warmups repeats inner_iters]\n";
    return 2;
  }
  const int64_t m = parsePositive(argv[1], "M");
  const int64_t k = parsePositive(argv[2], "K");
  const int64_t n = parsePositive(argv[3], "N");
  const int warmups =
      static_cast<int>(argc > 4 ? parsePositive(argv[4], "warmups") : 3);
  const int repeats =
      static_cast<int>(argc > 5 ? parsePositive(argv[5], "repeats") : 11);
  const int innerIters =
      static_cast<int>(argc > 6 ? parsePositive(argv[6], "inner_iters") : 1);

  std::vector<float> a(static_cast<size_t>(m) * k);
  std::vector<float> b(static_cast<size_t>(k) * n);
  std::vector<float> initialC(static_cast<size_t>(m) * n);
  std::vector<float> c(static_cast<size_t>(m) * n);
  std::vector<float> reference(static_cast<size_t>(m) * n);
  fillInputs(a, b, initialC, m, k, n);
  computeReference(a, b, initialC, reference, m, k, n);

  MemRef2D aDesc = makeMemRef(a.data(), m, k);
  MemRef2D bDesc = makeMemRef(b.data(), k, n);
  MemRef2D cDesc = makeMemRef(c.data(), m, n);
  MemRef2D resultDesc{};

#ifdef BLIS_ADAPTER_ENABLED
  buddy_blis_reset_fringe_calls();
#endif

  std::vector<double> samples;
  samples.reserve(repeats);
  for (int sample = 0; sample < warmups + repeats; ++sample) {
    double elapsedMs = 0.0;
    for (int iteration = 0; iteration < innerIters; ++iteration) {
      c = initialC;
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
    for (int64_t i = 0; i < m; ++i) {
      for (int64_t j = 0; j < n; ++j) {
        const float actual = element(resultDesc, i, j);
        const float expected = reference[i * n + j];
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

  uint64_t fringeCalls = 0;
#ifdef BLIS_ADAPTER_ENABLED
  fringeCalls = buddy_blis_get_fringe_calls();
#endif
  const double operations = 2.0 * static_cast<double>(m) * k * n;
  const double gflops = operations / (medianMs * 1.0e6);
  const bool aliasesC = resultDesc.aligned == cDesc.aligned;

  std::cout << "m,k,n,median_ms,min_ms,max_ms,mean_ms,stddev_ms,p90_ms,"
               "gflops,max_abs_diff,max_rel_diff,checksum,output_aliases_c,"
               "fringe_calls,status\n";
  std::cout << m << ',' << k << ',' << n << ',' << std::fixed
            << std::setprecision(6) << medianMs << ',' << minMs << ',' << maxMs
            << ',' << meanMs << ',' << std::sqrt(variance) << ','
            << samples[p90Index] << ',' << std::setprecision(3) << gflops << ','
            << std::setprecision(8) << maxAbsDiff << ',' << maxRelDiff << ','
            << checksum << ',' << (aliasesC ? 1 : 0) << ',' << fringeCalls
            << ',' << (correct ? "PASS" : "FAIL") << '\n';
  return correct ? 0 : 1;
}
