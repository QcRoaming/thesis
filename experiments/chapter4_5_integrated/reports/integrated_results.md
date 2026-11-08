# Chapter 4 to Chapter 5 Integrated Pipeline

## Path Matrix

| Case | Candidate | Predicted | Observed | Correct | BLIS replacement | Fringe calls | Median ms |
|---|---|---|---|---|---|---:|---:|
| direct_anchor | `m24_n32_k64_pab_v1` | direct | direct | PASS | true | 0 | 0.440963 |
| adapt_mnk_tail | `m24_n32_k64_pab_v1` | adapt | adapt | PASS | true | 752 | 0.409608 |
| fallback_feature_miss | `m24_n32_k64_pnone_v0` | fallback | fallback | PASS | false | 0 | 14.875397 |

The direct and adapt cases contain the BLIS wrapper call and linked `bli_sgemm_haswell_asm_6x16` symbol. The adapt case also records the expected runtime fringe-call count. The feature-mismatch case remains on the generated MLIR fallback path.

## BaCO Smoke

- Source space: `expert_shell` (249 candidates).
- Declared pool/budget/evaluated: 6/6/6.
- Pool roles: {'core': 4, 'shell': 2}.
- Observed paths: {'direct': 5, 'fallback': 1}.
- Real microkernel evaluations: 5.
- Best observed candidate: `m24_n32_k64_pab_v1` at 0.440963 ms.

## Claim Boundary

This is an integration smoke experiment on one x86-64 AVX2/FMA host. It proves that Chapter 4 candidates and BaCO callbacks can drive the Chapter 5 real BLIS direct/adapt/fallback evaluator. The six-point budget is not the formal B1-B4 multi-seed comparison, and its timings are not a general performance conclusion.
