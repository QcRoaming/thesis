# Chapter 6 application-validation status

## Completed locally

- Qwen shape trace: **PASS**, 338 raw Linear calls and 192 canonical projection calls.
- Frozen-pool coverage: 100.00% of core calls and 100.00% of core projection FLOPs.
- Local exact-shape pool: **FAIL_UNSTABLE**, 8 workloads and 224 measured candidate points; timings are diagnostic-only because the stability gate failed.
- WSL measurement qualification: **FAIL_UNQUALIFIED**; qualifying CPUs: none. No second confirmatory local performance run is permitted by the frozen decision rule.
- Per-workload parameter audit: 20/24 active and 4 eliminated by static legality; the common-pool oracle is invariant.
- Host MLIR ABI smoke: **PASS**, `PASS cases=3 adapter_calls=3`.
- K230 static ELF: entry `0x200000000`, 452 RVV instruction matches, 3 predeclared cases.
- Core Chapter 4 generator modified for this closure: **no**.
- New compiler pass required: **no**; the bridge uses `transform.annotate` and `convert-linalg-to-std`.
- Physical K230 MLIR closure: **PASS**, 45 correct rows across 3 cases and 3 variants.
- C-adapter / MLIR-adapter geometric ratio: 0.9887, cluster-bootstrap 95% CI [0.9765, 1.0009]; parity acceptance: **True**.
- Physical K230 full candidate pool: **PASS**, 429 correct rows across 10 workloads; 8 direct and 2 adapt pool-oracle selections.
- Best generated adapter / complete OpenBLAS geometric relative performance: 0.6730, workload-bootstrap 95% CI [0.6193, 0.7253]; adapter wins: 0/10.
- Physical i9-14900 exact-shape pool: **PASS**, 870 correct rows across 10 workloads.
- Best generated Contract pool / complete BLIS geometric relative performance: 0.5448, workload-bootstrap 95% CI [0.4833, 0.6104]; generated wins: 0/10.

## External-evidence status

- The physical K230 and native i9-14900 exact-shape pools are complete; no hardware run remains pending inside the frozen thesis boundary.
- Current weighted-analysis status: **PASS**.

The physical K230 evidence now covers both representative compiler-to-adapter closure and the complete frozen candidate pool. Trace weighting projects measured GEMM times onto the frozen call trace; it is not end-to-end model latency.
