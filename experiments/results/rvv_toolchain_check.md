# RVV Toolchain Check

Generated at: 2026-07-01T06:56:02Z

## Tool Versions

```text
clang version 21.0.0git
Target: x86_64-unknown-linux-gnu
Thread model: posix
InstalledDir: /buddy-mlir/llvm/build/bin
Build config: +assertions
LLVM (http://llvm.org/):
  LLVM version 21.0.0git
  Optimized build with assertions.
  Default target: x86_64-unknown-linux-gnu
  Host CPU: skylake

  Registered Targets:
    riscv32 - 32-bit RISC-V
    riscv64 - 64-bit RISC-V
    x86     - 32-bit X86: Pentium-Pro and above
    x86-64  - 64-bit X86: EM64T and AMD64
```

## Command

```bash
/buddy-mlir/llvm/build/bin/clang -target riscv64-unknown-elf -march=rv64gcv -mabi=lp64d -O3 -c /buddy-mlir/jlq/thesis/experiments/mlir/rvv_saxpy.c -o /buddy-mlir/jlq/thesis/experiments/outputs/rvv/rvv_saxpy.o -Rpass=loop-vectorize
/buddy-mlir/llvm/build/bin/llvm-objdump -d --mattr=+v /buddy-mlir/jlq/thesis/experiments/outputs/rvv/rvv_saxpy.o
```

## Result

- Object file: /buddy-mlir/jlq/thesis/experiments/outputs/rvv/rvv_saxpy.o
- RVV-like instruction hits in objdump: 6
- Vectorizer remark:

```text
/buddy-mlir/jlq/thesis/experiments/mlir/rvv_saxpy.c:2:3: remark: vectorized loop (vectorization width: vscale x 4, interleaved count: 1) [-Rpass=loop-vectorize]
    2 |   for (int i = 0; i < n; ++i) {
      |   ^
```

## Objdump RVV Snippet

```text
       4: c22028f3     	csrr	a7, vlenb
      8a: 0d107757     	vsetvli	a4, zero, e32, m2, ta, ma
      8e: 2287e407     	vl2re32.v	v8, (a5)
      92: 2283e507     	vl2re32.v	v10, (t2)
      9a: 02851457     	vfadd.vv	v8, v8, v10
      9e: 22830427     	vs2r.v	v8, (t1)
```

QEMU/real-board correctness was not executed in this check. For the 2026-06-30 midterm, this is toolchain and instruction-generation evidence while Milk-V Jupiter is not yet available.
