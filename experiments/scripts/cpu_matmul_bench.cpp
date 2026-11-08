#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

namespace {

using Clock = std::chrono::steady_clock;

struct CaseConfig {
  int n;
  int tm;
  int tn;
  int tk;
  const char *name;
};

void fill_inputs(int n, std::vector<float> &a, std::vector<float> &b) {
  for (int i = 0; i < n; ++i) {
    for (int k = 0; k < n; ++k) {
      a[i * n + k] = static_cast<float>(((i * 17 + k * 13) % 101) - 50) / 101.0f;
    }
  }
  for (int k = 0; k < n; ++k) {
    for (int j = 0; j < n; ++j) {
      b[k * n + j] = static_cast<float>(((k * 19 + j * 7) % 97) - 48) / 97.0f;
    }
  }
}

void matmul_default(int n, const float *a, const float *b, float *c) {
  for (int i = 0; i < n; ++i) {
    for (int j = 0; j < n; ++j) {
      float acc = 0.0f;
      for (int k = 0; k < n; ++k) {
        acc += a[i * n + k] * b[k * n + j];
      }
      c[i * n + j] = acc;
    }
  }
}

void matmul_tiled(int n, int tm, int tn, int tk, const float *a, const float *b, float *c) {
  std::fill(c, c + static_cast<std::size_t>(n) * n, 0.0f);
  for (int ii = 0; ii < n; ii += tm) {
    const int i_end = std::min(ii + tm, n);
    for (int jj = 0; jj < n; jj += tn) {
      const int j_end = std::min(jj + tn, n);
      for (int kk = 0; kk < n; kk += tk) {
        const int k_end = std::min(kk + tk, n);
        for (int i = ii; i < i_end; ++i) {
          for (int j = jj; j < j_end; ++j) {
            float acc = c[i * n + j];
            for (int k = kk; k < k_end; ++k) {
              acc += a[i * n + k] * b[k * n + j];
            }
            c[i * n + j] = acc;
          }
        }
      }
    }
  }
}

float max_abs_diff(const std::vector<float> &x, const std::vector<float> &y) {
  float max_diff = 0.0f;
  for (std::size_t i = 0; i < x.size(); ++i) {
    max_diff = std::max(max_diff, std::fabs(x[i] - y[i]));
  }
  return max_diff;
}

float checksum(const std::vector<float> &x) {
  volatile float sink = 0.0f;
  for (float v : x) {
    sink += v;
  }
  return sink;
}

double run_once(const CaseConfig &cfg, const std::vector<float> &a,
                const std::vector<float> &b, std::vector<float> &c) {
  const auto start = Clock::now();
  if (cfg.tm == 0) {
    matmul_default(cfg.n, a.data(), b.data(), c.data());
  } else {
    matmul_tiled(cfg.n, cfg.tm, cfg.tn, cfg.tk, a.data(), b.data(), c.data());
  }
  const auto end = Clock::now();
  return std::chrono::duration<double, std::milli>(end - start).count();
}

} // namespace

int main() {
  std::cout << "workload,shape,schedule,tile_m,tile_n,tile_k,median_ms,min_ms,max_abs_diff,checksum\n";

  const std::vector<int> shapes = {128, 256};
  for (int n : shapes) {
    std::vector<float> a(static_cast<std::size_t>(n) * n);
    std::vector<float> b(static_cast<std::size_t>(n) * n);
    std::vector<float> c(static_cast<std::size_t>(n) * n);
    std::vector<float> reference(static_cast<std::size_t>(n) * n);
    fill_inputs(n, a, b);

    CaseConfig baseline{n, 0, 0, 0, "default_ijk"};
    matmul_default(n, a.data(), b.data(), reference.data());

    std::vector<CaseConfig> cases = {
        baseline,
        {n, 16, 16, 32, "tile_16_16_32"},
        {n, 32, 32, 32, "tile_32_32_32"},
    };

    for (const CaseConfig &cfg : cases) {
      std::vector<double> samples;
      const int warmups = n <= 128 ? 2 : 1;
      const int repeats = n <= 128 ? 11 : 7;
      for (int r = 0; r < warmups + repeats; ++r) {
        std::fill(c.begin(), c.end(), 0.0f);
        double ms = run_once(cfg, a, b, c);
        if (r >= warmups) {
          samples.push_back(ms);
        }
      }
      std::sort(samples.begin(), samples.end());
      const double median = samples[samples.size() / 2];
      const double min_ms = samples.front();
      const float diff = max_abs_diff(c, reference);
      const float sum = checksum(c);
      std::cout << "matmul," << n << "x" << n << "x" << n << ','
                << cfg.name << ',' << cfg.tm << ',' << cfg.tn << ',' << cfg.tk << ','
                << std::fixed << std::setprecision(4) << median << ',' << min_ms << ','
                << std::setprecision(6) << diff << ',' << sum << "\n";
    }
  }
}
