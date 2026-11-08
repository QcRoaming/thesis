#!/usr/bin/env python3
"""Regression tests for the corrected same-pool prior protocol."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

from experiment_lib import (  # noqa: E402
    PROCESSED,
    canonicalize_pool,
    load_config,
    load_host_corpus,
    load_workloads,
    method_prior,
    parameter_liveness_audit,
    prepare_calibration,
)


class SamePoolPriorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config()
        cls.workloads = load_workloads(cls.config)
        cls.pools = canonicalize_pool(cls.config, cls.workloads)
        cls.hosts = [
            load_host_corpus(environment, cls.pools, cls.workloads)
            for environment in cls.config["environments"]
        ]

    def test_canonical_pool_contains_unique_active_tuples(self) -> None:
        for workload_id, pool in self.pools.items():
            tuples = {
                (row["tile_m"], row["tile_n"], row["tile_k"])
                for row in pool
            }
            self.assertEqual(len(pool), len(tuples), workload_id)
            self.assertGreaterEqual(len(pool), self.config["budget"])
            self.assertLess(len(pool), 28)

    def test_inactive_vectorize_is_not_a_search_parameter(self) -> None:
        self.assertNotIn("vectorize", self.config["active_search_parameters"])
        self.assertIn("vectorize", self.config["excluded_inactive_parameters"])
        aliased = 0
        for pool in self.pools.values():
            for row in pool:
                aliases = json.loads(row["source_aliases"])
                aliased += len(aliases) > 1
        self.assertGreater(aliased, 0)

    def test_both_hosts_cover_the_identical_canonical_domain(self) -> None:
        domains = []
        for host in self.hosts:
            domains.append({
                workload_id: {
                    host["records"][index]["canonical_id"]
                    for index in indices
                }
                for workload_id, indices in host["by_workload"].items()
            })
        self.assertEqual(domains[0], domains[1])

    def test_holdout_targets_are_absent_from_calibration(self) -> None:
        for host in self.hosts:
            calibration = prepare_calibration(host, self.workloads, self.config)
            holdout = np.asarray([
                row["split"] == "holdout" for row in host["records"]
            ])
            self.assertTrue(np.all(np.isnan(calibration["y"][holdout])))
            self.assertTrue(np.all(np.isfinite(calibration["y"][~holdout])))

    def test_method_priors_share_pool_and_normalize(self) -> None:
        host = self.hosts[0]
        calibration = prepare_calibration(host, self.workloads, self.config)
        workload_id = next(
            workload_id for workload_id, indices in host["by_workload"].items()
            if host["records"][indices[0]]["split"] == "holdout"
        )
        indices = host["by_workload"][workload_id]
        self.assertIsNone(method_prior(
            "B2_no_prior_baco", indices, host, calibration, self.config
        ))
        for method in ("B3_static_prior_baco", "B4_calibrated_prior_baco"):
            prior = method_prior(method, indices, host, calibration, self.config)
            self.assertEqual(len(prior), len(indices))
            self.assertAlmostEqual(sum(prior), 1.0, places=10)
            self.assertTrue(all(value > 0.0 for value in prior))

    def test_prior_probabilities_align_with_baco_token_order(self) -> None:
        host = self.hosts[0]
        calibration = prepare_calibration(host, self.workloads, self.config)
        rows = host["records"]
        workload_id = next(
            workload_id for workload_id, indices in host["by_workload"].items()
            if rows[indices[0]]["split"] == "holdout"
        )
        indices = sorted(
            host["by_workload"][workload_id],
            key=lambda index: rows[index]["canonical_id"],
        )
        static_prior = method_prior(
            "B3_static_prior_baco", indices, host, calibration, self.config
        )
        calibrated_prior = method_prior(
            "B4_calibrated_prior_baco", indices, host, calibration, self.config
        )
        expected_static = min(
            range(len(indices)),
            key=lambda position: (
                -float(rows[indices[position]]["active_static_score"]),
                rows[indices[position]]["canonical_id"],
            ),
        )
        predictions = calibration["x"][indices] @ calibration["posterior"].mean
        expected_calibrated = int(np.argmin(predictions))
        self.assertEqual(int(np.argmax(static_prior)), expected_static)
        self.assertEqual(int(np.argmax(calibrated_prior)), expected_calibrated)

    def test_all_declared_search_parameters_are_live(self) -> None:
        rows = parameter_liveness_audit(self.pools, self.hosts, self.config)
        self.assertEqual(
            {row["parameter"] for row in rows},
            set(self.config["active_search_parameters"]),
        )
        self.assertTrue(all(row["status"] == "PASS" for row in rows))

    def test_formal_acceptance_if_generated(self) -> None:
        path = PROCESSED / "acceptance_summary.json"
        if not path.exists():
            self.skipTest("formal experiment has not been generated yet")
        summary = json.loads(path.read_text(encoding="utf-8"))
        if summary["mode"] != "formal":
            self.skipTest("current artifact is a smoke run")
        self.assertIn(summary["status"], {"PASS", "PARTIAL", "FAIL"})
        if summary["status"] == "PASS":
            self.assertTrue(all(summary["conditions"].values()))
        elif summary["status"] == "PARTIAL":
            self.assertFalse(summary["scope_complete_for_two_environment_acceptance"])
        else:
            self.assertTrue(summary["scope_complete_for_two_environment_acceptance"])
            self.assertFalse(all(summary["conditions"].values()))
        if summary["status"] != "PASS":
            for key, value in summary["conditions"].items():
                if key != "calibrated_prior_ci_gain_on_at_least_two_environments":
                    self.assertTrue(value, key)


if __name__ == "__main__":
    unittest.main()
