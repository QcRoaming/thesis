# CGO 2025 Transform Dialect 4.5 实验：课题可复用信息

## 1. 文档范围

本文档提取以下材料中对当前 GEMM 专家调度空间课题可复用的信息：

- 论文：`../../论文阅读清单/The MLIR Transform Dialect.pdf`
- 论文第 4.5 节：PDF 第 11 页，论文页码 251
- 图 10、图 11：PDF 第 11 页
- 图 12：PDF 第 12 页，论文页码 252
- 本目录中的 6 个核心文件：
  `parametric_transform.mlir`、`performance_exploration.py`、
  `search_settings.json`、`search_batch_matmul.c`、`CMakeLists.txt`、
  `run_all.sh`

论文信息：Martin Paul Luecke 等，*The MLIR Transform Dialect: Your
Compiler Is More Powerful Than You Think*，CGO 2025，DOI：
`10.1145/3696443.3708922`。

本文件只记录能够迁移到课题实现、实验设计和论文写作中的信息，不是整篇论文摘要。

## 2. 必须保持一致的术语

| 统一术语 | 本文含义 | 不应混用的表述 |
|---|---|---|
| payload IR | 被优化的计算 IR | input script |
| Transform script | 控制 payload IR 变换的 Transform Dialect IR | payload |
| 参数化 Transform 模板 | 含 `tile0`--`tile3`、`do_vect` 占位参数的 Transform script | 已实例化脚本 |
| 配置实例 | 调优器给出的一组具体参数 | 搜索空间 |
| feasible/valid | 原实验中的编译可行状态 | 数值正确、Contract 兼容、替换成功 |
| observed replacement | 生成 IR 或可执行文件中实际出现目标库调用 | Contract 预测为 direct |
| fallback | 未进入专用库路径但仍可正确执行的通用 lowering | 编译失败 |

## 3. 论文第 4.5 节能够直接支持的结论

第 4.5 节展示的核心不是新的搜索算法，而是 Transform Dialect 与外部调优器之间的接口：

1. Transform script 将 tile size 和 vectorization 决策暴露为可替换参数。
2. BaCO 为参数生成配置。
3. 每个配置被写回 Transform script，重新编译并运行。
4. 实测 runtime 返回给 BaCO，形成闭环。
5. 论文报告搜索过程逐步找到更优 tile size，最终 speedup 为 **1.68**。

图 12 的横轴是评估次数，纵轴是当前 best-so-far speedup。它可作为本课题绘制“小预算收敛曲线”的直接结构参考。

### 3.1 不能混写的结果

- **1.68 倍**是第 4.5 节 BaCO 搜索 tiling/vectorization 参数的最终结果。
- **0.017 s、20 倍以上加速**属于第 4.4 节的 libxsmm microkernel replacement 实验。
- 当前提取的 `parametric_transform.mlir` 没有
  `transform.to_library`，因此这些文件本身不能证明发生了 libxsmm replacement。
- `linalg.batch_matmul` 上的 `library_call="libsxmm_smm"` 属性也不能单独作为实际替换证据；必须检查变换后 IR、LLVM IR 或最终符号。

这一区分与本课题现有的“Contract 预测 direct，但 observed path 为 fallback”边界完全一致。

## 4. 六个核心文件的角色

| 文件 | 原实验职责 | 课题中的可复用角色 |
|---|---|---|
| `parametric_transform.mlir` | payload、参数化 tiling/vectorization 和 lowering pipeline | Transform 模板与参数槽位参考 |
| `search_settings.json` | BaCO 参数、约束、初始样本、迭代数和可行性字段 | 由专家空间导出的 tuner 配置 |
| `performance_exploration.py` | 配置实例化、编译、执行、runtime 回传 | evaluator/tuner adapter 骨架 |
| `search_batch_matmul.c` | 构造 MemRef、运行 15 次、输出中位 runtime | AOT benchmark driver 的反例与部分参考 |
| `CMakeLists.txt` | Transform 执行、schedule 擦除、LLVM IR 翻译、目标链接 | 编译流水线阶段参考 |
| `run_all.sh` | 启动 Case Study 5 并绘制优化曲线 | 一键实验入口与结果绘图参考 |

## 5. 原实验闭环

当前文件体现的执行链为：

