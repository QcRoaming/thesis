# K230 RVV Backend Experiment

This package implements and measures a second hardware backend for the thesis.
It targets the K230 C908 big core under RT-Smart and uses the official K230 SDK
toolchain.

Generated static ELF variants:

- `k230_gemm_scalar.elf`: scalar blocked control, compiled without RVV.
- `k230_gemm_rvv.elf`: scalar control plus explicit RVV tiled candidates.
- `k230_gemm_openblas.elf`: the same candidates plus OpenBLAS
  `RISCV64_ZVL128B` full SGEMM.

The RVV candidates encode generic, BLIS, OpenBLAS and cross-source schedule
hints. They do not pretend to be the source libraries' internal microkernels.
The full OpenBLAS row is independently labelled.

The official K230 GCC 12 prerelease implements RVV 1.0 with an older intrinsic
API spelling than current OpenBLAS. The build therefore generates and
force-includes an auditable compatibility header. It does not modify the
OpenBLAS source worktree or replace the `RISCV64_ZVL128B` microkernel/packing
path.

Build:

```bash
python3 scripts/build_k230_elfs.py
python3 scripts/render_k230_report.py
python3 -m unittest discover -s tests -v
```

The build emits `build/k230_rvv_backend_deployment.tar.gz`. Extract it on the
K230 big-core filesystem, enter `k230_rvv_backend`, then run:

```sh
K230_REPS=5 K230_WARMUPS=1 sh board/run_k230_suite.sh
```

Return the generated `board_results` directory and import it with:

```bash
python3 scripts/import_board_results.py board_results
```

For a board whose RT-Smart console is attached to Linux as `/dev/ttyACM1`, the
host can run and capture the same suite directly:

```bash
python3 scripts/run_board_via_serial.py \
  --port /dev/ttyACM1 \
  --output-dir raw/board_results
python3 scripts/import_board_results.py raw/board_results
```

The serial runner waits for the `msh />` prompt, runs the three ELF files
sequentially, retains complete raw logs, extracts only benchmark CSV rows, and
checks the expected row count and correctness status before returning.

The physical-board run in `raw/board_results_20260716_rtsmart_valid/` produced
560 correct timing rows across eight workloads. The imported summary is
`processed/k230_board_summary.json`, and the thesis-facing interpretation is in
`reports/k230_elf_results.md`.

Current status: `board_results_imported`. Runtime claims remain limited to the
recorded K230 board, RT-Smart runtime, pinned toolchain, binaries and harness.
