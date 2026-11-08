# 手动转移到 WSL

此目录是当前容器 `/buddy-mlir/jlq/thesis` 的轻量工作副本，已按正文、实验、源码快照、文档、文献和依赖分类。目标位置为 WSL 的 `/home/jlq/project/thesis`。此处的文件尚未转移到 WSL。

为缩小传输量，本副本排除了：

- `third_party/k230_sdk/`（约 5.6 GiB）；
- 全部 TIFF 导出图（39 个，约 430 MiB）。

原容器的 `/buddy-mlir/jlq/thesis` 仍保留这些内容。TIFF 可由对应绘图脚本生成；运行图像 QA 前需要恢复它们。K230 开发或重新构建 SDK 时需要另行复制 SDK。LLVM/MLIR 构建和 Python 虚拟环境也未包含在本目录中。

i9 实验只保留已校验的返回归档、导入后的结果、汇总报告和版本配置；离线部署与再运行资产已清理。K230 实验保留当前板上结果、汇总报告和来源记录；轻量副本不含 K230 SDK。迁移后，部分旧实验脚本仍须修改原 `/buddy-mlir` 路径才能再次运行。

论文 PDF 构建与结果校验的完整步骤见 [`BUILD_AND_CHECK.md`](BUILD_AND_CHECK.md)。在迁移后的论文根目录运行 `make pdf` 编译 PDF，运行 `make check` 核对已保存的 i9/K230 结果、证据文件及源码快照；这两项都不需要重新构建 LLVM 或连接目标设备。

复制到 WSL 后可做基本检查：

```bash
test -f /home/jlq/project/thesis/nwputhesis/build/graduate.pdf
cd /home/jlq/project/thesis/compiler_snapshot && sha256sum -c SHA256SUMS.txt
cd /home/jlq/project/thesis/experiments/x86_cross_host/results && sha256sum -c thesis-x86-result--20260716T115026Z.tar.gz.sha256
cd /home/jlq/project/thesis/experiments/chapter6_external_validation/returned/i9 && sha256sum -c chapter6-i9-result-20260722T085806Z.tar.gz.sha256
cd /home/jlq/project/thesis && make check
```