```text
search_settings.json
  -> BaCO 生成 config
  -> 文本实例化 parametric_transform.mlir
  -> specialized_transform.mlir
  -> mlir-transform-opt 执行 Transform script
  -> 擦除 Transform schedule
  -> mlir-translate 生成 LLVM IR
  -> clang 编译并与 C driver 链接
  -> 运行 search_batch_matmul
  -> 输出 runtime 中位数
  -> {runtime, Valid} 返回 BaCO
  -> CSV 与 best-so-far 曲线
```

关键源码锚点：

- 参数替换：`performance_exploration.py:52-69`
- 每个配置重新构建：`performance_exploration.py:72-103`
- runtime/Valid 返回：`performance_exploration.py:101-111`
- 参数化 tiling：`parametric_transform.mlir:53-60`
- 条件 vectorization：`parametric_transform.mlir:62-72`
- lowering pipeline：`parametric_transform.mlir:23-50`
- MLIR 到目标文件：`CMakeLists.txt:26-64`
- 15 次测量与中位数：`search_batch_matmul.c:131-160,198-216`

## 6. 参数空间语义

payload 为固定 shape 的 `f32` batch matmul：

```text
B = 6
M = 196
N = 256
K = 2304
A: 6x196x2304
B: 6x2304x256
C: 6x196x256
```

参数与约束如下：

| 参数 | 对应循环 | 范围 | 约束 | 课题映射 |
|---|---|---|---|---|
| `tile0` | batch/B | `[0, 6]` | 0 或 6 的因子 | batch tile；普通 GEMM 可移除 |
| `tile1` | M | `[0, 196]` | 0 或 196 的因子 | `tile_m` |
| `tile2` | N | `[0, 256]` | 0 或 256 的因子 | `tile_n` |
| `tile3` | K | `[0, 2304]` | 0 或 2304 的因子 | `tile_k` |
| `do_vect` | vectorization | `{0,1}` | `tile3` 非 4 的倍数时必须为 0 | `vectorize` 条件参数 |

0 表示该维不生成 tile loop。它不只是普通数值，还会改变
`tile_using_for` 返回的 loop handle 数量。因此
`handle_dynamic_types()` 会统计 0 的个数并重写 `%loops:N` 和结果类型列表。

按当前 JSON 约束枚举推算：

- `tile0` 有 5 个值；
- `tile1` 有 10 个值；
- `tile2` 有 10 个值；
- `tile3` 有 28 个值；
- 加入二值 vectorization 后，未考虑条件依赖的组合数为 28,000；
- 应用 `tile3`/`do_vect` 依赖后，组合数为 25,000。

上述计数是依据当前 `search_settings.json` 计算的结果，不是论文直接报告的数据。

## 7. 最值得复用的设计模式

### 7.1 payload 与调度分离

计算语义保存在 payload IR，搜索参数只出现在 Transform script。这样，同一 payload 可以复用多个调度实例，也能在不修改计算代码的情况下替换 tuner。

课题中应继续保持：

```text
linalg.matmul payload
+ 参数化 Transform 模板
+ Task Context / Contract / Expert Rules
+ tuner config
```

### 7.2 条件参数通过 `transform.alternatives` 表达

本地模板把 `do_vect` 写成 Transform 参数常量。第一条 alternative 先断言参数等于 1，再执行 vectorization；断言失败时进入空 alternative，保留 tiled 实现。

这个模式可扩展为：

```text
direct replacement
  -> adapt with packing/tail handling
  -> generic vectorized fallback
  -> scalar/tiled fallback
```

但每条路径必须输出独立的 observed outcome，不能只依靠 alternative 的静态顺序推断实际执行路径。

### 7.3 调优器只依赖统一 evaluator 接口

BaCO 不直接理解 MLIR。它只需要：

```text
config -> objective + feasibility
```

因此，专家搜索空间生成器可以独立于 BaCO：先生成参数域、条件依赖和初始设计点，再由 evaluator 负责 Transform 实例化、编译和测量。以后替换为随机搜索、贝叶斯优化或其他 tuner 时，后端不必重写。

### 7.4 编译失败作为可行性信号

原实验返回 `Valid=0` 供 BaCO 的 feasible predictor 学习，说明编译失败不必终止整个搜索。

本课题应把单一 `Valid` 扩展为：

```text
policy_legal
transform_status
compile_status
correctness_status
contract_prediction
execution_path
microkernel_replaced
failure_stage
failure_reason
runtime_ms
gflops
```

这与第三章成果包中的结构化结果字段保持一致。

### 7.5 best-so-far 是首要搜索指标

