# Chapter 4 Invariant Validation

| Invariant | Evidence | Status |
|---|---|---|
| Every tuning candidate is semantically and Transform legal | `generic`, `contract_only`, `expert_core`, and `expert_shell` exclude `reject`; tests 33-36 | PASS |
| Every `direct` candidate satisfies all checked Contract dimensions | Checker emits `DIRECT_CONTRACT_MATCH` only after dtype/ISA/MR-NR/K/layout/stride/alignment/packing/tail/ABI/Transform checks; tests 6-8 | PASS |
| Every `adapt` candidate has a declared finite adapter | Tail and K-remainder actions are explicit; tests 9-11, 25-26 | PASS |
| Every `fallback` candidate has generic lowering | no-Contract and interface misses map to `generic_mlir_tiled_loop`; tests 12-13, 18-24 | PASS |
| `reject` never enters tuning | generation membership filters and shell property tests; tests 14-18, 33-39 | PASS |
| Soft priors do not decide correctness | score is assigned after checker path and cannot mutate it; tests 31-32 | PASS |
| Every candidate is traceable to Rule/Contract sources | source hashes, candidate provenance, and tests 42-45 | PASS |

The integration suite additionally verifies three real Transform/AOT path examples and a six-evaluation BaCO run. Full result: **53/53 tests pass**.
