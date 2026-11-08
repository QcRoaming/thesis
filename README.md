# 论文项目目录

GitHub 私有仓库：<https://github.com/QcRoaming/thesis>。克隆、归档范围及依赖版本见 [`GITHUB.md`](GITHUB.md)。

本目录集中存放论文正文、实验、源码依赖、文献与过程文档。迁往 WSL 时以整个目录为单位复制，保留内部相对路径。

| 分类 | 目录 | 内容 |
| --- | --- | --- |
| 正文 | `nwputhesis/` | LaTeX 正文、图、字体与 `build/graduate.pdf` |
| 实验 | `experiments/` | 脚本、原始记录、处理结果、报告与证据目录；从 `FINAL_EXPERIMENT_AUDIT.md` 开始阅读 |
| 编译器源码快照 | `compiler_snapshot/` | 本地 Buddy-MLIR 的 `midend` 和 `buddy-opt` 源码及校验清单 |
| BLIS 与第三方依赖 | `blis/`、`third_party/` | BLIS、OpenBLAS、BaCO、K230 SDK 等；LLVM 构建不在本目录 |
| 文档 | `documents/` | 研究叙事、评审与修订、写作规范、中期报告 |
| 文献 | `论文阅读清单/` | 阅读材料及 Transform Dialect 论文 |
| 模板参考 | `latex-template-for-npu-thesis-2025/` | 学校 LaTeX 模板参考 |

清理记录见 `CLEANUP_LOG.md`。`experiments/x86_cross_host/` 现在仅存 i9 结果、解释报告和版本配置；离线部署包与再运行脚本已删除。其他实验脚本仍按原始 `/buddy-mlir/jlq/thesis` 层级寻找 Buddy-MLIR、LLVM 与 Python 环境；换目录后复现实验需要重配路径。

当前容器中另有轻量转移副本 `/buddy-mlir/thesis-transfer`。该副本省略 K230 SDK 和 TIFF 导出图，具体边界见其中的 `TRANSFER_NOTES.md`。
