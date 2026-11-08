# Dynamic-shape and multi-shape results

同一个动态 scalar-loop fallback 二进制和同一个动态 BLIS 二进制分别覆盖全部 shape。

Baseline：Dynamic linalg.matmul is one-shot bufferized and lowered to scalar loops without explicit tiling or vectorization.

| Shape | Path | Fallback ms | BLIS ms | BLIS GFLOP/s | Speedup | Fringe calls/trial |
|---|---|---:|---:|---:|---:|---:|
| aligned_small_48x64x64 | direct | 0.154280 | 0.009036 | 43.517 | 17.074x | 0 |
| aligned_medium_96x128x128 | direct | 1.568194 | 0.074477 | 42.238 | 21.056x | 0 |
| aligned_anchor_192x256x256 | direct | 17.159672 | 0.584018 | 43.091 | 29.382x | 0 |
| k_tail_48x67x64 | adapt | 0.220195 | 0.011034 | 37.307 | 19.956x | 0 |
| mn_tail_50x64x70 | adapt | 0.196797 | 0.015409 | 29.074 | 12.772x | 143 |
| all_tail_190x250x250 | adapt | 12.203317 | 0.630816 | 37.650 | 19.345x | 2068 |
| micro_fringe_19x65x17 | adapt | 0.016455 | 0.003329 | 12.613 | 4.943x | 110 |

## Aggregate

- Shape 数量：7（direct 3，adapt 4）。
- 独立 trial 行数：42。
- Shape 级几何平均加速：15.905x。
- Shape bootstrap 95% 区间：[10.250x, 22.036x]。
- Direct shape 几何平均：21.941x。
- Adapt shape 几何平均：12.495x。
- 全部数值校验通过，且每个 trial 的 fringe 调用计数与解析计算一致。

## Claim boundary

One x86-64 AVX2/FMA host, f32 rank-2 row-major MemRefs, one dynamic kernel binary per variant, fixed 6x16 BLIS Haswell microkernel, and a scalar-loop dynamic fallback. The bootstrap interval resamples shapes, not hosts.
