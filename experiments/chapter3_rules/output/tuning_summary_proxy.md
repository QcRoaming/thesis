# Equal-budget Random Search

- Backend: `proxy`
- Metric: `proxy_score` (higher is better)
- Budget per task and space: `16`
- Seed: `17`

> Proxy scores are deterministic pipeline smoke-test data, not measured performance.

| Task | Space | Final best |
|---|---|---:|
| matmul_aligned_192x256x256_f32 | expert | 2.2512 |
| matmul_aligned_192x256x256_f32 | expert_remove_cache_blocking | 1.8343 |
| matmul_aligned_192x256x256_f32 | expert_remove_compatibility_checker | 2.1216 |
| matmul_aligned_192x256x256_f32 | expert_remove_mr_nr | 1.3200 |
| matmul_aligned_192x256x256_f32 | expert_remove_packing | 1.1623 |
| matmul_aligned_192x256x256_f32 | generic | 0.8593 |
| matmul_edge_128x128x128_f32 | expert | 2.2241 |
| matmul_edge_128x128x128_f32 | expert_remove_cache_blocking | 1.2878 |
| matmul_edge_128x128x128_f32 | expert_remove_compatibility_checker | 1.5343 |
| matmul_edge_128x128x128_f32 | expert_remove_mr_nr | 2.2555 |
| matmul_edge_128x128x128_f32 | expert_remove_packing | 1.1324 |
| matmul_edge_128x128x128_f32 | generic | 1.0507 |
