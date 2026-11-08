from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
import importlib.util
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
EXTERNAL = PROJECT.parent / "chapter6_external_validation"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class ApplicationValidationTests(unittest.TestCase):
    def test_serial_runner_extracts_complete_frozen_matrix(self) -> None:
        path = PROJECT / "scripts" / "run_k230_mlir_via_serial.py"
        spec = importlib.util.spec_from_file_location("k230_serial_runner", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        lines = []
        for case_id in sorted(module.CASES):
            expected_path = "direct" if case_id.startswith("direct") else "adapt"
            for variant in sorted(module.VARIANTS):
                observed = "library" if variant == "openblas_full" else expected_path
                path_match = "0" if variant == "openblas_full" else "1"
                for trial in range(5):
                    lines.append(
                        f"{variant},{case_id},workload,candidate,{expected_path},"
                        f"1,1,1,1,1,1,{trial},0.1,1.0,0.0,1,{observed},"
                        f"{path_match},0,0,0,0,0,1,0,0,1"
                    )
        payload = ("noise\r\n" + "\r\n".join(lines) + "\r\nmsh />").encode()
        csv_text, rows = module.extract_csv(payload, 5)
        self.assertTrue(csv_text.startswith(module.CSV_HEADER))
        self.assertEqual(len(rows), 45)

    def test_qwen_trace_is_complete_for_core_projections(self) -> None:
        summary = read_json(PROJECT / "processed" / "qwen_trace_summary.json")
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["raw_linear_calls"], 338)
        self.assertEqual(summary["raw_core_projection_calls"], 336)
        self.assertEqual(summary["canonical_core_calls"], 192)
        self.assertEqual(summary["canonical_workload_rows"], 8)
        self.assertEqual(summary["core_call_coverage"], 1.0)
        self.assertEqual(summary["core_flop_coverage"], 1.0)
        self.assertLess(summary["all_linear_flop_coverage"], 1.0)

    def test_qwen_trace_matches_frozen_workloads(self) -> None:
        with (PROJECT / "processed" / "qwen_trace_workloads.csv").open(
            newline="", encoding="utf-8"
        ) as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(row["all_frozen_workload_matches"] == "True" for row in rows))
        self.assertEqual({int(row["call_count"]) for row in rows}, {24})
        self.assertEqual({int(row["m"]) for row in rows}, {8, 32})

    def test_k230_closure_static_audit(self) -> None:
        manifest = read_json(
            PROJECT / "provenance" / "k230_mlir_closure_manifest.json"
        )
        self.assertEqual(manifest["status"], "elf_ready_awaiting_board_measurement")
        self.assertEqual(manifest["host_abi_smoke"]["status"], "PASS")
        self.assertEqual(len(manifest["cases"]), 3)
        for case in manifest["cases"]:
            self.assertTrue(all(case["checks"].values()))
        elf = manifest["target_elf"]
        self.assertEqual(int(elf["entry_point"], 16), 0x200000000)
        self.assertGreater(elf["rvv_instruction_matches"], 0)
        self.assertIn("sgemm_kernel", elf["required_symbols"])
        self.assertFalse(manifest["reuse_audit"]["core_generator_modified_for_closure"])
        self.assertFalse(manifest["reuse_audit"]["new_compiler_pass_required"])

    def test_k230_physical_closure_passes_registered_acceptance(self) -> None:
        summary = read_json(
            PROJECT / "processed" / "k230_mlir_closure_summary.json"
        )
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["correctness_rows"], 45)
        self.assertEqual(summary["cases"], 3)
        self.assertEqual(summary["variants"], 3)
        self.assertTrue(summary["parity_acceptance"])
        lower, upper = summary["c_adapter_over_mlir_adapter_ci95"]
        self.assertLessEqual(lower, 1.0)
        self.assertGreaterEqual(upper, 1.0)
        report = (
            PROJECT / "reports" / "application_validation_status.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Physical K230 MLIR closure: **PASS**", report)
        self.assertNotIn("Run the closure ELF on the physical K230", report)

    def test_generator_freeze_is_unchanged(self) -> None:
        freeze = read_json(EXTERNAL / "provenance" / "generator_freeze.json")
        generator = Path(freeze["path"])
        self.assertEqual(sha256(generator), freeze["sha256"])

    def test_transform_ir_retargets_each_adapter(self) -> None:
        manifest = read_json(
            PROJECT / "provenance" / "k230_mlir_closure_manifest.json"
        )
        for case in manifest["cases"]:
            case_dir = PROJECT / "build" / "k230_mlir_closure" / "cases" / case["id"]
            input_text = (case_dir / "input.mlir").read_text(encoding="ascii")
            transformed = (case_dir / "transformed.mlir").read_text(encoding="utf-8")
            llvm_ir = (case_dir / "kernel.ll").read_text(encoding="utf-8")
            self.assertIn("linalg.generic", input_text)
            self.assertIn("transform.annotate", input_text)
            self.assertIn(f"call @{case['adapter_symbol']}", transformed)
            self.assertNotIn("linalg.generic", transformed)
            self.assertIn(case["mlir_entry_symbol"], llvm_ir)

    def test_deployment_archive_matches_manifest(self) -> None:
        deployment = read_json(
            PROJECT / "provenance" / "k230_mlir_closure_deployment.json"
        )
        archive = Path(deployment["path"])
        self.assertTrue(archive.is_file())
        self.assertEqual(sha256(archive), deployment["sha256"])
        with tarfile.open(archive, "r:gz") as bundle:
            names = bundle.getnames()
        self.assertTrue(any(name.endswith("k230_mlir_closure.elf") for name in names))
        self.assertTrue(any(name.endswith("input.mlir") for name in names))
        self.assertTrue(any(name.endswith("kernel.ll") for name in names))

    def test_k230_importer_accepts_complete_synthetic_result(self) -> None:
        cases = read_json(PROJECT / "data" / "k230_mlir_closure_cases.json")["cases"]
        matrix = read_json(EXTERNAL / "processed" / "k230_candidate_matrix.json")["rows"]
        lookup = {(row["workload_id"], row["candidate_id"]): row for row in matrix}
        workloads = {
            row["id"]: row
            for row in read_json(EXTERNAL / "data" / "transformer_workloads.json")["workloads"]
        }
        rows: list[dict[str, object]] = []
        variants = {
            "c_adapter_direct": 0.0100,
            "mlir_transform_adapter": 0.0101,
            "openblas_full": 0.0050,
        }
        adapter_calls = 0
        for case in cases:
            matrix_row = lookup[(case["workload_id"], case["candidate_id"])]
            workload = workloads[case["workload_id"]]
            for variant, elapsed in variants.items():
                for trial in range(2):
                    if variant != "openblas_full":
                        adapter_calls += 1
                    adapt = case["expected_path"] == "adapt"
                    rows.append({
                        "variant": variant,
                        "case_id": case["id"],
                        "workload_id": case["workload_id"],
                        "candidate_id": case["candidate_id"],
                        "expected_path": case["expected_path"],
                        "m": workload["m"], "k": workload["k"], "n": workload["n"],
                        "tile_m": matrix_row["tile_m"],
                        "tile_n": matrix_row["tile_n"],
                        "tile_k": matrix_row["tile_k"],
                        "trial": trial,
                        "time_seconds": elapsed + trial * 0.00001,
                        "gflops": 1.0,
                        "projection_error": 0.0,
                        "correct": 1,
                        "observed_path": "library" if variant == "openblas_full" else case["expected_path"],
                        "path_match": 0 if variant == "openblas_full" else 1,
                        "initialize_seconds": 0.0,
                        "pack_a_seconds": 0.001,
                        "pack_b_seconds": 0.001,
                        "kernel_seconds": 0.007,
                        "scatter_seconds": 0.001,
                        "kernel_calls": 1 if variant != "openblas_full" else 0,
                        "fringe_calls": 1 if adapt and variant != "openblas_full" else 0,
                        "k_tail_calls": 1 if adapt and variant != "openblas_full" else 0,
                        "adapter_calls": adapter_calls,
                    })
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = root / "board_results"
            result.mkdir()
            write_csv(result / "k230_mlir_closure.csv", rows)
            output_root = root / "output"
            subprocess.run(
                [sys.executable, str(PROJECT / "scripts" / "import_k230_mlir_results.py"),
                 str(result), "--output-root", str(output_root)],
                check=True,
                capture_output=True,
                text=True,
            )
            summary = read_json(
                output_root / "processed" / "k230_mlir_closure_summary.json"
            )
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(summary["correctness_rows"], 18)
            self.assertTrue(summary["parity_acceptance"])

    def test_trace_weighted_analyzer_on_synthetic_i9_pool(self) -> None:
        with (PROJECT / "processed" / "qwen_trace_workloads.csv").open(
            newline="", encoding="utf-8"
        ) as stream:
            trace = list(csv.DictReader(stream))
        workloads = sorted({row["workload_id"] for row in trace})
        rows: list[dict[str, object]] = []
        for workload_id in workloads:
            rows.append({
                "workload_id": workload_id, "variant": "B5_blis",
                "candidate_id": "", "median_ms": 1.0, "static_score": "",
            })
            for index in range(10):
                rows.append({
                    "workload_id": workload_id,
                    "variant": f"candidate:c{index}",
                    "candidate_id": f"c{index}",
                    "median_ms": 0.70 + index * 0.02,
                    "static_score": 100.0 - index,
                })
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            i9 = root / "i9"
            write_csv(i9 / "processed" / "i9_transformer_aggregates.csv", rows)
            manifest = {
                "candidate_manifests": {
                    f"c{index}": {"pipeline_ms": 10.0 + index}
                    for index in range(10)
                }
            }
            manifest_path = i9 / "provenance" / "i9_transformer_manifest.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            output_root = root / "output"
            subprocess.run(
                [sys.executable,
                 str(PROJECT / "scripts" / "analyze_trace_weighted_results.py"),
                 "--i9-root", str(i9), "--output-root", str(output_root)],
                check=True,
                capture_output=True,
                text=True,
            )
            summary = read_json(output_root / "processed" / "trace_weighted_summary.json")
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(summary["targets_analyzed"], ["i9_14900"])
            self.assertEqual(summary["policy_run_rows"], 54)
            self.assertEqual(summary["policy_summary_rows"], 22)
            self.assertEqual(summary["guarded_prior_comparison_rows"], 4)

    def test_local_x86_trace_pool_failure_is_complete_and_disclosed(self) -> None:
        root = PROJECT / "targets" / "i7_10750h"
        summary = read_json(root / "processed" / "summary.json")
        self.assertEqual(summary["status"], "FAIL_UNSTABLE")
        self.assertEqual(summary["target"], "i7_10750h_wsl2")
        self.assertEqual(summary["workloads"], 8)
        self.assertEqual(summary["candidate_measurements"], 224)
        self.assertTrue(summary["all_expected_workloads_present"])
        self.assertTrue(summary["common_pool_oracle_invariant"])
        self.assertTrue(summary["all_parameters_audited"])
        self.assertEqual(summary["active_parameter_audits"], 20)
        self.assertEqual(summary["conditionally_eliminated_parameter_audits"], 4)
        self.assertTrue(all(
            values["active"] for values in summary["parameter_liveness"].values()
        ))
        with (root / "raw" / "trials.csv").open(
            newline="", encoding="utf-8"
        ) as stream:
            trials = list(csv.DictReader(stream))
        self.assertEqual(len(trials), 2088)
        self.assertTrue(all(row["status"] == "PASS" for row in trials))
        self.assertTrue(summary["confirmatory_protocol"])
        self.assertEqual(summary["batch_count"], 3)
        self.assertEqual(summary["process_medians_per_variant"], 9)
        self.assertFalse(summary["stability"]["stability_pass"])
        self.assertLess(summary["stability"]["variant_pass_fraction"], 0.95)

    def test_local_x86_measurement_qualification_blocks_remeasurement(self) -> None:
        root = PROJECT / "targets" / "i7_10750h" / "qualification"
        summary = read_json(root / "processed" / "summary.json")
        self.assertEqual(summary["status"], "FAIL_UNQUALIFIED")
        self.assertTrue(summary["qualification_only"])
        self.assertFalse(summary["performance_claims_allowed"])
        self.assertEqual(summary["jobs"], 120)
        self.assertEqual(summary["qualifying_cpus"], [])
        self.assertIsNone(summary["selected_cpu"])
        with (root / "processed" / "cpu_summary.csv").open(
            newline="", encoding="utf-8"
        ) as stream:
            cpus = list(csv.DictReader(stream))
        self.assertEqual(len(cpus), 6)
        self.assertTrue(all(row["qualification_pass"] == "False" for row in cpus))

    def test_weighted_analyzer_rejects_unstable_local_pool(self) -> None:
        completed = subprocess.run(
            [sys.executable,
             str(PROJECT / "scripts" / "analyze_trace_weighted_results.py"),
             "--local-x86-root", str(PROJECT / "targets" / "i7_10750h")],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("FAIL_UNSTABLE", completed.stderr)


if __name__ == "__main__":
    unittest.main()
