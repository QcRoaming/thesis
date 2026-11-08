import csv
import json
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def rows(path):
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


@unittest.skipUnless((PROJECT / "processed" / "chapter6_summary.json").exists(), "formal run not completed")
class Chapter6ArtifactTests(unittest.TestCase):
    def test_all_baselines_cover_36_shapes_and_pass(self):
        data = rows(PROJECT / "processed" / "measurement_aggregates.csv")
        for variant in ("B0_scalar", "B0_optimized", "B5_blis"):
            selected = [row for row in data if row["variant"] == variant]
            self.assertEqual(len(selected), 36)
            self.assertTrue(all(row["all_pass"].lower() == "true" for row in selected))

    def test_complete_blis_frontend_is_linked(self):
        manifests = json.loads((PROJECT / "processed" / "binary_manifests.json").read_text())
        self.assertTrue(manifests["B5_blis"]["blis_frontend_symbol"])
        self.assertTrue(manifests["B5_blis"]["blis_kernel_symbol"])
        self.assertTrue(manifests["B0_optimized"]["packed_vector_fma_present"])

    def test_dynamic_reference_summary(self):
        summary = json.loads((PROJECT / "processed" / "baseline_summary.json").read_text())
        self.assertEqual(summary["workload_count"], 36)
        self.assertEqual(summary["optimized_beats_scalar_count"], 36)
        self.assertGreater(summary["optimized_over_scalar_gmean"], 1.0)
        self.assertLess(summary["optimized_relative_to_blis_gmean"], 1.0)

    def test_candidate_paths_match(self):
        summary = json.loads((PROJECT / "processed" / "measurement_summary.json").read_text())
        self.assertEqual(summary["compile_failure_count"], 0)
        self.assertTrue(summary["all_candidate_predictions_match"])

    def test_formal_tuning_matrix(self):
        status = json.loads((PROJECT / "processed" / "tuning_status.json").read_text())
        self.assertEqual(status["run_count"], 680)
        self.assertEqual(status["trace_count"], 17000)
        self.assertTrue(status["all_valid"])
        self.assertGreaterEqual(status["duplicate_evaluations"], 0)

    def test_holdout_records_empty_space_fallback(self):
        data = rows(PROJECT / "processed" / "holdout_zero_shot.csv")
        self.assertEqual(len(data), 48)
        self.assertTrue(all(row["correct"].lower() == "true" for row in data))
        fallback = [row for row in data if row["empty_space_fallback"].lower() == "true"]
        self.assertTrue(fallback)
        self.assertTrue(all(row["selected_from_method"] in {"B1", "B2", "B3"} for row in fallback))

    def test_required_tables_and_figures_exist(self):
        for number in range(1, 5):
            self.assertTrue(list((PROJECT / "tables").glob(f"table6-{number}_*.csv")))
            self.assertTrue(list((PROJECT / "tables").glob(f"table6-{number}_*.tex")))
        for number in range(1, 12):
            for suffix in ("svg", "pdf", "tiff", "png"):
                self.assertTrue(list((PROJECT / "figures").glob(f"fig6-{number}_*.{suffix}")))

    def test_claim_boundary_is_explicit(self):
        summary = json.loads((PROJECT / "processed" / "chapter6_summary.json").read_text())
        self.assertEqual(summary["RQ6"]["additional_dtype_performance"], "not_run")
        self.assertEqual(summary["RQ6"]["cross_host_performance"], "not_run")
        self.assertIn("Single-thread", summary["claim_boundary"])

    def test_chapter3_human_signoff_is_complete(self):
        summary = json.loads((PROJECT / "processed" / "chapter6_summary.json").read_text())
        self.assertEqual(summary["RQ1"]["machine_check_pass_ratio"], 1.0)
        self.assertEqual(summary["RQ1"]["human_signoff_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
