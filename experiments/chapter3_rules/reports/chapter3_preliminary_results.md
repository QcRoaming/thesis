# 第3章预备实证结果摘要

> 本报告只用于证明研究问题值得研究，不替代第6章正式实验。

## 实验范围

- 工作负载：8 个 `linalg.matmul` f32 shape。
- 通用参数空间：每个 shape 原始空间 336 个候选。
- 实际测量：48 个 Transform/AOT 候选；另有 16 个策略拒绝。
- 流程：Transform Dialect → LLVM IR → clang AOT → 正确性与性能测量。

## 可直接引用的预备结果

- 合法空间缩减比例为 16.7%—37.5%；小 K shape 的缩减最大。
- 已尝试候选编译成功率为 100.0%。
- 已编译候选数值正确率为 100.0%。
- 实际 BLIS microkernel 替换率为 0.0%。
- 正确候选 fallback 比例为 100.0%。
- 相对各 shape 最优样本的归一化性能中位数为 0.265，范围为 0.070—1.000。
- 相对未分块默认路径的 speedup 中位数为 1.683×。
- native 编译时间中位数为 2955.9 ms/候选。

## 解释边界

当前 Transform 模板仅实例化 tiling 与可选 vectorization，尚未实现 BLIS packing/replacement adapter。
因此 0% replacement 和 100% fallback 是实际系统边界，不是 checker 模拟值，也不能用于断言专家空间
的最终性能。预备实验能够支持的结论仅是：通用空间存在策略不兼容候选、性能密度较低，且现有
Transform 后端尚不能利用已建模的 direct microkernel Contract。
