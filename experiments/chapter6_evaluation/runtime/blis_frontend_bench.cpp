#include "blis.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <vector>

namespace {
using Clock = std::chrono::steady_clock;

int64_t positive(const char *value, const char *name) {
  const long long parsed = std::strtoll(value, nullptr, 10);
  if (parsed <= 0) {
    std::cerr << name << " must be positive\n";
    std::exit(2);
  }
  return static_cast<int64_t>(parsed);
}

void fill(std::vector<float> &a, std::vector<float> &b,
          std::vector<float> &initialC, int64_t m, int64_t k, int64_t n) {
  for (int64_t i = 0; i < m; ++i)
    for (int64_t p = 0; p < k; ++p)
      a[i * k + p] = static_cast<float>(((i * 17 + p * 13) % 101) - 50) / 101.0f;
  for (int64_t p = 0; p < k; ++p)
    for (int64_t j = 0; j < n; ++j)
      b[p * n + j] = static_cast<float>(((p * 19 + j * 7) % 97) - 48) / 97.0f;
  for (int64_t i = 0; i < m; ++i)
    for (int64_t j = 0; j < n; ++j)
      initialC[i * n + j] = static_cast<float>(((i * 3 + j * 5) % 23) - 11) / 113.0f;
}

void reference(const std::vector<float> &a, const std::vector<float> &b,
               const std::vector<float> &initialC, std::vector<float> &out,
               int64_t m, int64_t k, int64_t n) {
  out = initialC;
  for (int64_t i = 0; i < m; ++i)
    for (int64_t j = 0; j < n; ++j)
      for (int64_t p = 0; p < k; ++p)
        out[i * n + j] += a[i * k + p] * b[p * n + j];
}
} // namespace

int main(int argc, char **argv) {
  if (argc < 4) {
    std::cerr << "usage: blis_frontend_bench M K N [warmups repeats inner_iters]\n";
    return 2;
  }
  const int64_t m = positive(argv[1], "M");
  const int64_t k = positive(argv[2], "K");
  const int64_t n = positive(argv[3], "N");
  const int warmups = static_cast<int>(argc > 4 ? positive(argv[4], "warmups") : 2);
  const int repeats = static_cast<int>(argc > 5 ? positive(argv[5], "repeats") : 7);
  const int innerIters = static_cast<int>(argc > 6 ? positive(argv[6], "inner_iters") : 1);

  std::vector<float> a(static_cast<size_t>(m) * k);
  std::vector<float> b(static_cast<size_t>(k) * n);
  std::vector<float> initialC(static_cast<size_t>(m) * n);
  std::vector<float> c(static_cast<size_t>(m) * n);
  std::vector<float> expected(static_cast<size_t>(m) * n);
  fill(a, b, initialC, m, k, n);
  reference(a, b, initialC, expected, m, k, n);

  const float alpha = 1.0f;
  const float beta = 1.0f;
  bli_init();
  std::vector<double> samples;
  samples.reserve(repeats);
  for (int sample = 0; sample < warmups + repeats; ++sample) {
    double elapsed = 0.0;
    for (int iteration = 0; iteration < innerIters; ++iteration) {
      c = initialC;
      const auto start = Clock::now();
      bli_sgemm(BLIS_NO_TRANSPOSE, BLIS_NO_TRANSPOSE, m, n, k, &alpha,
                a.data(), k, 1, b.data(), n, 1, &beta, c.data(), n, 1);
      const auto end = Clock::now();
      elapsed += std::chrono::duration<double, std::milli>(end - start).count();
    }
    if (sample >= warmups)
      samples.push_back(elapsed / innerIters);
  }
  bli_finalize();

  std::sort(samples.begin(), samples.end());
  const double medianMs = samples[samples.size() / 2];
  const double minMs = samples.front();
  const double maxMs = samples.back();
  double meanMs = 0.0;
  for (double value : samples)
    meanMs += value;
  meanMs /= samples.size();
  double variance = 0.0;
  for (double value : samples) {
    const double delta = value - meanMs;
    variance += delta * delta;
  }
  variance /= samples.size();

  float maxAbsDiff = 0.0f;
  float maxRelDiff = 0.0f;
  double checksum = 0.0;
  bool correct = true;
  for (size_t index = 0; index < c.size(); ++index) {
    const float absDiff = std::fabs(c[index] - expected[index]);
    const float relDiff = absDiff / std::max(std::fabs(expected[index]), 1.0e-6f);
    maxAbsDiff = std::max(maxAbsDiff, absDiff);
    maxRelDiff = std::max(maxRelDiff, relDiff);
    checksum += c[index];
    if (absDiff > 1.0e-3f + 1.0e-4f * std::fabs(expected[index]))
      correct = false;
  }
  const double gflops = 2.0 * static_cast<double>(m) * k * n / (medianMs * 1.0e6);
  std::cout << "m,k,n,median_ms,min_ms,max_ms,mean_ms,stddev_ms,gflops,"
               "max_abs_diff,max_rel_diff,checksum,status\n";
  std::cout << m << ',' << k << ',' << n << ',' << std::fixed
            << std::setprecision(6) << medianMs << ',' << minMs << ',' << maxMs
            << ',' << meanMs << ',' << std::sqrt(variance) << ','
            << std::setprecision(3) << gflops << ',' << std::setprecision(8)
            << maxAbsDiff << ',' << maxRelDiff << ',' << checksum << ','
            << (correct ? "PASS" : "FAIL") << '\n';
  return correct ? 0 : 1;
}
