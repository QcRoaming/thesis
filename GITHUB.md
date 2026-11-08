# GitHub 归档

仓库：<https://github.com/QcRoaming/thesis>，首次上传日期：2026-11-08，默认分支：`main`。仓库设为私有。

## 克隆和校验

使用已登录对应 GitHub 账号的 GitHub CLI：

```bash
gh repo clone QcRoaming/thesis
cd thesis
make check
```

论文阅读版为 [`nwputhesis/build/graduate.pdf`](nwputhesis/build/graduate.pdf)，双面印刷版为 [`nwputhesis/build/graduate-print.pdf`](nwputhesis/build/graduate-print.pdf)。构建说明见 [`BUILD_AND_CHECK.md`](BUILD_AND_CHECK.md)。

## 归档范围

- 包含论文正文、字体、两份最终 PDF、文档、文献、编译器源码快照、实验脚本、原始记录、结果归档及校验文件。
- `experiments/` 中的日志也是实验记录；不使用全局 `*.log` 规则排除。
- `.gitattributes` 禁用自动换行转换，保持源码快照和实验文件的原始字节，避免跨平台克隆改变哈希。
- 排除编辑器本地设置、Python 缓存、LaTeX 中间文件，以及依赖仓库自身忽略的可重建产物。论文最终 PDF 和校验引用的证据文件明确保留。
- 嵌套仓库以当前工作目录的实际文件快照纳入本仓库，包含本地修改；不上传各自的 `.git` 历史，也不依赖 Git 子模块下载。原本地嵌套仓库的 Git 元数据保留原位。
- 迁移副本原本省略的 K230 SDK、TIFF、LLVM/MLIR 构建及 Python 环境仍需另备，详见 [`TRANSFER_NOTES.md`](TRANSFER_NOTES.md)。克隆后可检查已保存的实验结果；重新运行硬件实验仍需匹配的环境和路径配置。

## 嵌套源码基线

以下是首次上传时本地仓库可读的 HEAD。归档文件包含本地修改，不能仅凭上游提交复原。

| 目录 | 上游 | 本地 HEAD |
| --- | --- | --- |
| `nwputhesis/` | <https://github.com/1195343015/nwputhesis> | `8a8481f8b998f8c497298877ebc018d8635ebfb9` |
| `nwputhesis/fonts/` | <https://github.com/1195343015/nwputhesis-fonts> | `669b397d7e410871c88a4826df4598a749a5c1b9` |
| `latex-template-for-npu-thesis-2025/` | <https://gitee.com/tmrnic/latex-template-for-npu-thesis-2025> | `53bf7452db80303c53b00cf7d9cb1c314e162718` |
| `third_party/OpenBLAS/` | <https://github.com/OpenMathLib/OpenBLAS> | `b338322e9afc063d95e2c117e85bedf28213295a` |
| `third_party/baco/` | <https://github.com/baco-authors/baco> | `167b19699ead224b661da4abad560306f677e215` |
| `blis/blis/` | <https://github.com/flame/blis> | `36df51a81cc732eeadbf2e6732941dd5400db47d` |

`third_party/OpenBLAS-k230/` 的迁移副本含不可解析的 `.git` 指针，无法从该副本读取 HEAD；其当前源码同样作为普通文件快照保留。各依赖的许可证与版权声明随源码保留。
