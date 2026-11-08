# Transform Demo Check

Generated at: 2026-07-01T06:55:30Z

- Case set: smoke
- Case count: 4

## Tool Versions

```text
LLVM (http://llvm.org/):
  LLVM version 21.0.0git
  Optimized build with assertions.
LLVM (http://llvm.org/):
  LLVM version 21.0.0git
  Optimized build with assertions.
LLVM (http://llvm.org/):
  LLVM version 21.0.0git
  Optimized build with assertions.
  Default target: x86_64-unknown-linux-gnu
  Host CPU: skylake

  Registered Targets:
    riscv32 - 32-bit RISC-V
```

## Metrics

```text
case	transformed_lines	linalg_matmul	scf_for	vector_contract	vector_transfer_read	vector_transfer_write	scalable_vector_ops	llvm_lines	llvm_ir_bytes	rvv_object_bytes	rvv_vsetvli_hits	rvv_vector_hits
matmul_128_f32_tile_16_16_32	27	0	3	1	3	1	0	2932	169001	53168	114	3450
matmul_128_f32_tile_32_32_32	26	0	3	1	3	1	0	7649	466370	177600	796	10544
matmul_256_f32_tile_32_32_32	26	0	3	1	3	1	0	7649	466370	178000	796	10544
matmul_m1_k4096_n11008_f32_tile_1_32_32	25	0	2	1	3	1	0	3498	190510	54496	333	3062
```

## RVV Evidence

The generated LLVM IR was compiled with llc for riscv64 +v. Instruction
counts establish code-generation evidence only; they are not performance metrics.
A zero scalable_vector_ops value means this Transform pipeline still uses
fixed-size MLIR vectors even though LLVM may legalize them to RVV instructions.
