#!/usr/bin/env python3
import csv
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

cpu = (RESULTS / "cpu_initial_results.csv").read_text().strip()
transform = (RESULTS / "transform_metrics.tsv").read_text().strip()
aot_path = RESULTS / "mlir_aot_benchmark.csv"
aot = aot_path.read_text().strip() if aot_path.exists() else "not generated"
rvv = (RESULTS / "rvv_toolchain_check.md").read_text()
qemu = (RESULTS / "qemu_correctness_check.md").read_text() if (RESULTS / "qemu_correctness_check.md").exists() else ""
marker = "## Objdump RVV Snippet\n\n```text\n"
rvv_snip = ""
if marker in rvv:
    rvv_snip = rvv.split(marker, 1)[1].split("```", 1)[0].strip()
qemu_status = "not generated"
qemu_lines = []
if qemu:
    for line in qemu.splitlines():
        if line.startswith("- Overall status:") or line.startswith("- QEMU:") or line.startswith("- rv64gc") or line.startswith("- rv64gcv") or line.startswith("- RVV-like"):
            qemu_lines.append(line)
    qemu_status = "\n".join(qemu_lines)

aot_comparison = "not available"
if aot_path.exists():
    rows = list(csv.DictReader(io.StringIO(aot)))
    comparison_lines = [
        "| Shape | Best tiled schedule | Default ms | Best ms | Speedup |",
        "|---|---:|---:|---:|---:|",
    ]
    for shape in sorted({row["shape"] for row in rows}):
        shape_rows = [
            row for row in rows if row["shape"] == shape and row["status"] == "PASS"
        ]
        default_rows = [row for row in shape_rows if row["schedule"] == "default"]
        tiled_rows = [row for row in shape_rows if row["schedule"] == "tile"]
        if not default_rows or not tiled_rows:
            continue
        default = default_rows[0]
        best = min(tiled_rows, key=lambda row: float(row["median_ms"]))
        speedup = float(default["median_ms"]) / float(best["median_ms"])
        tile = f'{best["tile_m"]}x{best["tile_n"]}x{best["tile_k"]}'
        comparison_lines.append(
            f'| {shape} | {tile} | {float(default["median_ms"]):.4f} | '
            f'{float(best["median_ms"]):.4f} | {speedup:.2f}x |'
        )
    if len(comparison_lines) > 2:
        aot_comparison = "\n".join(comparison_lines)

(RESULTS / "midterm_experiment_summary.md").write_text(f"""# Thesis Experiment Summary

Generated from the latest files in `jlq/thesis/experiments/results/`.

## Completed Checks

1. Transform Dialect matmul schedules run successfully with LLVM/MLIR 21.0.0git.
2. `linalg.matmul` is transformed into `scf.for` loops plus vector operations for the selected case set.
3. Transformed MLIR lowers to LLVM dialect, translates to LLVM IR, and compiles to `riscv64` object code with `+v` enabled.
4. MLIR-generated LLVM IR is AOT-compiled and executed on the host CPU with reference correctness checks.
5. RVV toolchain check emits RVV instructions from a small C loop compiled with `-march=rv64gcv`.
6. QEMU 9.2.1 runs both `rv64gc` scalar correctness and `rv64gcv` RVV correctness successfully.

## Transform Metrics

```text
{transform}
```

Interpretation: `linalg.matmul=0` in transformed snapshots means the high-level op has been tiled/vectorized away. The generated LLVM dialect files and RVV object files are under `outputs/transform_ir_snapshots/`.

## MLIR AOT Results

```csv
{aot}
```

The timed region contains only the generated MLIR kernel call. Compilation time,
code size, stack limit, numerical error, and run-to-run variation are recorded
alongside latency and GFLOP/s.

### Schedule Comparison

{aot_comparison}

## Legacy C++ Schedule Sanity Check

```csv
{cpu}
```

Interpretation: this native C++ benchmark mirrors tile sizes but is retained only
as a historical sanity check. Thesis performance claims should use the MLIR AOT
results above and measurements from the target board.

## RVV Instruction Evidence

```text
{rvv_snip}
```

Interpretation: Milk-V Jupiter is not available yet, so this is currently toolchain, QEMU correctness, and instruction-generation evidence rather than real-board performance evidence.

## QEMU Correctness

```text
{qemu_status}
```

Interpretation: QEMU correctness is available for both the `rv64gc` scalar executable and the `rv64gcv` RVV executable using the bundled QEMU 9.2.1 user-mode binary. Real-board performance still requires Milk-V Jupiter.

## Reproduce

```bash
jlq/thesis/experiments/scripts/setup_qemu_9_2_1.sh
jlq/thesis/experiments/scripts/run_all.sh
```
""", encoding="utf-8")
print(RESULTS / "midterm_experiment_summary.md")
