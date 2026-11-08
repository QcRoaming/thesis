# i9-14900 external-validation results

- Formal import status: **PASS** (formal protocol, integrity, completeness, and correctness passed).
- Correct rows / measurement groups: 870 / 290.
- Generated Contract pool / complete BLIS geometric relative performance: 0.5448 (workload bootstrap 95% CI [0.4833, 0.6104]); wins: 0/10.
- Median/max group trial CV: 0.45% / 11.04%; groups above 5%: 12.
- Selected-candidate/BLIS max trial CV: 7.86% / 3.81%.
- No i9 CV acceptance threshold was frozen before measurement. The 5% analysis is therefore reported only as a sensitivity check, not as a retrospective pass gate.
- Sensitivity check excludes ['gate_up_prefill_m32']; remaining ratio 0.5357 (95% CI [0.4720, 0.6076]).
- perf stat availability: 0/6; this does not affect the primary wall-time result.
- Sparse Data-only vs Expert+Data: 0/10 significant benefits and 2 significant harms; the incremental expert performance-feature claim remains **STOP**.

| Workload | Shape MxKxN | Best tile | Path | Generated / BLIS | Candidate CV | BLIS CV |
|---|---:|---:|---|---:|---:|---:|
| down_decode_m8 | 8x4864x896 | 6x256x256 | adapt | 0.4216 | 0.28% | 3.81% |
| down_fringe_m33 | 33x4865x895 | 24x256x256 | adapt | 0.6551 | 0.11% | 0.14% |
| down_prefill_m32 | 32x4864x896 | 24x256x256 | adapt | 0.6547 | 0.24% | 0.13% |
| gate_up_decode_m8 | 8x896x9728 | 6x192x32 | adapt | 0.5086 | 0.43% | 2.20% |
| gate_up_prefill_m32 | 32x896x9728 | 6x256x64 | adapt | 0.6339 | 7.86% | 1.45% |
| out_decode_m8 | 8x896x896 | 6x192x128 | adapt | 0.4170 | 0.49% | 2.31% |
| out_prefill_m32 | 32x896x896 | 24x256x256 | adapt | 0.6543 | 0.40% | 0.14% |
| qkv_decode_m8 | 8x896x1152 | 6x256x256 | adapt | 0.4275 | 0.13% | 3.41% |
| qkv_fringe_m17 | 17x897x1153 | 6x256x256 | adapt | 0.5121 | 1.14% | 0.35% |
| qkv_prefill_m32 | 32x896x1152 | 24x256x256 | adapt | 0.6609 | 2.44% | 0.26% |

A ratio above 1 means that the generated Contract schedule is faster. These are single-threaded f32 GEMM kernel-package measurements, not end-to-end model latency. The negative library-boundary result does not invalidate legality transfer, parameter liveness, or independent backend integration evidence.
