# 第五章图形契约

## 总体规范

- 绘图后端：Python，使用 Matplotlib、Seaborn、Pandas 和 NumPy。
- 统计单位：候选、workload、seed、目标主机和部署 horizon 必须分开标注。
- 颜色语义：`G0` 为灰色，`G1/B1` 为蓝色，Contract 空间或 `B2` 为青色，校准方法为橙色，完整库为黑色，拒绝或负向边界为红色。
- 输出：每幅图同时导出 SVG、PDF、600 dpi TIFF 和 PNG 预览；SVG 保留可编辑文字。
- 共同风险：离线 replay 不写成重新编译或硬件测量；置信区间不外推到未采样主机；完整库对照不替换为标量 fallback。

## 图5-1 Contract 变异与故障检测

- 主要结论：三个微内核包的 24 个危险单字段变异均被拒绝或安全降级，字段诊断与预期一致；buffer 内容损坏由运行时 reference 检出，不属于静态 checker 的能力范围。
- 证据链：`e1_mutation_results.csv` 和 `e1_fault_injection.csv`。
- 面板：
  - a：8 类危险字段在 3 个 package 上的处理矩阵，区分 fallback 与 reject。
  - b：正例路径、危险变异和隔离故障注入的通过率。
- 统计单位：package-field case；隔离进程故障 case。
- 风险控制：图中不把运行时故障检测归因于静态 checker。

## 图5-2 原始域、通用合法域与 Contract 域

- 主要结论：Contract 将平均候选数压缩到 104.4，同时把微内核可调用密度提高到 1.0，并在规范化后消除当前定义下的 IR 重复。
- 证据链：`e2_space_classification.csv` 和 `e2_first_callable.csv`。
- 面板：
  - a：36 个 workload 上的平均保留候选数，使用对数坐标。
  - b：平均 callable density。
  - c：规范化前后的平均 IR duplicate ratio。
- 统计单位：workload；柱高为 36 个 workload 的均值。
- 风险控制：候选密度不等同于性能；`G0` 的 callable density 按 direct/adapt 计。

## 图5-3 规范化前后的跨工作负载分布

- 主要结论：direct/adapt 路径不消费的 `vectorize` 被规范化后，36 个工作负载的 Contract 候选均减少 50%，均值由 208.7 降为 104.4。
- 证据链：`e2_space_classification.csv` 中 C 空间的规范化前后候选数。
- 面板：按六类工作负载排序的配对竖线；空心方块表示规范化前，实心圆表示规范化后。
- 统计单位：workload；每条竖线是一组确定性的前后配对，不使用推断统计。
- 风险控制：该图只证明不活跃参数折叠对空间规模的影响，不推导搜索性能或部署收益。

## 图5-4 参数规范化与冻结离线重放

- 主要结论：移除微内核路径不消费的 `vectorize` 后，C 池候选数减半，D90 略降，原 BaCO 轨迹按 callback 横轴计算的 time-to-90% 中位数从 11.5 降到 8.0。
- 证据链：`e2_summary.json`、`e2_normalized_convergence.csv` 和规范化前 `fixed_budget_results.csv`。
- 面板：
  - a：规范化前后 C 池平均候选数。
  - b：规范化前后 D90。
  - c：40 条 run 的 callback 轴 time-to-90% 分布，右删失 run 以预算加一记录。
- 统计单位：候选/workload；候选比例；workload-seed run。
- 风险控制：明确标注为冻结实测语料上的离线 BaCO replay，没有新编译或硬件测量；D90 下降和 callback 轴 time-to-90 改善同时报告。该图用于参数规范化消融，不把 8.0 写成唯一查询数，也不用于主张 BaCO 优于随机。

## 图5-5 B1至B4固定预算搜索

- 主要结论：在原异构空间协议中，B2 的 best-at-25 几何均值最高；B3/B4 更早接近各自池内最优，但没有超过完整 BLIS 的稳定证据。
- 证据链：`convergence_normalized.csv`、`fixed_budget_results.csv` 和 `fixed_budget_summary.csv`。
- 面板：
  - a：8 个 tune workload、5 个 seed 上的 best-so-far 中位数和四分位带，完整 BLIS 为 1。
  - b：best-at-25 几何均值及 95% bootstrap 区间。
- 统计单位：workload-seed trajectory；最终区间重采样 40 条 trajectory。
- 风险控制：该置信区间不包含主机变化；不同方法的候选成员不同，结果只回答原协议下的总体方法比较。

## 图5-6 硬 packing 边界与软信息增量

- 主要结论：移除 packing 规则会破坏生成路径的主要性能来源；目标数据改善低预算搜索，但当前 BLIS 软性能字段在目标数据之上没有稳定增量。
- 证据链：`fixed_budget_summary.csv` 和终止实验 `paired_comparisons.csv`。
- 面板：
  - a：完整 B4 与去除 packing 规则的 best-at-25/BLIS 结果。
  - b：Data-only 相对 no-prior、Expert+Data 相对 Data-only 在 budget 5/10 的配对比值。
- 统计单位：workload-seed trajectory；12 个 holdout workload 的配对 cluster bootstrap。
- 风险控制：packing 消融改变候选成员，不能解释为单参数的纯因果效应；软信息比较使用严格同池结果。

## 图5-7 四层迁移边界与跨主机复制

- 主要结论：Contract Schema 和合法执行在受测 package/host 上可复用，生成器复用是分层的，性能排序及校准收益受目标环境影响。
- 证据链：`e3_reuse_audit.csv`、`cross_host_summary.json` 和同池 `paired_comparisons.csv`。
- 面板：
  - a：表示、核心生成、合法执行和性能排序四层证据矩阵。
  - b：i7/i9 上 calibrated-prior 相对 no-prior 的 budget 5/10 配对区间。
- 统计单位：package/host 层级审计；12 个 holdout workload 的配对 cluster bootstrap。
- 风险控制：OpenBLAS RVV 标记为 package-local 生成路径；i7 收益未在 i9 显著复制。

## 图5-8 完整库边界与成本摊销

- 主要结论：预声明的 i9 和 K230 exact-shape 场景中，生成路径均低于完整库；K230 C adapter 与 MLIR adapter 达到 wrapper parity。i7 只有事后筛选的 19-shape 合成场景在很长 horizon 上出现正净值。
- 证据链：i9/K230 external summaries、K230 MLIR closure summary、`e4_value_curves.csv` 和 `e4_break_even_summary.csv`。
- 面板：
  - a：i9 生成池/BLIS、K230 adapter/OpenBLAS 与 K230 C adapter/MLIR adapter 的几何比和 95% CI。
  - b：i7 事后场景的点估计净值与 LCB95 净值曲线，标出两个 break-even。
- 统计单位：workload cluster；closure case cluster；synthetic deployment cycle。
- 风险控制：i7 曲线明确标记为 post-hoc descriptive upper bound；一个 cycle 不是一次模型推理；i9/K230 的 guarded decision 在正文和表格中给出，不画流程图。
