import csv
import json
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
CONFIG = json.loads(
    (PROJECT / "data" / "experiment_config.json").read_text(encoding="utf-8")
)
SUMMARY_PATH = PROJECT / "processed" / "go_nogo_summary.json"
RAW_PATH = PROJECT / "raw" / "region_trials.csv"


class TransformerRegionGoNoGoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        with RAW_PATH.open(newline="", encoding="utf-8") as handle:
            cls.rows = list(csv.DictReader(handle))

    def test_strong_baseline_is_frozen(self):
        variants = {entry["id"] for entry in CONFIG["variants"]}
        self.assertEqual(
            variants,
            {
                "independent_blis",
                "concatenated_blis",
                "repacked_a_microkernel",
                "shared_a_microkernel",
            },
        )

    def test_model_dimensions_are_internally_consistent(self):
        model = CONFIG["model"]
        self.assertEqual(
            model["hidden_size"] // model["num_attention_heads"],
            model["head_dim"],
        )
        qkv = next(
            region for region in CONFIG["regions"] if region["id"] == "qkv"
        )
        self.assertEqual(qkv["branch_n"], [896, 128, 128])
        self.assertEqual(model["intermediate_size"], 4864)
        self.assertEqual(CONFIG["microkernel_contract"]["kc"], 256)
        self.assertGreaterEqual(
            CONFIG["microkernel_contract"]["packed_alignment_bytes"], 32
        )

    def test_complete_measurement_matrix(self):
        expected = (
            len(CONFIG["regions"])
            * len(CONFIG["phases"])
            * len(CONFIG["variants"])
            * int(CONFIG["measurement"]["trials"])
        )
        if self.summary["mode"] == "formal_local":
            self.assertEqual(len(self.rows), expected)
        self.assertEqual(self.summary["case_count"], 8)
        self.assertEqual(self.summary["variant_count"], 4)

    def test_all_paths_are_correct(self):
        self.assertTrue(self.summary["all_correct"])
        self.assertTrue(all(row["status"] == "PASS" for row in self.rows))

    def test_shared_packing_count_is_one(self):
        shared = [
            row for row in self.rows if row["variant"] == "shared_a_microkernel"
        ]
        repacked = [
            row for row in self.rows if row["variant"] == "repacked_a_microkernel"
        ]
        self.assertTrue(shared)
        self.assertTrue(
            all(int(row["activation_pack_count"]) == 1 for row in shared)
        )
        self.assertTrue(
            all(
                int(row["activation_pack_count"]) == int(row["branch_count"])
                for row in repacked
            )
        )

    def test_real_blis_microkernel_symbol_is_linked(self):
        symbols = (PROJECT / "reports" / "symbols.log").read_text(encoding="utf-8")
        self.assertIn("bli_sgemm_haswell_asm_6x16", symbols)

    def test_measurement_protocol_is_single_thread_and_interleaved(self):
        source = (PROJECT / "runtime" / "region_fanout_bench.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn("bli_thread_set_thread_impl(BLIS_SINGLE)", source)
        self.assertIn("bli_thread_set_num_threads(1)", source)
        self.assertIn("benchmarkTrial", source)
        measurement = CONFIG["measurement"]
        self.assertEqual(measurement["blis_threads"], 1)
        self.assertEqual(
            measurement["variant_interleaving"], "per_repeat_rotating_order"
        )

    def test_decision_is_machine_readable(self):
        self.assertIn(
            self.summary["decision"],
            {
                "PROVISIONAL_GO_PENDING_SECOND_HOST",
                "NO_GO_STRONG_BASELINE_NOT_BEATEN",
                "INVALID_CORRECTNESS_FAILURE",
            },
        )
        self.assertIn(
            "shared_a_microkernel_vs_concatenated_blis",
            self.summary["criterion_checks"],
        )

    def test_strict_complete_blis_portfolio_is_reported(self):
        comparison = "shared_a_microkernel_vs_best_complete_blis"
        self.assertIn(comparison, self.summary["comparison_summaries"])
        self.assertTrue(
            all(comparison in row for row in self.summary["case_results"])
        )

    def test_packing_only_counterfactual_is_reported(self):
        mechanism = self.summary["packing_reuse_mechanism"]
        self.assertGreaterEqual(
            mechanism["packing_only_ideal_maximum_speedup"], 1.0
        )
        self.assertTrue(
            all(
                row["packing_only_ideal_speedup_vs_repacked"] >= 1.0
                for row in self.summary["case_results"]
            )
        )


if __name__ == "__main__":
    unittest.main()
