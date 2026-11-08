# K230 MLIR/Transform closure results

- Status: **PASS**
- Correct rows: 45
- C-adapter / MLIR-adapter geometric ratio: 0.9887 (cluster bootstrap 95% CI [0.9765, 1.0009])
- MLIR-adapter / complete-OpenBLAS geometric relative performance: 0.7518

| Case | Shape | Path | C / MLIR time | MLIR / OpenBLAS performance | CV |
|---|---:|---|---:|---:|---:|
| adapt_down_fringe_m33 | 33x4865x895 | adapt | 0.9765 | 0.9489 | 0.14% |
| adapt_qkv_fringe_m17 | 17x897x1153 | adapt | 0.9889 | 0.6013 | 0.17% |
| direct_qkv_prefill_m32 | 32x896x1152 | direct | 1.0009 | 0.7446 | 0.22% |

The C and MLIR variants call the same candidate-specific C-interface adapter, which reuses the frozen OpenBLAS packing and internal sgemm_kernel source. This is representative closure evidence, not a full-pool rerun.
