# QEMU Correctness Check

Generated at: 2026-07-01T06:56:02Z

## Status

- Overall status: PASS
- QEMU: qemu-riscv64 version 9.2.1 (Debian 1:9.2.1+ds-1ubuntu5.2)
- rv64gc scalar QEMU correctness: PASS (exit=0)
- rv64gcv RVV QEMU execution: PASS (exit=0)
- RVV-like instruction hits in rv64gcv objdump: 14

## Commands

```bash
/buddy-mlir/llvm/build/bin/clang -target riscv64-unknown-linux-gnu -march=rv64gc -mabi=lp64d -O3 -nostdlib -static -ffreestanding -fuse-ld=lld -Wl,-e,_start /buddy-mlir/jlq/thesis/experiments/mlir/rvv_correctness.c -o /buddy-mlir/jlq/thesis/experiments/outputs/rvv/rv64gc_correctness.elf
/buddy-mlir/jlq/thesis/experiments/tools/qemu-9.2.1/bin/qemu-riscv64 /buddy-mlir/jlq/thesis/experiments/outputs/rvv/rv64gc_correctness.elf
/buddy-mlir/llvm/build/bin/clang -target riscv64-unknown-linux-gnu -march=rv64gcv -mabi=lp64d -O3 -nostdlib -static -ffreestanding -fuse-ld=lld -Wl,-e,_start -Rpass=loop-vectorize /buddy-mlir/jlq/thesis/experiments/mlir/rvv_correctness.c -o /buddy-mlir/jlq/thesis/experiments/outputs/rvv/rv64gcv_correctness.elf
/buddy-mlir/jlq/thesis/experiments/tools/qemu-9.2.1/bin/qemu-riscv64 -cpu rv64,v=true,vext_spec=v1.0,vlen=128,elen=64 /buddy-mlir/jlq/thesis/experiments/outputs/rvv/rv64gcv_correctness.elf
```

## Vectorizer Remark

```text
/buddy-mlir/jlq/thesis/experiments/mlir/rvv_correctness.c:7:3: remark: vectorized loop (vectorization width: vscale x 4, interleaved count: 1) [-Rpass=loop-vectorize]
    7 |   for (int i = 0; i < n; ++i) {
      |   ^
/buddy-mlir/jlq/thesis/experiments/mlir/rvv_correctness.c:20:3: remark: vectorized loop (vectorization width: vscale x 4, interleaved count: 1) [-Rpass=loop-vectorize]
   20 |   for (int i = 0; i < 64; ++i) {
      |   ^
/buddy-mlir/jlq/thesis/experiments/mlir/rvv_correctness.c:29:3: remark: vectorized loop (vectorization width: vscale x 4, interleaved count: 1) [-Rpass=loop-vectorize]
   29 |   for (int i = 0; i < 64; ++i) {
      |   ^
```

## RVV Objdump Snippet

```text
   1115c: c22028f3     	csrr	a7, vlenb
   111e2: 0d107757     	vsetvli	a4, zero, e32, m2, ta, ma
   111e6: 2287e407     	vl2re32.v	v8, (a5)
   111ea: 2283e507     	vl2re32.v	v10, (t2)
   111f2: 02851457     	vfadd.vv	v8, v8, v10
   111f6: 22830427     	vs2r.v	v8, (t1)
   11212: c22029f3     	csrr	s3, vlenb
   11230: 0d107657     	vsetvli	a2, zero, e32, m2, ta, ma
   1126a: 22868727     	vs2r.v	v14, (a3)
   1127a: 22878727     	vs2r.v	v14, (a5)
   11288: 22878527     	vs2r.v	v10, (a5)
   11302: 0d107657     	vsetvli	a2, zero, e32, m2, ta, ma
   11330: 2284e707     	vl2re32.v	v14, (s1)
   11334: 05107057     	vsetvli	zero, zero, e32, m2, ta, mu
```

## QEMU Output: rv64gc

```text
```

## QEMU Output: rv64gcv

```text
```

