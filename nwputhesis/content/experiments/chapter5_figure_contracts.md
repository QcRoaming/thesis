# 第五章图表契约

后端：R / ggplot2 / patchwork。

当前状态：没有真实实验数据，因此不渲染图，不生成占位图片。

## 图 5-A：搜索空间质量

- 核心结论：真实数据补齐后，该图用于比较 kernel-aware expert space 与 generic tiling space 的有效候选比例和候选动作分布。
- 证据链：`search_space_summary.csv` 中的 `direct_count`、`adapt_count`、`fallback_count`、`reject_count`、`valid_rate`。
- 图类型：quantitative grid。
- 风险：候选总数和有效候选定义必须与正文公式一致；不能把 fallback 误写为 direct replacement 成功。

## 图 5-B：搜索收敛过程

- 核心结论：真实数据补齐后，该图用于比较固定预算下不同搜索空间的 best-so-far 曲线。
- 证据链：`convergence_trace.csv` 中按 `budget_step` 记录的 `best_latency_ms` 或 `best_gflops`。
- 图类型：quantitative grid。
- 风险：失败候选应作为状态记录，而不是伪装为极慢的有效测量。

## 图 5-C：替换成功率与消融

- 核心结论：真实数据补齐后，该图用于展示 compatibility checker 和各类专家规则对 replacement 成功率与性能搜索的贡献。
- 证据链：`replacement_success.csv` 与 `ablation_summary.csv`。
- 图类型：quantitative grid。
- 风险：消融对比必须使用相同 benchmark、相同预算和相同测量流程。
