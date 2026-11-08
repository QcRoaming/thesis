# K230 OpenBLAS 外部后端验证包

本包验证的是第二个库和第二种 ISA：K230 C908（RV64GCV）上的 OpenBLAS
`RISCV64_ZVL128B` SGEMM。ELF 已静态链接，不要求板端联网或安装编译工具。

## 实验内容

- 使用冻结的 10 个 Transformer GEMM shape；
- 使用同一 Chapter 4 空间生成器读取 OpenBLAS 8x8 Contract；
- adapter 显式执行 A/B packing，并直接调用 OpenBLAS 内部 `sgemm_kernel`；
- 支持非整除 M/N/K，记录 direct/adapt、kernel/fringe 调用数；
- 与完整单线程 `cblas_sgemm` 在同一 ELF、同一输入和同一计时方法下比较；
- 输出 packing、microkernel、scatter 和总耗时。

## 部署到 SD 卡

在 Windows 中解压归档，并将整个目录放到 CanMV SD 卡根目录：

```text
CanMV\sdcard\chapter6-k230-openblas-external-validation
```

RT-Smart 中对应路径必须是：

```text
/sdcard/chapter6-k230-openblas-external-validation
```

## 串口运行（推荐）

从工作站当前源码目录执行：

```bash
python3 scripts/run_k230_external_via_serial.py \
  --port /dev/ttyACM1 \
  --board-root /sdcard/chapter6-k230-openblas-external-validation \
  --output-dir board_results
```

运行器按冻结协议要求得到 429 行：399 行 Contract adapter 候选结果和
30 行完整 OpenBLAS 基线结果。它会逐一核对 10 个 workload、133 个可执行候选、
trial、shape、tile、direct/adapt 路径和 correctness；缺行或协议不匹配会直接失败。
默认超时为 4 小时，运行过程中每 30 秒报告一次已捕获字节数和结果行数。

可先探测目录：

```bash
python3 scripts/run_k230_external_via_serial.py \
  --port /dev/ttyACM1 \
  --output-dir board_results \
  --probe-storage
```

## 板端手动运行

解压后进入包目录：

```sh
chmod +x build/k230_external/k230_openblas_contract_pool.elf
chmod +x board/run_k230_external_validation.sh
K230_REPS=3 K230_WARMUPS=1 sh board/run_k230_external_validation.sh
```

若 RT-Smart 环境不能执行脚本或设置环境变量，可直接运行静态 ELF。ELF 默认已经
固定为 `K230_REPS=3` 和 `K230_WARMUPS=1`：

```sh
./build/k230_external/k230_openblas_contract_pool.elf
```

将整个 `board_results` 目录复制回工作站。导入命令：

```bash
python3 scripts/import_k230_external_results.py /path/to/board_results
```

## 判读边界

本实验是单线程 f32 GEMM、微内核包可扩展性与机制开销证据，不代表完整模型
端到端时延。`openblas_full` 是完整 OpenBLAS SGEMM 对照；
`contract_adapter` 是空间生成参数驱动的显式 packing + microkernel 路径。
