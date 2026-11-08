# i9-14900 跨主机实验结果

i9-14900 目标机实验已完成。本目录保留结果与理解结果所需的版本信息：

- `data/experiment_config.json`：目标环境与固定版本；
- `results/`：目标机返回的压缩归档及 SHA-256；
- `imported/`：导入后的原始测量、处理结果、报告及 provenance；
- `processed/`：导入审计与跨主机汇总；
- `reports/`：论文使用的结论与边界；
- `x86_cross_host_artifact_index.md`：结果入口。

已删除离线部署包、打包缓存、运行脚本和目标机操作指南。因此，此目录用于检查已完成的实验结果，不提供再次部署或重新测量的环境。验证返回归档时在 `results/` 中运行 `sha256sum -c *.sha256`。
