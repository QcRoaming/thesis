#!/usr/bin/env python3
"""Build the compact MVP report and action-distribution table."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from jlq.thesis.experiments.chapter3_rules.scripts.rulelib import load_yaml


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "output"


def cpu_model() -> str:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.exists():
        return "unknown"
    for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("model name") and ":" in line:
            return line.split(":", 1)[1].strip()
    return "unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts", type=Path, default=DATA_DIR / "expert_facts.yaml")
    parser.add_argument("--space-summary", type=Path, default=OUTPUT_DIR / "space_summary.json")
    parser.add_argument("--trace", type=Path, default=OUTPUT_DIR / "tuning_trace.csv")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "mvp_report.md")
    parser.add_argument(
        "--distribution", type=Path, default=OUTPUT_DIR / "action_distribution.csv"
    )
    return parser.parse_args()


def read_trace(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    args = parse_args()
    facts_document = load_yaml(args.facts)
    fact = facts_document["facts"][0]
    space_rows = json.loads(args.space_summary.read_text(encoding="utf-8"))["spaces"]
    trace_rows = read_trace(args.trace)

    args.distribution.parent.mkdir(parents=True, exist_ok=True)
    distribution_rows = []
    for row in space_rows:
        total = row["generated"]
        distribution_rows.append(
            {
                "task_id": row["task_id"],
                "space": row["space"],
                "generated": total,
                "tuner_eligible": row["tuner_eligible"],
                **{
                    f"{action}_ratio": f"{row[action] / total:.6f}"
                    for action in ("direct", "adapt", "fallback", "reject")
                },
            }
        )
    with args.distribution.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(distribution_rows[0]))
        writer.writeheader()
        writer.writerows(distribution_rows)

    by_task_space = {(row["task_id"], row["space"]): row for row in space_rows}
    best_rows: dict[tuple[str, str], dict[str, str]] = {}
    for row in trace_rows:
        key = (row["task_id"], row["space"])
        if key not in best_rows or float(row["score"]) > float(best_rows[key]["score"]):
            best_rows[key] = row
    metric = trace_rows[0]["metric"] if trace_rows else "not_run"

    micro = fact["microkernel"]
    cache = fact["cache_blocking"]
    vector = fact["vectorization"]
    lines = [
        "# BLIS Expert-Space MVP Report",
        "",
        "## Extracted fact",
        "",
        f"- Kernel: `{micro['symbol']}`",
        f"- Register tile: `{micro['mr']}x{micro['nr']}`",
        f"- Cache blocking: `MC={cache['mc']}, KC={cache['kc']}, NC={cache['nc']}`",
        f"- Packing kernel: `{fact['packing']['kernel']}`",
        f"- ISA: `{', '.join(vector['isa'])}`; vector lanes for f32: `{vector['lanes']}`",
        f"- Source revision: `{facts_document['source']['revision']}`",
        "",
        "## Search-space size and contract outcomes",
        "",
        "`Eligible` is the number sent to the tuner under that variant's policy.",
        "The four outcome columns are pre-measurement contract classifications.",
        "",
        "| Task | Space | Generated | Eligible | Direct | Adapt | Fallback | Reject |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(space_rows, key=lambda item: (item["task_id"], item["space"])):
        lines.append(
            f"| {row['task_id']} | {row['space']} | {row['generated']} | "
            f"{row['tuner_eligible']} | {row['direct']} | {row['adapt']} | "
            f"{row['fallback']} | {row['reject']} |"
        )

    lines.extend(["", "## Generic vs expert", ""])
    tasks = sorted({row["task_id"] for row in space_rows})
    for task_id in tasks:
        generic = by_task_space[(task_id, "generic")]["tuner_eligible"]
        expert = by_task_space[(task_id, "expert")]["tuner_eligible"]
        reduction = 100.0 * (1.0 - expert / generic)
        lines.append(
            f"- `{task_id}`: `{generic}` generic candidates vs `{expert}` expert "
            f"candidates, a `{reduction:.1f}%` reduction."
        )

    if trace_rows:
        lines.extend(
            [
                "",
                "## Equal-budget search",
                "",
                f"Metric: `{metric}` (higher is better).",
                "",
                "| Task | Space | Final best | Best candidate action |",
                "|---|---|---:|---|",
            ]
        )
        for (task_id, space), row in sorted(best_rows.items()):
            lines.append(
                f"| {task_id} | {space} | {float(row['score']):.4f} | "
                f"{row['action']} |"
            )
        lines.append("")
        if metric == "proxy_score":
            lines.append(
                "> These scores only validate the pipeline and convergence accounting; "
                "they are not measured performance."
            )
        else:
            lines.extend(
                [
                    f"> Native host: `{cpu_model()}`. The source facts target Haswell; the",
                    "> host is ISA-compatible but is not the same microarchitecture.",
                    "> Native GFLOP/s comes from the bundled tiled C++ proxy kernel, not BLIS",
                    "> or the final MLIR AOT code path.",
                ]
            )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "This MVP validates source-backed fact extraction, contract classification, "
            "space generation, equal-budget sampling, native measurement plumbing, and "
            "ablation bookkeeping. `direct/adapt/fallback/reject` are checker decisions, "
            "not observed MLIR library-replacement success rates. A final thesis experiment "
            "must compile each retained Transform Dialect candidate and record the actual "
            "replacement/lowering outcome.",
            "",
        ]
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.distribution}")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
