# Qwen2.5-0.5B GEMM shape-trace coverage

- Status: **PASS**
- Raw Linear calls: 338
- Raw Transformer projection calls: 336
- Canonical fused projection calls: 192
- Core projection call coverage: 100.00%
- Core projection FLOP coverage: 100.00%
- Coverage including lm_head FLOPs: 72.44%

| Scenario | Workload | Shape MxKxN | Calls | FLOPs | Covered |
|---|---|---:|---:|---:|---|
| decode_batch8 | down_decode_m8 | 8x4864x896 | 24 | 1673527296 | yes |
| decode_batch8 | gate_up_decode_m8 | 8x896x9728 | 24 | 3347054592 | yes |
| decode_batch8 | out_decode_m8 | 8x896x896 | 24 | 308281344 | yes |
| decode_batch8 | qkv_decode_m8 | 8x896x1152 | 24 | 396361728 | yes |
| prefill_batch1_seq32 | down_prefill_m32 | 32x4864x896 | 24 | 6694109184 | yes |
| prefill_batch1_seq32 | gate_up_prefill_m32 | 32x896x9728 | 24 | 13388218368 | yes |
| prefill_batch1_seq32 | out_prefill_m32 | 32x896x896 | 24 | 1233125376 | yes |
| prefill_batch1_seq32 | qkv_prefill_m32 | 32x896x1152 | 24 | 1585446912 | yes |

The trace executes Hugging Face Qwen2 model control flow with stateless shape-preserving modules. It is evidence for operator shapes and multiplicities, not model accuracy or end-to-end latency. Q/K/V and Gate/Up calls are retained in the raw trace and fused only in the canonical view used to map the existing measurement pool.
