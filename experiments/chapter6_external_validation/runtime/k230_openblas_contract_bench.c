#define _POSIX_C_SOURCE 200809L

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <cblas.h>

#include "k230_external_config.h"

/* OpenBLAS internal GEMM kernel ABI for the RISCV64_ZVL128B target. */
extern int sgemm_kernel(long m, long n, long k, float alpha, float *packed_a,
                        float *packed_b, float *c, long ldc);

typedef struct {
  float *packed_a;
  float *packed_b;
  float *column_major_c;
} workspace_t;

typedef struct {
  double initialize_seconds;
  double pack_a_seconds;
  double pack_b_seconds;
  double kernel_seconds;
  double scatter_seconds;
  long kernel_calls;
  long fringe_calls;
  long k_tail_calls;
} counters_t;

static double now_seconds(void) {
  struct timespec value;
  clock_gettime(CLOCK_MONOTONIC, &value);
  return (double)value.tv_sec + (double)value.tv_nsec * 1.0e-9;
}

static float input_value(size_t index, uint32_t salt) {
  uint32_t x = (uint32_t)index * 1664525u + 1013904223u + salt;
  return ((float)(x & 0xffffu) / 32768.0f - 1.0f) * 0.125f;
}

static int next_panel_width(int remaining) {
  if (remaining >= 8)
    return 8;
  if (remaining >= 4)
    return 4;
  if (remaining >= 2)
    return 2;
  return 1;
}

/* Pack an MxK panel in the 8/4/2/1 layout consumed by sgemm_kernel. */
static void pack_a_panel(const float *a, int lda, int row0, int k0, int mb,
                         int kb, float *packed) {
  size_t offset = 0;
  int local_row = 0;
  while (local_row < mb) {
    int rows = next_panel_width(mb - local_row);
    for (int p = 0; p < kb; ++p)
      for (int r = 0; r < rows; ++r)
        packed[offset++] = a[(size_t)(row0 + local_row + r) * lda + k0 + p];
    local_row += rows;
  }
}

/* Pack a KxN panel in the 8/4/2/1 layout consumed by sgemm_kernel. */
static void pack_b_panel(const float *b, int ldb, int k0, int column0, int kb,
                         int nb, float *packed) {
  size_t offset = 0;
  int local_column = 0;
  while (local_column < nb) {
    int columns = next_panel_width(nb - local_column);
    for (int p = 0; p < kb; ++p)
      for (int column = 0; column < columns; ++column)
        packed[offset++] =
            b[(size_t)(k0 + p) * ldb + column0 + local_column + column];
    local_column += columns;
  }
}

static workspace_t allocate_workspace(int m, int n, int tk) {
  workspace_t workspace;
  workspace.packed_a = (float *)malloc((size_t)m * tk * sizeof(float));
  workspace.packed_b = (float *)malloc((size_t)n * tk * sizeof(float));
  workspace.column_major_c = (float *)malloc((size_t)m * n * sizeof(float));
  if (!workspace.packed_a || !workspace.packed_b || !workspace.column_major_c) {
    fprintf(stderr, "workspace allocation failed for M=%d N=%d TK=%d\n", m, n,
            tk);
    exit(2);
  }
  return workspace;
}

static void release_workspace(workspace_t *workspace) {
  free(workspace->packed_a);
  free(workspace->packed_b);
  free(workspace->column_major_c);
  memset(workspace, 0, sizeof(*workspace));
}

static counters_t execute_contract_adapter(const k230_candidate_t *candidate,
                                           const float *a, const float *b,
                                           float *c, int m, int n, int k,
                                           workspace_t *workspace) {
  counters_t counters;
  memset(&counters, 0, sizeof(counters));

  double start = now_seconds();
  memset(workspace->column_major_c, 0, (size_t)m * n * sizeof(float));
  counters.initialize_seconds = now_seconds() - start;

  for (int kk = 0; kk < k; kk += candidate->tile_k) {
    int kb = candidate->tile_k < k - kk ? candidate->tile_k : k - kk;

    start = now_seconds();
    for (int ii = 0; ii < m; ii += candidate->tile_m) {
      int mb = candidate->tile_m < m - ii ? candidate->tile_m : m - ii;
      pack_a_panel(a, k, ii, kk, mb, kb, workspace->packed_a + (size_t)ii * kb);
    }
    counters.pack_a_seconds += now_seconds() - start;

    start = now_seconds();
    for (int jj = 0; jj < n; jj += candidate->tile_n) {
      int nb = candidate->tile_n < n - jj ? candidate->tile_n : n - jj;
      pack_b_panel(b, n, kk, jj, kb, nb, workspace->packed_b + (size_t)jj * kb);
    }
    counters.pack_b_seconds += now_seconds() - start;

    start = now_seconds();
    for (int jj = 0; jj < n; jj += candidate->tile_n) {
      int nb = candidate->tile_n < n - jj ? candidate->tile_n : n - jj;
      for (int ii = 0; ii < m; ii += candidate->tile_m) {
        int mb = candidate->tile_m < m - ii ? candidate->tile_m : m - ii;
        int status = sgemm_kernel(
            (long)mb, (long)nb, (long)kb, 1.0f,
            workspace->packed_a + (size_t)ii * kb,
            workspace->packed_b + (size_t)jj * kb,
            workspace->column_major_c + (size_t)jj * m + ii, (long)m);
        if (status != 0) {
          fprintf(stderr, "sgemm_kernel returned %d\n", status);
          exit(5);
        }
        ++counters.kernel_calls;
        if ((mb % K230_CONTRACT_MR) != 0 || (nb % K230_CONTRACT_NR) != 0)
          ++counters.fringe_calls;
        if (kb != candidate->tile_k)
          ++counters.k_tail_calls;
      }
    }
    counters.kernel_seconds += now_seconds() - start;
  }

  start = now_seconds();
  for (int i = 0; i < m; ++i)
    for (int j = 0; j < n; ++j)
      c[(size_t)i * n + j] = workspace->column_major_c[(size_t)j * m + i];
  counters.scatter_seconds = now_seconds() - start;
  return counters;
}

