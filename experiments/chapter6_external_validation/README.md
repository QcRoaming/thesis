# Chapter 6 external validation

本目录补齐优秀硕士论文所需的跨主机、跨库和跨 ISA 验证，且不改写已经得到的
负面结论。实验协议在外部测量前冻结，目标是回答三个独立问题：

1. 在稀疏校准预算下，Expert+Data 是否稳定优于 Data-only；
2. 生成调度在真实 Transformer GEMM shape 上相对完整 BLIS/OpenBLAS 的性能边界；
3. 接入 OpenBLAS RVV microkernel 时，是否只需新增 Contract、候选数据、adapter
   和部署代码，而无需改写核心空间生成算法。

## 冻结协议

- 10 个 Qwen2.5-0.5B 结构启发的 f32 GEMM shape，含 decode、prefill 和 fringe；
- i9：BLIS Haswell 6x16 Contract，28 个 workload-specific 公共池候选；
- K230：OpenBLAS `RISCV64_ZVL128B` 8x8 Contract，16 个冻结候选；
- 完整库对照：单线程 BLIS SGEMM 与单线程 OpenBLAS `cblas_sgemm`；
- 正确性投影在计时区外；搜索、编译、packing、kernel 与 scatter 成本分开保存；
- Data-only 和 Expert+Data 使用同一公共池、同一预算和同一 holdout；
- M=8 下由 Contract/extent 导致唯一合法 `tile_m=6`，正式输出标记为
  `conditionally_eliminated`，不把它伪装为活跃搜索维度。

完整参数见 [experiment_config.json](data/experiment_config.json)。

## 结果与保留的部署包

结果归档路径、SHA-256 和 K230 包命令见
[EXTERNAL_VALIDATION_ARTIFACT_INDEX.md](EXTERNAL_VALIDATION_ARTIFACT_INDEX.md)。

i9 实验已完成，正式返回归档与已导入的 `raw/`、`processed/`、`reports/`
仍保留，部署包、目标机脚本和编译产物已清理。K230 包携带已静态链接的
RT-Smart ELF，板端无需联网和编译。

## 本机验证

```bash
python3 scripts/build_external_packages.py
python3 -m unittest discover -s tests -v
python3 ../chapter4_space/tests/test_chapter4.py
```

`build_external_packages.py` 现在只生成 K230 包。i9 的导入校验脚本仍用于
验证已经保存的返回结果，不生成新的目标机部署包。

当前已经完成主机侧 MLIR/BLIS smoke、稀疏回放 full run、K230 host-stub
packing/fringe 验证、RV64GCV 静态 ELF 审计、返回归档校验，以及独立的
3-case/45-row K230 MLIR wrapper 闭环。K230 的 10-shape、133-candidate
external pool 也已在物理板上完成 429/429 条正确测量并通过严格导入；生成
adapter 相对完整 OpenBLAS 的 workload 几何性能为 0.6730，95% CI
[0.6193, 0.7253]，因此结果支持独立后端接入与合法执行，不支持超越完整库的
性能主张。外部 i9 Transformer-shape 测量也已完成，结果见
`processed/i9_external_summary.json` 和 `reports/i9_external_results.md`。
