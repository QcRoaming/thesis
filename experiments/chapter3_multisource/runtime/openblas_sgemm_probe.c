#define _POSIX_C_SOURCE 200809L

#include <cblas.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

typedef struct {
  int m;
  int n;
  int k;
} shape_t;

static double now_seconds(void) {
  struct timespec value;
  clock_gettime(CLOCK_MONOTONIC, &value);
  return (double)value.tv_sec + (double)value.tv_nsec * 1.0e-9;
}

static float value_at(size_t index, uint32_t salt) {
  uint32_t x = (uint32_t)index * 1664525u + 1013904223u + salt;
  return ((float)(x & 0xffffu) / 32768.0f - 1.0f) * 0.25f;
}

static int validate(const float *a, const float *b, const float *c, int m,
                    int n, int k, double *max_error) {
  double worst = 0.0;
  for (int i = 0; i < m; ++i) {
    for (int j = 0; j < n; ++j) {
      double expected = 0.0;
      for (int p = 0; p < k; ++p)
        expected += (double)a[(size_t)i * k + p] * b[(size_t)p * n + j];
      double error = fabs(expected - c[(size_t)i * n + j]);
      if (error > worst)
        worst = error;
    }
  }
  *max_error = worst;
  return worst <= 2.0e-4 * (double)(k > 1 ? k : 1);
}

int main(void) {
  const shape_t shapes[] = {
      {63, 65, 67}, {192, 256, 256}, {257, 129, 193}, {512, 512, 512}};
  const int shape_count = (int)(sizeof(shapes) / sizeof(shapes[0]));
  printf("library,target,m,n,k,trial,time_seconds,gflops,max_abs_error,correct\n");
  for (int s = 0; s < shape_count; ++s) {
    int m = shapes[s].m, n = shapes[s].n, k = shapes[s].k;
    size_t a_count = (size_t)m * k;
    size_t b_count = (size_t)k * n;
    size_t c_count = (size_t)m * n;
    float *a = (float *)aligned_alloc(64, ((a_count * sizeof(float) + 63) / 64) * 64);
    float *b = (float *)aligned_alloc(64, ((b_count * sizeof(float) + 63) / 64) * 64);
    float *c = (float *)aligned_alloc(64, ((c_count * sizeof(float) + 63) / 64) * 64);
    if (!a || !b || !c)
      return 2;
    for (size_t i = 0; i < a_count; ++i)
      a[i] = value_at(i, 17u);
    for (size_t i = 0; i < b_count; ++i)
      b[i] = value_at(i, 71u);

    cblas_sgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans, m, n, k, 1.0f, a,
                k, b, n, 0.0f, c, n);
    double max_error = 0.0;
    int correct = validate(a, b, c, m, n, k, &max_error);
    for (int trial = 0; trial < 7; ++trial) {
      double start = now_seconds();
      cblas_sgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans, m, n, k, 1.0f,
                  a, k, b, n, 0.0f, c, n);
      double elapsed = now_seconds() - start;
      double gflops = 2.0 * (double)m * n * k / elapsed / 1.0e9;
      printf("OpenBLAS,haswell,%d,%d,%d,%d,%.9g,%.9g,%.9g,%d\n", m, n,
             k, trial, elapsed, gflops, max_error, correct);
    }
    free(a);
    free(b);
    free(c);
    if (!correct)
      return 3;
  }
  return 0;
}
