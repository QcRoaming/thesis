# Chapter 6 application-level validation

本实验包补充三项在正式矩阵实验之后仍然缺失的证据，但不改写已有负面结果：

1. `linalg.generic -> Transform Dialect -> linalg library-call lowering -> LLVM IR -> RV64 ELF -> OpenBLAS packing/sgemm_kernel` 的 K230 代表性闭环；
2. 由 Hugging Face `Qwen2ForCausalLM` 实际模块调用产生的 GEMM shape trace，以及与冻结测量池的覆盖映射。
3. 在本机 i7 上对 8 个精确 trace shape 的 28 候选同池测量，并用冻结稳定性门槛决定其是否具有性能主张资格。

## K230 MLIR 闭环

三个案例在板端测量前冻结：一个无尾部 `direct` 和两个 M/N/K 三维尾部 `adapt`。Transform IR 将候选专属 adapter 名写入 `library_call` 属性，`convert-linalg-to-std` 生成外部调用，再由同一个外部验证 adapter 源码执行 OpenBLAS 8x8 packing 和内部 `sgemm_kernel`。

本实验同时测量：

- 直接调用相同 C adapter；
- 经过 MLIR C interface wrapper 调用该 adapter；
- 完整 `cblas_sgemm`。

因此 MLIR/C 比值用于检查编译器桥接开销，OpenBLAS 对照用于限定生成路径的性能边界。

## Qwen trace

trace 脚本实例化固定配置的 `Qwen2ForCausalLM`，将带权重模块替换为无权重、保持输出形状的模块，然后真实执行模型控制流。该过程记录每个 `Linear` 的实际输入形状，但不下载模型权重，也不把 shape execution 误写成模型性能。

原始 Q/K/V 与 Gate/Up 调用同时保留；规范化视图将它们分别合并为 QKV 和 Gate-Up GEMM，以对齐已冻结的融合投影测量池。`lm_head` 保留在原始 trace 中，但不进入 24 层 Transformer block 的核心覆盖率。

## 一键构建

```bash
python3 scripts/run_application_validation.py
python3 -m unittest discover -s tests -v
```

本机 i7 的第一次确认性测量完成了 2088 个进程，但只有 15.95% 的
workload/variant 组通过 robust-CV 门槛，因此状态为 `FAIL_UNSTABLE`。随后冻结
并执行了 120 进程的 CPU/计时窗口资格测试；6 个 CPU 代表均未使四个诊断组
全部通过，状态为 `FAIL_UNQUALIFIED`。两批数据完整保留，但不进入性能主张。

复现资格诊断：

```bash
python3 scripts/run_application_validation.py --run-local-qualification
```

资格测试只用于判断 WSL 环境能否稳定测量，不用于选择最快 CPU 或形成性能
结论。按冻结决策，本机不再通过修改阈值或反复重测追求通过；trace-weighted
结果等待原生 i9 或 K230 精确-shape结果。

K230 返回结果后：

```bash
python3 scripts/import_k230_mlir_results.py /path/to/board_results
```

外部 i9/K230 精确-shape结果返回后，可合并生成 trace-weighted 报告：

```bash
python3 scripts/analyze_trace_weighted_results.py \
  --i9-root /path/to/i9_result_root \
  --k230-root ../chapter6_external_validation
```

当前边界为单线程、行主序 f32 GEMM。该实验不代表完整模型端到端时延。
