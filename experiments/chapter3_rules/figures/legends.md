# Chapter 3 Figure Legends

**Figure 3-1 | Preliminary empirical behavior of the bounded generic Transform
space.** a, Observed outcome composition for 64 non-baseline records across
eight f32 `linalg.matmul` shapes: 48 candidates were compiled and measured, and
16 were rejected before compilation. Fallback passes completed Transform
application, LLVM lowering, native compilation, execution, and correctness
checking but contained no BLIS call.
b, Performance of six measured candidates per shape normalized to the best
candidate observed for that shape. Points encode whether Transform
vectorization was enabled. c, Median best-so-far normalized performance and
interquartile range across eight shapes under a six-candidate evaluation budget.
Source: `raw/preliminary_aot.csv`; one seed (17); descriptive analysis only.

**Figure 3-2 | Boundary between hard compatibility and soft performance
knowledge.** a, BLIS facts instantiate two execution-validated, same-backend
Contracts. The OpenBLAS profile remains source evidence with an explicit
conflict and isolation record because its internal ABI is not integrated. b,
The BLIS-derived static soft score and its six workload-family interactions
are represented separately from the shared f64 target measurements. The frozen
i7-10750H evaluation used 12 holdout workloads and five seeds. Expert+Data
showed no clear incremental gain over Data-only; neither model can change
correctness constraints.

**Figure 3-3 | Evidence grading and normalization flow.** Source, build, and
measurement evidence pass through extraction, independent checks, ambiguity
logging, schema normalization, and downstream consumption. Machine checks and
the human-review queue remain separate states; target measurements update
ordering only, while hard execution paths remain fixed.

**Figure 3-4 | End-to-end provenance for the 192×256×256 f32 case.** The BLIS
Haswell source registration yields a 6×16 Contract and a 24×32×64 candidate.
The frozen preliminary Transform prototype is Contract-eligible, but its absent
packing makes both its end-to-end prediction and observation fallback. The
integrated `pack_mode=ab` pipeline materializes A/B panels, emits the BLIS
wrapper and kernel symbol, passes correctness with a maximum absolute error of
1.37e-6, and observes the predicted direct path.
