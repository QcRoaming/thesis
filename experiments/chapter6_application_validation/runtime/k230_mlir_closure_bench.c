#define main k230_external_benchmark_main
#include "k230_openblas_contract_bench.c"
#undef main

#include "k230_mlir_closure_config.h"

typedef struct {
  float *allocated;
  float *aligned;
  intptr_t offset;
  intptr_t sizes[2];
  intptr_t strides[2];
} memref2d_f32_t;

typedef void (*closure_entry_t)(memref2d_f32_t *, memref2d_f32_t *,
                                memref2d_f32_t *);

static counters_t k230_mlir_last_counters;
static long k230_mlir_adapter_calls;

static float *memref_data(memref2d_f32_t *descriptor) {
  return descriptor->aligned + descriptor->offset;
}

static void validate_descriptors(const char *case_id, memref2d_f32_t *a,
                                 memref2d_f32_t *b, memref2d_f32_t *c, int m,
                                 int k, int n) {
  int valid = a && b && c && a->aligned && b->aligned && c->aligned &&
              a->sizes[0] == m && a->sizes[1] == k && b->sizes[0] == k &&
              b->sizes[1] == n && c->sizes[0] == m && c->sizes[1] == n &&
              a->strides[0] == k && a->strides[1] == 1 &&
              b->strides[0] == n && b->strides[1] == 1 &&
              c->strides[0] == n && c->strides[1] == 1;
  if (!valid) {
    fprintf(stderr, "invalid MLIR memref descriptor for %s\n", case_id);
    exit(7);
  }
}

#define DEFINE_ADAPTER(token, case_text, workload_text, candidate_text,          \
                       path_text, m_value, k_value, n_value, tm_value, tn_value, \
                       tk_value)                                                 \
  static workspace_t token##_workspace;                                          \
  static int token##_workspace_ready;                                            \
  void _mlir_ciface_k230_contract_adapter_##token(                               \
      memref2d_f32_t *a, memref2d_f32_t *b, memref2d_f32_t *c) {                \
    validate_descriptors(case_text, a, b, c, m_value, k_value, n_value);          \
    if (!token##_workspace_ready) {                                               \
      token##_workspace = allocate_workspace(m_value, n_value, tk_value);         \
      token##_workspace_ready = 1;                                                \
    }                                                                             \
    const k230_candidate_t candidate = {candidate_text, tm_value, tn_value,       \
                                        tk_value};                                \
    k230_mlir_last_counters = execute_contract_adapter(                           \
        &candidate, memref_data(a), memref_data(b), memref_data(c), m_value,      \
        n_value, k_value, &token##_workspace);                                    \
    ++k230_mlir_adapter_calls;                                                    \
  }

K230_MLIR_CLOSURE_CASES(DEFINE_ADAPTER)
#undef DEFINE_ADAPTER

#define DECLARE_MLIR_ENTRY(token, case_text, workload_text, candidate_text,       \
                           path_text, m_value, k_value, n_value, tm_value,        \
                           tn_value, tk_value)                                    \
  extern void _mlir_ciface_k230_mlir_##token(                                    \
      memref2d_f32_t *, memref2d_f32_t *, memref2d_f32_t *);

K230_MLIR_CLOSURE_CASES(DECLARE_MLIR_ENTRY)
#undef DECLARE_MLIR_ENTRY

typedef struct {
  const char *case_id;
  const char *workload_id;
  const char *candidate_id;
  const char *expected_path;
  int m;
  int k;
  int n;
  int tile_m;
  int tile_n;
  int tile_k;
  closure_entry_t direct_entry;
  closure_entry_t mlir_entry;
} closure_case_t;

