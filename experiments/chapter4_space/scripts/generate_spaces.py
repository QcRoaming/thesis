#!/usr/bin/env python3
"""Generate all Chapter 4 schedule spaces and traceable artifacts."""

from __future__ import annotations

import argparse
import json
import time
import tracemalloc
from pathlib import Path

from chapter4lib import (
    PROJECT_DIR,
    generate_spaces_for_task,
    load_inputs,
    provenance_record,
    raw_candidates,
    select_contract,
    summarize_task,
    write_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project = args.project.resolve()
    inputs = load_inputs(project)
    candidates = raw_candidates(inputs["space_config"]["raw_domain"])
    all_rows = []
    summary_rows = []
    selection_rows = []
    provenance_rows = []
    registry = []
    generation_metrics = []

    for task in inputs["tasks"]:
        tracemalloc.start()
        started = time.perf_counter()
        spaces, rows, selection_log = generate_spaces_for_task(
            task, candidates, inputs["contracts"], inputs["space_config"]
        )
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        contract, _ = select_contract(task, inputs["contracts"])
        for row in rows:
            provenance_rows.append(
                provenance_record(row, task, contract, inputs["rules"], inputs["source_files"])
            )
        all_rows.extend(rows)
        selection_rows.extend(selection_log)
        summary_rows.append(summarize_task(task, rows, spaces))
        generation_metrics.append(
            {
                "task_id": task["id"],
                "raw_count": len(rows),
                "elapsed_ms": round(elapsed_ms, 6),
                "peak_bytes": peak_bytes,
                "microseconds_per_candidate": round(elapsed_ms * 1000.0 / len(rows), 6),
            }
        )
        for space_id, members in spaces.items():
            write_csv(project / "processed" / "spaces" / f"{task['id']}__{space_id}.csv", members)
        registry.append(
            {
                "task_id": task["id"],
                "selected_contract": contract,
                "selection_candidates": selection_log,
            }
        )

    write_csv(project / "raw" / "candidate_decisions.csv", all_rows)
    write_csv(project / "processed" / "space_summary.csv", summary_rows)
    write_csv(project / "processed" / "contract_selection.csv", selection_rows)
    write_csv(project / "processed" / "generation_complexity.csv", generation_metrics)
    write_csv(project / "provenance" / "candidate_provenance.csv", provenance_rows)
    (project / "processed" / "contract_registry.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "import_sources": inputs["source_files"],
                "entries": registry,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "processed" / "space_summary.json").write_text(
        json.dumps(summary_rows, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary_rows, indent=2))


if __name__ == "__main__":
    main()
