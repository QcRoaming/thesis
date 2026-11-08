from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SUMMARY = PROJECT / "processed" / "integrated_summary.json"
PATHS = PROJECT / "raw" / "path_matrix.csv"
TRACE = PROJECT / "processed" / "baco_tuning_trace.csv"


@unittest.skipUnless(SUMMARY.exists() and PATHS.exists() and TRACE.exists(), "evidence not generated")
class IntegratedPipelineEvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        with PATHS.open(encoding="utf-8") as stream:
            cls.paths = list(csv.DictReader(stream))
        with TRACE.open(encoding="utf-8") as stream:
            cls.trace = list(csv.DictReader(stream))

    def test_path_matrix_covers_all_policy_outcomes(self) -> None:
        self.assertEqual(
            self.summary["path_matrix"]["observed_path_counts"],
            {"direct": 1, "adapt": 1, "fallback": 1},
        )

    def test_predictions_match_real_execution(self) -> None:
        self.assertTrue(self.summary["path_matrix"]["all_predictions_match_observations"])
        self.assertTrue(all(row["predicted_path"] == row["observed_path"] for row in self.paths))

    def test_direct_and_adapt_really_link_blis(self) -> None:
        replaced = [row for row in self.paths if row["microkernel_replaced"] == "True"]
        self.assertEqual({row["observed_path"] for row in replaced}, {"direct", "adapt"})
        self.assertTrue(all(row["has_blis_kernel_symbol"] == "True" for row in replaced))

    def test_adapt_executes_expected_fringe(self) -> None:
        adapt = next(row for row in self.paths if row["observed_path"] == "adapt")
        self.assertGreater(int(adapt["fringe_calls"]), 0)
        self.assertEqual(adapt["fringe_calls"], adapt["expected_fringe_calls"])

    def test_all_path_cases_pass_correctness(self) -> None:
        self.assertTrue(self.summary["path_matrix"]["all_correct"])
        self.assertTrue(all(row["status"] == "PASS" for row in self.paths))

    def test_baco_drives_real_evaluator(self) -> None:
        baco = self.summary["baco"]
        self.assertEqual(baco["evaluated"], baco["budget"])
        self.assertEqual(baco["valid_count"], baco["evaluated"])
        self.assertGreater(baco["real_microkernel_evaluations"], 0)
        self.assertTrue(baco["all_predictions_match_observations"])

    def test_pool_contains_core_and_shell(self) -> None:
        self.assertGreater(self.summary["baco"]["pool_role_counts"].get("core", 0), 0)
        self.assertGreater(self.summary["baco"]["pool_role_counts"].get("shell", 0), 0)


if __name__ == "__main__":
    unittest.main()