static counters_t execute_openblas(const float *a, const float *b, float *c,
                                   int m, int n, int k) {
  counters_t counters;
  memset(&counters, 0, sizeof(counters));
  cblas_sgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans, m, n, k, 1.0f, a, k,
              b, n, 0.0f, c, n);
  return counters;
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
    double expected = 0.0;
    double observed = 0.0;
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

static double counter_total(const counters_t *counters) {
  return counters->initialize_seconds + counters->pack_a_seconds +
         counters->pack_b_seconds + counters->kernel_seconds +
         counters->scatter_seconds;
}

static void print_row(const char *variant, const char *candidate_id,
                      const char *predicted_path, const k230_workload_t *workload,
                      int tile_m, int tile_n, int tile_k, int trial,
                      double elapsed, double error, const counters_t *counters) {
  double operations = 2.0 * workload->m * workload->n * workload->k;
  double gflops = operations / elapsed / 1.0e9;
  int correct = isfinite(error) && error < 2.0e-3;
  printf("%s,%s,%s,%s,%d,%d,%d,%d,%d,%d,%d,%.9g,%.9g,%.9g,%d,"
         "%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%ld,%ld,%ld\n",
         variant, candidate_id, predicted_path, workload->id, workload->m,
         workload->k, workload->n, tile_m, tile_n, tile_k, trial, elapsed,
         gflops, error, correct, counters->initialize_seconds,
         counters->pack_a_seconds, counters->pack_b_seconds,
         counters->kernel_seconds, counters->scatter_seconds,
         counter_total(counters), counters->kernel_calls,
         counters->fringe_calls, counters->k_tail_calls);
  fflush(stdout);
}

int main(void) {
  const int repetitions = env_int("K230_REPS", 3);
  const int warmups = env_int("K230_WARMUPS", 1);
  printf("variant,candidate_id,predicted_path,workload_id,m,k,n,tile_m,tile_n,"
         "tile_k,trial,time_seconds,gflops,projection_error,correct,"
         "initialize_seconds,pack_a_seconds,pack_b_seconds,kernel_seconds,"
         "scatter_seconds,counter_total_seconds,kernel_calls,fringe_calls,"
         "k_tail_calls\n");

  for (int workload_index = 0; workload_index < K230_WORKLOAD_COUNT;
       ++workload_index) {
    const k230_workload_t *workload = &k230_workloads[workload_index];
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

    for (int candidate_index = 0; candidate_index < K230_CANDIDATE_COUNT;
         ++candidate_index) {
      const k230_candidate_t *candidate = &k230_candidates[candidate_index];
      const char *path = k230_predicted_paths[workload_index][candidate_index];
      if (!k230_candidate_active[workload_index][candidate_index])
        continue;
      workspace_t workspace =
          allocate_workspace(workload->m, workload->n, candidate->tile_k);
      fprintf(stderr, "[adapter] %s %s %dx%dx%d\n", workload->id,
              candidate->id, workload->m, workload->k, workload->n);
      for (int warmup = 0; warmup < warmups; ++warmup)
        execute_contract_adapter(candidate, a, b, c, workload->m, workload->n,
                                 workload->k, &workspace);
      counters_t check = execute_contract_adapter(
          candidate, a, b, c, workload->m, workload->n, workload->k,
          &workspace);
      double error = projection_error(a, b, c, workload->m, workload->n,
                                      workload->k);
      if (!isfinite(error) || error >= 2.0e-3) {
        fprintf(stderr, "projection failure: workload=%s candidate=%s error=%g\n",
                workload->id, candidate->id, error);
        return 3;
      }
      (void)check;
      for (int trial = 0; trial < repetitions; ++trial) {
        double start = now_seconds();
        counters_t counters = execute_contract_adapter(
            candidate, a, b, c, workload->m, workload->n, workload->k,
            &workspace);
        double elapsed = now_seconds() - start;
        print_row("contract_adapter", candidate->id, path, workload,
                  candidate->tile_m, candidate->tile_n, candidate->tile_k,
                  trial, elapsed, error, &counters);
      }
      release_workspace(&workspace);
    }

    fprintf(stderr, "[library] %s openblas_full %dx%dx%d\n", workload->id,
            workload->m, workload->k, workload->n);
    for (int warmup = 0; warmup < warmups; ++warmup)
      execute_openblas(a, b, c, workload->m, workload->n, workload->k);
    execute_openblas(a, b, c, workload->m, workload->n, workload->k);
    double error =
        projection_error(a, b, c, workload->m, workload->n, workload->k);
    if (!isfinite(error) || error >= 2.0e-3) {
      fprintf(stderr, "OpenBLAS projection failure: workload=%s error=%g\n",
              workload->id, error);
      return 3;
    }
    for (int trial = 0; trial < repetitions; ++trial) {
      double start = now_seconds();
      counters_t counters =
          execute_openblas(a, b, c, workload->m, workload->n, workload->k);
      double elapsed = now_seconds() - start;
      print_row("openblas_full", "openblas_full", "library", workload, 0, 0,
                0, trial, elapsed, error, &counters);
    }

    free(a);
    free(b);
    free(c);
  }
  return 0;
}
