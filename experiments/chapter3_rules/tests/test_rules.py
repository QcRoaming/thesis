#!/usr/bin/env python3

from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from extract_blis_facts import DEFAULT_BLIS_ROOT, extract_fact  # noqa: E402
from rulelib import (  # noqa: E402
    assess_candidate,
    compatible_contract,
    load_contracts,
    load_tasks,
)


class RuleMvpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tasks = load_tasks(PROJECT_DIR / "data" / "gemm_tasks.yaml")
        cls.contracts = load_contracts(
            PROJECT_DIR / "data" / "microkernel_contracts.yaml"
        )
        cls.aligned = next(task for task in cls.tasks if "aligned" in task.id)
        cls.edge = next(task for task in cls.tasks if "edge" in task.id)
        cls.contract = compatible_contract(cls.aligned, cls.contracts)

    def classify(self, task, tile_m, tile_n, tile_k, pack=True):
        return assess_candidate(
            task,
            self.contract,
            tile_m=tile_m,
            tile_n=tile_n,
            tile_k=tile_k,
            pack_a=pack,
            pack_b=pack,
            vectorize=True,
        )[0]

    def test_direct_candidate(self) -> None:
        self.assertEqual(self.classify(self.aligned, 24, 32, 64), "direct")

    def test_edge_candidate_requires_adapter(self) -> None:
        self.assertEqual(self.classify(self.edge, 24, 32, 64), "adapt")

    def test_unaligned_candidate_falls_back(self) -> None:
        self.assertEqual(self.classify(self.aligned, 32, 32, 64), "fallback")

    def test_invalid_vector_tile_is_rejected(self) -> None:
        self.assertEqual(self.classify(self.aligned, 24, 12, 64), "reject")

    def test_extractor_cross_checks_kernel_shape(self) -> None:
        fact, contract = extract_fact(DEFAULT_BLIS_ROOT, "haswell", "f32")
        self.assertEqual((fact["microkernel"]["mr"], fact["microkernel"]["nr"]), (6, 16))
        self.assertTrue(fact["constraints"]["mr_nr_verified_against_kernel"])
        self.assertEqual(contract["kernel"], "bli_sgemm_haswell_asm_6x16")


if __name__ == "__main__":
    unittest.main()
