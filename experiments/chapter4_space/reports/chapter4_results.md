# Chapter 4 Result Summary

## Generated Spaces

| Task | Raw | Executable | Contract-only | Expert-core | Shell | Expert+Shell |
|---|---:|---:|---:|---:|---:|---:|
| `anchor_192x256x256_f32` | 2600 | 2400 | 560 | 224 | 25 | 249 |
| `tail_190x250x250_f32` | 2600 | 1584 | 336 | 28 | 4 | 32 |
| `small_64x64x64_f32` | 2600 | 576 | 96 | 43 | 5 | 48 |
| `rect_48x256x64_f32` | 2600 | 840 | 160 | 80 | 9 | 89 |
| `aligned_192x256x256_f64` | 2600 | 2400 | 700 | 259 | 29 | 288 |
| `feature_mismatch_192x256x256_f32` | 2600 | 2400 | 0 | 0 | 0 | 0 |

The feature-mismatch task intentionally has no Contract/core space but retains 2,400 executable generic fallback schedules.

## Transform/AOT Path Evidence

| Case | Predicted | Observed | Correctness | Median ms | GFLOP/s |
|---|---|---|---|---:|---:|
| `direct_anchor` | direct | fallback | pass | 9.670296 | 2.602 |
| `adapt_mnk_tail` | adapt | fallback | pass | 8.939995 | 2.657 |
| `fallback_feature_miss` | fallback | fallback | pass | 21.992206 | 1.144 |

All three policy templates compile and pass numerical checking. All are observed fallback because emitted LLVM IR contains no BLIS call.

## BaCO Smoke Run

- Full Expert+Shell lookup: **249** schedules.
- Declared low-IR-expansion pool: **6** schedules.
- Budget/evaluations: **6/6**; valid: **6**.
- Unique/duplicate schedule evaluations: **4/2**.
- Best retained measurement: `m168_n192_k256_pab_v1`, **17.519251 ms**.

BaCO is unmodified. Expert rules construct the domain, lookup, and initial-design metadata; they do not alter BaCO's probabilistic model.

## Claim Boundary

The artifacts support Chapter 4 claims about space construction, compatibility classification, conditional domains, Transform instantiation, and tuner integration. They do **not** support a claim of observed BLIS microkernel replacement; packing and a real MLIR-to-BLIS call adapter remain future Chapter 5 work.
