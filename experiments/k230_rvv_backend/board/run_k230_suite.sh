#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
OUT=${1:-"$ROOT/board_results"}
mkdir -p "$OUT"

date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/run_timestamp_utc.txt"
uname -a > "$OUT/uname.txt"
cat /proc/cpuinfo > "$OUT/cpuinfo.txt"
: "${K230_REPS:=5}"
: "${K230_WARMUPS:=1}"
export K230_REPS K230_WARMUPS

for elf in k230_gemm_scalar k230_gemm_rvv k230_gemm_openblas; do
  "$ROOT/build/elf/$elf.elf" > "$OUT/$elf.csv" 2> "$OUT/$elf.stderr.log"
done

sha256sum "$ROOT"/build/elf/*.elf "$OUT"/*.csv > "$OUT/sha256sums.txt"
echo "K230 board suite complete: $OUT"
