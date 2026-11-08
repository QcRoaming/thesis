# Equal-budget Random Search

- Backend: `native`
- Metric: `gflops` (higher is better)
- Budget per task and space: `8`
- Seed: `17`
- Native host: `Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz`
- Compiler: `clang version 21.0.0git`
- Warmups/repeats: `1/3`

> Native GFLOP/s measures the bundled tiled C++ proxy kernel. It validates the
> tuning/measurement loop but is not a BLIS or final MLIR AOT performance claim.

| Task | Space | Final best |
|---|---|---:|
| matmul_aligned_192x256x256_f32 | expert | 10.6726 |
| matmul_aligned_192x256x256_f32 | expert_remove_cache_blocking | 10.6213 |
| matmul_aligned_192x256x256_f32 | expert_remove_compatibility_checker | 10.6083 |
| matmul_aligned_192x256x256_f32 | expert_remove_mr_nr | 10.0418 |
| matmul_aligned_192x256x256_f32 | expert_remove_packing | 7.8851 |
| matmul_aligned_192x256x256_f32 | generic | 8.5707 |
| matmul_edge_128x128x128_f32 | expert | 8.7068 |
| matmul_edge_128x128x128_f32 | expert_remove_cache_blocking | 8.9099 |
| matmul_edge_128x128x128_f32 | expert_remove_compatibility_checker | 7.4358 |
| matmul_edge_128x128x128_f32 | expert_remove_mr_nr | 9.4682 |
| matmul_edge_128x128x128_f32 | expert_remove_packing | 11.3623 |
| matmul_edge_128x128x128_f32 | generic | 9.8866 |
