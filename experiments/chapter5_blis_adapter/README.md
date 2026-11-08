# Chapter 5: real BLIS packing and call adapter

本目录独立生成第五章的真实微内核替换证据，不覆盖第四章冻结结果。它复用第四章的
`192x256x256 f32` 任务和 `24x32x64` 候选参数，并新增以下实现：

1. `buddy-materialize-blis-packed-matmul`：把 buffer-semantics
   `linalg.matmul` 改写为 BLIS 兼容的 A/B packing 与 6x16 微块循环；
2. `transform.buddy.call_microkernel`：只把已准备好的 placeholder 调用重定向到
   `buddy_blis_sgemm_6x16`；
3. C++ adapter：把 MLIR lowering 后的地址与 offset 参数桥接到
   `bli_sgemm_haswell_asm_6x16` ABI；
4. 同任务普通 Transform vectorization 基线、数值校验、符号校验和性能测量。

完整运行：

```bash
python3 jlq/thesis/experiments/chapter5_blis_adapter/scripts/run_chapter5_full.py
```

静态锚点结果见 `processed/chapter5_summary.json`，动态多 shape 结果见
`processed/dynamic_multishape_summary.json`。

当前覆盖行主序 f32 GEMM 的静态 direct、M/N/K fringe adapt，以及一个动态二进制
跨多个运行时 shape 的执行。任意 stride/layout、其他 dtype/微内核 Contract、并行执行
和跨机器统计仍不在本次结论范围内。
