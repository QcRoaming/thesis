# Buddy-MLIR 编译器源码快照

`buddy-mlir/midend/` 和 `buddy-mlir/tools/buddy-opt/` 从当前 `/buddy-mlir` 工作区复制，包含论文使用的 Microkernel Dialect、BLIS microkernel 转换及其本地未提交修改。基准提交记录在 `BUDDY_MLIR_BASE_REVISION.txt`。

此目录用于保存与论文实验对应的源码，不是独立的 Buddy-MLIR 构建。复现实验仍需匹配版本的 Buddy-MLIR 主仓库和外部 LLVM/MLIR 安装。

复制后的完整性可在本目录执行：

```bash
sha256sum -c SHA256SUMS.txt
```