论文图 12 不只报告最终最优值，还报告搜索过程。课题实验应在相同 budget 下比较：

- generic space；
- Contract-only space；
- Expert-core space；
- Expert+Shell space；
- 各消融配置。

每条曲线至少记录随机种子、测量预算、失败候选是否计入 budget，以及中位数/四分位区间或置信区间。

## 8. 不能直接复用的内容与风险

### 8.1 当前目录不是独立可运行成果

`CMakeLists.txt` 还引用以下未提取的静态支持文件：

- `run_with_timeout.py`
- `batch_matmul.c`
- `batch_matmul.mlir`

`specialized_transform.mlir` 不属于静态缺失文件，它应由
`performance_exploration.py` 针对每个配置生成；在搜索开始前不存在是正常状态。

另外，路径固定为 `/home/lib/...`、`/home/scripts/...` 和 LLVM/Clang 18。当前课题使用 LLVM 21，Transform op 名称、pass 名称和工具命令需要逐项迁移，不能假定文件可直接编译。

### 8.2 参数实例化是脆弱的文本替换

`specialized_script.replace(key, value)` 不理解 MLIR 语法，可能替换注释或其他同名子串；`handle_dynamic_types()` 还依赖单行、四个十进制整数的正则表达式。课题中可以把它作为最小原型，但正式实现应使用以下任一方式：

1. 从结构化模板生成 Transform IR；
2. 使用明确且唯一的占位符，例如 `@TILE_M@`；
3. 实例化后立即运行 parser/verifier，并保存失败原因。

### 8.3 `Valid` 只代表构建成功，不代表正确

原 evaluator 在构建成功时直接返回 `Valid=1`，C driver 没有参考实现或数值比较。因此论文 4.5 的可行性不能转换为本课题的 correctness pass。

课题中必须采用以下顺序：

```text
Transform 合法
-> 编译成功
-> 数值正确
-> 执行路径确认
-> 性能进入目标函数
```

### 8.4 无效候选返回 `runtime=0` 有目标污染风险

当前脚本对编译失败返回 `{runtime: 0, Valid: 0}`。若可行性过滤失效或分析脚本忽略 `Valid`，0 会被错误解释为最优 runtime。建议无效候选使用 `null`、`NaN` 或显式惩罚值，并要求所有绘图/统计先过滤状态字段。

### 8.5 MemRef descriptor 参数与声明 shape 不一致

`search_batch_matmul.c:193-195` 的 descriptor 构造至少存在以下不一致：

- A 声明为 `[B,M,K]`，但调用传入 `[B,M,N]` 的 sizes；
- B 声明为 `[B,K,N]`，但调用仍传入 `m` 和 `lda=k`，其 sizes/strides 与 B 的实际布局不一致；
- C 是返回值 descriptor，调用约定需要结合生成的 C wrapper 核验。

即使静态 shape lowering 可能不读取全部动态字段，也不能把这一写法迁移到课题。应分别构造 A/B/C descriptor，并用正确性测试和 AddressSanitizer 验证 ABI。

### 8.6 测量协议不足以支撑正式实验

原 C driver：

- 无预热；
- 随机输入使用当前时间作为种子；
- 不固定 CPU affinity；
- 不记录线程数与环境；
- runtime 超过 1 s 时提前终止并复制该次时间；
- 每次调用返回新分配的 C，但没有释放返回 buffer；
- 只输出一个 runtime，没有正确性、GFLOP/s 或失败原因。

这些行为可用于演示调优接口，不足以直接作为论文第六章测量协议。

### 8.7 本地文件没有实现 library replacement

论文图 10 展示了：

```text
to_library(libxsmm) -> vectorize -> identity
```

但本地 `parametric_transform.mlir` 只有：

```text
conditional vectorize -> identity
```

而 `CMakeLists.txt` 虽定义 `LIBXSMM_LIB_PATH`，链接命令没有实际使用该路径或链接 libxsmm。故本目录适合复用调优闭环，不适合复用为 direct/adapt library path 的实现。

## 9. 映射到当前课题的推荐接口

建议保留论文的 evaluator 思路，但把接口扩展为：

