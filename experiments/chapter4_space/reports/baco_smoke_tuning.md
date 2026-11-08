# Chapter 4 BaCO Smoke Tuning

- BaCO commit: `167b19699ead224b661da4abad560306f677e215`
- Task: `anchor_192x256x256_f32`
- Exported full Expert+Shell schedules: **249**
- Bounded smoke-run pool: **6**
- Budget/evaluated: **6/6**
- Unique/duplicate schedule evaluations: **4/2**
- Valid compile-and-correctness rows: **6**
- Best schedule: `m168_n192_k256_pab_v1` at **17.519251 ms**

BaCO is unmodified. Expert knowledge constructs the finite domain, lookup, and ranked initial-design file; it does not alter BaCO's probabilistic model.
Only rank 1 is consumed as BaCO's native parameter default in this smoke run; the remaining DOE points are BaCO uniform samples.

The smoke pool uses `tile_m=168`, `tile_n>=128`, and `tile_k>=128` to retain an M fringe and bound vector IR expansion observed during an aborted broad-domain attempt.

Files: `tuner/baco_scenario.json`, `tuner/expert_shell_lookup.json`, `tuner/baco_tuning_pool.json`, `raw/baco_callback_log.jsonl`, `processed/baco_tuning_trace.csv`, and `tuner/run/baco.log`.
