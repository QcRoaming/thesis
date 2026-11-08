# Qwen trace-weighted target results

- Status: **PASS**
- Targets analyzed: ['i9_14900', 'k230_c908']
- Trace workload rows: 8

| Target | Scenario | Policy | Budget | Weighted ms | / Library | Break-even inferences |
|---|---|---|---:|---:|---:|---:|
| i9_14900 | decode_batch8 | complete_library | 0 | 117.0284 | 1.0000 | not reached |
| i9_14900 | decode_batch8 | pool_oracle | 28 | 243.8388 | 0.4799 | not reached |
| i9_14900 | decode_batch8 | pool_oracle_guarded | 29 | 117.0284 | 1.0000 | not reached |
| i9_14900 | decode_batch8 | static_expert | 5 | 281.0475 | 0.4164 | not reached |
| i9_14900 | decode_batch8 | static_expert | 10 | 273.7908 | 0.4274 | not reached |
| i9_14900 | decode_batch8 | static_expert_guarded | 5 | 117.0284 | 1.0000 | not reached |
| i9_14900 | decode_batch8 | static_expert_guarded | 10 | 117.0284 | 1.0000 | not reached |
| i9_14900 | decode_batch8 | uniform_random | 5 | 255.0204 | 0.4589 | not reached |
| i9_14900 | decode_batch8 | uniform_random | 10 | 251.3872 | 0.4655 | not reached |
| i9_14900 | decode_batch8 | uniform_random_guarded | 5 | 117.0284 | 1.0000 | not reached |
| i9_14900 | decode_batch8 | uniform_random_guarded | 10 | 117.0284 | 1.0000 | not reached |
| i9_14900 | prefill_batch1_seq32 | complete_library | 0 | 265.4171 | 1.0000 | not reached |
| i9_14900 | prefill_batch1_seq32 | pool_oracle | 28 | 413.7632 | 0.6415 | not reached |
| i9_14900 | prefill_batch1_seq32 | pool_oracle_guarded | 29 | 265.4171 | 1.0000 | not reached |
| i9_14900 | prefill_batch1_seq32 | static_expert | 5 | 465.0018 | 0.5708 | not reached |
| i9_14900 | prefill_batch1_seq32 | static_expert | 10 | 444.8747 | 0.5966 | not reached |
| i9_14900 | prefill_batch1_seq32 | static_expert_guarded | 5 | 265.4171 | 1.0000 | not reached |
| i9_14900 | prefill_batch1_seq32 | static_expert_guarded | 10 | 265.4171 | 1.0000 | not reached |
| i9_14900 | prefill_batch1_seq32 | uniform_random | 5 | 425.6463 | 0.6236 | not reached |
| i9_14900 | prefill_batch1_seq32 | uniform_random | 10 | 420.3270 | 0.6315 | not reached |
| i9_14900 | prefill_batch1_seq32 | uniform_random_guarded | 5 | 265.4171 | 1.0000 | not reached |
| i9_14900 | prefill_batch1_seq32 | uniform_random_guarded | 10 | 265.4171 | 1.0000 | not reached |
| k230_c908 | decode_batch8 | complete_library | 0 | 3595.5689 | 1.0000 | not reached |
| k230_c908 | decode_batch8 | pool_oracle | 16 | 6386.9493 | 0.5630 | not reached |
| k230_c908 | decode_batch8 | pool_oracle_guarded | 17 | 3595.5689 | 1.0000 | not reached |
| k230_c908 | decode_batch8 | static_expert | 5 | 8100.4044 | 0.4439 | not reached |
| k230_c908 | decode_batch8 | static_expert | 10 | 6386.9493 | 0.5630 | not reached |
| k230_c908 | decode_batch8 | static_expert_guarded | 5 | 3595.5689 | 1.0000 | not reached |
| k230_c908 | decode_batch8 | static_expert_guarded | 10 | 3595.5689 | 1.0000 | not reached |
| k230_c908 | decode_batch8 | uniform_random | 5 | 6491.1698 | 0.5539 | not reached |
| k230_c908 | decode_batch8 | uniform_random | 10 | 6386.9493 | 0.5630 | not reached |
| k230_c908 | decode_batch8 | uniform_random_guarded | 5 | 3595.5689 | 1.0000 | not reached |
| k230_c908 | decode_batch8 | uniform_random_guarded | 10 | 3595.5689 | 1.0000 | not reached |
| k230_c908 | prefill_batch1_seq32 | complete_library | 0 | 6953.3778 | 1.0000 | not reached |
| k230_c908 | prefill_batch1_seq32 | pool_oracle | 16 | 9689.7484 | 0.7176 | not reached |
| k230_c908 | prefill_batch1_seq32 | pool_oracle_guarded | 17 | 6953.3778 | 1.0000 | not reached |
| k230_c908 | prefill_batch1_seq32 | static_expert | 5 | 11540.9884 | 0.6025 | not reached |
| k230_c908 | prefill_batch1_seq32 | static_expert | 10 | 10054.3893 | 0.6916 | not reached |
| k230_c908 | prefill_batch1_seq32 | static_expert_guarded | 5 | 6953.3778 | 1.0000 | not reached |
| k230_c908 | prefill_batch1_seq32 | static_expert_guarded | 10 | 6953.3778 | 1.0000 | not reached |
| k230_c908 | prefill_batch1_seq32 | uniform_random | 5 | 9809.9022 | 0.7088 | not reached |
| k230_c908 | prefill_batch1_seq32 | uniform_random | 10 | 9729.5404 | 0.7147 | not reached |
| k230_c908 | prefill_batch1_seq32 | uniform_random_guarded | 5 | 6953.3778 | 1.0000 | not reached |
| k230_c908 | prefill_batch1_seq32 | uniform_random_guarded | 10 | 6953.3778 | 1.0000 | not reached |

Weighted latency covers the 24 Transformer blocks represented by the canonical trace and excludes lm_head. Tuning cost uses measured kernel time plus target-side compile-pipeline time when available; it is a lower bound because orchestration and process startup are not fully charged.

## Guarded static prior versus guarded random

| Target | Scenario | Budget | Static speedup / random median | Seed wins |
|---|---|---:|---:|---:|
| i9_14900 | decode_batch8 | 5 | 1.0000 | 0/5 |
| i9_14900 | decode_batch8 | 10 | 1.0000 | 0/5 |
| i9_14900 | prefill_batch1_seq32 | 5 | 1.0000 | 0/5 |
| i9_14900 | prefill_batch1_seq32 | 10 | 1.0000 | 0/5 |
| k230_c908 | decode_batch8 | 5 | 1.0000 | 0/5 |
| k230_c908 | decode_batch8 | 10 | 1.0000 | 0/5 |
| k230_c908 | prefill_batch1_seq32 | 5 | 1.0000 | 0/5 |
| k230_c908 | prefill_batch1_seq32 | 10 | 1.0000 | 0/5 |

This comparison uses five deterministic random seeds. With only four projection regions per scenario, it is reported as a bounded application diagnostic rather than a new confidence-interval claim.
