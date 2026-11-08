#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <limits>
#include <type_traits>
#include <vector>

#ifndef KERNEL_SYMBOL
#error "KERNEL_SYMBOL must name the MLIR-generated function"
#endif

#ifndef SCALAR_TYPE
#define SCALAR_TYPE float
#endif

#define CONCAT_IMPL(a, b) a##b
#define CONCAT(a, b) CONCAT_IMPL(a, b)
#define C_INTERFACE(symbol) CONCAT(_mlir_ciface_, symbol)

namespace {

using Scalar = SCALAR_TYPE;
using Clock = std::chrono::steady_clock;

struct MemRef2D {
  Scalar *allocated;
  Scalar *aligned;
  int64_t offset;
  int64_t sizes[2];
  int64_t strides[2];
};

extern "C" void C_INTERFACE(KERNEL_SYMBOL)(MemRef2D *result, MemRef2D *a,
                                           MemRef2D *b, MemRef2D *c);
extern "C" void buddy_blis_reset_fringe_calls();
extern "C" uint64_t buddy_blis_get_fringe_calls();

MemRef2D makeMemRef(Scalar *data, int64_t rows, int64_t cols) {
  return {data, data, 0, {rows, cols}, {cols, 1}};
}

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

double projectionWeight(int64_t j) {
  return static_cast<double>((j * 17 + 3) % 29 - 14) / 14.0;
}

Scalar element(const MemRef2D &memref, int64_t i, int64_t j) {
  return memref.aligned[memref.offset + i * memref.strides[0] +
                        j * memref.strides[1]];
}

double projectionError(const std::vector<Scalar> &a,
                       const std::vector<Scalar> &b,
                       const std::vector<Scalar> &initialC,
                       const MemRef2D &actual, int64_t m, int64_t k,
                       int64_t n) {
  std::vector<double> br(static_cast<size_t>(k), 0.0);
  for (int64_t p = 0; p < k; ++p)
    for (int64_t j = 0; j < n; ++j)
      br[p] += static_cast<double>(b[p * n + j]) * projectionWeight(j);
  double worst = 0.0;
  for (int64_t i = 0; i < m; ++i) {
    double expected = 0.0;
    double observed = 0.0;
    for (int64_t p = 0; p < k; ++p)
      expected += static_cast<double>(a[i * k + p]) * br[p];
    for (int64_t j = 0; j < n; ++j) {
      const double weight = projectionWeight(j);
      expected += static_cast<double>(initialC[i * n + j]) * weight;
      observed += static_cast<double>(element(actual, i, j)) * weight;
    }
    worst = std::max(worst,
                     std::fabs(observed - expected) / (1.0 + std::fabs(expected)));
  }
  return worst;
}

} // namespace

int main(int argc, char **argv) {
  if (argc < 4) {
    std::cerr << "usage: benchmark M K N [warmups repeats inner_iters]\n";
    return 2;
  }
  const int64_t m = positive(argv[1], "M");
  const int64_t k = positive(argv[2], "K");
  const int64_t n = positive(argv[3], "N");
  const int warmups = static_cast<int>(argc > 4 ? positive(argv[4], "warmups") : 1);
  const int repeats = static_cast<int>(argc > 5 ? positive(argv[5], "repeats") : 3);
  const int innerIters =
      static_cast<int>(argc > 6 ? positive(argv[6], "inner_iters") : 1);

  std::vector<Scalar> a(static_cast<size_t>(m) * k);
  std::vector<Scalar> b(static_cast<size_t>(k) * n);
  std::vector<Scalar> initialC(static_cast<size_t>(m) * n);
  std::vector<Scalar> c(static_cast<size_t>(m) * n);
  fill(a, b, initialC, m, k, n);
  MemRef2D aDesc = makeMemRef(a.data(), m, k);
  MemRef2D bDesc = makeMemRef(b.data(), k, n);
  MemRef2D cDesc = makeMemRef(c.data(), m, n);
  MemRef2D resultDesc{};
  buddy_blis_reset_fringe_calls();

  std::vector<double> samples;
  samples.reserve(repeats);
  for (int sample = 0; sample < warmups + repeats; ++sample) {
    double elapsedMs = 0.0;
    for (int iteration = 0; iteration < innerIters; ++iteration) {
      c = initialC;
      const auto start = Clock::now();
      C_INTERFACE(KERNEL_SYMBOL)(&resultDesc, &aDesc, &bDesc, &cDesc);
      const auto end = Clock::now();
      elapsedMs += std::chrono::duration<double, std::milli>(end - start).count();
    }
    if (sample >= warmups)
      samples.push_back(elapsedMs / innerIters);
  }
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

  const bool hasOutput = resultDesc.aligned != nullptr;
  const double error = hasOutput
                           ? projectionError(a, b, initialC, resultDesc, m, k, n)
                           : std::numeric_limits<double>::infinity();
  const double tolerance = std::is_same<Scalar, float>::value ? 3.0e-3 : 1.0e-9;
  const bool correct = std::isfinite(error) && error < tolerance;
  double checksum = 0.0;
  if (hasOutput)
    for (int64_t i = 0; i < m; ++i)
      for (int64_t j = 0; j < n; ++j)
        checksum += static_cast<double>(element(resultDesc, i, j));
  const double operations = 2.0 * static_cast<double>(m) * k * n;
  const double gflops = operations / (medianMs * 1.0e6);
  const bool aliasesC = hasOutput && resultDesc.aligned == cDesc.aligned;
  std::cout << "m,k,n,median_ms,min_ms,max_ms,mean_ms,stddev_ms,gflops,"
               "max_abs_diff,max_rel_diff,checksum,output_aliases_c,"
               "fringe_calls,status\n";
  std::cout << m << ',' << k << ',' << n << ',' << std::fixed
            << std::setprecision(9) << medianMs << ',' << minMs << ',' << maxMs
            << ',' << meanMs << ',' << std::sqrt(variance) << ','
            << std::setprecision(3) << gflops << ',' << std::setprecision(12)
            << error << ',' << error << ',' << checksum << ','
            << (aliasesC ? 1 : 0) << ',' << buddy_blis_get_fringe_calls() << ','
            << (correct ? "PASS" : "FAIL") << '\n';
  return correct ? 0 : 1;
}
