# Three termination validation results

## Registered decisions

- `claim_expert_performance_rules_have_incremental_value`: **STOP**
- `claim_practical_search_savings_after_calibration`: **STOP**
- `claim_second_microkernel_contract_is_extensible`: **GO**
- `claim_independent_backend_extensibility`: **NOT_TESTED**

## Data-only vs Expert+Data

- Budget 5: Data-only oracle fraction 0.9682; Expert+Data 0.9764; paired speedup 1.0085 (95% CI 0.9992-1.0266).
- Budget 10: Data-only oracle fraction 0.9968; Expert+Data 0.9968; paired speedup 1.0000 (95% CI 0.9999-1.0000).

The hard Contract and candidate pool are shared. Therefore this comparison
tests only the incremental value of BLIS-derived soft performance-score
features after target data are available.

## Time-to-95%-oracle and amortization

- `B2_no_prior_baco` reaches 95%-oracle in 7.90 evaluations on average (median 5.0, p90 16.1).
- `D0_data_only_baco` reaches 95%-oracle in 3.08 evaluations on average (median 2.0, p90 8.0).
- `D1_expert_plus_data_baco` reaches 95%-oracle in 3.08 evaluations on average (median 2.5, p90 6.0).

- `D0_data_only_baco`: 591 calibration target rows, 531.95 s complete observed cost, 4.817 mean evaluations saved per holdout, compile-inclusive break-even 2293.6 workloads; amortized in 12 workloads = False.
- `D1_expert_plus_data_baco`: 591 calibration target rows, 531.97 s complete observed cost, 4.817 mean evaluations saved per holdout, compile-inclusive break-even 2339.0 workloads; amortized in 12 workloads = False.

Cost accounting uses measured compiler pipeline and benchmark subprocess wall
times. The kernel-runtime-only values remain lower bounds and are not used for
the practical gate.

## Second microkernel package

- Second Contract status: **GO**.
- Generated workloads: 36; pool rows: 1008; paths: {'adapt': 756, 'direct': 252}.
- Frozen formal evidence: 128 binaries and 3132 trial rows, path match = True.
- Independent backend status: **NOT_TESTED**.
- Validation mode: Post-hoc structural audit of the existing f64 package plus fresh direct/adapt executions; not a clean-room replay from an f32-only revision.

This establishes that the current system supports a second BLIS Haswell microkernel Contract (f64 6x8) with the unchanged core space generator. Because the f64 support predates this post-hoc audit, it is not a clean-room history proof. It does not establish a second library, ISA, or independent backend.

## Thesis interpretation

A master's thesis remains defensible as a compiler-system construction and rigorous boundary study: hard compatibility knowledge, executable Transform/LLVM/BLIS integration, negative evidence for soft performance transfer, calibration economics, and a scoped second-Contract extension. It must not claim broadly beneficial expert performance priors or backend-agnostic extensibility without supporting evidence.

Claim boundary: Single-host offline policy replay over the complete i7 f64 Contract corpus. Holdout targets are read only after BaCO selects a unique candidate. Calibration-cost accounting uses observed compiler pipeline and benchmark subprocess wall times from the frozen corpus; these are machine-specific. The extension audit establishes a second BLIS Haswell microkernel Contract, not an independent library or ISA backend.