```python
def evaluate(task, contract, rules, config):
    decision = compatibility_check(task, contract, config)
    if decision.path == "reject":
        return rejected_result(decision)

    transform_ir = instantiate_transform(decision, config)
    transform_result = run_transform(transform_ir)
    compile_result = compile_to_native(transform_result)
    correctness = check_correctness(compile_result)
    observed_path = inspect_symbols_and_ir(compile_result)
    performance = measure_only_if_correct(compile_result)

    return {
        "config": config,
        "contract_id": contract.id,
        "rule_ids": decision.rule_ids,
        "predicted_path": decision.path,
        "observed_path": observed_path.path,
        "microkernel_replaced": observed_path.replaced,
        "compile_status": compile_result.status,
        "correctness_status": correctness.status,
        "runtime_ms": performance.runtime_ms,
        "gflops": performance.gflops,
        "provenance": decision.provenance,
    }
```

### 9.1 第四章可复用内容

- 使用条件参数域描述 tile、packing、vectorization 和 path。
- 将维度整除条件从固定数字改为 Task Context 生成。
- 将硬编码 `vector_size=4` 改为 Contract/Fact 中的 dtype-specific lane 数；当前 Haswell `f32` 应为 8 lane，`f64` 应为 4 lane。
- 把 `do_vect` 的单一依赖扩展为 packing、tail、replacement 和 fallback 的条件依赖。
- 将 Contract 兼容预测与后端是否实现 adapter 分开。

### 9.2 第五章可复用内容

- 保留“配置实例化 -> Transform -> LLVM IR -> AOT -> 运行”的 evaluator 分层。
- 每个阶段保存命令、stdout、stderr、耗时和返回码。
- 编译缓存按 Transform 实例 hash 管理，避免每个候选无条件 `make clean`。
- 使用结构化 CSV/JSONL，而不是只让可执行文件输出一个浮点数。
- 把生成脚本、IR、LLVM IR、符号检查和测量结果放入同一 candidate 目录。

### 9.3 第六章可复用内容

- 绘制相同 budget 下的 best-so-far 曲线。
- 单独报告 policy reject、Transform failure、compile failure、correctness failure、direct、adapt 和 fallback。
- 报告 raw/legal/executable space size，而不是只报告 tuner 采样次数。
- 同时报告搜索时间、单候选编译时间和单候选运行时间。

## 10. 与第三章贯穿案例的正式对齐

本节所称“对齐”是指参数接口、执行闭环和证据字段对齐，不要求两个案例使用
相同 workload，也不改写第三章已经冻结的预备实验数据。论文 4.5 的对象是
固定 shape 的 `linalg.batch_matmul`，第三章贯穿案例则是普通
`linalg.matmul`；二者共同提供的是“配置驱动 Transform”的实验接口。

### 10.1 workload 与参数映射

| 对齐项 | 论文 4.5 | 第三章贯穿案例 | 对齐结论 |
|---|---|---|---|
| 计算 | `linalg.batch_matmul` | `linalg.matmul` | 算子族一致，batch 语义不同 |
| shape | `B=6, M=196, N=256, K=2304` | `M=192, N=256, K=256` | 不做数值等同，不迁移论文最优配置 |
| batch tile | `tile0` | 无 | 普通 GEMM 中删除该参数，可视为无 batch 维而非 `tile0=0` |
| M tile | `tile1` | `tile_m=24` | 映射为 $T_M$ |
| N tile | `tile2` | `tile_n=32` | 映射为 $T_N$ |
| K tile | `tile3` | `tile_k=64` | 映射为 $T_K$ |
| 向量化开关 | `do_vect` | `vectorize=true` | 映射为 $V=1$ |
| vector lane 来源 | 模板约束中固定为 4 | Haswell `f32` Contract 给出 8 | 只对齐开关，不复制固定 lane 数 |

因此，论文参数接口到第三章锚点配置的投影为：

```text
(tile0, tile1, tile2, tile3, do_vect)
    -> (batch omitted, tile_m, tile_n, tile_k, vectorize)
    -> (omitted, 24, 32, 64, true)
```

锚点配置满足 `192/24=8`、`256/32=8` 和 `256/64=4`，因而三个
tile 均能整除对应维度；`tile_n=32` 同时是 Haswell `f32` 8-lane
向量宽度和 NR=16 的整数倍。这里的合法性来自第三章 Task Context、Contract
和规则，不来自论文 4.5 针对固定 shape 编写的 divisor 列表。

### 10.2 执行闭环映射

