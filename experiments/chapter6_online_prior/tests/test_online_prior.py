from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
PROCESSED = PROJECT / "processed"
RAW = PROJECT / "raw"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class OnlinePriorArtifactTests(unittest.TestCase):
    def test_extended_corpus_is_complete_and_real(self) -> None:
        summary = json.loads((PROCESSED / "extended_measurement_summary.json").read_text())
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["contract_cases"], 1008)
        self.assertEqual(summary["split_case_counts"], {
            "design": 420, "validation": 252, "holdout": 336,
        })
        self.assertTrue(summary["all_pass"])
        self.assertTrue(summary["all_predictions_match"])

    def test_holdout_is_not_used_for_fit_or_selection(self) -> None:
        summary = json.loads((PROCESSED / "online_prior_summary.json").read_text())
        self.assertEqual(summary["holdout_outcomes_used_for_fit"], 0)
        self.assertEqual(summary["holdout_outcomes_used_for_hyperparameters"], 0)
        self.assertEqual(summary["design_cases"], 420)
        self.assertEqual(summary["validation_cases"], 252)
        self.assertEqual(summary["holdout_cases"], 336)

    def test_every_policy_has_unique_fixed_budget_trajectories(self) -> None:
        rows = read_csv(RAW / "online_prior_traces.csv")
        groups: dict[tuple[str, str, str], list[dict[str, str]]] = {}
        for row in rows:
            groups.setdefault((row["method"], row["workload_id"], row["seed"]), []).append(row)
        self.assertEqual(len(groups), 5 * (9 + 12) * 5)
        for values in groups.values():
            self.assertEqual(len(values), 25)
            self.assertEqual(len({row["candidate_id"] for row in values}), 25)
            self.assertEqual([int(row["iteration"]) for row in values], list(range(1, 26)))

    def test_online_feedback_is_revealed_after_selection(self) -> None:
        rows = read_csv(RAW / "online_prior_traces.csv")
        for row in rows:
            self.assertEqual(int(row["revealed_before_selection"]), int(row["iteration"]) - 1)

    def test_fixed_budget_summary_is_complete(self) -> None:
        rows = read_csv(PROCESSED / "fixed_budget_summary.csv")
        self.assertEqual(len(rows), 2 * 5 * 4)
        self.assertEqual({int(row["budget"]) for row in rows}, {5, 10, 15, 25})
        for row in rows:
            self.assertGreater(float(row["relative_to_pool_best_gmean"]), 0.0)
            self.assertLessEqual(float(row["relative_to_pool_best_gmean"]), 1.0000001)


if __name__ == "__main__":
    unittest.main()
