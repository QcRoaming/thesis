# K230 RVV Backend Build Results

## Evidence boundary

Current status: `board_results_imported`.

The official-toolchain ELF evidence and returned physical-board CSV files have been imported. Runtime claims must use the board summary below and remain limited to the recorded K230 configuration.

## Pinned toolchain and library

- K230 SDK revision: `7e302f733311d284be255f0d81d3463b6ae6ee6d`
- Compiler: `riscv64-unknown-linux-musl-gcc (GCC) 12.0.1 20220505 (prerelease)`
- OpenBLAS revision: `b338322e9afc063d95e2c117e85bedf28213295a`
- OpenBLAS target: `RISCV64_ZVL128B`
- OpenBLAS static library SHA-256: `234e9bb378d62d19f60321fbea252e7106396746c96ef8d77f62cfa92574d508`
- RVV compatibility mappings: 425 intrinsics and 23 tuple types

The compatibility layer is force-included by a compiler wrapper and leaves the detached OpenBLAS source worktree unmodified. It maps the ratified `__riscv_` intrinsic spelling and tuple API to the older spelling implemented by the official K230 GCC 12 prerelease.

## ELF artifacts

| ELF | Bytes | RVV opcode matches | SHA-256 |
|---|---:|---:|---|
| `k230_gemm_scalar.elf` | 197808 | 3 | `2d991cebc32787cec2bc5898ae2634ac62f001ed60b2ade894fb6bd5c76fbf98` |
| `k230_gemm_rvv.elf` | 197832 | 53 | `2ccd3b1eb4d92cf1e944f5002a19627d2e25975fc5fb4ce22b942b4a3a9aa912` |
| `k230_gemm_openblas.elf` | 288144 | 372 | `339ed7717bfaa368a63171e86cf04762b8fe8ffd8bcb5b5343146cf1c6ddc052` |

All three files are ELF64 RISC-V, statically linked, and have no `INTERP` program header. The RVV and OpenBLAS variants contain substantially more vector opcode matches than the scalar control.

## Board deployment

Deployment archive: `/buddy-mlir/jlq/thesis/experiments/k230_rvv_backend/build/k230_rvv_backend_deployment.tar.gz`  
Archive SHA-256: `83c7cccccf6dab52af59b0bcee1b93cca8c34d17dbaa95376e76ad6eb1a81c6c`

After extracting the archive on the K230 big-core filesystem:

```sh
cd k230_rvv_backend
K230_REPS=5 K230_WARMUPS=1 sh board/run_k230_suite.sh
```

Return the generated `board_results/` directory and import it on the host:

```bash
python3 scripts/import_board_results.py /path/to/board_results
```

## Imported board results

Rows: 560; aggregates: 112; all correct: `true`.

| Binary | Workload | Best candidate | Median GFLOP/s | Trials |
|---|---|---|---:|---:|
| `openblas` | `anchor` | `openblas_full` | 4.54126 | 5 |
| `openblas` | `rect_fringe` | `openblas_full` | 4.14353 | 5 |
| `openblas` | `square_1024` | `openblas_full` | 4.73675 | 5 |
| `openblas` | `square_512` | `openblas_full` | 4.81407 | 5 |
| `openblas` | `tall` | `openblas_full` | 4.72563 | 5 |
| `openblas` | `tiny_fringe` | `openblas_full` | 3.78338 | 5 |
| `openblas` | `wide` | `openblas_full` | 4.68003 | 5 |
| `openblas` | `wide_fringe` | `openblas_full` | 4.26106 | 5 |
| `rvv` | `anchor` | `rvv_openblas_8x8x240` | 0.928814 | 5 |
| `rvv` | `rect_fringe` | `rvv_generic_16x16x64` | 1.68603 | 5 |
| `rvv` | `square_1024` | `rvv_generic_16x16x64` | 0.297405 | 5 |
| `rvv` | `square_512` | `rvv_generic_16x16x64` | 0.46533 | 5 |
| `rvv` | `tall` | `rvv_generic_32x32x128` | 1.00323 | 5 |
| `rvv` | `tiny_fringe` | `rvv_generic_32x32x128` | 1.87707 | 5 |
| `rvv` | `wide` | `rvv_generic_16x16x64` | 0.421646 | 5 |
| `rvv` | `wide_fringe` | `rvv_cross_source_16x8x240` | 0.621492 | 5 |
| `scalar` | `anchor` | `scalar` | 0.254234 | 5 |
| `scalar` | `rect_fringe` | `scalar` | 0.351203 | 5 |
| `scalar` | `square_1024` | `scalar` | 0.175763 | 5 |
| `scalar` | `square_512` | `scalar` | 0.219364 | 5 |
| `scalar` | `tall` | `scalar` | 0.235858 | 5 |
| `scalar` | `tiny_fringe` | `scalar` | 0.360488 | 5 |
| `scalar` | `wide` | `scalar` | 0.222538 | 5 |
| `scalar` | `wide_fringe` | `scalar` | 0.250087 | 5 |

## Cross-workload comparisons

- Best measured explicit-RVV schedule per workload versus the in-process scalar control: `2.29x` geometric mean.
- Complete OpenBLAS SGEMM versus the in-process scalar control: `13.47x` geometric mean.

| Workload | Best RVV candidate | RVV / scalar | OpenBLAS / scalar |
|---|---|---:|---:|
| `anchor` | `rvv_openblas_8x8x240` | 2.46x | 12.03x |
| `rect_fringe` | `rvv_generic_16x16x64` | 3.82x | 9.43x |
| `square_1024` | `rvv_generic_16x16x64` | 1.47x | 23.35x |
| `square_512` | `rvv_generic_16x16x64` | 1.43x | 14.76x |
| `tall` | `rvv_generic_32x32x128` | 2.70x | 12.71x |
| `tiny_fringe` | `rvv_generic_32x32x128` | 4.22x | 8.51x |
| `wide` | `rvv_generic_16x16x64` | 1.58x | 17.52x |
| `wide_fringe` | `rvv_cross_source_16x8x240` | 2.12x | 14.63x |

## Schedule-transfer evidence

| RVV candidate | Geomean / scalar | Workloads above scalar |
|---|---:|---:|
| `rvv_blis_16x4x640` | 0.85x | 5 / 8 |
| `rvv_cross_source_16x8x240` | 1.87x | 7 / 8 |
| `rvv_generic_16x16x64` | 1.93x | 8 / 8 |
| `rvv_generic_32x32x128` | 1.80x | 6 / 8 |
| `rvv_openblas_8x8x240` | 1.82x | 7 / 8 |

The winning explicit-RVV schedule changes with shape: generic candidates win six of eight workloads, while OpenBLAS-derived and cross-source candidates each win one. The fixed BLIS-derived candidate reaches only `0.85x` geometric mean relative to scalar. These measurements support transferring compatibility constraints and candidate seeds, but not treating a source library's fixed parameters as a target-independent performance ranking.

The complete OpenBLAS result is an optimized library reference with its own microkernel and packing path. It is not interchangeable with the explicit-RVV schedule candidates.
