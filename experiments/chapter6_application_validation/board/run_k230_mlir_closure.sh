#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
OUT="$ROOT/board_results"
mkdir -p "$OUT"

: "${K230_MLIR_REPS:=5}"
: "${K230_MLIR_WARMUPS:=1}"
export K230_MLIR_REPS K230_MLIR_WARMUPS

ELF="$ROOT/build/k230_mlir_closure/k230_mlir_closure.elf"
if test ! -x "$ELF"; then
  chmod +x "$ELF"
fi

"$ELF" > "$OUT/k230_mlir_closure.csv" \
  2> "$OUT/k230_mlir_closure.stderr.log"

echo "K230 MLIR closure complete: $OUT"
