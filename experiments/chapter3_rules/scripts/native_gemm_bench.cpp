#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

namespace {

using Clock = std::chrono::steady_clock;

int positive(const char *text, const char *name) {
  const long value = std::strtol(text, nullptr, 10);
  if (value <= 0) {
    std::cerr << name << " must be positive\n";
    std::exit(2);
  }
  return static_cast<int>(value);
}

void fillInputs(int m, int k, int n, std::vector<float> &a,
                std::vector<float> &b) {
  for (int i = 0; i < m; ++i)
    for (int p = 0; p < k; ++p)
      a[static_cast<size_t>(i) * k + p] =
          static_cast<float>(((i * 17 + p * 13) % 101) - 50) / 101.0f;
  for (int p = 0; p < k; ++p)
    for (int j = 0; j < n; ++j)
      b[static_cast<size_t>(p) * n + j] =
          static_cast<float>(((p * 19 + j * 7) % 97) - 48) / 97.0f;
}

void referenceGemm(int m, int k, int n, const float *a, const float *b,
                   float *c) {
  std::fill(c, c + static_cast<size_t>(m) * n, 0.0f);
  for (int i = 0; i < m; ++i)
    for (int p = 0; p < k; ++p) {
      const float av = a[static_cast<size_t>(i) * k + p];
      for (int j = 0; j < n; ++j)
        c[static_cast<size_t>(i) * n + j] +=
            av * b[static_cast<size_t>(p) * n + j];
    }
}

template <bool Vectorize>
inline void updateRow(int width, float av, const float *b, float *c) {
  if constexpr (Vectorize) {
#pragma clang loop vectorize(enable)
    for (int j = 0; j < width; ++j)
      c[j] += av * b[j];
  } else {
#pragma clang loop vectorize(disable)
    for (int j = 0; j < width; ++j)
      c[j] += av * b[j];
  }
}

template <bool Vectorize>
void unpackedGemm(int m, int k, int n, int tm, int tn, int tk, int mr,
                  int nr, const float *a, const float *b, float *c) {
  for (int jj = 0; jj < n; jj += tn) {
    const int jEnd = std::min(jj + tn, n);
    for (int kk = 0; kk < k; kk += tk) {
      const int kEnd = std::min(kk + tk, k);
      for (int ii = 0; ii < m; ii += tm) {
        const int iEnd = std::min(ii + tm, m);
        for (int ir = ii; ir < iEnd; ir += mr) {
          const int irEnd = std::min(ir + mr, iEnd);
          for (int jr = jj; jr < jEnd; jr += nr) {
            const int jrEnd = std::min(jr + nr, jEnd);
            for (int i = ir; i < irEnd; ++i)
              for (int p = kk; p < kEnd; ++p)
                updateRow<Vectorize>(
                    jrEnd - jr, a[static_cast<size_t>(i) * k + p],
                    b + static_cast<size_t>(p) * n + jr,
                    c + static_cast<size_t>(i) * n + jr);
          }
        }
      }
    }
  }
}

template <bool Vectorize>
void packedGemm(int m, int k, int n, int tm, int tn, int tk, int mr, int nr,
                const float *a, const float *b, float *c,
                std::vector<float> &packedA, std::vector<float> &packedB) {
  for (int jj = 0; jj < n; jj += tn) {
    const int jn = std::min(tn, n - jj);
    for (int kk = 0; kk < k; kk += tk) {
      const int kn = std::min(tk, k - kk);
      for (int p = 0; p < kn; ++p)
        std::copy_n(b + static_cast<size_t>(kk + p) * n + jj, jn,
                    packedB.data() + static_cast<size_t>(p) * jn);
      for (int ii = 0; ii < m; ii += tm) {
        const int im = std::min(tm, m - ii);
        for (int i = 0; i < im; ++i)
          std::copy_n(a + static_cast<size_t>(ii + i) * k + kk, kn,
                      packedA.data() + static_cast<size_t>(i) * kn);
        for (int ir = 0; ir < im; ir += mr) {
          const int irEnd = std::min(ir + mr, im);
          for (int jr = 0; jr < jn; jr += nr) {
            const int jrEnd = std::min(jr + nr, jn);
            for (int i = ir; i < irEnd; ++i)
              for (int p = 0; p < kn; ++p)
                updateRow<Vectorize>(
                    jrEnd - jr, packedA[static_cast<size_t>(i) * kn + p],
                    packedB.data() + static_cast<size_t>(p) * jn + jr,
                    c + static_cast<size_t>(ii + i) * n + jj + jr);
          }
        }
      }
    }
  }
}

template <bool Vectorize>
void runGemm(bool packing, int m, int k, int n, int tm, int tn, int tk,
             int mr, int nr, const float *a, const float *b, float *c,
             std::vector<float> &packedA, std::vector<float> &packedB) {
  if (packing)
    packedGemm<Vectorize>(m, k, n, tm, tn, tk, mr, nr, a, b, c, packedA,
                          packedB);
  else
    unpackedGemm<Vectorize>(m, k, n, tm, tn, tk, mr, nr, a, b, c);
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 13) {
    std::cerr << "usage: native_gemm_bench M K N TM TN TK MR NR PACK VECTORIZE "
                 "WARMUPS REPEATS\n";
    return 2;
  }
  const int m = positive(argv[1], "M");
  const int k = positive(argv[2], "K");
  const int n = positive(argv[3], "N");
  const int tm = positive(argv[4], "TM");
  const int tn = positive(argv[5], "TN");
  const int tk = positive(argv[6], "TK");
  const int mr = positive(argv[7], "MR");
  const int nr = positive(argv[8], "NR");
  const bool packing = std::string(argv[9]) == "1";
  const bool vectorize = std::string(argv[10]) == "1";
  const int warmups = positive(argv[11], "WARMUPS");
  const int repeats = positive(argv[12], "REPEATS");

