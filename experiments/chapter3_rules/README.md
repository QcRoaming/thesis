# 第3章成果包：高性能库知识的证据化建模与微内核契约

本目录对应《毕业论文导向_论文结构最终版》第3章的自动化成果。它包含真实
BLIS 源码事实、两个目标微内核 Contract、五类 Expert Rule、核验与歧义记录、
8 个 shape 的真实 MLIR Transform/AOT 预备实验，以及由 R 生成的图3-1至图3-4
和表3-1至表3-3。正文还结合多来源、f64 Contract 和正式路径语料解释
硬兼容性知识与可校准软性能知识的边界。

## 一键复现

绘图环境固定为 R 4.3.3，依赖版本记录在 `environment-r.yml`。当前工作区采用
用户级 Conda 前缀 `/home/jlq/.local/share/conda-envs/thesis-r`，并通过
`/home/jlq/.local/bin/Rscript` 暴露命令，不需要管理员权限。重新创建环境可执行：

```bash
conda env create \
  --prefix /home/jlq/.local/share/conda-envs/thesis-r \
  --file jlq/thesis/experiments/chapter3_rules/environment-r.yml
```

```bash
python3 jlq/thesis/experiments/chapter3_rules/scripts/run_chapter3.py
```

图件统一使用 PATH 中的 `Rscript`、ggplot2、patchwork、svglite 和 ragg 生成，
不使用 Python 绘图库。绘图入口为：

```bash
Rscript jlq/thesis/experiments/chapter3_rules/scripts/plot_chapter3_figures.R
```

默认会复用 `build/` 中按候选保存的编译与测量缓存。重新执行全部测量：

```bash
python3 jlq/thesis/experiments/chapter3_rules/scripts/run_chapter3.py \
  --force-measurements
```

仅重新生成知识库、报告和图表：

```bash
python3 jlq/thesis/experiments/chapter3_rules/scripts/run_chapter3.py \
  --skip-measurements
```

论文编译环境固定为 TinyTeX v2026.05，安装前缀为
`/home/jlq/.local/share/TinyTeX`。`xelatex`、`latexmk`、`biber` 和 `tlmgr`
均已通过 `/home/jlq/.local/bin` 暴露到 PATH。这里的 R 包 `tinytex` 是 R
侧管理接口，TinyTeX 发行版和论文所需 TeX 宏包已经单独安装完成。

## 第3章必需成果对应关系

| 论文要求 | 目录成果 |
|---|---|
| 范围与固定版本 | `research-scope.md` |
| Fact Extractor | `scripts/extract_blis_facts.py` |
| Facts JSON/CSV | `data/facts.json`, `data/facts.csv` |
| Fact Schema | `schemas/fact.schema.json` |
| 两个真实 Contract | `data/microkernel_contracts.yaml` |
| Contract Validator | `scripts/validate_artifacts.py` |
| 五类真实 Rule | `data/expert_rules.yaml` |
| Rule Schema | `schemas/rule.schema.json` |
| 核验集与字段覆盖率 | `verification/` |
| 歧义与冲突记录 | `data/ambiguities.csv`, `data/conflicts.csv` |
| 贯穿 provenance | `provenance/`, `reports/provenance_case.md` |
| 真实预备实验 | `raw/preliminary_aot.csv`, `processed/`, `reports/preliminary_experiment.md` |
| 图3-1至图3-4 | `figures/`、`scripts/plot_chapter3_figures.R` |
| 表3-1至表3-3 | `tables/` |

完整状态见 `chapter3_artifact_index.md`。

## 真实预备实验路径

```text
linalg.matmul
→ Transform Dialect 参数实例化
→ transform-interpreter
→ bufferization / linalg-to-loops
→ LLVM dialect
→ LLVM IR
→ clang++ AOT
→ 数值正确性检查与性能测量
```

冻结预备实验所用的 Transform 模板只实现 tiling 与可选 vectorization，当时尚未
实现 BLIS packing 和 microkernel replacement。因此，冻结记录中的
`microkernel_replaced=false` 与 fallback 是实际观测的历史系统边界，不是模拟数据。
后续集成已经补齐 packing 与调用适配器；完整专家空间评估属于第5章。

## 人工核验边界

16 条核验记录已经通过机器一致性与源码定位检查，并由论文作者于
2026-07-15 明确签核，`human_status` 均为 `verified`。签字依据独立保存在
`verification/human_signoffs.json`，机器检查与人工签核仍作为两个字段报告。

## 旧 C++ MVP

`scripts/run_mvp.py` 和 `output/` 保留早期 C++ tiled-proxy 闭环，仅用于开发回归。
论文第3章的预备实证应引用 `raw/preliminary_aot.csv`，不能引用 proxy score。
