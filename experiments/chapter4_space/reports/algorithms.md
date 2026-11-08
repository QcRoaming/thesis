# Chapter 4 Formal Algorithms

## Algorithm 4-1: Microkernel-aware Space Generation

**Input:** Task Context `T`, Contract Registry `C`, Expert Rules `R`, raw parameter domain `D`, exploration ratio `rho`.

**Output:** `S_legal`, path mapping `gamma`, `S_contract`, `S_exec`, `S_core`, `S_shell`, `S_tune`, and candidate provenance.

```text
1  contract, selection_log <- SelectContract(T, C)
2  U <- CartesianProduct(D)
3  for candidate s in U:
4      params <- ConstructConditionalDomain(s, T, contract)
5      decision <- CompatibilityCheck(params, T, contract)
6      if decision.path != reject:
7          insert s into S_exec
8      if decision.path in {direct, adapt}:
9          insert s into S_contract
10     score[s] <- RankBySoftPriors(s, T, contract, decision)
11     provenance[s] <- Trace(T, contract, R, decision)
12 S_core <- candidates satisfying hard/conditional rules and core score predicate
13 S_shell <- DeterministicStratifiedSample(S_exec \ S_core, rho)
14 assert S_shell contains no reject candidate
15 S_tune <- S_core union S_shell
16 return all sets, decisions, selection_log, provenance
```

Implementation: `generate_spaces_for_task` in `scripts/chapter4lib.py`.

## Algorithm 4-2: Conditional Parameter Domain Construction

```text
1  emit tile_m, tile_n, tile_k, pack_mode, vectorize
2  if pack_mode == ab:
3      emit pack_a=true, pack_b=true, pack_layout=blis_panel
4      emit call_convention=BLIS GEMM_UKR ABI
5  else:
6      omit pack_layout and emit generic MLIR memref convention
7  if a Contract is selected and vectorize is enabled:
8      emit vector_lanes=contract.vectorization.lanes
9  if M/N have a Contract fringe:
10     emit mn_tail_strategy=finite_fringe_adapter
11 if K has a main-loop remainder:
12     emit k_remainder_strategy=scalar_cleanup_adapter
13 return the instantiated parameter object
```

Implementation: `conditional_parameters` in `scripts/chapter4lib.py`.

## Algorithm 4-3: Candidate Ranking and Initial Design Selection

```text
1  reject candidates receive no finite score
2  assign path prior: direct > adapt > fallback
3  add cache-divisor/proximity, packing, vectorization, and block-size bonuses
4  sort by descending score, then path class, then stable candidate ID
5  greedily select candidates with unseen (tile_m, tile_n, tile_k)
6  fill remaining design slots from the stable ranking
7  return the first requested number of candidates
```

The score is a soft prior. It does not modify `gamma`, numerical correctness, or any reject decision. Implementation: `score_candidate` and `rank_and_select_initial`.
