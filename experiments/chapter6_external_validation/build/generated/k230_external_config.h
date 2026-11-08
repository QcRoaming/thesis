/* Generated from the frozen external-validation JSON inputs. */
#ifndef K230_EXTERNAL_CONFIG_H
#define K230_EXTERNAL_CONFIG_H

#define K230_CONTRACT_MR 8
#define K230_CONTRACT_NR 8
#define K230_WORKLOAD_COUNT 10
#define K230_CANDIDATE_COUNT 16

typedef struct { const char *id; int m; int k; int n; } k230_workload_t;
typedef struct { const char *id; int tile_m; int tile_n; int tile_k; } k230_candidate_t;

static const k230_workload_t k230_workloads[K230_WORKLOAD_COUNT] = {
  {"qkv_decode_m8", 8, 896, 1152},
  {"gate_up_decode_m8", 8, 896, 9728},
  {"down_decode_m8", 8, 4864, 896},
  {"out_decode_m8", 8, 896, 896},
  {"qkv_prefill_m32", 32, 896, 1152},
  {"gate_up_prefill_m32", 32, 896, 9728},
  {"down_prefill_m32", 32, 4864, 896},
  {"out_prefill_m32", 32, 896, 896},
  {"qkv_fringe_m17", 17, 897, 1153},
  {"down_fringe_m33", 33, 4865, 895},
};

static const k230_candidate_t k230_candidates[K230_CANDIDATE_COUNT] = {
  {"m8_n8_k64_pab_v1", 8, 8, 64},
  {"m8_n8_k128_pab_v1", 8, 8, 128},
  {"m8_n8_k240_pab_v1", 8, 8, 240},
  {"m8_n8_k256_pab_v1", 8, 8, 256},
  {"m8_n16_k64_pab_v1", 8, 16, 64},
  {"m8_n16_k128_pab_v1", 8, 16, 128},
  {"m8_n16_k240_pab_v1", 8, 16, 240},
  {"m8_n32_k128_pab_v1", 8, 32, 128},
  {"m8_n32_k240_pab_v1", 8, 32, 240},
  {"m8_n32_k256_pab_v1", 8, 32, 256},
  {"m16_n8_k128_pab_v1", 16, 8, 128},
  {"m16_n16_k64_pab_v1", 16, 16, 64},
  {"m16_n16_k240_pab_v1", 16, 16, 240},
  {"m32_n8_k128_pab_v1", 32, 8, 128},
  {"m32_n16_k240_pab_v1", 32, 16, 240},
  {"m32_n32_k256_pab_v1", 32, 32, 256},
};

static const char *k230_predicted_paths[K230_WORKLOAD_COUNT][K230_CANDIDATE_COUNT] = {
  {"direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "reject", "reject", "reject", "reject", "reject", "reject"},
  {"direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "reject", "reject", "reject", "reject", "reject", "reject"},
  {"direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "reject", "reject", "reject", "reject", "reject", "reject"},
  {"direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "reject", "reject", "reject", "reject", "reject", "reject"},
  {"direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct"},
  {"direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct"},
  {"direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct"},
  {"direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct", "direct"},
  {"adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "reject", "reject", "reject"},
  {"adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt", "adapt"},
};

static const unsigned char k230_candidate_active[K230_WORKLOAD_COUNT][K230_CANDIDATE_COUNT] = {
  {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0},
  {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0},
  {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0},
  {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0},
  {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
  {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
  {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
  {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
  {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0},
  {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
};

#endif
