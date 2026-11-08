from __future__ import annotations

import csv
import hashlib
import json
import os
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[3]
TEST_MODE = os.environ.get("CGO_EXTENSION_TEST_MODE", "all")


def requires_mode(mode: str):
    return unittest.skipUnless(
        TEST_MODE in ("all", mode),
        f"{mode} artifact checks are disabled in {TEST_MODE} mode",
    )


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path):
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CgoExtensionTests(unittest.TestCase):
    def test_pass_is_typed_for_f32_and_f64(self):
        source = (
            REPO / "midend" / "lib" / "Conversion" / "MatMulOptimization"
            / "MatMulBlisMicrokernel.cpp"
        ).read_text(encoding="utf-8")
        self.assertIn("matching f32 or f64 element types", source)
        self.assertIn("MemRefType::get({tileM / mr, tileK, mr}, elementType)", source)
        self.assertNotIn("getF32FloatAttr", source)

    def test_runtime_has_both_contract_wrappers(self):
        source = (PROJECT / "runtime" / "blis_microkernel_adapter.cpp").read_text(
            encoding="utf-8"
        )
        for symbol in (
            "buddy_blis_sgemm_6x16",
            "buddy_blis_sgemm_6x16_fringe",
            "buddy_blis_dgemm_6x8",
            "buddy_blis_dgemm_6x8_fringe",
        ):
            self.assertIn(symbol, source)

    def test_optuna_is_pinned(self):
        config = load_json(PROJECT / "data" / "experiment_config.json")
        self.assertEqual(config["optuna"]["version"], "4.9.0")
        self.assertEqual(config["optuna"]["duplicate_policy"], "prune_and_resample_until_unique_budget")

    @requires_mode("smoke")
    def test_f64_smoke_covers_direct_and_adapt(self):
        summary = load_json(PROJECT / "processed" / "f64_smoke_summary.json")
        self.assertEqual(summary["status"], "PASS")
        self.assertGreater(summary["observed_paths"].get("direct", 0), 0)
        self.assertGreater(summary["observed_paths"].get("adapt", 0), 0)
        self.assertTrue(summary["all_predictions_match"])

    @requires_mode("smoke")
    def test_true_online_smoke_has_no_objective_cache(self):
        traces = load_csv(PROJECT / "raw" / "true_online_smoke_traces.csv")
        self.assertEqual(len(traces), 20)
        for row in traces:
            self.assertEqual(row["fresh_process"].lower(), "true")
            self.assertEqual(row["objective_cache_hit"].lower(), "false")
            self.assertEqual(int(row["revealed_before_selection"]), int(row["iteration"]) - 1)

    @requires_mode("smoke")
    def test_optuna_smoke_counts_unique_budget(self):
        traces = load_csv(PROJECT / "raw" / "optuna_smoke_traces.csv")
        callbacks = load_csv(PROJECT / "raw" / "optuna_smoke_callbacks.csv")
        self.assertEqual(len(traces), 5)
        self.assertEqual(len({row["candidate_id"] for row in traces}), 5)
        self.assertGreater(len(callbacks), len(traces))
        self.assertTrue(any(row["state"] == "PRUNED_DUPLICATE" for row in callbacks))

    @requires_mode("formal")
    def test_multisource_keeps_hard_contracts_separate(self):
        summary = load_json(PROJECT / "processed" / "multisource_summary.json")
        self.assertEqual(summary["status"], "PASS")
        self.assertFalse(summary["incompatible_hard_contracts_merged"])
        self.assertFalse(summary["openblas_runtime_derived_r_fabricated"])

    @requires_mode("formal")
    def test_formal_f64_matrix_is_complete(self):
        summary = load_json(PROJECT / "processed" / "f64_contract_summary.json")
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["workloads"], 36)
        self.assertEqual(summary["trial_rows"], 36 * 29 * 3)
        self.assertTrue(summary["all_predictions_match"])

    @requires_mode("formal")
    def test_formal_live_protocols_use_fresh_unique_objectives(self):
        online = load_csv(PROJECT / "raw" / "true_online_traces.csv")
        optuna = load_csv(PROJECT / "raw" / "optuna_traces.csv")
        self.assertEqual(len(online), 12 * 4 * 5 * 25)
        self.assertEqual(len(optuna), 12 * 5 * 25)
        for rows in (online, optuna):
            self.assertTrue(all(row["fresh_process"].lower() == "true" for row in rows))
            self.assertTrue(all(row["objective_cache_hit"].lower() == "false" for row in rows))
        groups = {}
        for row in optuna:
            groups.setdefault((row["workload_id"], row["seed"]), []).append(row)
        self.assertTrue(all(len({row["candidate_id"] for row in rows}) == 25 for rows in groups.values()))

    @requires_mode("formal")
    def test_formal_manifest_hashes_outputs(self):
        manifest = load_json(PROJECT / "provenance" / "cgo_extension_manifest.json")
        for name, expected in manifest["outputs"].items():
            path = Path(name)
            self.assertTrue(path.is_file())
            self.assertEqual(sha256(path), expected)


if __name__ == "__main__":
    unittest.main()
