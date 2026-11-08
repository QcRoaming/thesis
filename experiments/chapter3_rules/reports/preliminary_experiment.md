# Chapter 3 Preliminary MLIR Experiment

This is a small-scale motivation experiment, not the Chapter 6 formal evaluation.

- Shapes: **8**
- Non-baseline sampled rows: **64**
- Compile pass ratio among attempted samples: **100.0%**
- Correctness pass ratio among compiled samples: **100.0%**
- Observed microkernel replacement ratio: **0.0%**
- Observed fallback ratio: **100.0%**

The current Transform template implements tiling and optional vectorization but no BLIS
packing/replacement adapter. Therefore successful candidates are expected to be observed
as fallback. This is a measured system boundary, not a simulated replacement failure.

Raw rows: `raw/preliminary_aot.csv`.
