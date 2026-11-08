# 面试讲解稿：一段 matmul 如何编译并运行

展示时使用 [面试展示版](thesis_architecture_present.png)，备讲时对照 [原完整编译链图](thesis_architecture.png)。两版均先沿中间的 **①→⑥** 讲程序如何变化，再指出 A/B/C/D 对应的论文研究。主例使用已贯通的 **BLIS f32、x86、6×16 微内核** 路径。

## 30 秒介绍

我的论文从一段 tensor 语义的 `linalg.matmul` 出发，研究怎样让 MLIR 生成能够正确调用专家库微内核的程序。我提取微内核的布局、边界和 ABI 条件，生成可搜索的调度候选；候选选定后，生成 packing、边界处理和外部调用，再沿 MLIR、LLVM 和原生链接得到可执行文件，实际运行并验证。我的工作主要落在调用条件建模、候选空间，以及编译器到微内核之间的适配层。

## 对照主图，约 3 分钟

**① 先看程序入口。** 输入是一段动态 shape 的 `linalg.matmul`，A、B、C 都是 tensor。它描述 `C_out = C_in + A × B`，还没有规定怎么分块、怎么摆放数据、调用哪个微内核。图上方的 A/B 是论文的前置研究：从固定版本源码提取 Fact，区分必须满足的 Contract 和只影响性能偏好的 Profile；结合任务的 shape、dtype 和目标 ISA，生成 direct、adapt、fallback 或 reject 诊断，并去掉不影响该路径生成代码的参数别名。

**候选如何控制编译？** BaCO 选择一个候选 token，我把它实例化成 Transform IR。它是一段控制编译变换的调度程序，指定分块参数和调用目标；图中向下的箭头表示它驱动下面的变换。下面横向流动的才是待执行的 matmul 程序。

**② 从 tensor 到 memref。** BLIS 路径先使用 MLIR 已有的 one-shot bufferization，把 tensor 语义改成 memref 语义。此时矩阵有了显式内存表示，核心计算仍然是 `linalg.matmul`。这一步复用 MLIR。

**③ 这是编译器实现的重点。** 我的 packing pass 消费这个 memref matmul，生成 SCF 分块循环、A/B panel 的分配和搬运，并生成主块与尾块的占位调用。以 6×16 微内核为例，完整块直接写 C；M/N 尾块先用临时 6×16 缓冲承接计算，再写回有效区域；K 尾块传入实际 K 长度。接着，自定义 `transform.buddy.call_microkernel` 把这些已准备好的占位调用绑定到 C++ wrapper。处理完后，程序变成循环、内存操作和外部调用，结果保存为 `transformed.mlir`。

**④ 继续走标准编译链。** 复用已有 lowering 把程序降到 MLIR 的 LLVM dialect，得到 `llvm.mlir`；再由 `mlir-translate` 导出真正的 LLVM IR，得到 `kernel.ll`。这两个文件属于不同的 IR 表示，前一个仍然是 MLIR。

**⑤⑥ 最后链接并运行。** `clang++ -O3` 编译 `kernel.ll`，同时链接本文的 C++ ABI adapter、`libblis.a` 和测试 driver，产生可执行文件。运行时 driver 传入矩阵，生成的循环完成 packing，再经 wrapper 调用 BLIS 原有的 `bli_sgemm_haswell_asm_6x16`，最后得到 C。微内核汇编本身是复用的；我的 adapter 负责把生成代码传来的地址、偏移和 stride 接到它的 ABI。

**最后指出 D：我怎样知道链路成立？** 我联合检查数值结果、IR 调用、链接符号和运行时 fringe 计数，再把性能交给调优器。部署评价还要对比完整 BLIS，并计入编译和调优成本。论文的核心价值是把“哪些候选能执行、怎样满足调用条件、实际走了哪条路径”串起来；当前结果不能支持普遍快于完整库的结论。

## 从最小输入看每一步的产物

下面是实际入口 `dynamic_payload()` 使用的 tensor 语义程序，函数名简化为 `matmul`。图中的主路径还会将它包在带 `buddy.payload` 属性的 module 内，供 Transform 定位。

```mlir
func.func @matmul(
    %A: tensor<?x?xf32>,
    %B: tensor<?x?xf32>,
    %C: tensor<?x?xf32>) -> tensor<?x?xf32>
    attributes {llvm.emit_c_interface} {
  %0 = linalg.matmul
    ins(%A, %B : tensor<?x?xf32>, tensor<?x?xf32>)
    outs(%C : tensor<?x?xf32>) -> tensor<?x?xf32>
  return %0 : tensor<?x?xf32>
}
```

`outs(%C)` 提供累加初值；C 初始化为零时才是通常写的 `C = A × B`。当前 driver 使用非零初始 C，验证的是 `C_out = C_in + A × B`。

