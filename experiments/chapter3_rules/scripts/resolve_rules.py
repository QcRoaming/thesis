#!/usr/bin/env python3
"""Resolve shape/Contract prior conflicts without silent overrides."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent


def resolve_dimension(shape_value: int, prior_value: int, dimension: str) -> tuple[int, dict | None]:
    selected = min(shape_value, prior_value)
    if prior_value <= shape_value:
        return selected, None
    return selected, {
        "field": f"tile_{dimension}",
        "candidate_values": f"shape={shape_value};expert_prior={prior_value}",
        "winner": str(selected),
        "winner_source": "semantic_and_shape_legality",
        "suppressed_source": "same_backend_E1_cache_prior",
        "resolution": "clip_to_shape_extent",
        "silent_override": "false",
    }


def resolve_shape(shape: dict, contract: dict) -> tuple[dict, list[dict]]:
    selected = {}
    conflicts = []
    for dim, block_name in (("m", "mc"), ("n", "nc"), ("k", "kc")):
        value, conflict = resolve_dimension(
            int(shape[dim]), int(contract["cache_blocking"][block_name]), dim
        )
        selected[f"tile_{dim}"] = value
        if conflict:
            conflict.update(
                {
                    "shape_id": shape["id"],
                    "contract_id": contract["kernel_id"],
                }
            )
            conflicts.append(conflict)
    return selected, conflicts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project = args.project.resolve()
    shapes = yaml.safe_load((project / "data" / "preliminary_shapes.yaml").read_text())["shapes"]
    contracts = yaml.safe_load((project / "data" / "microkernel_contracts.yaml").read_text())["contracts"]
    contract = next(item for item in contracts if item["dtype"] == "f32")
    conflicts = []
    for shape in shapes:
        _, rows = resolve_shape(shape, contract)
        conflicts.extend(rows)
    output = project / "data" / "conflicts.csv"
    fieldnames = [
        "shape_id",
        "contract_id",
        "field",
        "candidate_values",
        "winner",
        "winner_source",
        "suppressed_source",
        "resolution",
        "silent_override",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(conflicts)
    print(f"wrote {len(conflicts)} conflict decisions to {output}")


if __name__ == "__main__":
    main()
