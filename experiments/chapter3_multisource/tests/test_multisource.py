#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import yaml


PROJECT = Path(__file__).resolve().parents[1]


class MultiSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts_doc = yaml.safe_load((PROJECT / "data/multisource_facts.yaml").read_text())
        cls.contracts = yaml.safe_load((PROJECT / "data/multisource_contracts.yaml").read_text())["contracts"]
        cls.conflicts = yaml.safe_load((PROJECT / "data/conflicts.yaml").read_text())["conflicts"]
        cls.summary = json.loads((PROJECT / "processed/summary.json").read_text())

    def test_two_independent_sources_and_pinned_revisions(self) -> None:
        self.assertEqual(set(self.facts_doc["sources"]), {"BLIS", "OpenBLAS"})
        for source in self.facts_doc["sources"].values():
            self.assertRegex(source["revision"], r"^[0-9a-f]{40}$")

    def test_expected_backend_specific_tiles(self) -> None:
        facts = {item["id"]: item for item in self.facts_doc["facts"]}
        expected = {
            "blis.haswell.gemm.f32": (6, 16),
            "openblas.haswell.gemm.f32": (8, 4),
            "blis.rv64iv_vlen128.gemm.f32": (16, 4),
            "openblas.riscv64_zvl128b.gemm.f32": (8, 8),
        }
        for fact_id, tile in expected.items():
            kernel = facts[fact_id]["compatibility_knowledge"]["microkernel"]
            self.assertEqual((kernel["mr"], kernel["nr"]), tile)

    def test_contracts_do_not_merge_conflicting_abis(self) -> None:
        self.assertEqual(len(self.contracts), 4)
        self.assertEqual(len({row["fact_id"] for row in self.contracts}), 4)
        self.assertTrue(all(row["compatibility_policy"] == "hard_backend_specific" for row in self.contracts))

    def test_performance_knowledge_is_soft(self) -> None:
        for fact in self.facts_doc["facts"]:
            self.assertEqual(fact["performance_knowledge"]["kind"], "soft_prior")
        performance_conflicts = [row for row in self.conflicts if row["knowledge_class"] == "performance"]
        self.assertEqual(len(performance_conflicts), 2)
        self.assertTrue(all("calibrat" in row["resolution"] for row in performance_conflicts))

    def test_evidence_hashes_match_sources(self) -> None:
        sources = self.facts_doc["sources"]
        for fact in self.facts_doc["facts"]:
            root = Path(sources[fact["library"]]["path"])
            for evidence in fact["evidence"]:
                digest = hashlib.sha256((root / evidence["file"]).read_bytes()).hexdigest()
                self.assertEqual(digest, evidence["sha256"])

    def test_summary_counts(self) -> None:
        self.assertEqual(self.summary["source_count"], 2)
        self.assertEqual(self.summary["fact_count"], 4)
        self.assertEqual(self.summary["contract_count"], 4)
        self.assertEqual(self.summary["conflict_count"], 4)


if __name__ == "__main__":
    unittest.main()
