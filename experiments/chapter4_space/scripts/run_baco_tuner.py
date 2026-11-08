#!/usr/bin/env python3
"""Export and execute a small real BaCO tuning loop over Expert+Shell."""

from __future__ import annotations

import argparse
import csv
import json
import random
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

from chapter4lib import (
    Candidate,
    PROJECT_DIR,
    generate_spaces_for_task,
    load_inputs,
    rank_and_select_initial,
    raw_candidates,
    write_csv,
)
from transform_runner import evaluate_transform


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT_DIR)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def baco_commit(project: Path) -> str:
    repo = project.parent.parent / "third_party" / "baco"
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True, capture_output=True, check=True
    )
    return completed.stdout.strip()


def build_scenario(run_dir: Path, schedule_indices: list[int], budget: int) -> dict[str, Any]:
    doe = min(4, budget)
    return {
        "application_name": "chapter4_expert_shell_matmul",
        "optimization_objectives": ["runtime_ms"],
        "optimization_method": "bayesian_optimization",
        "optimization_iterations": max(0, budget - doe),
        "design_of_experiment": {
            "doe_type": "random sampling",
            "number_of_samples": doe,
            "allow_repetitions": False,
        },
        "models": {"model": "gaussian_process"},
        "GP_model": "gpy",
        "hyperparameter_optimization_iterations": 1,
        "acquisition_function": "EI",
        "normalize_inputs": True,
        "predict_noiseless": False,
        "allow_duplicate_samples": False,
        "local_search_random_points": 500,
        "local_search_starting_points": 5,
        "input_parameters": {
            "schedule_index": {
                "parameter_type": "ordinal",
                "values": schedule_indices,
                "parameter_default": schedule_indices[0],
                "transform": "none",
            }
        },
        "feasible_output": {
            "enable_feasible_predictor": True,
            "name": "Valid",
            "true_value": "True",
            "false_value": "False",
        },
        "run_directory": str(run_dir),
        "log_file": "baco.log",
        "output_data_file": "baco_samples.csv",
    }


