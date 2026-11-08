#!/usr/bin/env python3
import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a static f32 linalg.matmul and optional Transform schedule."
    )
    parser.add_argument("--m", type=int, required=True)
    parser.add_argument("--k", type=int, required=True)
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tile-m", type=int, default=0)
    parser.add_argument("--tile-n", type=int, default=0)
    parser.add_argument("--tile-k", type=int, default=0)
    args = parser.parse_args()

    if min(args.m, args.k, args.n) <= 0:
        parser.error("matrix dimensions must be positive")
    tiles = (args.tile_m, args.tile_n, args.tile_k)
    if any(tile < 0 for tile in tiles):
        parser.error("tile sizes cannot be negative")
    if any(tiles) and not all(tiles):
        parser.error("tile-m, tile-n, and tile-k must be set together")
    return args


def payload(args: argparse.Namespace) -> str:
    return f"""func.func @{args.symbol}(
    %A: tensor<{args.m}x{args.k}xf32>,
    %B: tensor<{args.k}x{args.n}xf32>,
    %C: tensor<{args.m}x{args.n}xf32>) -> tensor<{args.m}x{args.n}xf32>
    attributes {{llvm.emit_c_interface}} {{
  %0 = linalg.matmul
    ins(%A, %B : tensor<{args.m}x{args.k}xf32>, tensor<{args.k}x{args.n}xf32>)
    outs(%C : tensor<{args.m}x{args.n}xf32>) -> tensor<{args.m}x{args.n}xf32>
  return %0 : tensor<{args.m}x{args.n}xf32>
}}
"""


def transform(args: argparse.Namespace) -> str:
    if args.tile_m == 0:
        return ""
    return f"""
module attributes {{transform.with_named_sequence}} {{
  transform.named_sequence @__transform_main(
      %module_op: !transform.any_op {{transform.consumed}}) {{
    %matmul = transform.structured.match ops{{[\"linalg.matmul\"]}} in %module_op
      : (!transform.any_op) -> !transform.any_op
    %tiled, %loops:3 = transform.structured.tile_using_for %matmul
      tile_sizes [{args.tile_m}, {args.tile_n}, {args.tile_k}]
      : (!transform.any_op) -> (!transform.any_op, !transform.any_op,
          !transform.any_op, !transform.any_op)
    %func = transform.get_parent_op %tiled {{isolated_from_above}}
      : (!transform.any_op) -> !transform.any_op
    transform.structured.vectorize_children_and_apply_patterns %func
      : (!transform.any_op) -> !transform.any_op
    %bufferized = transform.bufferization.one_shot_bufferize
      layout{{IdentityLayoutMap}} %module_op
      {{bufferize_function_boundaries = true}}
      : (!transform.any_op) -> !transform.any_op
    transform.yield
  }}
}}
"""


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload(args) + transform(args), encoding="utf-8")


if __name__ == "__main__":
    main()
