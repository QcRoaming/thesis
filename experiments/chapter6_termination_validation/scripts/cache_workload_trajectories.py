#!/usr/bin/env python3
"""Populate BaCO trajectory caches for one holdout workload."""

from __future__ import annotations

import argparse
import os

from run_termination_validation import (
    load_measurement_costs,
    load_state,
    prepare_model,
    run_trajectories,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workload_id")
    args = parser.parse_args()
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    config, _, workloads, _, full_host = load_state()
    if args.workload_id not in full_host["by_workload"]:
        raise KeyError(args.workload_id)
    indices = full_host["by_workload"][args.workload_id]
    if full_host["records"][indices[0]]["split"] != "holdout":
        raise ValueError(f"{args.workload_id} is not a holdout workload")
    host = {
        **full_host,
        "by_workload": {args.workload_id: indices},
    }
    models = {
        "data_only": prepare_model(
            "data_only", full_host, workloads, config
        ),
        "expert_plus_data": prepare_model(
            "expert_plus_data", full_host, workloads, config
        ),
    }
    run_trajectories(
        config,
        host,
        models,
        load_measurement_costs(config),
        force=False,
    )


if __name__ == "__main__":
    main()