  std::vector<float> a(static_cast<size_t>(m) * k);
  std::vector<float> b(static_cast<size_t>(k) * n);
  std::vector<float> c(static_cast<size_t>(m) * n);
  std::vector<float> reference(static_cast<size_t>(m) * n);
  std::vector<float> packedA(static_cast<size_t>(tm) * tk);
  std::vector<float> packedB(static_cast<size_t>(tk) * tn);
  fillInputs(m, k, n, a, b);
  referenceGemm(m, k, n, a.data(), b.data(), reference.data());

  std::vector<double> samples;
  for (int sample = 0; sample < warmups + repeats; ++sample) {
    std::fill(c.begin(), c.end(), 0.0f);
    const auto start = Clock::now();
    if (vectorize)
      runGemm<true>(packing, m, k, n, tm, tn, tk, mr, nr, a.data(),
                    b.data(), c.data(), packedA, packedB);
    else
      runGemm<false>(packing, m, k, n, tm, tn, tk, mr, nr, a.data(),
                     b.data(), c.data(), packedA, packedB);
    const auto end = Clock::now();
    if (sample >= warmups)
      samples.push_back(
          std::chrono::duration<double, std::milli>(end - start).count());
  }
  std::sort(samples.begin(), samples.end());
  const double medianMs = samples[samples.size() / 2];
  const double operations = 2.0 * m * k * n;
  const double gflops = operations / (medianMs * 1.0e6);
  float maxDiff = 0.0f;
  for (size_t index = 0; index < c.size(); ++index)
    maxDiff = std::max(maxDiff, std::fabs(c[index] - reference[index]));
  const bool correct = maxDiff <= 2.0e-3f;

  std::cout << std::fixed << std::setprecision(8)
            << "{\"median_ms\":" << medianMs << ",\"gflops\":" << gflops
            << ",\"max_abs_diff\":" << maxDiff << ",\"status\":\""
            << (correct ? "PASS" : "FAIL") << "\"}\n";
  return correct ? 0 : 1;
}