| 阶段 | 程序或产物 | 论文插入的位置 |
| --- | --- | --- |
| ① 输入 | `input.mlir` 同时包含 tensor matmul payload 和独立的 Transform 调度 | A/B 形成可接纳候选；token 决定哪段调度被实例化 |
| ② bufferization | tensor 参数变为 memref，仍有 `linalg.matmul`；主流程不单独落盘此中间状态 | 复用 `transform.bufferization.one_shot_bufferize`，设置 identity layout 与函数边界 bufferization |
| ③ packing / fringe / 绑定 | `transformed.mlir`：`scf.for`、`scf.if`、`memref.alloc/load/store`、对 wrapper 的 `func.call` | C：本文 pass 生成面板与边界代码，自定义 Transform op 重定向占位调用 |
| ④ 标准 lowering 与导出 | `llvm.mlir` → `kernel.ll` | 复用 `--convert-linalg-to-loops --test-lower-to-llvm`，再用 `mlir-translate --mlir-to-llvmir` |
| ⑤ 原生编译与链接 | `kernel.ll` + adapter `.cpp` + `libblis.a` + driver `.cpp` → `benchmark` 可执行文件 | C 的 ABI adapter 在这里参与构建；编译器和 BLIS 库复用 |
| ⑥ CPU 执行 | driver → 生成的函数 → wrapper → BLIS 微内核；C 保存在输出内存，driver 输出正确性和性能记录 | D 核对结果、调用证据和成本；性能反馈给搜索器 |

Transform IR 的关键顺序如下；这是调度动作摘要，完整可执行版本见 `blis_schedule()`：

```text
one_shot_bufferize
  → apply_registered_pass "buddy-materialize-blis-packed-matmul"
      (tile-m / tile-n / tile-k / mr / nr)
  → 匹配 direct 与 fringe placeholder
  → transform.buddy.call_microkernel 绑定各自 wrapper
```

调用绑定完成后，`--buddy-finalize-transform-payload` 整理 payload，再执行 canonicalize/CSE。Transform 调度在编译阶段被解释执行；目标 CPU 执行的是生成的计算代码。

## 路径分支怎样讲

主图横向六步展开 **direct/adapt 的 BLIS 路径**。Direct 仍有 A/B packing；adapt 表示还要满足已支持的尾块等适配义务。MLIR 的动态边界分支在运行时选择完整块或尾块，候选的路径标签由任务和候选条件预测，再以运行证据核对。

Fallback 使用另一段调度，从 tensor matmul 开始，顺序为 **tensor tiling → 可选 vectorization → bufferization → 标准 lowering → 编译运行**。它绕开本文的 BLIS packing pass 和 BLIS wrapper。Reject 候选不进入后续编译。四类路径描述的是明确的判定与实现边界，并不意味着任何不受支持的输入都会自动得到可执行的 fallback。

BLIS f64 复用核心生成逻辑并采用对应的核参数和 adapter；OpenBLAS RVV 复用 Contract 语义与验证接口，保留包内生成与适配实现。主图的小注用于说明这一范围，讲解时不要把 RVV 说成通过图中的同一个 BLIS pass。

## 用一个尾块案例补充③

选择 M=190、N=250、K=250，候选 `tile_m=24`、`tile_n=32`、`tile_k=64`，微内核为 6×16：

1. Contract 给出 MR/NR、A/B panel 布局、边界和 ABI 条件。Checker 将此候选判为 adapt。
2. Pass 生成的 A 面板为 `[tile_m / 6, tile_k, 6]`，B 面板为 `[tile_n / 16, tile_k, 16]`。搬运时检查边界，无效位置补零。
3. 最末 M/N 微块只有 4 行、10 列有效。生成代码分配 6×16 临时 C，把有效的原 C 拷进去、其余清零，调用后只回写有效区域。这部分由 pass 生成的 SCF/memref 代码完成。
4. K 分为 64、64、64、58，最后一次调用传 `actualK=58`。Wrapper 使用 `alpha=1`、`beta=1`，保持各 K 块与初始 C 的累加语义。
5. 自定义 Transform op 负责把 direct/fringe placeholder 绑定到各自 wrapper。Fringe wrapper 记录调用次数，然后和 direct wrapper 一样调用真实 BLIS 微内核；临时 C 的构造和回写已在生成代码中。

这个例子可把 **调用条件 → 调度参数 → IR 改写 → 真实 ABI → 运行证据** 连成一句话。

## 常见追问

