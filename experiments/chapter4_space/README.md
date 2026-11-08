# Chapter 4: Microkernel-aware Schedule-Space Generation

This package contains the runnable methods and evidence needed to write Chapter 4 of the thesis control document.

## One-command Reproduction

```bash
python3 /buddy-mlir/jlq/thesis/experiments/chapter4_space/scripts/run_chapter4.py
```

The default command reuses native measurement caches and preserves the frozen complete BaCO trace. To recompile and remeasure all Transform and BaCO candidates:

```bash
python3 /buddy-mlir/jlq/thesis/experiments/chapter4_space/scripts/run_chapter4.py --force-measurements
```

Figure generation always uses `/buddy-mlir/jlq/skills/.venv/bin/python` as required by the workspace rule. BaCO runs from the system Python installation and the pinned local checkout under `thesis/third_party/baco`.

## Implemented Closed Loop

1. Load six Task Contexts and the Chapter 3 Contract/Rule registry by content hash.
2. Generate a 2,600-point raw domain for each task.
3. Run the full Compatibility Checker over dtype, ISA, MR/NR, K, layout, stride, alignment, packing, tail, call convention, and Transform legality.
4. Emit Generic, Contract-only, Expert-core, and Expert+Shell spaces with conditional parameters and candidate provenance.
5. Instantiate direct/adapt/fallback policy examples as real Transform Dialect programs.
6. Lower to LLVM IR, compile with clang, execute, check numerical correctness, and record the observed path.
7. Export an Expert+Shell lookup to unmodified BaCO and execute a six-evaluation smoke tuning run.
8. Build tables, figures, complexity reports, invariant tests, and a complete artifact index.

## Important Boundary

The checker predicts direct/adapt/fallback policy paths. The current Transform backend implements tiling, optional vectorization, finite loop-bound handling, bufferization, lowering, and native execution, but does not yet materialize BLIS panel packing or a BLIS call. Consequently, all successful native examples are observed as fallback in LLVM IR. This package never relabels predicted direct/adapt as observed replacement.

## Main Outputs

- `processed/space_summary.csv`: four-space counts for all Task Contexts.
- `raw/candidate_decisions.csv`: per-candidate path, reason, action, score, and checks.
- `provenance/candidate_provenance.csv`: source-to-candidate traceability.
- `raw/transform_paths.csv`: real direct/adapt/fallback policy-template measurements.
- `processed/baco_tuning_trace.csv`: complete six-evaluation BaCO trace.
- `figures/`: Figure 4-1 through Figure 4-5 in SVG/PDF/TIFF/PNG.
- `tables/`: Table 4-1 through Table 4-3 in CSV and XeLaTeX.
- `reports/`: algorithms, invariants, complexity, environment, QA, and result summaries.
- `build/`: input MLIR, transformed MLIR, LLVM dialect, LLVM IR, ELF, and command logs.

## Validation

```bash
python3 -m unittest discover \
  -s /buddy-mlir/jlq/thesis/experiments/chapter4_space/tests -v
```

Expected result: **53 tests pass**.
