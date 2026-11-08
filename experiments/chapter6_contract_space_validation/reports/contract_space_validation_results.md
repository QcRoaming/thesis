# Contract 与调度空间补充验证结果

本报告由 `scripts/run_all.py` 生成。E1-E3 为本次静态/结构验证，E2 的编译项重放既有真实二进制清单，E4 只复用已经完成的 i7、i9 和 K230 测量。

## E1 契约独立负例与单字段变异

- 3 个 package 共 30 个 gold case，其中 24 个单字段危险变异。
- Mutation Score = 1.000；false accept = 0；false reject = 0。
- path/phase/diagnostic-field accuracy = 1.000/1.000/1.000。
- 两个隔离故障注入均由 reference GEMM 检出错误结果：2/2。
- 能力边界：静态 checker 不能识别声明正确但物理内容已损坏的 packed buffer。

## E2 调度空间内在价值

- 完成 36 x 2600 = 93600 次静态分类。
- checker 单候选耗时 median/p95 = 1.183/6.112 us。
- 三层空间汇总：

| 空间 | 规范化前 | 规范化后 | 平均缩减率 | callable density | IR 重复率(前->后) | 首个 callable | D90 | time-to-90% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| G0 | 2600.0 | 2600.0 | 0.000 | 0.080 | 0.500->0.500 | 10.0 | 未测 | 未测 |
| G1 | 1056.2 | 951.9 | 0.634 | 0.105 | 0.405->0.342 | 7.0 | 0.0268 | 10.5 |
| C | 208.7 | 104.4 | 0.960 | 1.000 | 0.500->0.000 | 1.0 | 0.1875 | 8.0 |

- 8 x 3 x 32 = 768 条抽样项均能映射到既有真实成功编译 manifest；这不是 768 次新编译。
- 已将 direct/adapt 微内核路径上不活跃的 `vectorize` 规范为 false。C 的平均候选数由 208.7 降至 104.4，IR 重复率由 0.500 降至 0.000。
- 最终规范化方法使用 8 workload x 5 seed x 25 budget 的离线 BaCO replay：D90=0.1875，time-to-90%-pool-best=8.0，达到阈值比例=0.925。replay 只读取冻结目标值，没有重新编译或硬件测量。
- 规范化前消融结果保留为 D90=0.1964、time-to-90%-pool-best=11.5。最终 D90 下降 0.0089，time-to-90% 改善 3.5 次，均按冻结协议报告。
- 规范化 replay 共 40 条运行、1000 次 callback，其中 21 次重复；224 个最终池项中 166 个有成对 canonical IR，58 个仅有单边历史 IR，后者依赖静态活性审计。
- 同一 28 点池和 25 个唯一候选查询预算下，BaCO/random 的达到率为 0.925/1.000，中位 T90 为 7.5/7.0。BaCO 为取得 1000 个唯一查询共消费 1021 次 callback，其中 21 次重复；random 无重复。
- budget 5 的 BaCO-random 平均 best-fraction 配对差为 0.0032，workload-cluster 95% CI=[-0.0636, 0.0643]；当前结果不支持 BaCO 优于均匀随机。
- G1 的 D90/time-to-90% 仍是规范化前历史测量；G0 没有既有性能池。

## E3 Contract package 复用审计

- 三个 package 的 schema 交集/并集为 31/34 个 leaf path，intersection-over-union 复用率为 0.912。
- 逐 package 共享字段覆盖率为 blis_haswell_f32_6x16=0.969, blis_haswell_f64_6x8=0.969, openblas_riscv64_zvl128b_f32_8x8=0.939；共享核心中的 package-ID 特判数为 0。
- BLIS f64 的既有 before/after 哈希审计显示核心 generator 不变：True。
- OpenBLAS RVV 已证明第二库/第二 ISA 的 Contract、adapter 和合法执行，但当前使用 package-local 生成路径。
- 因而“任意新 package 均零核心修改”的强主张为 False；可支持的是 schema 复用和 BLIS 内第二 dtype 的核心复用。
- 无可靠 onboarding 工时日志，也无三个 package 的干净历史 LOC delta，报告不作事后估算。

## E4 搜索经济性

| 场景 | 单位 | 单位净节省点估计 | 95% CI | 点估计 break-even | LCB95 break-even |
|---|---|---:|---:|---:|---:|
| i7 f64 事后 winning shapes | deployment cycle | 3.207157 ms | [0.717318, 4.066746] | 165864.6 cycles | 741587.4 cycles |
| i9 Qwen exact shapes | inference | -275.156448 ms | [-483.488434, -108.277634] | 无有限值 | 无有限值 |
| K230 Qwen exact shapes | inference | -5527.751064 ms | [-9632.592838, -2078.069330] | 无有限值 | 无有限值 |

- i7 成本分解：`C_c=58.239 ms`，`sum C_s,j=531895.625 ms`（测量 32115.966 ms，唯一编译 499779.660 ms）。源日志只支持聚合 `sum C_s,j`，不报告虚构的逐 shape 分摊。
- `POST_HOC_DESCRIPTIVE_UPPER_BOUND`：i7 winning set 在观察性能后选择，只是描述性上界。deployment cycle 定义为对这 19 个 shape 各调用一次的等频合成单位，不是一次模型 inference，也不是实测部署频率。
既有 D0/D1 的 2293.6/2339.0 workloads 是后续调优服务任务数，不是单矩阵调用数，也不是模型 inference 数。只有 `LCB95(V(H)) > 0` 时才判定搜索值得。

## 结论边界

E1 支持 Contract 作为可诊断的安全门；E2 在消除微内核路径不活跃的 `vectorize` 后给出有效唯一空间指标；E3 量化了 schema 复用且只部分支持 package 化复用；E4 表明调优价值依赖设备、shape 分布和完整库基线，不能从局部候选胜出泛化为普遍收益。

## 结果路径

- `processed/e1_mutation_results.csv`、`e1_fault_injection.csv`、`e1_summary.json`
- `processed/e2_space_classification.csv`、`e2_first_callable.csv`、`e2_compile_replay.csv`、`e2_summary.json`
- `processed/e2_random_search_traces.csv`、`e2_baco_random_paired.csv`、`e2_baco_random_summary.json`
- `processed/e3_reuse_audit.csv`、`e3_summary.json`
- `processed/e4_break_even_summary.csv`、`e4_value_curves.csv`、`e4_summary.json`
