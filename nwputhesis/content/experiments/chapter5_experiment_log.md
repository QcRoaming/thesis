---
exp_id: GEMM-B-260708-001
title: Kernel-aware GEMM 调度搜索空间实验记录
system: GEMM
type: schedule-space-evaluation
date: 2026-07-08
status: planned
data_status: pending_real_measurements
raw_materials: []
notes: >
  本记录为第五章实验的数据记录模板与待补清单。当前尚未写入真实运行数据，
  不得据此生成性能提升、成功率或收敛速度等定量结论。
---

# Kernel-aware GEMM 调度搜索空间实验记录

本文件用于记录第五章“系统实现与实验分析”所需的实验材料。由于当前没有提供真实运行日志、CSV、计时结果或图像材料，本记录只建立数据字段和待补清单，不构成已完成实验。

## 实验目标

验证 kernel-aware expert space 相对 generic tiling space 是否在以下维度上具有更好的搜索空间质量：

1. 有效候选比例；
2. direct/adapt/fallback/reject 候选分布；
3. Microkernel/Library replacement 成功率；
4. 固定搜索预算下的 best-so-far 收敛过程；
5. 真实测量性能；
6. MR/NR、Cache Blocking、Packing、Vectorization、Compatibility Checker 等规则的消融影响。

## 待补原始材料

- [ ] 实验平台信息：CPU 型号、核心数、缓存层次、内存容量、操作系统、编译器版本、MLIR/LLVM commit、BLAS/libxsmm 版本。
- [ ] benchmark 配置：矩阵规模、dtype、转置标志、batch size、动态/静态 shape、重复次数和随机种子。
- [ ] 搜索空间导出日志：每个 candidate 的参数、规则命中、contract 匹配结果、动作类型和失败原因。
- [ ] 编译与正确性日志：compile status、correctness status、失败类型和错误摘要。
- [ ] 性能测量日志：warmup、repeat、latency、GFLOPS、best-so-far trace、measurement noise。
- [ ] 消融实验日志：关闭规则项、候选空间变化、收敛变化和最终性能变化。

## 数据文件规范

第五章配套 CSV 模板位于 `content/experiments/chapter5_data/`。所有数值只能由真实实验流程写入，不应手工估计。

## 异常记录

当前无真实实验异常记录。后续若出现编译失败、运行时错误、结果不一致、测量噪声异常或 R 绘图失败，应在本节追加原因、复现命令和处理方式。

## 原始材料

当前没有归档原始实验材料。后续真实实验产生的日志、CSV、图片和命令行输出应统一归档，并在本节列出路径。
