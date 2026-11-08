#!/usr/bin/env python3
"""Protocol, generator, package, and static ELF tests for external validation."""

from __future__ import annotations

import hashlib
import csv
import json
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import unittest
from collections import defaultdict
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
EXPERIMENTS = PROJECT.parent
sys.path.insert(0, str(PROJECT / "scripts"))

from build_k230_external_package import build_matrix  # noqa: E402
from import_i9_external_results import audit_archive  # noqa: E402
from run_k230_external_via_serial import protocol, validate_rows  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ExternalValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(
            (PROJECT / "data" / "experiment_config.json").read_text(encoding="utf-8")
        )
        cls.workloads, cls.candidates, cls.matrix = build_matrix()
        cls.by_workload = defaultdict(list)
        for row in cls.matrix:
            cls.by_workload[row["workload_id"]].append(row)

    def test_protocol_is_frozen(self):
        self.assertEqual(self.config["protocol_status"], "frozen_before_external_measurement")

    def test_transformer_workload_count(self):
        self.assertEqual(len(self.workloads), 10)

    def test_transformer_has_regular_and_fringe_shapes(self):
        self.assertTrue(any(row["family"] == "model_rect" for row in self.workloads))
        self.assertTrue(any(row["family"] == "tail" for row in self.workloads))

    def test_k230_candidate_count(self):
        self.assertEqual(len(self.candidates), 16)
        self.assertEqual(len({row["id"] for row in self.candidates}), 16)

    def test_k230_matrix_complete(self):
        self.assertEqual(len(self.matrix), len(self.workloads) * len(self.candidates))

    def test_every_workload_has_at_least_ten_executable_candidates(self):
        for workload_id, rows in self.by_workload.items():
            self.assertGreaterEqual(
                sum(bool(row["executable"]) for row in rows), 10, workload_id
            )

    def test_runtime_never_activates_rejected_candidate(self):
        self.assertTrue(
            all(row["predicted_path"] != "reject" for row in self.matrix if row["executable"])
        )

    def test_regular_shapes_have_direct_candidates(self):
        regular = {row["id"] for row in self.workloads if row["family"] == "model_rect"}
        for workload_id in regular:
            self.assertTrue(
                any(row["executable"] and row["predicted_path"] == "direct"
                    for row in self.by_workload[workload_id])
            )

    def test_fringe_shapes_use_adapt(self):
        fringe = {row["id"] for row in self.workloads if row["family"] == "tail"}
        for workload_id in fringe:
            self.assertTrue(
                all(row["predicted_path"] == "adapt"
                    for row in self.by_workload[workload_id] if row["executable"])
            )

    def test_openblas_contract_descriptors_propagate(self):
        active = [row for row in self.matrix if row["executable"]]
        self.assertTrue(all(row["pack_layout"] == "openblas_rvv_8x8_panel" for row in active))
        self.assertTrue(
            all(row["call_convention"] == "OpenBLAS internal GEMM kernel ABI" for row in active)
        )

    def test_k230_parameters_are_live(self):
        active = [row for row in self.matrix if row["executable"]]
        for parameter in ("tile_m", "tile_n", "tile_k"):
            self.assertGreater(len({int(row[parameter]) for row in active}), 1, parameter)

    def test_generator_freeze_matches(self):
        freeze = json.loads(
            (PROJECT / "provenance" / "generator_freeze.json").read_text(encoding="utf-8")
        )
        generator = EXPERIMENTS / "chapter4_space" / "scripts" / "chapter4lib.py"
        self.assertEqual(freeze["sha256"], sha256(generator))

    def test_k230_elf_static_manifest(self):
        manifest = json.loads(
            (PROJECT / "provenance" / "k230_external_manifest.json").read_text(encoding="utf-8")
        )
        self.assertTrue(manifest["elf"]["static"])
        self.assertEqual(manifest["elf"]["entry_point"], "0x200000000")
        self.assertGreater(manifest["elf"]["rvv_instruction_matches"], 0)
        self.assertIn("sgemm_kernel", manifest["elf"]["required_symbols"])
        self.assertIn("cblas_sgemm", manifest["elf"]["required_symbols"])

    def test_k230_elf_hash_matches(self):
        manifest = json.loads(
            (PROJECT / "provenance" / "k230_external_manifest.json").read_text(encoding="utf-8")
        )
        elf = Path(manifest["elf"]["path"])
        self.assertEqual(manifest["elf"]["sha256"], sha256(elf))

    def test_i9_physical_formal_result_passes_strict_import_audit(self):
        archive = (
            PROJECT
            / "returned"
            / "i9"
            / "chapter6-i9-result-20260722T085806Z.tar.gz"
        )
        summary, rows = audit_archive(archive)
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["correctness_rows"], 870)
        self.assertEqual(summary["candidate_measurements"], 280)
        self.assertEqual(summary["measurement_groups"], 290)
        self.assertEqual(summary["unique_candidate_binaries"], 86)
        self.assertEqual(summary["executables_verified"], 87)
        self.assertEqual(summary["internal_manifest_outputs_verified"], 11)
        self.assertEqual(len(rows), 10)
        self.assertEqual(summary["generated_wins"], 0)
        self.assertLess(summary["generated_relative_to_blis_ci95"][1], 1.0)
        self.assertLess(
            summary["sensitivity_generated_relative_to_blis_ci95"][1], 1.0
        )
        self.assertIsNone(summary["pre_registered_i9_cv_gate"])
        self.assertEqual(
            summary["sensitivity_excluded_workloads"], ["gate_up_prefill_m32"]
        )
        self.assertLess(summary["max_projection_error"], 2.0e-3)
        self.assertEqual(summary["perf_measurements_available"], 0)
        self.assertEqual(summary["expert_plus_data_significant_benefits"], 0)
        self.assertEqual(summary["expert_performance_increment_claim"], "STOP")

    def test_k230_archive_contains_board_entrypoint(self):
        archive = PROJECT / "build" / "packages" / "chapter6-k230-openblas-external-validation.tar.gz"
        with tarfile.open(archive, "r:gz") as bundle:
            names = set(bundle.getnames())
        root = "chapter6-k230-openblas-external-validation"
        self.assertIn(f"{root}/board/run_k230_external_validation.sh", names)
        self.assertIn(f"{root}/scripts/run_k230_external_via_serial.py", names)
        self.assertIn(
            f"{root}/build/k230_external/k230_openblas_contract_pool.elf", names
        )

    def test_k230_serial_protocol_covers_every_frozen_result(self):
        frozen = protocol(
            PROJECT / "processed" / "k230_candidate_matrix.json", 3
        )
        self.assertEqual(len(frozen["workloads"]), 10)
        self.assertEqual(len(frozen["active"]), 133)
        self.assertEqual(frozen["contract_rows"], 399)
        self.assertEqual(frozen["baseline_rows"], 30)
        self.assertEqual(frozen["total_rows"], 429)

        rows = []
        for (workload_id, candidate_id), candidate in sorted(
            frozen["active"].items()
        ):
            workload = frozen["workloads"][workload_id]
            for trial in range(3):
                rows.append({
                    "variant": "contract_adapter",
                    "candidate_id": candidate_id,
                    "predicted_path": candidate["predicted_path"],
                    "workload_id": workload_id,
                    "m": str(workload["m"]),
                    "k": str(workload["k"]),
                    "n": str(workload["n"]),
                    "tile_m": str(candidate["tile_m"]),
                    "tile_n": str(candidate["tile_n"]),
                    "tile_k": str(candidate["tile_k"]),
                    "trial": str(trial),
                    "correct": "1",
                })
        for workload_id, workload in sorted(frozen["workloads"].items()):
            for trial in range(3):
                rows.append({
                    "variant": "openblas_full",
                    "candidate_id": "openblas_full",
                    "predicted_path": "library",
                    "workload_id": workload_id,
                    "m": str(workload["m"]),
                    "k": str(workload["k"]),
                    "n": str(workload["n"]),
                    "tile_m": "0",
                    "tile_n": "0",
                    "tile_k": "0",
                    "trial": str(trial),
                    "correct": "1",
                })
        validate_rows(rows, frozen)
        with self.assertRaisesRegex(RuntimeError, "captured 428 CSV rows"):
            validate_rows(rows[:-1], frozen)

    def test_k230_physical_full_pool_result_passes_quality_gates(self):
        summary = json.loads(
            (PROJECT / "processed" / "k230_external_summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["workloads"], 10)
        self.assertEqual(summary["correctness_rows"], 429)
        self.assertEqual(summary["measurement_groups"], 143)
        self.assertEqual(summary["adapter_wins"], 0)
        self.assertLess(summary["adapter_relative_to_openblas_ci95"][1], 1.0)
        self.assertLess(summary["best_adapter_max_trial_cv"], 0.01)
        self.assertLess(summary["openblas_max_trial_cv"], 0.01)
        self.assertLess(summary["max_projection_error"], 2.0e-3)

    def test_k230_c_adapter_packing_and_fringe_on_host_stub(self):
        source = PROJECT / "runtime" / "k230_openblas_contract_bench.c"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "cblas.h").write_text(
                textwrap.dedent(
                    """
                    #ifndef TEST_CBLAS_H
                    #define TEST_CBLAS_H
                    typedef int blasint;
                    enum CBLAS_ORDER { CblasRowMajor = 101, CblasColMajor = 102 };
                    enum CBLAS_TRANSPOSE { CblasNoTrans = 111, CblasTrans = 112 };
                    void cblas_sgemm(const enum CBLAS_ORDER, const enum CBLAS_TRANSPOSE,
                                     const enum CBLAS_TRANSPOSE, const blasint,
                                     const blasint, const blasint, const float,
                                     const float *, const blasint, const float *,
                                     const blasint, const float, float *, const blasint);
                    #endif
                    """
                ),
                encoding="ascii",
            )
            (root / "k230_external_config.h").write_text(
                textwrap.dedent(
                    """
                    #ifndef K230_EXTERNAL_CONFIG_H
                    #define K230_EXTERNAL_CONFIG_H
                    #define K230_CONTRACT_MR 8
                    #define K230_CONTRACT_NR 8
                    #define K230_WORKLOAD_COUNT 1
                    #define K230_CANDIDATE_COUNT 1
                    typedef struct { const char *id; int m; int k; int n; } k230_workload_t;
                    typedef struct { const char *id; int tile_m; int tile_n; int tile_k; } k230_candidate_t;
                    static const k230_workload_t k230_workloads[] = {{"fringe", 9, 11, 10}};
                    static const k230_candidate_t k230_candidates[] = {{"tile", 8, 8, 8}};
                    static const char *k230_predicted_paths[1][1] = {{"adapt"}};
                    static const unsigned char k230_candidate_active[1][1] = {{1}};
                    #endif
                    """
                ).strip() + "\n",
                encoding="ascii",
            )
            stub = root / "openblas_stub.c"
            stub.write_text(
                textwrap.dedent(
                    """
                    #include <stdlib.h>
                    #include <cblas.h>

                    static int width(long remaining) {
                      if (remaining >= 8) return 8;
                      if (remaining >= 4) return 4;
                      if (remaining >= 2) return 2;
                      return 1;
                    }

                    int sgemm_kernel(long M, long N, long K, float alpha, float *A,
                                     float *B, float *C, long ldc) {
                      float *ua = calloc((size_t)M * K, sizeof(float));
                      float *ub = calloc((size_t)K * N, sizeof(float));
                      size_t pos = 0;
                      for (long base = 0; base < M;) {
                        int block = width(M - base);
                        for (long p = 0; p < K; ++p)
                          for (int r = 0; r < block; ++r)
                            ua[(base + r) * K + p] = A[pos++];
                        base += block;
                      }
                      pos = 0;
                      for (long base = 0; base < N;) {
                        int block = width(N - base);
                        for (long p = 0; p < K; ++p)
                          for (int column = 0; column < block; ++column)
                            ub[p * N + base + column] = B[pos++];
                        base += block;
                      }
                      for (long j = 0; j < N; ++j)
                        for (long i = 0; i < M; ++i)
                          for (long p = 0; p < K; ++p)
                            C[j * ldc + i] += alpha * ua[i * K + p] * ub[p * N + j];
                      free(ua);
                      free(ub);
                      return 0;
                    }

                    void cblas_sgemm(const enum CBLAS_ORDER order,
                                     const enum CBLAS_TRANSPOSE trans_a,
                                     const enum CBLAS_TRANSPOSE trans_b,
                                     const blasint M, const blasint N, const blasint K,
                                     const float alpha, const float *A, const blasint lda,
                                     const float *B, const blasint ldb, const float beta,
                                     float *C, const blasint ldc) {
                      (void)order; (void)trans_a; (void)trans_b;
                      for (blasint i = 0; i < M; ++i)
                        for (blasint j = 0; j < N; ++j) {
                          float value = beta * C[(size_t)i * ldc + j];
                          for (blasint p = 0; p < K; ++p)
                            value += alpha * A[(size_t)i * lda + p] * B[(size_t)p * ldb + j];
                          C[(size_t)i * ldc + j] = value;
                        }
                    }
                    """
                ),
                encoding="ascii",
            )
            executable = root / "adapter_test"
            compiled = subprocess.run(
                [
                    "gcc", "-std=c11", "-O0", "-I", str(root),
                    str(source), str(stub), "-lm", "-o", str(executable),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            completed = subprocess.run(
                [str(executable)],
                check=True,
                capture_output=True,
                text=True,
                env={"K230_REPS": "1", "K230_WARMUPS": "1"},
            )
            output_rows = list(csv.DictReader(completed.stdout.splitlines()))
            self.assertEqual(len(output_rows), 2)
            self.assertTrue(all(row["correct"] == "1" for row in output_rows))
            adapter = next(row for row in output_rows if row["variant"] == "contract_adapter")
            self.assertGreater(int(adapter["fringe_calls"]), 0)
            self.assertGreater(int(adapter["k_tail_calls"]), 0)


if __name__ == "__main__":
    unittest.main()
