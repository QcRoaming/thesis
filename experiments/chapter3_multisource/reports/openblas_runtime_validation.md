# OpenBLAS Runtime Validation

Pinned OpenBLAS `b338322e9afc063d95e2c117e85bedf28213295a` was built as a single-thread Haswell static library. All 4 shapes and 28 timed rows passed the independent reference check.

| M x N x K | Median GFLOP/s | Correct |
|---|---:|---|
| 63 x 65 x 67 | 45.256 | pass |
| 192 x 256 x 256 | 46.678 | pass |
| 257 x 129 x 193 | 59.672 | pass |
| 512 x 512 x 512 | 55.080 | pass |

These host measurements validate the extracted OpenBLAS source and public SGEMM execution path. They are not used as K230 performance results.
