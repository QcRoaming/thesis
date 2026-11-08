# Chapter 4 to Chapter 5 Integrated Pipeline

This package keeps the frozen Chapter 4 and Chapter 5 evidence intact while
connecting their live interfaces:

```text
Chapter 4 Task/Contract/Rules
  -> generated Expert+Shell candidates
  -> Compatibility Checker prediction
  -> unmodified BaCO callback
  -> Chapter 5 Transform schedule
  -> BLIS panel packing and microkernel call, or generic fallback
  -> correctness, path, fringe, and timing evidence
```

Run:

```bash
python3 jlq/thesis/experiments/chapter4_5_integrated/scripts/run_integrated_pipeline.py
```

The six-evaluation BaCO run is an integration smoke test. It is not the formal
multi-space, multi-seed Chapter 6 comparison.
