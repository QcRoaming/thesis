# i9 Transformer-shape Contract pool results

- Status: **PASS**
- Workloads: 10
- Generated-pool/complete-BLIS geometric ratio: 0.5448

| Workload | Shape MxKxN | Best tile | Path | Generated / BLIS |
|---|---:|---:|---|---:|
| down_decode_m8 | 8x4864x896 | 6x256x256 | adapt | 0.4216 |
| down_fringe_m33 | 33x4865x895 | 24x256x256 | adapt | 0.6551 |
| down_prefill_m32 | 32x4864x896 | 24x256x256 | adapt | 0.6547 |
| gate_up_decode_m8 | 8x896x9728 | 6x192x32 | adapt | 0.5086 |
| gate_up_prefill_m32 | 32x896x9728 | 6x256x64 | adapt | 0.6339 |
| out_decode_m8 | 8x896x896 | 6x192x128 | adapt | 0.4170 |
| out_prefill_m32 | 32x896x896 | 24x256x256 | adapt | 0.6543 |
| qkv_decode_m8 | 8x896x1152 | 6x256x256 | adapt | 0.4275 |
| qkv_fringe_m17 | 17x897x1153 | 6x256x256 | adapt | 0.5121 |
| qkv_prefill_m32 | 32x896x1152 | 24x256x256 | adapt | 0.6609 |

Correctness uses a deterministic projection outside the timed region. Results are single-threaded f32 GEMM kernel evidence, not full-model latency.
