# Translation and extraction notes

## 状态

- 模式：完整读本（非草稿）
- 输入类型：pdf-text
- 论文页数：21
- 正文覆盖：第 1–18 页全部可提取正文
- 参考文献覆盖：第 18–21 页，共 [1]–[58]
- 图：10 幅，全部提取并在 paper.md 中建立图卡
- 表：原文无表格
- OCR：未使用；全部页面均有可用文本层
- 缺页／跳过正文／未翻译正文：无

## 提取方法

使用 PDF 文本层直接提取，并按页面核对阅读顺序。原 PDF 为单栏排版；行末断词已重新连接，段落和章节顺序保持不变。图 1–10 多为矢量图或代码排版，不能通过内嵌位图完整提取，因此按页面坐标以 192 dpi 渲染后紧裁剪。所有裁剪均逐图目视复核，图注作为独立双语文本保留。

独立 pdf skill 在本次环境中不可用，因此依据 nature-reader 的 pdf-text 规则，使用本机 Poppler 工具完成文本与页面渲染；未改变源 PDF。

## 图像裁剪与放置

坐标为 PDF 页面坐标近似值 [x0, y0, x1, y1]，单位为 point；图卡使用经目视核验的紧裁剪。

| Figure | PDF page | BBox | Asset | Placed after |
|---|---:|---|---|---|
| F001 | 2 | [165.0, 532.5, 450.0, 639.0] | assets/fig01_tensorflow_stack.png | S009 |
| F002 | 3 | [162.75, 112.5, 451.5, 246.0] | assets/fig02_language_pipelines.png | S010 |
| F003 | 5 | [142.5, 78.0, 467.25, 240.0] | assets/fig03_operation_regions.png | S024 |
| F004 | 6 | [144.75, 70.5, 466.5, 357.75] | assets/fig04_polynomial_generic_ir.png | S028 |
| F005 | 9 | [147.75, 76.5, 468.0, 290.25] | assets/fig05_ods_definition.png | S052 |
| F006 | 10 | [147.75, 76.5, 468.0, 264.0] | assets/fig06_drr_pattern.png | S056 |
| F007 | 12 | [151.5, 75.75, 468.75, 217.5] | assets/fig07_tensorflow_ssa.png | S068 |
| F008 | 13 | [145.5, 73.5, 467.25, 234.0] | assets/fig08_affine_polynomial.png | S074 |
| F009 | 13 | [165.0, 591.0, 458.25, 703.5] | assets/fig09_fir_dispatch.png | S079 |
| F010 | 15 | [142.5, 468.75, 469.5, 562.5] | assets/fig10_inliner_interface.png | S093 |

## 翻译规则

- 保留 MLIR、LLVM、SSA、CFG、DAG、ODS、DRR、FIR、HPC 等标准缩写。
- Op、Pass、dialect 等高频术语按 paper.md 的术语表统一。
- lowering 译为“降低”，指从高层抽象转换到低层抽象，不译为性能意义上的“下降”。
- normalization 译为“归一化”，canonicalization 译为“规范化”，避免混同。
- 保留公式、标识符、Op 名称、类型名、数值、引用编号和程序语法。
- 参考文献题名不翻译，以保持检索准确性。

## 原文中的术语与排印问题

- ODS 在正文中出现 “Operation Descriptions”，图 5 又写作 “Operation Definition Syntax”；本读本统一以“操作定义规范（ODS）”指称机制，但原文栏保留各处写法。
- p.17 把 DRR 写成 “DDR”；译文按上下文标为“DRR（原文此处作 DDR）”。
- 原文栏保留作者版本中的明显语法或拼写问题，例如 p.4 的 “whith”、p.7 的 “This is a important”、p.11 的 “higher changes”、p.14 的 “MLIR begin” 和 “passes can uses”。译文按合理语义翻译，不复制这些错误。
- PDF 参考文献 [47] 原样含有 “=https://...”。

## 置信度

- 正文提取与章节顺序：high
- 公式、代码和标识符：high；代码同时保留在图像资产中
- 图像裁剪：high，全部经页面渲染目视复核
- 翻译：high；领域术语已通过统一术语表锁定