#define CASE_ROW(token, case_text, workload_text, candidate_text, path_text,      \
                 m_value, k_value, n_value, tm_value, tn_value, tk_value)        \
  {case_text, workload_text, candidate_text, path_text, m_value, k_value,         \
   n_value, tm_value, tn_value, tk_value,                                         \
   _mlir_ciface_k230_contract_adapter_##token,                                   \
   _mlir_ciface_k230_mlir_##token},

static const closure_case_t closure_cases[] = {
    K230_MLIR_CLOSURE_CASES(CASE_ROW)};
#undef CASE_ROW

static memref2d_f32_t make_memref(float *data, int rows, int columns) {
  memref2d_f32_t descriptor;
  descriptor.allocated = data;
  descriptor.aligned = data;
  descriptor.offset = 0;
  descriptor.sizes[0] = rows;
  descriptor.sizes[1] = columns;
  descriptor.strides[0] = columns;
  descriptor.strides[1] = 1;
  return descriptor;
}

static const char *observed_path(const counters_t *counters) {
  return counters->fringe_calls > 0 || counters->k_tail_calls > 0 ? "adapt"
                                                                  : "direct";
}

static void print_closure_row(const closure_case_t *test_case,
                              const char *variant, int trial, double elapsed,
                              double error, const counters_t *counters,
                              const char *path) {
  double operations = 2.0 * test_case->m * test_case->n * test_case->k;
  double gflops = operations / elapsed / 1.0e9;
  int correct = isfinite(error) && error < 2.0e-3;
  int path_match = strcmp(path, test_case->expected_path) == 0;
  printf("%s,%s,%s,%s,%s,%d,%d,%d,%d,%d,%d,%d,%.9g,%.9g,%.9g,%d,%s,%d,"
         "%.9g,%.9g,%.9g,%.9g,%.9g,%ld,%ld,%ld,%ld\n",
         variant, test_case->case_id, test_case->workload_id,
         test_case->candidate_id, test_case->expected_path, test_case->m,
         test_case->k, test_case->n, test_case->tile_m, test_case->tile_n,
         test_case->tile_k, trial, elapsed, gflops, error, correct, path,
         path_match, counters->initialize_seconds, counters->pack_a_seconds,
         counters->pack_b_seconds, counters->kernel_seconds,
         counters->scatter_seconds, counters->kernel_calls,
         counters->fringe_calls, counters->k_tail_calls,
         k230_mlir_adapter_calls);
  fflush(stdout);
}

static void run_adapter_variant(const closure_case_t *test_case,
                                const char *variant, closure_entry_t entry,
                                memref2d_f32_t *a_desc,
                                memref2d_f32_t *b_desc,
                                memref2d_f32_t *c_desc, const float *a,
                                const float *b, float *c, int warmups,
                                int repetitions) {
  for (int warmup = 0; warmup < warmups; ++warmup)
    entry(a_desc, b_desc, c_desc);
  entry(a_desc, b_desc, c_desc);
  double error = projection_error(a, b, c, test_case->m, test_case->n,
                                  test_case->k);
  if (!isfinite(error) || error >= 2.0e-3) {
    fprintf(stderr, "%s projection failure for %s: %g\n", variant,
            test_case->case_id, error);
    exit(8);
  }
  for (int trial = 0; trial < repetitions; ++trial) {
    double start = now_seconds();
    entry(a_desc, b_desc, c_desc);
    double elapsed = now_seconds() - start;
    const char *path = observed_path(&k230_mlir_last_counters);
    if (strcmp(path, test_case->expected_path) != 0) {
      fprintf(stderr, "%s path mismatch for %s: %s != %s\n", variant,
              test_case->case_id, path, test_case->expected_path);
      exit(9);
    }
    print_closure_row(test_case, variant, trial, elapsed, error,
                      &k230_mlir_last_counters, path);
  }
}

int main(void) {
  const int repetitions = env_int("K230_MLIR_REPS", 5);
  const int warmups = env_int("K230_MLIR_WARMUPS", 1);
  printf("variant,case_id,workload_id,candidate_id,expected_path,m,k,n,tile_m,"
         "tile_n,tile_k,trial,time_seconds,gflops,projection_error,correct,"
         "observed_path,path_match,initialize_seconds,pack_a_seconds,"
         "pack_b_seconds,kernel_seconds,scatter_seconds,kernel_calls,"
         "fringe_calls,k_tail_calls,adapter_calls\n");

  const int case_count =
      (int)(sizeof(closure_cases) / sizeof(closure_cases[0]));
  for (int index = 0; index < case_count; ++index) {
    const closure_case_t *test_case = &closure_cases[index];
    size_t a_count = (size_t)test_case->m * test_case->k;
    size_t b_count = (size_t)test_case->k * test_case->n;
    size_t c_count = (size_t)test_case->m * test_case->n;
    float *a = (float *)malloc(a_count * sizeof(float));
    float *b = (float *)malloc(b_count * sizeof(float));
    float *c = (float *)malloc(c_count * sizeof(float));
    if (!a || !b || !c)
      return 2;
    for (size_t i = 0; i < a_count; ++i)
      a[i] = input_value(i, 17u);
    for (size_t i = 0; i < b_count; ++i)
      b[i] = input_value(i, 71u);
    memref2d_f32_t a_desc = make_memref(a, test_case->m, test_case->k);
    memref2d_f32_t b_desc = make_memref(b, test_case->k, test_case->n);
    memref2d_f32_t c_desc = make_memref(c, test_case->m, test_case->n);

    fprintf(stderr, "[closure] %s direct C adapter\n", test_case->case_id);
    run_adapter_variant(test_case, "c_adapter_direct", test_case->direct_entry,
                        &a_desc, &b_desc, &c_desc, a, b, c, warmups,
                        repetitions);
    fprintf(stderr, "[closure] %s MLIR Transform adapter\n",
            test_case->case_id);
    run_adapter_variant(test_case, "mlir_transform_adapter",
                        test_case->mlir_entry, &a_desc, &b_desc, &c_desc, a, b,
                        c, warmups, repetitions);

    fprintf(stderr, "[closure] %s complete OpenBLAS\n", test_case->case_id);
    for (int warmup = 0; warmup < warmups; ++warmup)
      execute_openblas(a, b, c, test_case->m, test_case->n, test_case->k);
    execute_openblas(a, b, c, test_case->m, test_case->n, test_case->k);
    double error = projection_error(a, b, c, test_case->m, test_case->n,
                                    test_case->k);
    if (!isfinite(error) || error >= 2.0e-3)
      return 10;
    for (int trial = 0; trial < repetitions; ++trial) {
      double start = now_seconds();
      counters_t counters = execute_openblas(a, b, c, test_case->m,
                                             test_case->n, test_case->k);
      double elapsed = now_seconds() - start;
      print_closure_row(test_case, "openblas_full", trial, elapsed, error,
                        &counters, "library");
    }
    free(a);
    free(b);
    free(c);
  }
  return 0;
}
