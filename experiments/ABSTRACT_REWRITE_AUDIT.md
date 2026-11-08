# 摘要重写审计

## Draft rewrite

第一稿采用完整证据版结构，先写清方法链，再集中报告正确性、消融、同池比较和跨主机结果。

### 中文初稿

本文面向 MLIR Transform Dialect 的通用矩阵乘法（General Matrix Multiplication，GEMM）自动调优，构建了从高性能库源码事实到可执行调度候选的证据化生成流程。高性能库源码同时包含微内核接口条件和特定实现上的性能参数。若将二者直接写成同一组专家规则，自动调优系统便会混淆微内核调用资格与候选性能排序，并把只在来源平台有效的参数固化到搜索空间中。

研究固定 BLIS 与 OpenBLAS 的源码版本，将配置拆分为带来源位置、适用范围和核验状态的字段级 Expert Fact。数据类型、ISA、MR/NR、打包布局、尾部处理和调用 ABI 只有在执行后端已经实现并验证时才进入微内核 Target Contract；缓存分块与来源候选顺序保留为目标相关的软性能特征。Compatibility Checker 根据 Contract 将候选分为 direct、adapt、fallback 或 reject，目标测量只能更新可执行候选的排序，不能改写兼容性条件。生成结果经过 MLIR Transform、LLVM lowering、BLIS packing 与调用适配器执行，并接入 BaCO 完成有限预算搜索。

BLIS Haswell 主路径形成 22 条字段级 Fact、两个行主序单线程 Target Contract 和 5 类 Expert Rule，16 个源码核验案例均完成作者签核。六个生成任务共枚举 15,600 个候选，其中 10,200 个具有可执行路径，包括 1,420 个 direct、432 个 adapt 和 8,348 个 fallback；其余 5,400 个候选被拒绝。在已测试的两个 Contract 及其作用域内，1,256 个 f32 candidate-workload case 和 1,008 个 f64 case 均通过数值检查，端到端路径预测与运行观测一致。

单精度正式实验中，每种方法包含 40 个 run。预算为 25 时，Contract-only、Expert-core 与 Expert+Shell 所选候选相对完整 BLIS 前端的性能几何均值点估计分别为 0.948、0.791 和 0.800；Contract-only 的点估计最高，三种方法未另作配对显著性检验。移除 packing 规则后，同一指标由 0.800 降至 0.046。这项消融说明，packing 不能被当作可有可无的性能提示。

双精度同池实验包含 12 个留出 workload 和 5 个随机种子。预算为 5 时，Data-only 相对 no-prior 的所选候选性能比为 1.0488，95% 置信区间为 [1.0245,1.0752]；Expert+Data 相对 Data-only 为 1.0085，区间为 [0.9992,1.0266]，预算为 10 时该比值为 1.0000。现有 BLIS 派生软特征没有表现出明确增量，591 条校准记录约 531.95 s 的成本也未在 12 个留出 workload 内摊销。两台 x86 主机上的双精度 Contract 路径预测均与观测一致，但逐 workload 最优生成候选相对完整 BLIS 的性能几何均值从 i7-10750H 上的 1.064 变为 i9-14900 上的 0.804。

在已经实现的 Contract 和目标条件内，硬兼容知识可以复用；性能排序仍需目标平台测量。当前闭环限于行主序、单线程、rank-2 GEMM，两个 Contract 均来自 BLIS Haswell 后端，尚未覆盖任意 stride、多线程、批处理算子或独立后端。

### English draft

This thesis develops an evidence-tracked workflow that turns source-level knowledge from high-performance libraries into executable general matrix multiplication (GEMM) schedules for MLIR Transform Dialect. Library sources contain both microkernel interface conditions and performance parameters chosen for a particular implementation. Encoding both as one set of expert rules conflates eligibility for a microkernel call with performance ranking and can hard-code assumptions that hold only on the source platform.

The workflow pins revisions of BLIS and OpenBLAS and decomposes their configurations into field-level Expert Facts with source locations, applicability scopes, and verification states. Data type, ISA, MR/NR, packed layouts, tail handling, and the call ABI enter a microkernel Target Contract only when the execution backend implements and validates them. Cache blocks and source-specific candidate ordering remain target-dependent soft performance features. A Compatibility Checker classifies each candidate as direct, adapt, fallback, or reject. Target measurements may reorder executable candidates but cannot change compatibility conditions. Generated schedules pass through MLIR Transform, LLVM lowering, BLIS packing, and call adapters, and BaCO searches the resulting finite space under a fixed budget.