| 阶段 | 论文 4.5 | 第三章贯穿案例 |
|---|---|---|
| 配置来源 | BaCO | 当前为专家空间内的 seeded random；后续可替换为 BaCO |
| 参数域来源 | 固定 shape 的整数范围与 divisor 约束 | BLIS Fact/Contract/Rule 与 Task Context |
| 实例化 | 文本替换 Transform 模板 | 结构化参数生成 Transform 实例 |
| 编译链 | Transform -> LLVM IR -> clang | Transform -> LLVM IR -> clang AOT |
| 可行性 | `Valid` 表示构建可行 | `policy_legal`、Transform 与 compile 状态分开记录 |
| 正确性 | 原 evaluator 未验证 | 独立 `correctness_status` |
| 路径证据 | 未区分预测路径与实际替换 | `predicted_path`、`observed_path`、`microkernel_replaced` |
| 调优反馈 | runtime 与 `Valid` | 仅正确候选的 runtime/GFLOP/s，加结构化失败原因 |

对齐后的单条 provenance 链为：

```text
BLIS source
-> Fact -> Contract -> Expert Rule -> conditional candidate domain
-> {tile_m=24, tile_n=32, tile_k=64, vectorize=true}
-> Transform instance -> LLVM IR -> clang AOT
-> compile=pass -> correctness=pass
-> predicted_path=direct -> observed_path=fallback
-> microkernel_replaced=false -> tuner feedback
```

该链条保留论文 4.5 的 evaluator 形状，但把单一 `Valid` 扩展为第三章所需的
证据状态。因而 Contract 预测为 direct 不能等同于实际发生 library/microkernel
replacement；当前模板缺少 packing 和 BLIS adapter 时，正确结果仍应记为
fallback。

### 10.3 章节衔接与数据边界

- 第三章负责把源码证据归一化为 Fact、Contract、Rule，并产出锚点配置及其
  provenance。
- 第四章可把论文 4.5 的 BaCO 接口接到同一 evaluator，但搜索域必须由专家
  规则生成，不能复制 `search_settings.json` 中的固定 shape 范围。
- 第五章负责把配置实例化为 Transform，并记录 lowering、AOT、正确性与执行
  路径证据。
- 第六章可复用 best-so-far 曲线形式，但论文 4.5 的 1.68 倍加速只能作为相关
  工作结果，不能写成本文实验结果。
- 本次对齐不修改第三章的原始 CSV、shape 配置、锚点 JSON 和图 3-4 数据；后续
  接入 BaCO 或实现 BLIS adapter 时新增观测记录，不回填既有结果。

## 11. 建议的迁移顺序

1. 先复用 `search_settings.json` 的“整数参数 + 条件依赖”思想，不复制固定 shape 数值。
2. 将 `performance_exploration.py` 拆成 tuner adapter、Transform runner、compiler runner、correctness checker 和 measurement runner。
3. 用第三章 Fact/Contract/Rule 生成参数域和约束。
4. 先跑通 generic fallback，确认与现有 Chapter 3 AOT 路径一致。
5. 再增加 packing 和 BLIS direct/adapt 模板。
6. 只有在 LLVM IR 或最终符号中观察到 BLIS 调用后，才记录 replacement success。
7. 最后接入 BaCO；在 BaCO 未接入前，可用同一 evaluator 运行 seeded random search 验证接口。

## 12. 可直接用于论文的边界表述

> Luecke 等人在 Transform Dialect 的性能探索案例中，将 batch matrix
> multiplication 的 tile size 与 vectorization 决策暴露给 BaCO，并通过
> “参数实例化、Transform 执行、编译、运行和测量反馈”构成自动调优闭环。
> 该案例报告最终获得 1.68 倍加速，说明 Transform script 可以作为外部
> 调优器的显式调度接口。本文复用这一闭环结构，但不复用其固定参数空间：
> 本文的参数域、条件依赖和初始设计点由目标微内核 Contract 与专家规则生成，
> 并进一步区分编译可行性、数值正确性、Contract 预测路径和实际微内核替换结果。

引用该表述时使用论文 DOI `10.1145/3696443.3708922`，并将 1.68 倍结果明确归于论文第 4.5 节。不要把第 4.4 节的 0.017 s 或 20 倍以上 libxsmm 加速并入该段。

## 13. 当前文件检查结果

- `performance_exploration.py`：Python 语法通过。
- `search_settings.json`：JSON 解析通过。
- `run_all.sh`：Bash 语法通过。
- 当前目录缺少 3 个静态支持文件；`specialized_transform.mlir` 还需在运行时生成，因此当前目录不能独立复现实验。
- 当前文件适合提取架构与接口，不应未经修正直接用于正式性能数据。
