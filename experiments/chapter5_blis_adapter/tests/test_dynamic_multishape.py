import csv
import json
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = PROJECT / "processed" / "dynamic_multishape_summary.json"
RAW_PATH = PROJECT / "raw" / "dynamic_multishape_trials.csv"


@unittest.skipUnless(SUMMARY_PATH.exists() and RAW_PATH.exists(), "dynamic evidence not generated")
class DynamicMultiShapeEvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        with RAW_PATH.open(encoding="utf-8") as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.shapes = {row["shape_id"]: row for row in cls.summary["shape_summaries"]}

    def test_one_dynamic_binary_per_variant_covers_every_shape(self):
        kernel = self.summary["dynamic_kernel"]
        self.assertTrue(kernel["one_binary_per_variant_for_all_shapes"])
        self.assertEqual(kernel["compile_count"], 2)
        expected_rows = (
            self.summary["overall"]["shape_count"]
            * 2
            * self.summary["measurement"]["trials"]
        )
        self.assertEqual(len(self.rows), expected_rows)
        for variant in {row["variant"] for row in self.rows}:
            hashes = {row["executable_sha256"] for row in self.rows if row["variant"] == variant}
            self.assertEqual(len(hashes), 1)

    def test_dynamic_ir_contains_direct_and_fringe_paths(self):
        variants = {row["variant"]: row for row in self.summary["dynamic_kernel"]["compiled_variants"]}
        direct = variants["dynamic_blis"]
        self.assertTrue(direct["has_dynamic_dims"])
        self.assertTrue(direct["has_temporary_c"])
        self.assertTrue(direct["has_direct_call"])
        self.assertTrue(direct["has_fringe_call"])
        self.assertTrue(direct["has_blis_kernel_symbol"])

    def test_all_trials_pass_nonzero_c_reference(self):
        self.assertTrue(self.summary["overall"]["all_correct"])
        self.assertTrue(all(row["status"] == "PASS" for row in self.rows))
        self.assertLess(max(float(row["max_abs_diff"]) for row in self.rows), 2.0e-5)
        self.assertTrue(all(row["output_aliases_c"] == "1" for row in self.rows))

    def test_fringe_counts_match_runtime_execution(self):
        self.assertTrue(self.summary["overall"]["fringe_counts_match"])
        self.assertEqual(self.shapes["aligned_anchor_192x256x256"]["fringe_calls_per_trial"], [0])
        self.assertEqual(self.shapes["k_tail_48x67x64"]["fringe_calls_per_trial"], [0])
        self.assertGreater(self.shapes["mn_tail_50x64x70"]["fringe_calls_per_trial"][0], 0)
        self.assertGreater(self.shapes["all_tail_190x250x250"]["fringe_calls_per_trial"][0], 0)

    def test_direct_and_adapt_shape_classes_are_present(self):
        overall = self.summary["overall"]
        self.assertGreater(overall["direct_shape_count"], 0)
        self.assertGreater(overall["adapt_shape_count"], 0)
        self.assertEqual(self.shapes["k_tail_48x67x64"]["expected_path"], "adapt")

    def test_bootstrap_interval_is_well_formed(self):
        overall = self.summary["overall"]
        lower, upper = overall["geometric_mean_speedup_95ci_bootstrap"]
        self.assertGreater(lower, 0.0)
        self.assertLessEqual(lower, overall["geometric_mean_speedup"])
        self.assertGreaterEqual(upper, overall["geometric_mean_speedup"])


if __name__ == "__main__":
    unittest.main()
