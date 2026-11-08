import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

from chapter6lib import METHOD_TO_SPACE, build_space_state, load_config, space_summary


class Chapter6SpaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config, cls.workloads = load_config()
        cls.inputs, cls.state = build_space_state(cls.workloads, cls.config)

    def test_frozen_matrix(self):
        self.assertEqual(len(self.workloads), 36)
        self.assertEqual(sum(row["tune"] for row in self.workloads), 8)
        self.assertGreaterEqual(sum(row["split"] == "holdout" for row in self.workloads), 8)

    def test_all_methods_have_equal_declared_pool(self):
        expected = self.config["pool_size"]
        budget = self.config["budget"]
        for item in self.state.values():
            if not item["workload"]["tune"]:
                continue
            for method in METHOD_TO_SPACE:
                self.assertEqual(len(item["pools"][method]), expected)
                self.assertGreaterEqual(len(item["pools"][method]), budget)

    def test_spaces_are_nested(self):
        for item in self.state.values():
            ids = {
                name: {row["candidate_id"] for row in members}
                for name, members in item["spaces"].items()
            }
            self.assertTrue(ids["contract_only"] <= ids["generic"])
            self.assertTrue(ids["expert_core"] <= ids["contract_only"])
            self.assertTrue(ids["expert_core"] <= ids["expert_shell"])

    def test_summary_has_one_row_per_workload(self):
        rows = space_summary(self.state)
        self.assertEqual(len(rows), 36)
        self.assertTrue(all(row["raw_count"] == 2600 for row in rows))


if __name__ == "__main__":
    unittest.main()
