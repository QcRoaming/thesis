# 第3章写作—成果映射

## 3.1 问题上下文与知识来源边界

引用 `research-scope.md`。必须同时写明知识源为 Haswell、测量主机为
i7-10750H，两者仅 ISA 兼容，不能混称为同一微架构。

## 3.2 通用调度空间的预备实证分析

引用 `reports/chapter3_preliminary_results.md`、图3-1、
`processed/preliminary_space_sizes.csv` 和 `processed/preliminary_best_so_far.csv`。
只写预备结论，不做第6章式正式性能宣称。

## 3.3 专家事实抽取方法

描述活动预处理分支识别、context 注册提取、kernel setup 交叉核对、原子化
Fact 输出和版本固定流程。方法名称使用“半自动抽取与核验”。

## 3.4 专家事实统一表示

引用表3-1、`schemas/fact.schema.json`、`data/facts.json` 和
`reports/extraction_quality.md`。明确 E1/E2/E3 与 automatic/derived 的区别。

## 3.5 目标微内核 Contract 建模

引用表3-2和两个真实 Contract：f32 6×16、f64 6×8。区分
`kernel_requirements` 与 `adapter_capabilities`，alignment 保持歧义状态。

## 3.6 专家规则构建方法

引用表3-3。五类规则为 register blocking、cache blocking、packing、
vectorization、tail/fallback；每条规则都包含条件、强度、优先级、scope、
source facts 和 conflict policy。

## 3.7 证据等级、迁移范围与冲突处理

引用 `data/evidence_levels.yaml`、`data/ambiguities.csv` 和
`data/conflicts.csv`。强调 shape/语义约束覆盖 cache prior 时会记录 suppressed
source，不静默覆盖。

## 3.8 贯穿案例

引用图3-4、`provenance/anchor_192x256x256.json` 和
`reports/provenance_case.md`。核心是区分 Contract 预测 direct 与实际 fallback。

## 3.9 本章小结

本章已完成知识获取、统一表示和小规模问题实证；实际 packing/replacement
adapter、专家核心/探索外壳和完整调优闭环属于后续章节，不能提前声称已完成。