The BLIS Haswell path contains 22 field-level Facts, two row-major single-threaded Target Contracts, and five classes of Expert Rules; all 16 source-verification cases received author sign-off. Six generation tasks enumerated 15,600 candidates. Of these, 10,200 retained executable paths, including 1,420 direct, 432 adapt, and 8,348 fallback candidates, while 5,400 were rejected. Within the two tested Contracts and their declared scopes, all 1,256 f32 candidate-workload cases and 1,008 f64 cases passed numerical validation, and every predicted end-to-end path matched its runtime observation.

The formal f32 evaluation used 40 runs per method. At a budget of 25, the point estimates of geometric mean performance relative to the full BLIS frontend were 0.948 for Contract-only, 0.791 for Expert-core, and 0.800 for Expert+Shell. The Contract-only estimate was the highest; the three methods were not subjected to an additional paired significance test. Removing the packing rule reduced the same metric from 0.800 to 0.046. This ablation shows that packing cannot be treated as an optional performance hint.

The same-pool f64 experiment used 12 holdout workloads and five random seeds. At a budget of 5, Data-only achieved a selected-candidate performance ratio of 1.0488 over no-prior, with a 95% confidence interval of [1.0245,1.0752]. Expert+Data achieved 1.0085 over Data-only, with an interval of [0.9992,1.0266], and the ratio was 1.0000 at a budget of 10. The current BLIS-derived soft features therefore provide no clear incremental benefit, and the 531.95 s cost of 591 calibration records was not amortized over the 12 holdouts. Path predictions for the f64 Contract matched observations on both x86 hosts, but the geometric mean performance of the best generated candidate per workload relative to full BLIS changed from 1.064 on the i7-10750H to 0.804 on the i9-14900.

Within the implemented Contracts and tested target conditions, hard compatibility knowledge transfers, whereas performance ranking still requires target measurements. The current pipeline is limited to row-major, single-threaded rank-2 GEMM. Both Contracts belong to the BLIS Haswell backend; arbitrary strides, multithreading, batched operators, and an independent backend remain outside the validated scope.

## What makes the below so obviously AI generated?

- 六段正文把所有可用数字都塞进摘要，读起来更像实验报告，中文也明显超出学校普通硕士论文摘要的建议篇幅。
- 方法段暗示所有候选都经过 BLIS packing 和微内核调用，遗漏了 fallback 使用通用 lowering 的事实。
- “这项消融说明”和英文的总结句收束得过于整齐，容易把当前实现中的结论写成普遍规律。
- 数字段的句长和节奏过于接近，多个比较连续出现，却没有始终说明这些数字分别回答正确性、软特征增量还是迁移边界问题。
- “hard compatibility knowledge transfers” 的范围过宽，证据只覆盖两个受测 x86 主机、两个同后端 Contract 和声明的执行条件。
- 初稿还保留了模板基金占位语，不能出现在送审稿中。

## Final rewrite

定稿位于 `jlq/thesis/nwputhesis/content/thesis/graduate/abstract.tex`。修改包括：

- 用四段完成问题、方法、结果和边界的论证，不再逐项罗列所有实验产物。
- 明确 direct 与 adapt 调用 BLIS 微内核，fallback 使用通用 lowering。
- 明确 15,600 与 10,200 是检查器分类结果，不是全部候选均已编译实测。
- 将 1.0488 和 1.0085 写为配对加速比的几何均值，并保留置信区间。
- 将 packing 结论限定在当前 BLIS 微内核调用链，将硬兼容知识的复用限定在两台受测 x86 主机。
- 删除基金和英文模板占位文本。中文正文按去除空白但保留数字、标点和拉丁字符的口径为 996 个字符，英文正文为 385 个空白分词。中英文各使用 6 个关键词，并各自排在一个正文页内。
- 最终中英文正文均未使用 em dash、en dash 或作为破折号的双连字符。

## Evidence boundary

定稿不声称静态专家规则普遍提高性能，不声称性能排序可以跨主机迁移，也不声称已完成任意步长、多线程、批处理算子、端到端模型或独立后端验证。两个已执行验证的 Contract 均来自 BLIS Haswell 后端。
