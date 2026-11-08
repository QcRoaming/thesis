#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
  float *allocated; float *aligned; intptr_t offset;
  intptr_t sizes[2]; intptr_t strides[2];
} memref2d_f32_t;
static int adapter_calls;

void _mlir_ciface_k230_mlir_direct_qkv_prefill_m32(memref2d_f32_t *, memref2d_f32_t *, memref2d_f32_t *);
void _mlir_ciface_k230_contract_adapter_direct_qkv_prefill_m32(memref2d_f32_t *a, memref2d_f32_t *b, memref2d_f32_t *c) {
  if (a->sizes[0] != 32 || a->sizes[1] != 896 ||
      b->sizes[0] != 896 || b->sizes[1] != 1152 ||
      c->sizes[0] != 32 || c->sizes[1] != 1152) exit(20);
  c->aligned[c->offset] = 1001.0f;
  ++adapter_calls;
}

void _mlir_ciface_k230_mlir_adapt_qkv_fringe_m17(memref2d_f32_t *, memref2d_f32_t *, memref2d_f32_t *);
void _mlir_ciface_k230_contract_adapter_adapt_qkv_fringe_m17(memref2d_f32_t *a, memref2d_f32_t *b, memref2d_f32_t *c) {
  if (a->sizes[0] != 17 || a->sizes[1] != 897 ||
      b->sizes[0] != 897 || b->sizes[1] != 1153 ||
      c->sizes[0] != 17 || c->sizes[1] != 1153) exit(20);
  c->aligned[c->offset] = 1002.0f;
  ++adapter_calls;
}

void _mlir_ciface_k230_mlir_adapt_down_fringe_m33(memref2d_f32_t *, memref2d_f32_t *, memref2d_f32_t *);
void _mlir_ciface_k230_contract_adapter_adapt_down_fringe_m33(memref2d_f32_t *a, memref2d_f32_t *b, memref2d_f32_t *c) {
  if (a->sizes[0] != 33 || a->sizes[1] != 4865 ||
      b->sizes[0] != 4865 || b->sizes[1] != 895 ||
      c->sizes[0] != 33 || c->sizes[1] != 895) exit(20);
  c->aligned[c->offset] = 1003.0f;
  ++adapter_calls;
}

static memref2d_f32_t desc(float *data, intptr_t rows, intptr_t cols) {
  memref2d_f32_t value = {data, data, 0, {rows, cols}, {cols, 1}};
  return value;
}
int main(void) {
  float a = 0.0f, b = 0.0f, c = 0.0f;
  memref2d_f32_t a1 = desc(&a, 32, 896);
  memref2d_f32_t b1 = desc(&b, 896, 1152);
  memref2d_f32_t c1 = desc(&c, 32, 1152);
  _mlir_ciface_k230_mlir_direct_qkv_prefill_m32(&a1, &b1, &c1);
  if (c != 1001.0f) return 31;
  memref2d_f32_t a2 = desc(&a, 17, 897);
  memref2d_f32_t b2 = desc(&b, 897, 1153);
  memref2d_f32_t c2 = desc(&c, 17, 1153);
  _mlir_ciface_k230_mlir_adapt_qkv_fringe_m17(&a2, &b2, &c2);
  if (c != 1002.0f) return 32;
  memref2d_f32_t a3 = desc(&a, 33, 4865);
  memref2d_f32_t b3 = desc(&b, 4865, 895);
  memref2d_f32_t c3 = desc(&c, 33, 895);
  _mlir_ciface_k230_mlir_adapt_down_fringe_m33(&a3, &b3, &c3);
  if (c != 1003.0f) return 33;
  if (adapter_calls != 3) return 40;
  printf("PASS cases=3 adapter_calls=%d\n", adapter_calls);
  return 0;
}
