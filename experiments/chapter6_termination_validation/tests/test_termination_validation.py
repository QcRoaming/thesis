#!/usr/bin/env python3
"""Regression tests for the three termination validation experiments."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import run_termination_validation as experiment  # noqa: E402


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class TerminationValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        (
            cls.config,
            cls.same_pool_config,
            cls.workloads,
            cls.pools,
            cls.host,
        ) = experiment.load_state()

    def test_feature_ablation_changes_only_soft_expert_features(self) -> None:
        data = set(experiment.selected_feature_names("data_only"))
        expert = set(experiment.selected_feature_names("expert_plus_data"))
        removed = expert - data
        expected = {
            name for name in experiment.base.feature_names()
            if name == "active_static_score" or name.endswith("_x_static")
        }
        self.assertEqual(removed, expected)
        self.assertTrue(data < expert)

    def test_common_pool_has_unique_active_tuples(self) -> None:
        for workload_id, pool in self.pools.items():
            active = {
                (row["tile_m"], row["tile_n"], row["tile_k"])
                for row in pool
            }
            self.assertEqual(len(active), len(pool), workload_id)
            self.assertGreaterEqual(len(pool), max(self.config["checkpoints"]))

    def test_holdout_targets_are_absent_from_both_models(self) -> None:
        for mode in ("data_only", "expert_plus_data"):
            model = experiment.prepare_model(
                mode, self.host, self.workloads, self.config
            )
            self.assertEqual(
                int(experiment.np.isfinite(model["y"][model["holdout_mask"]]).sum()),
                0,
            )

    def test_formal_outputs_if_generated(self) -> None:
        summary_path = PROJECT / "processed" / "acceptance_summary.json"
        if not summary_path.exists():
            self.skipTest("formal outputs not generated")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        traces = rows(PROJECT / "raw" / "termination_traces.csv")
        run_summaries = rows(PROJECT / "raw" / "trajectory_summaries.csv")
        expected_runs = 12 * len(experiment.METHODS) * len(self.config["seeds"])
        self.assertEqual(len(run_summaries), expected_runs)
        self.assertTrue(all(int(row["duplicate_callbacks"]) == 0 for row in run_summaries))
        self.assertTrue(all(
            int(row["unique_measurements"]) == int(row["budget"])
            for row in run_summaries
        ))
        self.assertEqual(
            len({
                (row["workload_id"], row["method"], row["seed"])
                for row in traces
            }),
            expected_runs,
        )
        self.assertIn(summary["status"], {"GO", "MIXED"})

    def test_time_to_95_is_reached_by_pool_exhaustion(self) -> None:
        path = PROJECT / "processed" / "time_to_95_oracle.csv"
        if not path.exists():
            self.skipTest("formal outputs not generated")
        values = rows(path)
        self.assertEqual(len(values), 12 * len(experiment.METHODS) * len(self.config["seeds"]))
        self.assertTrue(all(row["reached"].lower() == "true" for row in values))
        self.assertTrue(all(
            int(row["evaluations_to_95_oracle"]) <= int(row["pool_size"])
            for row in values
        ))

    def test_second_microkernel_audit_keeps_claim_boundary(self) -> None:
        path = PROJECT / "processed" / "second_microkernel_audit.json"
        if not path.exists():
            self.skipTest("formal outputs not generated")
        audit = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(audit["independent_backend_status"], "NOT_TESTED")
        self.assertEqual(
            audit["core_generator_sha256_before"],
            audit["core_generator_sha256_after"],
        )
        if audit["second_microkernel_status"] == "GO":
            self.assertTrue(all(audit["conditions"].values()))


if __name__ == "__main__":
    unittest.main()
