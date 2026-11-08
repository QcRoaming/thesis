# K230 MLIR closure deployment

本包是主 K230 外部验证之后的独立确认实验。它不替换主候选池结果，只验证三个预声明案例的 MLIR/Transform 到真实 OpenBLAS adapter 闭环。

```sh
tar -xzf chapter6-k230-mlir-closure-validation.tar.gz
cd chapter6-k230-mlir-closure-validation
chmod +x board/run_k230_mlir_closure.sh
K230_MLIR_REPS=5 K230_MLIR_WARMUPS=1 sh board/run_k230_mlir_closure.sh
```

返回完整 `board_results` 目录。若不能执行脚本，可直接运行：

```sh
K230_MLIR_REPS=5 K230_MLIR_WARMUPS=1 \
  ./build/k230_mlir_closure/k230_mlir_closure.elf \
  > k230_mlir_closure.csv \
  2> k230_mlir_closure.stderr.log
```

板端无需联网或编译工具。

通过 RT-Smart 串口自动执行并在开发机保存原始日志：

```sh
python3 scripts/run_k230_mlir_via_serial.py \
  --port /dev/ttyACM1 \
  --board-root /sdcard/chapter6-k230-mlir-closure-validation \
  --output-dir board_results
```

串口驱动固定检查 45 行结果、三种 variant、三个预声明案例、correctness
以及 direct/adapt 路径匹配。当前实测 CanMV 固件将 Windows 可见的
`CanMV\sdcard` 映射为 RT-Smart `/sdcard`；`board-root` 必须指向该目录下
已经解压的包。其他固件若显式挂载了 `/sharefs`，可覆盖此参数。
