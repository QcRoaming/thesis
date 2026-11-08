import json
import re
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


class Chapter5EvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(
            (PROJECT / "processed" / "chapter5_summary.json").read_text(encoding="utf-8")
        )
        cls.results = {row["variant"]: row for row in cls.summary["results"]}

    def test_both_paths_pass(self):
        self.assertEqual(self.results["fallback_vectorized"]["status"], "PASS")
        self.assertEqual(self.results["direct_blis_6x16"]["status"], "PASS")

    def test_direct_path_is_real_replacement(self):
        direct = self.results["direct_blis_6x16"]
        self.assertEqual(direct["observed_path"], "direct")
        self.assertTrue(direct["microkernel_replaced"])
        self.assertTrue(direct["blis_kernel_symbol_present"])
        self.assertGreater(direct["packing_alloc_count"], 0)

    def test_transformed_ir_contains_packing_and_only_real_call(self):
        text = (PROJECT / "build" / "direct_blis_6x16" / "transformed.mlir").read_text(encoding="utf-8")
        self.assertIn("memref<4x64x6xf32>", text)
        self.assertIn("memref<2x64x16xf32>", text)
        self.assertIn("func.call @buddy_blis_sgemm_6x16", text)
        self.assertNotIn("func.call @buddy_microkernel_placeholder", text)
        self.assertNotIn("linalg.matmul", text)

    def test_linked_binary_contains_wrapper_and_blis_kernel(self):
        symbols = (PROJECT / "build" / "direct_blis_6x16" / "06_symbols.log").read_text(encoding="utf-8")
        self.assertRegex(symbols, re.compile(r"\bT buddy_blis_sgemm_6x16$", re.MULTILINE))
        self.assertRegex(symbols, re.compile(r"\bT bli_sgemm_haswell_asm_6x16$", re.MULTILINE))

    def test_wrapper_smoke_passes(self):
        text = (PROJECT / "raw" / "wrapper_smoke.csv").read_text(encoding="utf-8")
        self.assertIn("packed_6x16,67,0.00000000,PASS", text)


if __name__ == "__main__":
    unittest.main()
