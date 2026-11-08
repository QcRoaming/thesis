/* Generated from the frozen K230 MLIR closure cases. */
#ifndef K230_MLIR_CLOSURE_CONFIG_H
#define K230_MLIR_CLOSURE_CONFIG_H

#define K230_MLIR_CLOSURE_CASES(X) \
  X(direct_qkv_prefill_m32, "direct_qkv_prefill_m32", "qkv_prefill_m32", "m32_n8_k128_pab_v1", "direct", 32, 896, 1152, 32, 8, 128) \
  X(adapt_qkv_fringe_m17, "adapt_qkv_fringe_m17", "qkv_fringe_m17", "m16_n16_k240_pab_v1", "adapt", 17, 897, 1153, 16, 16, 240) \
  X(adapt_down_fringe_m33, "adapt_down_fringe_m33", "down_fringe_m33", "m32_n16_k240_pab_v1", "adapt", 33, 4865, 895, 32, 16, 240)

#endif
