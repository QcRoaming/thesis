# 论文迁移前清理记录

日期：2026-10-03。

## 已删除

- `experiments/x86_cross_host/dist/`：i9 离线部署包、校验文件及早期小包，删除前约 469 MiB。主归档在删除前通过 SHA-256 校验。
- `experiments/x86_cross_host/build/`：离线打包暂存与下载缓存，删除前约 986 MiB。
- `experiments/cgo_extension/build/binaries/`：可重建的编译程序、IR、逐例日志及 manifest，删除前约 370 MiB。
- `experiments/chapter6_evaluation/build/binaries/`：同类编译产物，删除前约 402 MiB。
- `experiments/x86_cross_host/results/thesis-x86-result--20260716T115026Z/`：与 `imported/` 对应目录逐文件比较一致的重复解包结果，约 77 MiB。返回结果归档及 `imported/` 保留。
- `experiments/x86_cross_host/` 内的部署、打包和再运行脚本、测试及目标机操作指南：i9 实验已完成，此目录现仅保留结果及解释结果所需的版本配置。
- `experiments/chapter6_external_validation/raw/i9_external/i9_14900_20260722T085806Z/build/`：约 130 MiB 的已编译程序；正式返回归档的哈希核对一致，归档中包含该目录。
- `experiments/chapter6_external_validation/` 的 i9 专用部署包、打包脚本、目标机脚本与旧操作说明；共享的结果校验脚本和应用验证仍需的分析代码保留。

这些删除使历史编译程序及其逐例 manifest 无法直接复验；论文使用的 `raw/`、`processed/`、`reports/`、`provenance/` 和最终 PDF 仍保留。两份 i9 结果归档及其校验文件已保留；离线部署包和 x86 专用重建脚本不再包含在整理后的目录中。

## 归类

- 顶层研究叙事、评审文件、写作指南和中期报告已归入 `documents/`。
- 顶层 Transform Dialect PDF 已归入 `论文阅读清单/`。
- 外部 Buddy-MLIR 的 `midend` 与 `buddy-opt` 源码已复制到 `compiler_snapshot/`；原仓库未改动。

K230 SDK、论文正式图表、被证据目录引用的原始数据和六个嵌套 Git 仓库仍在原位。整理后的原目录为 `/buddy-mlir/jlq/thesis`；便于用户手动转移的轻量副本为 `/buddy-mlir/thesis-transfer`，该副本排除了 K230 SDK 和 TIFF。
