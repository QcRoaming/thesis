#define _POSIX_C_SOURCE 200809L

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef K230_ENABLE_RVV
#include <riscv_vector.h>
#endif
#ifdef K230_ENABLE_OPENBLAS
#include <cblas.h>
#endif

typedef struct {
  const char *id;
  int m, n, k;
} workload_t;

typedef struct {
  const char *id;
  const char *implementation;
  const char *source_prior;
  int tm, tn, tk;
} candidate_t;

static const workload_t workloads[] = {
    {"tiny_fringe", 63, 65, 67},       {"anchor", 192, 256, 256},
    {"rect_fringe", 257, 129, 193},    {"wide_fringe", 191, 513, 257},
    {"square_512", 512, 512, 512},     {"tall", 768, 256, 384},
    {"wide", 256, 768, 384},           {"square_1024", 1024, 1024, 1024},
};

static const candidate_t candidates[] = {
    {"scalar", "scalar", "none", 16, 8, 64},
#ifdef K230_ENABLE_RVV
    {"rvv_generic_16x16x64", "rvv", "generic", 16, 16, 64},
    {"rvv_generic_32x32x128", "rvv", "generic", 32, 32, 128},
    {"rvv_blis_16x4x640", "rvv", "BLIS_rv64iv_VLEN128", 16, 4, 640},
    {"rvv_openblas_8x8x240", "rvv", "OpenBLAS_RISCV64_ZVL128B", 8, 8, 240},
    {"rvv_cross_source_16x8x240", "rvv", "cross_source", 16, 8, 240},
#endif
#ifdef K230_ENABLE_OPENBLAS
    {"openblas_full", "openblas", "OpenBLAS_full_SGEMM", 8, 8, 240},
#endif
};

static double now_seconds(void) {
  struct timespec value;
  clock_gettime(CLOCK_MONOTONIC, &value);
  return (double)value.tv_sec + (double)value.tv_nsec * 1.0e-9;
}

static float input_value(size_t index, uint32_t salt) {
  uint32_t x = (uint32_t)index * 1664525u + 1013904223u + salt;
  return ((float)(x & 0xffffu) / 32768.0f - 1.0f) * 0.125f;
}

static void scalar_gemm(const float *a, const float *b, float *c, int m, int n,
                        int k, int tm, int tn, int tk) {
  memset(c, 0, (size_t)m * n * sizeof(float));
  for (int ii = 0; ii < m; ii += tm) {
    int i_end = ii + tm < m ? ii + tm : m;
    for (int kk = 0; kk < k; kk += tk) {
      int k_end = kk + tk < k ? kk + tk : k;
      for (int jj = 0; jj < n; jj += tn) {
        int j_end = jj + tn < n ? jj + tn : n;
        for (int i = ii; i < i_end; ++i)
          for (int p = kk; p < k_end; ++p) {
            float av = a[(size_t)i * k + p];
            for (int j = jj; j < j_end; ++j)
              c[(size_t)i * n + j] += av * b[(size_t)p * n + j];
          }
      }
    }
  }
}

#ifdef K230_ENABLE_RVV
static void rvv_gemm(const float *a, const float *b, float *c, int m, int n,
                     int k, int tm, int tn, int tk) {
  memset(c, 0, (size_t)m * n * sizeof(float));
  for (int ii = 0; ii < m; ii += tm) {
    int i_end = ii + tm < m ? ii + tm : m;
    for (int kk = 0; kk < k; kk += tk) {
      int k_end = kk + tk < k ? kk + tk : k;
      for (int jj = 0; jj < n; jj += tn) {
        int j_end = jj + tn < n ? jj + tn : n;
        for (int i = ii; i < i_end; ++i) {
          int j = jj;
          while (j < j_end) {
            size_t vl = vsetvl_e32m2((size_t)(j_end - j));
            vfloat32m2_t acc = vle32_v_f32m2(c + (size_t)i * n + j, vl);
            for (int p = kk; p < k_end; ++p) {
              vfloat32m2_t bv = vle32_v_f32m2(b + (size_t)p * n + j, vl);
              acc = vfmacc_vf_f32m2(acc, a[(size_t)i * k + p], bv, vl);
            }
            vse32_v_f32m2(c + (size_t)i * n + j, acc, vl);
            j += (int)vl;
          }
        }
      }
    }
  }
}
#endif

