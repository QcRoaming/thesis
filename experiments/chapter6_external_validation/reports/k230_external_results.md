# K230 OpenBLAS external-backend results

- Status: **PASS**
- Workloads: 10
- Adapter / OpenBLAS geometric relative performance: 0.6730 (workload bootstrap 95% CI [0.6193, 0.7253])
- Exact-Qwen-shape adapter / OpenBLAS geometric relative performance: 0.6653
- Median/max group trial CV: 0.16% / 12.17%; groups above 5%: 1
- Max best-adapter/OpenBLAS trial CV: 0.30% / 0.28%
- Max projection error: 5.99e-06

| Workload | Shape MxKxN | Best tile | Path | Adapter / OpenBLAS performance | Pack share |
|---|---:|---:|---|---:|---:|
| down_decode_m8 | 8x4864x896 | 8x16x64 | direct | 0.6476 | 81.05% |
| down_fringe_m33 | 33x4865x895 | 32x16x240 | adapt | 0.7849 | 44.25% |
| down_prefill_m32 | 32x4864x896 | 16x16x64 | direct | 0.7708 | 56.08% |
| gate_up_decode_m8 | 8x896x9728 | 8x16x64 | direct | 0.5121 | 83.05% |
| gate_up_prefill_m32 | 32x896x9728 | 16x16x64 | direct | 0.6856 | 55.81% |
| out_decode_m8 | 8x896x896 | 8x16x64 | direct | 0.6471 | 80.76% |
| out_prefill_m32 | 32x896x896 | 16x16x64 | direct | 0.7652 | 55.27% |
| qkv_decode_m8 | 8x896x1152 | 8x16x64 | direct | 0.6008 | 81.82% |
| qkv_fringe_m17 | 17x897x1153 | 8x32x128 | adapt | 0.6325 | 58.09% |
| qkv_prefill_m32 | 32x896x1152 | 16x16x64 | direct | 0.7361 | 56.34% |

Relative performance is computed as OpenBLAS time divided by adapter time; values above 1 mean that the generated Contract adapter is faster. The comparison uses complete single-thread OpenBLAS SGEMM. They are kernel-package measurements rather than end-to-end model latency.
