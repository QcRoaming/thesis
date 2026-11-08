#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <vector>

extern "C" void buddy_blis_sgemm_6x16(int64_t k, uintptr_t aBase,
                                      int64_t aOffset, uintptr_t bBase,
                                      int64_t bOffset, uintptr_t cBase,
                                      int64_t cOffset, int64_t cRowStride,
                                      int64_t cColStride);

int main() {
  constexpr int64_t m = 6;
  constexpr int64_t n = 16;
  constexpr int64_t k = 67;

  std::vector<float> a(m * k);
  std::vector<float> b(k * n);
  std::vector<float> packedA(k * m);
  std::vector<float> packedB(k * n);
  std::vector<float> c(m * n, 0.0f);
  std::vector<float> reference(m * n, 0.0f);

  for (int64_t i = 0; i < m; ++i)
    for (int64_t p = 0; p < k; ++p)
      a[i * k + p] =
          static_cast<float>(((i * 17 + p * 13) % 101) - 50) / 101.0f;
  for (int64_t p = 0; p < k; ++p)
    for (int64_t j = 0; j < n; ++j)
      b[p * n + j] = static_cast<float>(((p * 19 + j * 7) % 97) - 48) / 97.0f;

  for (int64_t p = 0; p < k; ++p) {
    for (int64_t i = 0; i < m; ++i)
      packedA[p * m + i] = a[i * k + p];
    for (int64_t j = 0; j < n; ++j)
      packedB[p * n + j] = b[p * n + j];
  }

  for (int64_t i = 0; i < m; ++i)
    for (int64_t j = 0; j < n; ++j)
      for (int64_t p = 0; p < k; ++p)
        reference[i * n + j] += a[i * k + p] * b[p * n + j];

  buddy_blis_sgemm_6x16(k, reinterpret_cast<uintptr_t>(packedA.data()), 0,
                        reinterpret_cast<uintptr_t>(packedB.data()), 0,
                        reinterpret_cast<uintptr_t>(c.data()), 0, n, 1);

  float maxAbsDiff = 0.0f;
  for (size_t index = 0; index < c.size(); ++index)
    maxAbsDiff = std::max(maxAbsDiff, std::fabs(c[index] - reference[index]));

  const bool passed = maxAbsDiff <= 1.0e-4f;
  std::cout << "case,k,max_abs_diff,status\n"
            << "packed_6x16," << k << ',' << std::fixed << std::setprecision(8)
            << maxAbsDiff << ',' << (passed ? "PASS" : "FAIL") << '\n';
  return passed ? 0 : 1;
}
