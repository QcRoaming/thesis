#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


class ContractSpaceValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(PROJECT / "scripts" / "run_all.py")], check=True)
        cls.summary = json.loads((PROJECT / "processed" / "summary.json").read_text(encoding="utf-8"))

    def test_e1_independent_mutation_oracle(self) -> None:
        e1 = self.summary["E1"]
        self.assertEqual(e1["case_count"], 30)
        self.assertEqual(e1["mutation_count"], 24)
        self.assertEqual(e1["mutation_score"], 1.0)
        self.assertEqual(e1["false_accept_count"], 0)
        self.assertEqual(e1["false_reject_count"], 0)
        self.assertEqual(e1["faults_detected_by_reference"], 2)

    def test_e2_full_static_matrix_and_compile_replay(self) -> None:
        e2 = self.summary["E2"]
        self.assertEqual(e2["static_classification_count"], 36 * 2600)
        self.assertEqual(e2["compile_replay_count"], 8 * 3 * 32)
        self.assertEqual(e2["compile_replay_failure_count"], 0)
        self.assertGreater(e2["spaces"]["G0"]["mean_retained_count"], e2["spaces"]["G1"]["mean_retained_count"])
        self.assertGreater(e2["spaces"]["G1"]["mean_retained_count"], e2["spaces"]["C"]["mean_retained_count"])
        self.assertEqual(e2["spaces"]["C"]["mean_callable_density"], 1.0)
        self.assertGreater(
            e2["spaces"]["C"]["mean_pre_normalization_retained_count"],
            e2["spaces"]["C"]["mean_retained_count"]
        )
        self.assertEqual(e2["spaces"]["C"]["mean_ir_duplicate_ratio"], 0.0)
        self.assertGreater(e2["spaces"]["C"]["inactive_vectorize_removed_count"], 0)
        self.assertEqual(
            e2["spaces"]["C"]["measurement_status"],
            "final_normalized_pool_offline_baco_replay"
        )
        self.assertEqual(e2["spaces"]["C"]["D90"], 0.1875)
        self.assertEqual(e2["spaces"]["C"]["time_to_90_pool_best"], 8.0)
        self.assertEqual(
            e2["spaces"]["C"]["pre_normalization_ablation"]["time_to_90pct_pool_best"],
            11.5
        )
        replay = e2["normalized_baco_replay"]
        self.assertEqual(replay["run_count"], 40)
        self.assertEqual(replay["trace_count"], 1000)
        self.assertFalse(replay["compilation_performed"])
        self.assertFalse(replay["hardware_measurement_performed"])
        self.assertTrue(replay["report_regardless_of_outcome"])
        evidence = replay["normalization_evidence"]
        self.assertEqual(evidence["multi_alias_measured_groups"], 64)
        self.assertEqual(evidence["multi_alias_groups_with_matching_canonical_ir"], 64)
        self.assertEqual(
            evidence["selected_schedules_with_paired_canonical_ir"]
            + evidence["selected_schedules_without_paired_ir"],
            replay["normalized_final_method"]["candidate_count"]
        )

        comparison = e2["same_pool_random_comparison"]
        self.assertEqual(comparison["run_count_per_method"], 40)
        self.assertEqual(comparison["unique_query_budget"], 25)
        self.assertFalse(comparison["compilation_performed"])
        self.assertFalse(comparison["hardware_measurement_performed"])
        self.assertEqual(comparison["random"]["duplicate_queries"], 0)
        self.assertEqual(comparison["random"]["callback_count"], 40 * 25)
        self.assertEqual(
            comparison["baco"]["callbacks_consumed_to_unique_budget"],
            40 * 25 + comparison["baco"]["duplicate_callbacks_before_unique_budget"],
        )
        self.assertEqual(comparison["D90"], replay["normalized_final_method"]["D90"])
        self.assertEqual(
            comparison["baco"]["reached_90pct_pool_best_fraction"], 0.925
        )
        self.assertEqual(
            comparison["random"]["reached_90pct_pool_best_fraction"], 1.0
        )

        with (PROJECT / "processed" / "e2_normalized_pool.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            pool_rows = list(csv.DictReader(handle))
        self.assertEqual(len(pool_rows), 8 * 28)
        workload_ids = {row["workload_id"] for row in pool_rows}
        self.assertEqual(len(workload_ids), 8)
        for workload_id in workload_ids:
            rows = [row for row in pool_rows if row["workload_id"] == workload_id]
            self.assertEqual(len(rows), 28)
            self.assertEqual(len({row["canonical_schedule_id"] for row in rows}), 28)

    def test_e3_reports_partial_not_universal_reuse(self) -> None:
        e3 = self.summary["E3"]
        self.assertTrue(e3["f64_core_generator_hash_unchanged"])
        self.assertEqual(e3["package_id_special_cases_in_shared_core"], 0)
        self.assertFalse(e3["openblas_uses_same_core_generator"])
        self.assertFalse(e3["strong_reuse_claim_supported"])
        self.assertEqual(e3["schema_intersection_leaf_fields"], 31)
        self.assertEqual(e3["schema_union_leaf_fields"], 34)
        self.assertAlmostEqual(e3["schema_intersection_over_union_ratio"], 31 / 34)
        self.assertEqual(len(e3["package_shared_field_coverage_ratios"]), 3)

    def test_e4_keeps_horizon_types_separate(self) -> None:
        scenarios = {row["scenario"]: row for row in self.summary["E4"]["scenarios"]}
        self.assertTrue(scenarios["i7_f64_posthoc_winning_shapes"]["finite_break_even"])
        self.assertGreater(scenarios["i7_f64_posthoc_winning_shapes"]["saving_lcb95_ms"], 0.0)
        i7 = scenarios["i7_f64_posthoc_winning_shapes"]
        self.assertTrue(i7["posthoc_selection"])
        self.assertTrue(i7["lcb95_finite_break_even"])
        self.assertGreater(i7["lcb95_break_even_horizon"], i7["point_break_even_horizon"])
        self.assertAlmostEqual(i7["C_c_ms"] + i7["C_s_total_ms"], i7["total_cost_ms"])
        self.assertIn("synthetic equal-frequency", i7["deployment_cycle_definition"])
        for name in ("i9_qwen_exact_shapes", "k230_qwen_exact_shapes"):
            self.assertFalse(scenarios[name]["finite_break_even"])
            self.assertLess(scenarios[name]["saving_ucb95_ms"], 0.0)
            self.assertFalse(scenarios[name]["posthoc_selection"])


if __name__ == "__main__":
    unittest.main()
