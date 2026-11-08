#!/usr/bin/env python3
"""Isolated, safe numerical fault injection for Contract validation."""

from __future__ import annotations

import argparse
import json
import math
import random


def matmul(a: list[list[float]], b: list[list[float]], c: list[list[float]], beta: float) -> list[list[float]]:
    m, k, n = len(a), len(b), len(b[0])
    return [
        [sum(a[i][p] * b[p][j] for p in range(k)) + beta * c[i][j] for j in range(n)]
        for i in range(m)
    ]


def run(mode: str) -> dict[str, object]:
    rng = random.Random(20260723)
    m, k, n = 7, 9, 11
    a = [[rng.uniform(-1.0, 1.0) for _ in range(k)] for _ in range(m)]
    b = [[rng.uniform(-1.0, 1.0) for _ in range(n)] for _ in range(k)]
    c = [[rng.uniform(-1.0, 1.0) for _ in range(n)] for _ in range(m)]
    reference = matmul(a, b, c, 1.0)

    if mode == "scrambled_b_panel":
        # This models a descriptor-consistent buffer whose physical panel order is wrong.
        corrupted_b = [row[1:] + row[:1] for row in b]
        observed = matmul(a, corrupted_b, c, 1.0)
    elif mode == "broken_beta_tail":
        observed = matmul(a, b, c, 1.0)
        for j in range(n):
            observed[-1][j] -= c[-1][j]
    else:
        raise ValueError(mode)

    max_abs_error = max(
        abs(reference[i][j] - observed[i][j]) for i in range(m) for j in range(n)
    )
    return {
        "mode": mode,
        "isolated_process": True,
        "reference": "pure Python reference GEMM",
        "finite_output": all(math.isfinite(value) for row in observed for value in row),
        "max_abs_error": max_abs_error,
        "wrong_result_detected": max_abs_error > 1.0e-6,
        "invalid_isa_executed": False,
        "real_abi_corrupted": False
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("scrambled_b_panel", "broken_beta_tail"))
    args = parser.parse_args()
    print(json.dumps(run(args.mode), sort_keys=True))


if __name__ == "__main__":
    main()
