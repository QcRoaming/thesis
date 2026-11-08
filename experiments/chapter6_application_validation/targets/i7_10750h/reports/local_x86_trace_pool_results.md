# Local x86 Qwen-shape Contract pool results

- Target: `i7_10750h_wsl2`
- Status: **FAIL_UNSTABLE**
- Exact trace workloads: 8
- Candidate measurements: 224
- Confirmatory batches: 3
- Process medians per variant: 9
- Stability gate: **FAIL**
- Stable variant fraction: 15.95%
- Pool/BLIS batch-ratio relative spread: 11.43%
- Pool oracle / complete BLIS geometric ratio: 0.6714

| Workload | Shape MxKxN | Best tile | Path | Pool oracle / BLIS |
|---|---:|---:|---|---:|
| down_decode_m8 | 8x4864x896 | 6x256x256 | adapt | 0.5239 |
| down_prefill_m32 | 32x4864x896 | 24x256x256 | adapt | 0.6623 |
| gate_up_decode_m8 | 8x896x9728 | 6x256x64 | adapt | 0.6760 |
| gate_up_prefill_m32 | 32x896x9728 | 24x128x256 | adapt | 1.1583 |
| out_decode_m8 | 8x896x896 | 6x128x128 | adapt | 0.3829 |
| out_prefill_m32 | 32x896x896 | 24x128x256 | adapt | 0.9421 |
| qkv_decode_m8 | 8x896x1152 | 6x64x128 | adapt | 0.4976 |
| qkv_prefill_m32 | 32x896x1152 | 12x64x256 | adapt | 0.8468 |

These are single-thread f32 GEMM measurements for the eight exact Qwen trace shapes. They are not end-to-end model latency measurements.
