# Thesis Experiment Summary

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
case	transformed_lines	linalg_matmul	scf_for	vector_contract	vector_transfer_read	vector_transfer_write	scalable_vector_ops	llvm_lines	llvm_ir_bytes	rvv_object_bytes	rvv_vsetvli_hits	rvv_vector_hits
matmul_128_f32_tile_16_16_32	27	0	3	1	3	1	0	2932	169001	53168	114	3450
matmul_128_f32_tile_32_32_32	26	0	3	1	3	1	0	7649	466370	177600	796	10544
matmul_256_f32_tile_32_32_32	26	0	3	1	3	1	0	7649	466370	178000	796	10544
matmul_m1_k4096_n11008_f32_tile_1_32_32	25	0	2	1	3	1	0	3498	190510	54496	333	3062
```

Interpretation: `linalg.matmul=0` in transformed snapshots means the high-level op has been tiled/vectorized away. The generated LLVM dialect files and RVV object files are under `outputs/transform_ir_snapshots/`.

## MLIR AOT Results

```csv
case,shape,schedule,tile_m,tile_n,tile_k,warmups,repeats,inner_iters,stack_limit_kb,median_ms,min_ms,max_ms,mean_ms,stddev_ms,p90_ms,gflops,max_abs_diff,max_rel_diff,checksum,output_aliases_c,status,lowering_ms,native_compile_ms,llvm_ir_bytes,executable_bytes
matmul_128_default,128x128x128,default,0,0,0,3,11,5,65536,2.429496,2.065540,3.444761,2.461161,0.344362,2.588397,1.726,0.00000054,0.00047549,-3.11505761,1,PASS,57,1668,7073,26136
matmul_128_tile_16_16_32,128x128x128,tile,16,16,32,3,11,5,65536,1.022319,0.857639,1.803524,1.099328,0.260995,1.326103,4.103,0.00000061,0.00039948,-3.11501565,1,PASS,139,2700,168777,120344
matmul_128_tile_32_32_32,128x128x128,tile,32,32,32,3,11,5,65536,1.044615,0.931599,1.389915,1.077935,0.139361,1.238293,4.015,0.00000061,0.00039948,-3.11501565,1,PASS,323,8947,466146,415256
matmul_256_default,256x256x256,default,0,0,0,3,11,5,65536,23.860638,22.404364,25.193062,23.836426,0.849665,24.912812,1.406,0.00000083,0.00052111,2.96538857,1,PASS,51,1543,7073,26136
matmul_256_tile_16_16_32,256x256x256,tile,16,16,32,3,11,5,65536,9.954167,8.853645,11.169309,10.009496,0.801447,11.099948,3.371,0.00000107,0.00027640,2.96633828,1,PASS,154,2697,168777,120344
matmul_256_tile_32_32_32,256x256x256,tile,32,32,32,3,11,5,65536,9.506215,8.335388,13.138805,9.853588,1.444285,12.170614,3.530,0.00000107,0.00027640,2.96633828,1,PASS,324,9151,466146,415256
```

The timed region contains only the generated MLIR kernel call. Compilation time,
code size, stack limit, numerical error, and run-to-run variation are recorded
alongside latency and GFLOP/s.

### Schedule Comparison

| Shape | Best tiled schedule | Default ms | Best ms | Speedup |
|---|---:|---:|---:|---:|
| 128x128x128 | 16x16x32 | 2.4295 | 1.0223 | 2.38x |
| 256x256x256 | 32x32x32 | 23.8606 | 9.5062 | 2.51x |

## Legacy C++ Schedule Sanity Check

```csv
workload,shape,schedule,tile_m,tile_n,tile_k,median_ms,min_ms,max_abs_diff,checksum
matmul,128x128x128,default_ijk,0,0,0,2.0225,1.7584,0.000000,-3.115054
matmul,128x128x128,tile_16_16_32,16,16,32,1.8785,1.3481,0.000000,-3.115054
matmul,128x128x128,tile_32_32_32,32,32,32,1.6121,1.5194,0.000000,-3.115054
matmul,256x256x256,default_ijk,0,0,0,24.5840,20.5664,0.000000,2.965000
matmul,256x256x256,tile_16_16_32,16,16,32,21.0450,17.9513,0.000000,2.965000
matmul,256x256x256,tile_32_32_32,32,32,32,18.7813,16.8874,0.000000,2.965000
```

Interpretation: this native C++ benchmark mirrors tile sizes but is retained only
as a historical sanity check. Thesis performance claims should use the MLIR AOT
results above and measurements from the target board.

## RVV Instruction Evidence

```text
4: c22028f3     	csrr	a7, vlenb
      8a: 0d107757     	vsetvli	a4, zero, e32, m2, ta, ma
      8e: 2287e407     	vl2re32.v	v8, (a5)
      92: 2283e507     	vl2re32.v	v10, (t2)
      9a: 02851457     	vfadd.vv	v8, v8, v10
      9e: 22830427     	vs2r.v	v8, (t1)
```

Interpretation: Milk-V Jupiter is not available yet, so this is currently toolchain, QEMU correctness, and instruction-generation evidence rather than real-board performance evidence.

## QEMU Correctness

```text
- Overall status: PASS
- QEMU: qemu-riscv64 version 9.2.1 (Debian 1:9.2.1+ds-1ubuntu5.2)
- rv64gc scalar QEMU correctness: PASS (exit=0)
- rv64gcv RVV QEMU execution: PASS (exit=0)
- RVV-like instruction hits in rv64gcv objdump: 14
```

Interpretation: QEMU correctness is available for both the `rv64gc` scalar executable and the `rv64gcv` RVV executable using the bundled QEMU 9.2.1 user-mode binary. Real-board performance still requires Milk-V Jupiter.

## Reproduce

```bash
jlq/thesis/experiments/scripts/setup_qemu_9_2_1.sh
jlq/thesis/experiments/scripts/run_all.sh
```
