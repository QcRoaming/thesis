# 迁移后的构建与检验

目标目录：`/home/jlq/project/thesis`。本目录是论文正文、实验记录和编译器源码快照的归档，不是可独立构建整个 Buddy-MLIR 的仓库。K230 与 i9 的实验以现有结果为准；下面的检查不会连接设备、编译 LLVM 或重跑性能测试。

## 1. 解包并核对传输文件

将 `thesis-transfer.tar.gz` 和 `thesis-transfer.tar.gz.sha256` 手动复制到 WSL 的 `/home/jlq/project/`，然后执行：

```bash
cd /home/jlq/project
sha256sum -c thesis-transfer.tar.gz.sha256
tar -xzf thesis-transfer.tar.gz
cd thesis
```

如果直接复制 `thesis-transfer/` 目录，应将其改名为 `thesis/`，再进入该目录。

## 2. 检查已保存的结果

```bash
cd /home/jlq/project/thesis
make check
```

该命令仅需 `python3` 和 `make`，会检查现有 PDF 文件头、论文证据清单中 125 个路径、编译器源码快照 SHA-256、两份 i9 返回归档、三组 K230 原始结果 SHA-256，以及五份汇总 JSON 的状态。输出 `PASS` 才表示迁移文件齐全且这些哈希与归档一致；它不证明新机器上重跑的数值相同。

部分实验 JSON 保存的是采集时的 `/buddy-mlir/jlq/thesis` 绝对路径。这些字段是历史来源记录，移动后不会自动更新；`make check` 以当前目录中的相对文件和哈希进行校验。

## 3. 构建论文 PDF

WSL 需先有 `latexmk`、`xelatex`、`biber` 及模板使用的 TeX Live 宏包；模板自带字体位于 `nwputhesis/fonts/`。可先检查：

```bash
command -v latexmk xelatex biber
cd /home/jlq/project/thesis
make pdf
test -s nwputhesis/build/graduate.pdf
make check
```

`make pdf` 在 `nwputhesis/` 运行 `latexmk graduate.tex`，使用该目录的 `.latexmkrc` 调用 XeLaTeX 和 Biber，输出 `nwputhesis/build/graduate.pdf`。该配置启用了 `-shell-escape`。若缺少 TeX 宏包或字体，应先补齐本机 TeX Live 环境，再重新运行 `make pdf`。

`graduate.pdf` 默认是无空白隔页的阅读版，各章节仍另起一页，目录和页码随编译更新。学校 2025 版指南第 3.5 节要求正文各部分从奇数页开始；双面印刷时运行 `make pdf-print`，使用保留模板奇数页起排的 `nwputhesis/build/graduate-print.pdf`。该版会有排版所需的空白隔页。

## 4. 源码与实验的边界

`compiler_snapshot/` 保存论文使用的 `midend` 和 `buddy-opt` 源码以及哈希清单，供审阅和未来移植。这里没有完整的 Buddy-MLIR/LLVM 构建树；构建论文 PDF 或检查既有结果均不依赖它。若以后需要重编译编译器或复现实验，需另行准备匹配版本的 Buddy-MLIR、LLVM/MLIR、K230 SDK、设备与旧脚本路径。轻量包省略了 K230 SDK 和 TIFF 导出图，因此不支持直接重跑 K230 实验或 TIFF 图像 QA。
