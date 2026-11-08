# Transformer region shared-packing go/no-go

This package tests the cheapest falsifiable version of the proposed
Contract-guided Transformer linear-region direction.

It uses Qwen2.5-0.5B dimensions for two fan-out regions:

- QKV: `M x 896` multiplied by `896 x {896,128,128}`;
- Gate/Up: `M x 896` multiplied by two `896 x 4864` weights.

The frozen `M` values cover decode (`1`, `8`) and prefill (`64`, `256`). Four
execution variants separate the mechanism from weak baselines:

1. independent complete BLIS calls;
2. one complete BLIS call after offline weight concatenation;
3. persistent packed B plus activation repacking per branch;
4. persistent packed B plus one shared activation packing per region.

The runner pins the process to one physical CPU, explicitly forces the BLIS
runtime to one thread, and rotates the four variants at repeat granularity.
This interleaving keeps thermal and host-scheduler drift from being assigned to
one strategy merely because it ran earlier or later in a long trial.

Run the formal local probe with:

```bash
python3 jlq/thesis/experiments/transformer_region_go_nogo/scripts/run_go_nogo.py --skip-registry
```

Regenerate statistics and reports without rerunning the benchmark with:

```bash
python3 jlq/thesis/experiments/transformer_region_go_nogo/scripts/run_go_nogo.py --analyze-only --skip-registry
```

The local decision is provisional even when it passes. A publishable
cross-host claim requires repeating the frozen package on the i9-14900.
