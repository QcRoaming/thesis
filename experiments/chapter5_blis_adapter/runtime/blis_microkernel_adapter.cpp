#include "blis.h"

#include <cstdint>

extern "C" void bli_sgemm_haswell_asm_6x16(dim_t m, dim_t n, dim_t k,
                                           const void *alpha, const void *a,
                                           const void *b, const void *beta,
                                           void *c, inc_t rs_c, inc_t cs_c,
                                           const auxinfo_t *data,
                                           const cntx_t *cntx);

namespace {

uint64_t fringeCalls = 0;

void callBlis(int64_t k, uintptr_t aBase, int64_t aOffset, uintptr_t bBase,
              int64_t bOffset, uintptr_t cBase, int64_t cOffset,
              int64_t cRowStride, int64_t cColStride) {
  bli_init_once();

  const auto *a = reinterpret_cast<const float *>(aBase) + aOffset;
  const auto *b = reinterpret_cast<const float *>(bBase) + bOffset;
  auto *c = reinterpret_cast<float *>(cBase) + cOffset;
  const float alpha = 1.0f;
  const float beta = 1.0f;
  auxinfo_t aux{};

  bli_sgemm_haswell_asm_6x16(6, 16, static_cast<dim_t>(k), &alpha, a, b, &beta,
                             c, static_cast<inc_t>(cRowStride),
                             static_cast<inc_t>(cColStride), &aux,
                             bli_gks_query_cntx());
}

} // namespace

extern "C" void buddy_blis_sgemm_6x16(int64_t k, uintptr_t aBase,
                                      int64_t aOffset, uintptr_t bBase,
                                      int64_t bOffset, uintptr_t cBase,
                                      int64_t cOffset, int64_t cRowStride,
                                      int64_t cColStride) {
  callBlis(k, aBase, aOffset, bBase, bOffset, cBase, cOffset, cRowStride,
           cColStride);
}

extern "C" void buddy_blis_sgemm_6x16_fringe(int64_t k, uintptr_t aBase,
                                             int64_t aOffset, uintptr_t bBase,
                                             int64_t bOffset, uintptr_t cBase,
                                             int64_t cOffset,
                                             int64_t cRowStride,
                                             int64_t cColStride) {
  ++fringeCalls;
  callBlis(k, aBase, aOffset, bBase, bOffset, cBase, cOffset, cRowStride,
           cColStride);
}

extern "C" void buddy_blis_reset_fringe_calls() { fringeCalls = 0; }

extern "C" uint64_t buddy_blis_get_fringe_calls() { return fringeCalls; }
