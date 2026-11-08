#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

import yaml


PROJECT_DIR = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Chapter3ArtifactTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = json.loads((PROJECT_DIR / "data" / "facts.json").read_text())["facts"]
        cls.contracts = yaml.safe_load((PROJECT_DIR / "data" / "microkernel_contracts.yaml").read_text())["contracts"]
        cls.rules = yaml.safe_load((PROJECT_DIR / "data" / "expert_rules.yaml").read_text())["rules"]
        cls.raw = read_csv(PROJECT_DIR / "raw" / "preliminary_aot.csv")

    def test_atomic_fact_count(self) -> None:
        self.assertEqual(len(self.facts), 22)

    def test_fact_dtypes(self) -> None:
        self.assertEqual({fact["dtype"] for fact in self.facts}, {"f32", "f64"})

    def test_fact_ids_are_unique(self) -> None:
        ids = [fact["fact_id"] for fact in self.facts]
        self.assertEqual(len(ids), len(set(ids)))

    def test_fact_required_fields_are_complete(self) -> None:
        required = set(json.loads((PROJECT_DIR / "schemas" / "fact.schema.json").read_text())["required"])
        self.assertTrue(all(required <= set(fact) for fact in self.facts))

    def test_every_fact_is_source_traceable(self) -> None:
        self.assertTrue(all(fact["source_file"] and fact["source_line"] > 0 for fact in self.facts))

    def test_two_real_contracts_exist(self) -> None:
        self.assertEqual(len(self.contracts), 2)

    def test_f32_contract_shape(self) -> None:
        contract = next(item for item in self.contracts if item["dtype"] == "f32")
        self.assertEqual((contract["mr"], contract["nr"]), (6, 16))

    def test_f64_contract_shape(self) -> None:
        contract = next(item for item in self.contracts if item["dtype"] == "f64")
        self.assertEqual((contract["mr"], contract["nr"]), (6, 8))

    def test_contract_separates_kernel_and_adapter(self) -> None:
        self.assertTrue(all("kernel_requirements" in item and "adapter_capabilities" in item for item in self.contracts))

    def test_five_required_rule_categories(self) -> None:
        self.assertEqual(
            {rule["category"] for rule in self.rules},
            {"register_blocking", "cache_blocking", "packing", "vectorization", "tail_and_fallback"},
        )

    def test_rule_fact_references_resolve(self) -> None:
        known = {fact["fact_id"] for fact in self.facts}
        self.assertTrue(all(set(rule["source_fact_ids"]) <= known for rule in self.rules))

    def test_conflicts_are_not_silent(self) -> None:
        rows = read_csv(PROJECT_DIR / "data" / "conflicts.csv")
        self.assertGreater(len(rows), 0)
        self.assertTrue(all(row["silent_override"] == "false" for row in rows))

    def test_manual_review_signoff_is_complete_and_explicit(self) -> None:
        rows = read_csv(PROJECT_DIR / "verification" / "manual_verification.csv")
        self.assertEqual(len(rows), 16)
        self.assertTrue(all(row["machine_check"] == "pass" for row in rows))
        self.assertTrue(all(row["human_status"] == "verified" for row in rows))
        self.assertTrue(all(row["human_reviewer"] == "thesis_author" for row in rows))
        signoffs = json.loads(
            (PROJECT_DIR / "verification" / "human_signoffs.json").read_text(encoding="utf-8")
        )["signoffs"]
        self.assertEqual({row["case_id"] for row in rows}, {row["case_id"] for row in signoffs})

    def test_ambiguity_register_is_nonempty(self) -> None:
        rows = read_csv(PROJECT_DIR / "data" / "ambiguities.csv")
        self.assertGreaterEqual(len(rows), 5)

    def test_preliminary_shape_count(self) -> None:
        self.assertEqual(len({row["shape_id"] for row in self.raw}), 8)

    def test_preliminary_raw_row_count(self) -> None:
        self.assertEqual(len(self.raw), 72)

    def test_all_attempted_candidates_compile(self) -> None:
        attempted = [row for row in self.raw if row["candidate_kind"] == "sample"]
        self.assertEqual(len(attempted), 48)
        self.assertTrue(all(row["compile_status"] == "pass" for row in attempted))

    def test_all_compiled_candidates_are_correct(self) -> None:
        attempted = [row for row in self.raw if row["candidate_kind"] == "sample"]
        self.assertTrue(all(row["correctness_status"] == "pass" for row in attempted))

    def test_replacement_boundary_is_observed(self) -> None:
        attempted = [row for row in self.raw if row["candidate_kind"] == "sample"]
        self.assertTrue(all(row["microkernel_replaced"] == "false" for row in attempted))
        self.assertTrue(all(row["execution_path"] == "fallback" for row in attempted))

    def test_normalized_performance_is_bounded(self) -> None:
        values = [float(row["normalized_to_shape_best"]) for row in self.raw if row["candidate_kind"] == "sample"]
        self.assertTrue(all(0.0 < value <= 1.0 for value in values))

    def test_anchor_observation_is_fallback(self) -> None:
        anchor = next(row for row in self.raw if row["case_id"] == "anchor_192x256x256_anchor")
        self.assertEqual(anchor["status"], "FALLBACK_PASS")
        self.assertEqual(anchor["correctness_status"], "pass")

    def test_required_figures_exist(self) -> None:
        for index, stem in enumerate(
            (
                "fig3-1_preliminary_distribution",
                "fig3-2_fact_contract_rule_boundary",
                "fig3-3_evidence_normalization_flow",
                "fig3-4_provenance_case",
            ),
            1,
        ):
            with self.subTest(figure=index):
                self.assertGreater((PROJECT_DIR / "figures" / f"{stem}.pdf").stat().st_size, 1000)

    def test_r_is_the_registered_figure_backend(self) -> None:
        runner = (PROJECT_DIR / "scripts" / "run_chapter3.py").read_text(encoding="utf-8")
        figure_script = PROJECT_DIR / "scripts" / "plot_chapter3_figures.R"
        self.assertTrue(figure_script.is_file())
        self.assertIn('run_r("plot_chapter3_figures.R")', runner)
        qa = json.loads((PROJECT_DIR / "figures" / "figure_qa.json").read_text(encoding="utf-8"))
        self.assertTrue(all(item["backend"] == "R" for item in qa.values()))

    def test_required_tables_exist(self) -> None:
        for index in range(1, 4):
            matches = list((PROJECT_DIR / "tables").glob(f"table3-{index}_*.md"))
            self.assertEqual(len(matches), 1)


if __name__ == "__main__":
    unittest.main()