static void execute(const candidate_t *candidate, const float *a, const float *b,
                    float *c, int m, int n, int k) {
  if (strcmp(candidate->implementation, "scalar") == 0) {
    scalar_gemm(a, b, c, m, n, k, candidate->tm, candidate->tn, candidate->tk);
    return;
  }
#ifdef K230_ENABLE_RVV
  if (strcmp(candidate->implementation, "rvv") == 0) {
    rvv_gemm(a, b, c, m, n, k, candidate->tm, candidate->tn, candidate->tk);
    return;
  }
#endif
#ifdef K230_ENABLE_OPENBLAS
  if (strcmp(candidate->implementation, "openblas") == 0) {
    cblas_sgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans, m, n, k, 1.0f, a,
                k, b, n, 0.0f, c, n);
    return;
  }
#endif
  fprintf(stderr, "unsupported implementation: %s\n", candidate->implementation);
  exit(4);
}

/* Verify C=A*B with a deterministic projection in O(MK+KN+MN). */
static double projection_error(const float *a, const float *b, const float *c,
                               int m, int n, int k) {
  double *br = (double *)calloc((size_t)k, sizeof(double));
  if (!br)
    return INFINITY;
  for (int p = 0; p < k; ++p)
    for (int j = 0; j < n; ++j) {
      double r = ((j * 17 + 3) % 29 - 14) / 14.0;
      br[p] += (double)b[(size_t)p * n + j] * r;
    }
  double worst = 0.0;
  for (int i = 0; i < m; ++i) {
    double expected = 0.0, observed = 0.0;
    for (int p = 0; p < k; ++p)
      expected += (double)a[(size_t)i * k + p] * br[p];
    for (int j = 0; j < n; ++j) {
      double r = ((j * 17 + 3) % 29 - 14) / 14.0;
      observed += (double)c[(size_t)i * n + j] * r;
    }
    double relative = fabs(observed - expected) / (1.0 + fabs(expected));
    if (relative > worst)
      worst = relative;
  }
  free(br);
  return worst;
}

static int env_int(const char *name, int default_value) {
  const char *text = getenv(name);
  if (!text || !*text)
    return default_value;
  int value = atoi(text);
  return value > 0 ? value : default_value;
}

int main(void) {
  int repetitions = env_int("K230_REPS", 5);
  int warmups = env_int("K230_WARMUPS", 1);
  printf("binary,candidate,implementation,source_prior,workload,m,n,k,tile_m,"
         "tile_n,tile_k,trial,time_seconds,gflops,projection_error,correct\n");
  for (size_t w = 0; w < sizeof(workloads) / sizeof(workloads[0]); ++w) {
    const workload_t *workload = &workloads[w];
    size_t a_count = (size_t)workload->m * workload->k;
    size_t b_count = (size_t)workload->k * workload->n;
    size_t c_count = (size_t)workload->m * workload->n;
    float *a = (float *)malloc(a_count * sizeof(float));
    float *b = (float *)malloc(b_count * sizeof(float));
    float *c = (float *)malloc(c_count * sizeof(float));
    if (!a || !b || !c)
      return 2;
    for (size_t i = 0; i < a_count; ++i)
      a[i] = input_value(i, 17u);
    for (size_t i = 0; i < b_count; ++i)
      b[i] = input_value(i, 71u);
    for (size_t q = 0; q < sizeof(candidates) / sizeof(candidates[0]); ++q) {
      const candidate_t *candidate = &candidates[q];
      fprintf(stderr, "[%s] %s %dx%dx%d\n", K230_BINARY_ID, candidate->id,
              workload->m, workload->n, workload->k);
      for (int warmup = 0; warmup < warmups; ++warmup)
        execute(candidate, a, b, c, workload->m, workload->n, workload->k);
      execute(candidate, a, b, c, workload->m, workload->n, workload->k);
      double error = projection_error(a, b, c, workload->m, workload->n, workload->k);
      int correct = isfinite(error) && error < 2.0e-3;
      for (int trial = 0; trial < repetitions; ++trial) {
        double start = now_seconds();
        execute(candidate, a, b, c, workload->m, workload->n, workload->k);
        double elapsed = now_seconds() - start;
        double gflops = 2.0 * workload->m * workload->n * workload->k /
                        elapsed / 1.0e9;
        printf("%s,%s,%s,%s,%s,%d,%d,%d,%d,%d,%d,%d,%.9g,%.9g,%.9g,%d\n",
               K230_BINARY_ID, candidate->id, candidate->implementation,
               candidate->source_prior, workload->id, workload->m, workload->n,
               workload->k, candidate->tm, candidate->tn, candidate->tk, trial,
               elapsed, gflops, error, correct);
        fflush(stdout);
      }
      if (!correct)
        return 3;
    }
    free(a);
    free(b);
    free(c);
  }
  return 0;
}
