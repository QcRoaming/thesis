# Contract and schedule-space validation

本实验包补足四项独立验证：Contract 单字段变异、调度空间内在价值、package
复用审计和搜索经济性。它不重新测量已经完成的 i7/i9/K230 性能，而是把新静态
验证与冻结的真实测量连接成可重复分析。

## 一键执行

```bash
python3 scripts/run_normalized_baco_replay.py
python3 scripts/run_same_pool_random_baseline.py --analyze-only
python3 scripts/run_all.py
python3 -m unittest discover -s tests -v
python3 scripts/audit_documentation.py
```

`run_normalized_baco_replay.py` 只读取既有目标值，不调用编译器或硬件 benchmark。
若 replay 轨迹已冻结，只需重建映射与统计，可运行
`python3 scripts/run_normalized_baco_replay.py --analyze-only`。
`run_same_pool_random_baseline.py` 在同一 28 点冻结实测子池上比较 BaCO 与无放回
均匀随机排列；两种方法都按 25 个唯一候选查询计预算，不执行编译或硬件测量。

单独运行某项：

```bash
python3 scripts/run_all.py --only E1
python3 scripts/run_all.py --only E2
python3 scripts/run_all.py --only E3
python3 scripts/run_all.py --only E4
```

主报告为
[`reports/contract_space_validation_results.md`](reports/contract_space_validation_results.md)。

## E1：独立负例与单字段变异

- 对象：BLIS Haswell f32 6x16、BLIS Haswell f64 6x8、OpenBLAS
  RV64GCV f32 8x8。
- oracle：`data/mutation_oracle.json` 固定 expected path、首次拒绝阶段和诊断字段；
  checker 不生成 gold 标签。
- 每个 package 含 direct、adapt 和 8 个危险单字段变异，共 30 case。
- 两种 buffer fault 在独立 Python 进程中执行，只验证错误数值会被 reference GEMM
  发现，不执行错误 ISA 或破坏真实 ABI。

## E2：三层调度空间

- G0：2600 点原始笛卡尔积；G1：现有 B1 通用合法空间；C：现有 B2 硬
  Contract callable 空间。
- 对 36 个 workload 完成 93,600 次静态分类，并记录 path 分布、callable
  density、inactive-parameter 等价和规范化 Transform schedule 哈希重复率。
- G1/C 中 direct/adapt 候选进入 microkernel 路径后不消费 `vectorize`，因此离线
  规范化为 `false` 并按唯一 schedule 重算候选数、path、callable density、IR
  哈希和首次 callable；同时保留规范化前规模。
- 最终方法按冻结协议构造 8 个 28 点规范化实测池，使用 BaCO 3.0、5 个原 seed、
  budget 25 完成 40 条离线 replay。最终 D90 为 0.1875；按原 callback 横轴统计，
  time-to-90%-pool-best 为 8.0，40 条运行中 92.5% 达到阈值。旧 D90 0.1964 和
  11.5 次只保留为规范化前消融结果。
- 规范化池先折叠旧 B2 中的 `v0/v1`，再从既有 base B1-B4 实测 direct/adapt
  并集中按原 B2 稳定哈希回填到 28 点。池构造不读取性能，目标值只在 BaCO
  返回 token 后查询；本次没有重新编译或硬件测量。
- 28 点子池相对每个 workload 的完整规范化 C 空间覆盖率为 14.3%--46.7%，
  未加权均值为 24.5%；8 个池共 224 项，其中 direct/adapt 各 112 项。199 项
  来自旧 B2 语义折叠，25 项按稳定哈希从既有测量集中确定性回填。该过程不读取
  runtime，性能结论只适用于冻结实测子池，不描述完整 104.4 候选空间的性能分布。
- 在同一子池、seed 和 25 个唯一候选查询预算下，BaCO/random 的达到率为
  0.925/1.000，中位 T90 为 7.5/7.0。BaCO 为取得 1000 个唯一查询共消费
  1021 次 callback，其中 21 次重复；random 使用无放回排列，无重复查询。
  budget 5 的 BaCO-random 平均 best-fraction 差为 0.0032，workload-cluster
  95% CI 为 [-0.0636, 0.0643]；budget 10 的区间同样跨 0，budget 25 则因
  random 接近遍历整个有限池而略优。当前结果不支持 BaCO 优于均匀随机。
- 8 个代表 workload 的 768 条编译项来自既有真实
  `binary_manifests.json` 规范化前重放。它们证明这些抽样候选曾真实编译成功，
  但不是本次重新编译 768 次，也不表示每层均有 32 个唯一规范化候选，更不外推
  到未编译的 G0 候选。
- G1 的 D90/time-to-90% 仍为规范化前历史测量；G0 没有性能池，因此保持缺失。

## E3：package 复用审计

- schema leaf path 来自本包三个冻结 Contract，并报告三者交集、并集、
  intersection-over-union 及逐 package 共享字段覆盖率。
- BLIS f64 的核心修改数使用既有 before/after SHA-256 审计；OpenBLAS RVV
  当前为 package-local generator，明确标为部分复用。
- adapter/config 为当前树可复核 LOC，不冒充历史新增 LOC。
- automatic/derived/source-cross-check 数量来自既有 BLIS `facts.json` 和
  OpenBLAS 多源提取器；人工 onboarding 工时因无日志而不报告。

## E4：搜索经济性

- i7 f64 使用真实 trial 与校准成本，给出事后 winning-shape 上界场景；该筛选
  不是可部署的事前策略。
- 成本显式拆为 `C_c` 与聚合 `sum_j C_s,j`，并同时报告点估计和 LCB95
  break-even。现有日志没有逐 shape 的 `C_s,j`，因此不作事后均摊。
- i7 的 `deployment cycle` 是对 19 个事后 winning shape 各调用一次的等频合成
  单位，不等于模型 inference，也不代表真实部署频率。
- i9 与 K230 使用冻结 Qwen trace 的 8 个 exact shape 和真实 BLIS/OpenBLAS
  测量。分母为负时，即使假定搜索成本为零也不存在有限 break-even。
- 结果区分 tuning-task、deployment-cycle 和 model-inference 三种 horizon；既有
  2293.6/2339.0 是后续调优任务数，不是矩阵调用数。

## 结论边界

本包可支持“Contract 是可诊断安全门、硬约束提高 callable density、部分 package
知识可复用、搜索是否值得取决于 horizon 与完整库基线”。同池随机对照没有证明
BaCO 的增量优势。它不支持“硬空间必然更快找到最优点”“任意后端零核心修改”或
“生成路径普遍快于完整 BLAS 库”。
