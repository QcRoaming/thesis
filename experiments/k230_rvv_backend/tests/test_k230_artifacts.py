#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

from import_board_results import summarize_results
from run_board_via_serial import CSV_HEADER, extract_csv


class K230ArtifactTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((PROJECT / "provenance/elf_manifest.json").read_text())
        cls.deployment = json.loads((PROJECT / "provenance/deployment_manifest.json").read_text())

    def test_status_is_honest_before_board_execution(self) -> None:
        self.assertIn(
            self.manifest["status"],
            {"elf_ready_awaiting_board_results", "board_results_imported"},
        )
        if self.manifest["status"] == "elf_ready_awaiting_board_results":
            self.assertIsNone(self.manifest["board_results"])
        else:
            self.assertIsNotNone(self.manifest["board_results"])

    def test_three_static_riscv_elfs(self) -> None:
        self.assertEqual(len(self.manifest["artifacts"]), 3)
        for artifact in self.manifest["artifacts"]:
            path = Path(artifact["path"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), artifact["sha256"])
            self.assertTrue(artifact["static"])
            self.assertIn("RISC-V", artifact["elf_header"])
            self.assertEqual(int(artifact["entry_point"], 16), 0x200000000)

    def test_rvv_binaries_contain_vector_instructions(self) -> None:
        artifacts = {row["name"]: row for row in self.manifest["artifacts"]}
        self.assertGreater(artifacts["k230_gemm_rvv.elf"]["rvv_instruction_matches"], 0)
        self.assertGreater(artifacts["k230_gemm_openblas.elf"]["rvv_instruction_matches"], 0)
        # Static musl may contribute a few vector opcodes outside the benchmark.
        self.assertLess(
            artifacts["k230_gemm_scalar.elf"]["rvv_instruction_matches"],
            artifacts["k230_gemm_rvv.elf"]["rvv_instruction_matches"],
        )

    def test_openblas_elf_retains_sgemm_and_packing_symbols(self) -> None:
        artifacts = {row["name"]: row for row in self.manifest["artifacts"]}
        self.assertEqual(
            artifacts["k230_gemm_openblas.elf"]["required_symbols"],
            ["cblas_sgemm", "sgemm_kernel", "sgemm_oncopy", "sgemm_otcopy"],
        )

    def test_official_sdk_and_openblas_are_pinned(self) -> None:
        self.assertRegex(self.manifest["sdk"]["revision"], r"^[0-9a-f]{40}$")
        self.assertRegex(self.manifest["openblas"]["revision"], r"^[0-9a-f]{40}$")
        self.assertEqual(self.manifest["toolchain"]["archive_md5"], "e6c0ce95844595eb0153db8dfaa74bcb")

    def test_openblas_compatibility_is_audited(self) -> None:
        compatibility = self.manifest["openblas"]["rvv_intrinsic_compatibility"]
        header = Path(compatibility["header"])
        self.assertEqual(hashlib.sha256(header.read_bytes()).hexdigest(), compatibility["header_sha256"])
        self.assertGreater(compatibility["mapped_intrinsic_count"], 0)
        self.assertGreater(compatibility["mapped_tuple_type_count"], 0)
        self.assertIn("unmodified", compatibility["strategy"])

    def test_deployment_archive_is_hashed(self) -> None:
        archive = Path(self.deployment["path"])
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), self.deployment["sha256"])
        self.assertGreater(archive.stat().st_size, 0)
        self.assertEqual(len([name for name in self.deployment["members"] if name.endswith(".elf")]), 3)

    def test_board_import_keeps_binary_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result_dir = Path(temporary)
            cases = {
                "k230_gemm_scalar.csv": ("scalar", 1.0),
                "k230_gemm_rvv.csv": ("rvv", 2.0),
                "k230_gemm_openblas.csv": ("openblas", 3.0),
            }
            for filename, (binary, gflops) in cases.items():
                with (result_dir / filename).open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(
                        stream,
                        fieldnames=["binary", "candidate", "workload", "time_seconds", "gflops", "correct"],
                    )
                    writer.writeheader()
                    writer.writerow(
                        {
                            "binary": binary, "candidate": "scalar", "workload": "anchor",
                            "time_seconds": "1.0", "gflops": str(gflops), "correct": "1",
                        }
                    )
            summary = summarize_results(result_dir)
            self.assertEqual(summary["aggregate_count"], 3)
            medians = {row["binary"]: row["median_gflops"] for row in summary["aggregates"]}
            self.assertEqual(medians, {"openblas": 3.0, "rvv": 2.0, "scalar": 1.0})
            self.assertEqual(summary["comparisons"]["rvv_best_vs_scalar"]["workloads"], 0)

    def test_imported_board_comparisons_are_consistent(self) -> None:
        if self.manifest["status"] != "board_results_imported":
            self.skipTest("physical-board results have not been imported")
        summary = json.loads((PROJECT / "processed/k230_board_summary.json").read_text())
        comparisons = summary["comparisons"]
        self.assertEqual(summary["row_count"], 560)
        self.assertTrue(summary["all_correct"])
        self.assertEqual(len(summary["metadata_files"]), 2)
        self.assertEqual(comparisons["rvv_best_vs_scalar"]["workloads"], 8)
        self.assertGreater(comparisons["rvv_best_vs_scalar"]["geomean_speedup"], 1.0)
        self.assertEqual(comparisons["openblas_full_vs_scalar"]["workloads"], 8)
        self.assertGreater(comparisons["openblas_full_vs_scalar"]["geomean_speedup"], 1.0)

    def test_serial_capture_filters_shell_and_stderr_lines(self) -> None:
        payload = (
            b"/sharefs/k230_gemm_scalar.elf\r\n"
            b"[scalar] scalar 192x256x256\r\n"
            + CSV_HEADER.encode()
            + b"\r\n"
            b"scalar,scalar,scalar,none,anchor,192,256,256,16,8,64,0,"
            b"0.1,0.25,1e-06,1\r\n"
            b"msh />"
        )
        csv_text, rows = extract_csv(payload, "scalar")
        self.assertEqual(rows, 1)
        self.assertIn("scalar,scalar,scalar,none,anchor", csv_text)


if __name__ == "__main__":
    unittest.main()