def main() -> None:
    args = parse_args()
    project = args.project.resolve()
    inputs = load_inputs(project)
    tune_config = inputs["space_config"]["smoke_tuning"]
    task = next(task for task in inputs["tasks"] if task["id"] == tune_config["task_id"])
    candidates = raw_candidates(inputs["space_config"]["raw_domain"])
    spaces, _, _ = generate_spaces_for_task(task, candidates, inputs["contracts"], inputs["space_config"])
    selected_space = spaces[tune_config["space_id"]]
    if not selected_space:
        raise RuntimeError("selected BaCO space is empty")
    ordered = rank_and_select_initial(selected_space, len(selected_space))
    initial_size = next(
        item["initial_design_size"]
        for item in inputs["space_config"]["configs"]
        if item["id"] == tune_config["space_id"]
    )

    lookup = []
    for index, row in enumerate(ordered):
        lookup.append(
            {
                "schedule_index": index,
                "candidate_id": row["candidate_id"],
                "tile_m": row["tile_m"],
                "tile_n": row["tile_n"],
                "tile_k": row["tile_k"],
                "pack_mode": row["pack_mode"],
                "vectorize": row["vectorize"],
                "predicted_path": row["predicted_path"],
                "score": row["score"],
                "initial_design_rank": index + 1 if index < initial_size else None,
            }
        )
    tuner_dir = project / "tuner"
    run_dir = tuner_dir / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (tuner_dir / "expert_shell_lookup.json").write_text(json.dumps(lookup, indent=2) + "\n", encoding="utf-8")
    (tuner_dir / "initial_design.json").write_text(
        json.dumps(
            {
                "ranked_points": lookup[:initial_size],
                "baco_native_consumption": (
                    "rank 1 is parameter_default; remaining DOE points are sampled uniformly by unmodified BaCO"
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    # Small tiles can cause vector IR expansion and multi-minute -O3 compilation.
    # Keep the full lookup, but bound this smoke run to a declared low-expansion subset.
    tuning_pool = [
        item
        for item in lookup
        if item["tile_m"] == 168 and item["tile_n"] >= 128 and item["tile_k"] >= 128
    ]
    if len(tuning_pool) < int(tune_config["budget"]):
        raise RuntimeError("the bounded BaCO tuning pool is smaller than the requested budget")
    (tuner_dir / "baco_tuning_pool.json").write_text(
        json.dumps(
            {
                "selection_policy": "tile_m==168 and tile_n>=128 and tile_k>=128",
                "reason": "bound vector IR expansion during the Chapter 4 smoke run",
                "full_expert_shell_size": len(lookup),
                "members": tuning_pool,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    scenario = build_scenario(
        run_dir,
        [int(item["schedule_index"]) for item in tuning_pool],
        int(tune_config["budget"]),
    )
    scenario_path = tuner_dir / "baco_scenario.json"
    scenario_path.write_text(json.dumps(scenario, indent=2) + "\n", encoding="utf-8")

    callback_log = project / "raw" / "baco_callback_log.jsonl"
    if callback_log.exists():
        callback_log.unlink()
    invocation = 0

    def objective(configuration: dict[str, Any]) -> dict[str, Any]:
        nonlocal invocation
        invocation += 1
        index = int(round(float(configuration["schedule_index"])))
        item = lookup[index]
        candidate = Candidate(
            int(item["tile_m"]),
            int(item["tile_n"]),
            int(item["tile_k"]),
            str(item["pack_mode"]),
            bool(item["vectorize"]),
        )
        template = {
            "direct": "contract_direct_schedule",
            "adapt": "finite_tail_adapt_schedule",
            "fallback": "generic_fallback_schedule",
        }[item["predicted_path"]]
        started = time.perf_counter()
        measured = evaluate_transform(
            task,
            candidate,
            str(item["predicted_path"]),
            template,
            project / "build" / "baco" / f"{index:04d}_{candidate.id}",
            warmups=int(tune_config["warmups"]),
            repeats=int(tune_config["repeats"]),
            inner_iters=int(tune_config["inner_iters"]),
            force=args.force,
        )
        valid = measured["compile_status"] == "pass" and measured["correctness_status"] == "pass"
        runtime = float(measured["median_ms"]) if valid else 1.0e9
        record = {
            "invocation": invocation,
            **item,
            "Valid": valid,
            "runtime_ms": runtime,
            "observed_path": measured["observed_path"],
            "microkernel_replaced": measured["microkernel_replaced"],
            "compile_status": measured["compile_status"],
            "correctness_status": measured["correctness_status"],
            "callback_wall_ms": round((time.perf_counter() - started) * 1000.0, 6),
        }
        with callback_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return {"runtime_ms": runtime, "Valid": valid}

    seed = int(inputs["space_config"]["seed"])
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    from baco import run
    from baco.util.file import read_settings_file

    settings = read_settings_file(str(scenario_path))
    run.optimize(settings, objective)

    samples_path = run_dir / "baco_samples.csv"
    samples = list(csv.DictReader(samples_path.open(encoding="utf-8")))
    enriched = []
    best = float("inf")
    for iteration, row in enumerate(samples, 1):
        item = lookup[int(float(row["schedule_index"]))]
        runtime = float(row["runtime_ms"])
        valid = row.get("Valid", "False").lower() == "true"
        if valid:
            best = min(best, runtime)
        enriched.append(
            {
                "iteration": iteration,
                **item,
                "runtime_ms": runtime,
                "Valid": valid,
                "best_so_far_ms": best if best < float("inf") else None,
                "timestamp_ms": row.get("timestamp", row.get("Timestamp", "")),
            }
        )
    write_csv(project / "processed" / "baco_tuning_trace.csv", enriched)
    best_row = min((row for row in enriched if row["Valid"]), key=lambda row: row["runtime_ms"])
    summary = {
        "baco_commit": baco_commit(project),
        "task_id": task["id"],
        "space_id": tune_config["space_id"],
        "full_space_size": len(lookup),
        "baco_pool_size": len(tuning_pool),
        "budget": int(tune_config["budget"]),
        "evaluated": len(enriched),
        "unique_schedules": len({row["schedule_index"] for row in enriched}),
        "duplicate_evaluations": len(enriched) - len({row["schedule_index"] for row in enriched}),
        "valid_count": sum(row["Valid"] for row in enriched),
        "best": best_row,
        "all_observed_fallback": all(
            json.loads(line)["observed_path"] == "fallback"
            for line in callback_log.read_text(encoding="utf-8").splitlines()
            if line
        ),
        "seed": seed,
    }
    (project / "processed" / "baco_tuning_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    report = [
        "# Chapter 4 BaCO Smoke Tuning",
        "",
        f"- BaCO commit: `{summary['baco_commit']}`",
        f"- Task: `{summary['task_id']}`",
        f"- Exported full Expert+Shell schedules: **{summary['full_space_size']}**",
        f"- Bounded smoke-run pool: **{summary['baco_pool_size']}**",
        f"- Budget/evaluated: **{summary['budget']}/{summary['evaluated']}**",
        f"- Unique/duplicate schedule evaluations: **{summary['unique_schedules']}/{summary['duplicate_evaluations']}**",
        f"- Valid compile-and-correctness rows: **{summary['valid_count']}**",
        f"- Best schedule: `{best_row['candidate_id']}` at **{best_row['runtime_ms']:.6f} ms**",
        "",
        "BaCO is unmodified. Expert knowledge constructs the finite domain, lookup, and ranked initial-design file; it does not alter BaCO's probabilistic model.",
        "Only rank 1 is consumed as BaCO's native parameter default in this smoke run; the remaining DOE points are BaCO uniform samples.",
        "",
        "The smoke pool uses `tile_m=168`, `tile_n>=128`, and `tile_k>=128` to retain an M fringe and bound vector IR expansion observed during an aborted broad-domain attempt.",
        "",
        "Files: `tuner/baco_scenario.json`, `tuner/expert_shell_lookup.json`, `tuner/baco_tuning_pool.json`, `raw/baco_callback_log.jsonl`, `processed/baco_tuning_trace.csv`, and `tuner/run/baco.log`.",
        "",
    ]
    (project / "reports" / "baco_smoke_tuning.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
