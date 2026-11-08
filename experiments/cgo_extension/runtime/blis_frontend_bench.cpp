#include "blis.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <type_traits>
#include <vector>

#ifndef SCALAR_TYPE
#define SCALAR_TYPE float
#endif

namespace {

using Scalar = SCALAR_TYPE;
using Clock = std::chrono::steady_clock;

int64_t positive(const char *value, const char *name) {
  const long long parsed = std::strtoll(value, nullptr, 10);
  if (parsed <= 0) {
    std::cerr << name << " must be positive\n";
    std::exit(2);
  }
  return static_cast<int64_t>(parsed);
}

void fill(std::vector<Scalar> &a, std::vector<Scalar> &b,
          std::vector<Scalar> &initialC, int64_t m, int64_t k, int64_t n) {
  for (int64_t i = 0; i < m; ++i)
    for (int64_t p = 0; p < k; ++p)
      a[i * k + p] =
          static_cast<Scalar>(((i * 17 + p * 13) % 101) - 50) / Scalar(101);
  for (int64_t p = 0; p < k; ++p)
    for (int64_t j = 0; j < n; ++j)
      b[p * n + j] =
          static_cast<Scalar>(((p * 19 + j * 7) % 97) - 48) / Scalar(97);
  for (int64_t i = 0; i < m; ++i)
    for (int64_t j = 0; j < n; ++j)
      initialC[i * n + j] =
          static_cast<Scalar>(((i * 3 + j * 5) % 23) - 11) / Scalar(113);
}

void reference(const std::vector<Scalar> &a, const std::vector<Scalar> &b,
               const std::vector<Scalar> &initialC,
               std::vector<Scalar> &expected, int64_t m, int64_t k,
               int64_t n) {
  expected = initialC;
  for (int64_t i = 0; i < m; ++i)
    for (int64_t j = 0; j < n; ++j)
      for (int64_t p = 0; p < k; ++p)
        expected[i * n + j] += a[i * k + p] * b[p * n + j];
}

template <typename T> struct BlisGemm;

template <> struct BlisGemm<float> {
  static void run(int64_t m, int64_t n, int64_t k, const float *a,
                  const float *b, float *c) {
    const float alpha = 1.0f;
    const float beta = 1.0f;
    bli_sgemm(BLIS_NO_TRANSPOSE, BLIS_NO_TRANSPOSE, m, n, k, &alpha, a, k, 1,
              b, n, 1, &beta, c, n, 1);
  }
};

template <> struct BlisGemm<double> {
  static void run(int64_t m, int64_t n, int64_t k, const double *a,
                  const double *b, double *c) {
    const double alpha = 1.0;
    const double beta = 1.0;
    bli_dgemm(BLIS_NO_TRANSPOSE, BLIS_NO_TRANSPOSE, m, n, k, &alpha, a, k, 1,
              b, n, 1, &beta, c, n, 1);
  }
};

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
  const int innerIters =
      static_cast<int>(argc > 6 ? positive(argv[6], "inner_iters") : 1);

  std::vector<Scalar> a(static_cast<size_t>(m) * k);
  std::vector<Scalar> b(static_cast<size_t>(k) * n);
  std::vector<Scalar> initialC(static_cast<size_t>(m) * n);
  std::vector<Scalar> c(static_cast<size_t>(m) * n);
  std::vector<Scalar> expected(static_cast<size_t>(m) * n);
  fill(a, b, initialC, m, k, n);
  reference(a, b, initialC, expected, m, k, n);

  bli_init();
  std::vector<double> samples;
  samples.reserve(repeats);
  for (int sample = 0; sample < warmups + repeats; ++sample) {
    double elapsedMs = 0.0;
    for (int iteration = 0; iteration < innerIters; ++iteration) {
      c = initialC;
      const auto start = Clock::now();
      BlisGemm<Scalar>::run(m, n, k, a.data(), b.data(), c.data());
      const auto end = Clock::now();
      elapsedMs += std::chrono::duration<double, std::milli>(end - start).count();
    }
    if (sample >= warmups)
      samples.push_back(elapsedMs / innerIters);
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

  const double absoluteTolerance =
      std::is_same_v<Scalar, float> ? 1.0e-3 : 1.0e-10;
  const double relativeTolerance =
      std::is_same_v<Scalar, float> ? 1.0e-4 : 1.0e-11;
  double maxAbsDiff = 0.0;
  double maxRelDiff = 0.0;
  double checksum = 0.0;
  bool correct = true;
  for (size_t index = 0; index < c.size(); ++index) {
    const double actual = static_cast<double>(c[index]);
    const double wanted = static_cast<double>(expected[index]);
    const double absDiff = std::fabs(actual - wanted);
    const double relDiff = absDiff / std::max(std::fabs(wanted), 1.0e-15);
    maxAbsDiff = std::max(maxAbsDiff, absDiff);
    maxRelDiff = std::max(maxRelDiff, relDiff);
    checksum += actual;
    if (absDiff > absoluteTolerance + relativeTolerance * std::fabs(wanted))
      correct = false;
  }

  const double gflops = 2.0 * static_cast<double>(m) * k * n / (medianMs * 1.0e6);
  std::cout << "m,k,n,median_ms,min_ms,max_ms,mean_ms,stddev_ms,gflops,"
               "max_abs_diff,max_rel_diff,checksum,status\n";
  std::cout << m << ',' << k << ',' << n << ',' << std::fixed
            << std::setprecision(9) << medianMs << ',' << minMs << ',' << maxMs
            << ',' << meanMs << ',' << std::sqrt(variance) << ','
            << std::setprecision(3) << gflops << ',' << std::setprecision(12)
            << maxAbsDiff << ',' << maxRelDiff << ',' << checksum << ','
            << (correct ? "PASS" : "FAIL") << '\n';
  return correct ? 0 : 1;
}
