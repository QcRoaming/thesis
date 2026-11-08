#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
OUT=${1:-"$ROOT/board_results"}
ELF="$ROOT/build/k230_external/k230_openblas_contract_pool.elf"

mkdir -p "$OUT"
test -x "$ELF"

if command -v date >/dev/null 2>&1; then
  date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/run_timestamp_utc.txt" || true
fi
if command -v uname >/dev/null 2>&1; then
  uname -a > "$OUT/uname.txt" || true
fi
if test -r /proc/cpuinfo; then
  cat /proc/cpuinfo > "$OUT/cpuinfo.txt" || true
fi

: "${K230_REPS:=3}"
: "${K230_WARMUPS:=1}"
export K230_REPS K230_WARMUPS

"$ELF" > "$OUT/k230_openblas_contract_pool.csv" \
  2> "$OUT/k230_openblas_contract_pool.stderr.log"

if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "$ELF" "$OUT/k230_openblas_contract_pool.csv" \
    > "$OUT/sha256sums.txt"
fi

echo "K230 external validation complete: $OUT"
