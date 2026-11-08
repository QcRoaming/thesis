# Chapter 4 Transform Path Validation

The three rows exercise real parameterized Transform Dialect, lowering, LLVM IR translation, native compilation, execution, and correctness checking.

- Compile passes: **3/3**
- Correctness passes: **3/3**
- Observed BLIS replacements: **0**

`predicted_path` is the Compatibility Checker result. `observed_path` is inferred from emitted LLVM IR.
The current template materializes tiling/vectorization and finite loop-bound handling, but not BLIS panel packing or a BLIS call; therefore a predicted direct/adapt policy remains observed fallback.

Raw measurements: `raw/transform_paths.csv`.
Per-case IR, commands, logs, and manifests: `build/transform_paths/`.