| 追问 | 建议回答 |
| --- | --- |
| Transform IR 是 matmul 的下一层 IR 吗？ | 它表达对 payload 的变换计划，通过 handle 定位并改写 payload。图中的横向链才是计算程序的表示变化，向下的调度箭头负责驱动②③。 |
| 你具体实现了什么？ | 研究 A/B 是可追溯的 Contract/Profile、候选分类与规范化；C 是 BLIS packing/fringe pass、自定义调用绑定 op 和 C++ ABI adapter；D 是数值、IR、符号、运行路径和完整成本的联合评价。Bufferization、标准 lowering、LLVM/Clang、BaCO 和微内核本身都复用。 |
| 为什么不直接调用完整 BLAS？ | 标准独立 GEMM 应当与完整库比较，实验中完整库常常更快。论文解决的是编译器消费外部微内核时，怎样表示调用条件、生成适配代码与可搜索空间。融合等潜在用途属于后续方向。 |
| Contract 和一组 if 有什么区别？ | 检查仍落实为条件判断；新增的是固定 Schema、源码与版本来源、判定阶段、reason code，以及传给生成器的适配义务。说明它如何同时服务候选生成、诊断、后端适配和验证，比只强调名称更有说服力。 |
| 调用绑定 op 能直接替换任意 matmul 或 func.call 吗？ | 它要求目标是本文预先生成的 direct/fringe placeholder，并对不匹配的 handle 报告失败。Packing、循环和边界代码由前面的 pass 生成，绑定 op 负责声明 wrapper 并重定向 callee。 |
| 怎样证明没有悄悄走 fallback？ | 同时检查 LLVM IR 的 wrapper 调用、二进制的真实微内核符号、正确性与预期 fringe 计数。集成报告中 direct/adapt/fallback 三种实际路径分别核对；仅看到链接符号不构成完整运行证据。 |
| 性能提升多少？ | 先说基线。36 个 workload 的静态候选从每个 2,600 个缩到平均 104.4 个；1,256 个既有实测 case 的预测与运行路径一致。i9/K230 精确形状相对完整库的几何性能比为 0.5448/0.6730，各自 0/10 胜出；同一 28 点冻结池也没有 BaCO 稳定优于随机搜索的证据。空间统计、路径核对和性能比较要分别解释。 |
| 图中的反馈是否每轮都重新编译实测？ | 集成 evaluator 可以完成真实编译与运行，并有 BaCO 六点 smoke 证明连接成立；正式固定预算评价的部分轨迹读取冻结实测语料，独立在线测量另有实验。讲图时应注明所指实验。 |

## 面试官要看代码时

先打开真实总入口 [run_integrated_pipeline.py](../../experiments/chapter4_5_integrated/scripts/run_integrated_pipeline.py)：`dynamic_payload()` → `blis_schedule()` / `fallback_schedule()` → `evaluate_candidate()`，即可沿图走完整条链。该入口直接调用真实 BLIS evaluator。

| 图中位置 | 源码入口 | 可展示的内容 |
| --- | --- | --- |
| A：调用知识 | [extract_blis_facts.py](../../experiments/chapter3_rules/scripts/extract_blis_facts.py) | 固定源码事实、来源记录和核验 |
| B：任务与候选 | [chapter4lib.py](../../experiments/chapter4_space/scripts/chapter4lib.py) | Task、Contract、candidate 与路径判定 |
| B：参数规范化证据 | [run_all.py](../../experiments/chapter6_contract_space_validation/scripts/run_all.py)、[run_normalized_baco_replay.py](../../experiments/chapter6_contract_space_validation/scripts/run_normalized_baco_replay.py) | 路径上的参数活性、规范化签名和冻结池去重；这些脚本含评价流程，讲解时只读代码 |
| ①②及调度 | [run_integrated_pipeline.py](../../experiments/chapter4_5_integrated/scripts/run_integrated_pipeline.py) | tensor 输入、BLIS/fallback 两种调度、Transform interpreter、lowering、链接与运行 |
| ③：packing 与 fringe | [MatMulBlisMicrokernel.cpp](../../compiler_snapshot/buddy-mlir/midend/lib/Conversion/MatMulOptimization/MatMulBlisMicrokernel.cpp) | panel 布局、SCF 循环、动态边界、临时 C、占位调用 |
| ③：绑定 wrapper | [TransformOps.cpp](../../compiler_snapshot/buddy-mlir/midend/lib/Dialect/Microkernel/TransformOps.cpp) | handle 校验、失败传播、callee 重定向 |
| ⑤⑥：ABI adapter | [blis_microkernel_adapter.cpp](../../experiments/chapter5_blis_adapter/runtime/blis_microkernel_adapter.cpp) | 地址、offset、stride、alpha/beta 和真实 BLIS 符号 |
| ⑥：驱动与验证 | [dynamic_matmul_bench.cpp](../../experiments/chapter5_blis_adapter/runtime/dynamic_matmul_bench.cpp) | MemRef descriptor、输入初始化、reference、计时与 fringe 计数 |
| D：贯通证据 | [integrated_results.md](../../experiments/chapter4_5_integrated/reports/integrated_results.md) | direct/adapt/fallback、BLIS replacement 与 BaCO smoke 的结论边界 |

面对 AI 编译器岗位，沿图优先展开 **IR 改写、内存布局、动态边界、外部 ABI、调优接口和性能验证**；第一次讲解可以略过结果数字，把时间留给③与⑤⑥。
