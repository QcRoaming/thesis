#!/usr/bin/env python3
"""Unit, boundary, property, and artifact tests for the Chapter 4 prototype."""

from __future__ import annotations

import copy
import csv
import json
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "scripts"))

from chapter4lib import (  # noqa: E402
    Candidate,
    check_candidate,
    conditional_parameters,
    generate_spaces_for_task,
    is_expert_core,
    load_inputs,
    provenance_record,
    rank_and_select_initial,
    raw_candidates,
    score_candidate,
    select_contract,
    select_shell,
)


class Chapter4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inputs = load_inputs(PROJECT)
        cls.tasks = {task["id"]: task for task in cls.inputs["tasks"]}
        cls.candidates = raw_candidates(cls.inputs["space_config"]["raw_domain"])
        cls.anchor = cls.tasks["anchor_192x256x256_f32"]
        cls.tail = cls.tasks["tail_190x250x250_f32"]
        cls.mismatch = cls.tasks["feature_mismatch_192x256x256_f32"]
        cls.f32_contract, _ = select_contract(cls.anchor, cls.inputs["contracts"])
        cls.anchor_spaces, cls.anchor_rows, _ = generate_spaces_for_task(
            cls.anchor, cls.candidates, cls.inputs["contracts"], cls.inputs["space_config"]
        )

    def test_01_raw_space_count(self):
        self.assertEqual(len(self.candidates), 2600)

    def test_02_candidate_ids_unique(self):
        self.assertEqual(len({candidate.id for candidate in self.candidates}), len(self.candidates))

    def test_03_f32_contract_selected(self):
        self.assertEqual(self.f32_contract["id"], "haswell_f32_gemm_6x16")

    def test_04_f64_contract_selected(self):
        task = self.tasks["aligned_192x256x256_f64"]
        contract, _ = select_contract(task, self.inputs["contracts"])
        self.assertEqual(contract["nr"], 8)

    def test_05_feature_mismatch_selects_no_contract(self):
        contract, log = select_contract(self.mismatch, self.inputs["contracts"])
        self.assertIsNone(contract)
        self.assertTrue(all(not row["eligible"] for row in log))

    def test_06_direct_candidate(self):
        decision = check_candidate(Candidate(24, 32, 64, "ab", True), self.anchor, self.f32_contract)
        self.assertEqual(decision.path, "direct")

    def test_07_direct_reason(self):
        decision = check_candidate(Candidate(24, 32, 64, "ab", True), self.anchor, self.f32_contract)
        self.assertEqual(decision.reason_codes, ["DIRECT_CONTRACT_MATCH"])

    def test_08_direct_action(self):
        decision = check_candidate(Candidate(24, 32, 64, "ab", True), self.anchor, self.f32_contract)
        self.assertIn("invoke_contract_kernel", decision.actions)

    def test_09_tail_candidate_adapts(self):
        contract, _ = select_contract(self.tail, self.inputs["contracts"])
        decision = check_candidate(Candidate(24, 32, 64, "ab", True), self.tail, contract)
        self.assertEqual(decision.path, "adapt")

    def test_10_tail_reason(self):
        contract, _ = select_contract(self.tail, self.inputs["contracts"])
        decision = check_candidate(Candidate(24, 32, 64, "ab", True), self.tail, contract)
        self.assertIn("MN_TAIL_ADAPTER", decision.reason_codes)

    def test_11_tail_action(self):
        contract, _ = select_contract(self.tail, self.inputs["contracts"])
        decision = check_candidate(Candidate(24, 32, 64, "ab", True), self.tail, contract)
        self.assertIn("insert_finite_mn_fringe", decision.actions)

    def test_12_no_contract_falls_back(self):
        decision = check_candidate(Candidate(24, 32, 64, "none", False), self.mismatch, None)
        self.assertEqual(decision.path, "fallback")

    def test_13_no_contract_reason(self):
        decision = check_candidate(Candidate(24, 32, 64, "none", False), self.mismatch, None)
        self.assertEqual(decision.reason_codes, ["NO_MATCHING_CONTRACT"])

    def test_14_nonpositive_tile_rejected(self):
        decision = check_candidate(Candidate(0, 32, 64, "ab", True), self.anchor, self.f32_contract)
        self.assertEqual(decision.reason_codes, ["NON_POSITIVE_TILE"])

    def test_15_oversize_tile_rejected(self):
        decision = check_candidate(Candidate(256, 32, 64, "ab", True), self.anchor, self.f32_contract)
        self.assertEqual(decision.path, "reject")

    def test_16_oversize_transform_reason(self):
        decision = check_candidate(Candidate(256, 32, 64, "ab", True), self.anchor, self.f32_contract)
        self.assertIn("TRANSFORM_PRECONDITION_FAILED", decision.reason_codes)

    def test_17_unsupported_payload_rejected(self):
        task = copy.deepcopy(self.anchor)
        task["operation"] = "linalg.conv_2d_nchw_fchw"
        decision = check_candidate(Candidate(24, 32, 64, "ab", True), task, self.f32_contract)
        self.assertEqual(decision.reason_codes, ["UNSUPPORTED_OPERATION"])

    def test_18_missing_fallback_rejects_contract_miss(self):
        task = copy.deepcopy(self.mismatch)
        task["fallback_available"] = False
        decision = check_candidate(Candidate(24, 32, 64, "none", False), task, None)
        self.assertEqual(decision.path, "reject")

    def test_19_mr_nr_mismatch_falls_back(self):
        decision = check_candidate(Candidate(8, 24, 64, "ab", False), self.anchor, self.f32_contract)
        self.assertIn("MR_NR_MISMATCH", decision.reason_codes)

    def test_20_vector_lane_mismatch_falls_back(self):
        contract = copy.deepcopy(self.f32_contract)
        contract["vectorization"]["lanes"] = 6
        decision = check_candidate(Candidate(24, 32, 64, "ab", True), self.anchor, contract)
        self.assertIn("VECTOR_LANE_MISMATCH", decision.reason_codes)

    def test_21_missing_packing_falls_back(self):
        decision = check_candidate(Candidate(24, 32, 64, "none", True), self.anchor, self.f32_contract)
        self.assertIn("PACKING_REQUIRED", decision.reason_codes)

    def test_22_stride_mismatch_falls_back(self):
        task = copy.deepcopy(self.anchor)
        task["stride"]["c_inner"] = 2
        decision = check_candidate(Candidate(24, 32, 64, "ab", True), task, self.f32_contract)
        self.assertIn("STRIDE_MISMATCH", decision.reason_codes)

    def test_23_output_layout_mismatch_falls_back(self):
        task = copy.deepcopy(self.anchor)
        task["layout"]["c"] = "blocked"
        decision = check_candidate(Candidate(24, 32, 64, "ab", True), task, self.f32_contract)
        self.assertIn("OUTPUT_LAYOUT_MISMATCH", decision.reason_codes)

    def test_24_alignment_requirement_is_checked(self):
        contract = copy.deepcopy(self.f32_contract)
        contract["alignment"]["a_bytes"] = 64
        decision = check_candidate(Candidate(24, 32, 64, "ab", True), self.anchor, contract)
        self.assertIn("ALIGNMENT_UNAVAILABLE", decision.reason_codes)

    def test_25_k_remainder_adapts(self):
        decision = check_candidate(Candidate(24, 32, 18, "ab", True), self.tail, self.f32_contract)
        self.assertIn("K_REMAINDER_ADAPTER", decision.reason_codes)

    def test_26_tail_without_adapter_falls_back(self):
        task = copy.deepcopy(self.tail)
        task["available_adapters"]["mn_tail"] = False
        decision = check_candidate(Candidate(24, 32, 64, "ab", True), task, self.f32_contract)
        self.assertEqual(decision.path, "fallback")

    def test_27_conditional_pack_layout_present(self):
        params = conditional_parameters(Candidate(24, 32, 64, "ab", True), self.anchor, self.f32_contract)
        self.assertEqual(params["pack_layout"], "blis_panel")

    def test_28_conditional_pack_layout_absent(self):
        params = conditional_parameters(Candidate(24, 32, 64, "none", False), self.anchor, self.f32_contract)
        self.assertNotIn("pack_layout", params)

    def test_29_conditional_vector_lanes(self):
        params = conditional_parameters(Candidate(24, 32, 64, "ab", True), self.anchor, self.f32_contract)
        self.assertEqual(params["vector_lanes"], 8)

    def test_30_conditional_tail_strategy(self):
        params = conditional_parameters(Candidate(24, 32, 64, "ab", True), self.tail, self.f32_contract)
        self.assertIn("mn_tail_strategy", params)

    def test_31_direct_scores_above_fallback(self):
        direct_candidate = Candidate(24, 32, 64, "ab", True)
        fallback_candidate = Candidate(8, 24, 64, "none", False)
        direct = check_candidate(direct_candidate, self.anchor, self.f32_contract)
        fallback = check_candidate(fallback_candidate, self.anchor, self.f32_contract)
        self.assertGreater(
            score_candidate(direct_candidate, self.anchor, self.f32_contract, direct),
            score_candidate(fallback_candidate, self.anchor, self.f32_contract, fallback),
        )

    def test_32_score_does_not_change_path(self):
        candidate = Candidate(24, 32, 64, "ab", True)
        decision = check_candidate(candidate, self.anchor, self.f32_contract)
        _ = score_candidate(candidate, self.anchor, self.f32_contract, decision)
        self.assertEqual(decision.path, "direct")

    def test_33_core_contains_no_rejects(self):
        self.assertTrue(all(row["predicted_path"] != "reject" for row in self.anchor_spaces["expert_core"]))

    def test_34_generic_contains_no_rejects(self):
        self.assertTrue(all(row["predicted_path"] != "reject" for row in self.anchor_spaces["generic"]))

    def test_35_contract_only_paths(self):
        self.assertTrue(all(row["predicted_path"] in {"direct", "adapt"} for row in self.anchor_spaces["contract_only"]))

    def test_36_shell_contains_no_rejects(self):
        shell = [row for row in self.anchor_spaces["expert_shell"] if row.get("is_shell")]
        self.assertTrue(all(row["predicted_path"] != "reject" for row in shell))

    def test_37_shell_disjoint_from_core(self):
        core_ids = {row["candidate_id"] for row in self.anchor_spaces["expert_core"]}
        shell_ids = {row["candidate_id"] for row in self.anchor_spaces["expert_shell"] if row.get("is_shell")}
        self.assertTrue(core_ids.isdisjoint(shell_ids))

    def test_38_shell_is_deterministic(self):
        first = select_shell(self.anchor_rows, 0.1, 41, self.anchor["id"])
        second = select_shell(self.anchor_rows, 0.1, 41, self.anchor["id"])
        self.assertEqual([row["candidate_id"] for row in first], [row["candidate_id"] for row in second])

    def test_39_shell_ratio_near_target(self):
        members = self.anchor_spaces["expert_shell"]
        shell_count = sum(bool(row.get("is_shell")) for row in members)
        self.assertLess(abs(shell_count / len(members) - 0.1), 0.01)

    def test_40_initial_design_size(self):
        selected = rank_and_select_initial(self.anchor_spaces["expert_shell"], 8)
        self.assertEqual(len(selected), 8)

    def test_41_initial_design_unique(self):
        selected = rank_and_select_initial(self.anchor_spaces["expert_shell"], 8)
        self.assertEqual(len({row["candidate_id"] for row in selected}), 8)

    def test_42_provenance_has_contract(self):
        row = self.anchor_spaces["expert_core"][0]
        record = provenance_record(row, self.anchor, self.f32_contract, self.inputs["rules"], self.inputs["source_files"])
        self.assertEqual(record["contract_id"], self.f32_contract["id"])

    def test_43_provenance_has_rules(self):
        row = self.anchor_spaces["expert_core"][0]
        record = provenance_record(row, self.anchor, self.f32_contract, self.inputs["rules"], self.inputs["source_files"])
        self.assertGreaterEqual(len(record["rule_ids"]), 3)

    def test_44_provenance_has_source_hashes(self):
        row = self.anchor_spaces["expert_core"][0]
        record = provenance_record(row, self.anchor, self.f32_contract, self.inputs["rules"], self.inputs["source_files"])
        self.assertEqual(len(record["source_files"]["contracts"]["sha256"]), 64)

    def test_45_every_tuning_member_has_provenance_inputs(self):
        for row in self.anchor_spaces["expert_shell"]:
            self.assertTrue(row["contract_id"] or row["reason_codes"])

    def test_46_transform_path_artifact_passes(self):
        summary = json.loads((PROJECT / "processed" / "transform_paths_summary.json").read_text())
        self.assertEqual(summary["correctness_pass_count"], 3)

    def test_47_transform_path_has_each_prediction(self):
        summary = json.loads((PROJECT / "processed" / "transform_paths_summary.json").read_text())
        self.assertEqual(summary["predicted_path_counts"], {"direct": 1, "adapt": 1, "fallback": 1})

    def test_48_observed_replacement_boundary(self):
        summary = json.loads((PROJECT / "processed" / "transform_paths_summary.json").read_text())
        self.assertEqual(summary["observed_replacement_count"], 0)

    def test_49_baco_budget_completed(self):
        summary = json.loads((PROJECT / "processed" / "baco_tuning_summary.json").read_text())
        self.assertEqual(summary["evaluated"], summary["budget"])

    def test_50_baco_rows_valid(self):
        with (PROJECT / "processed" / "baco_tuning_trace.csv").open() as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(all(row["Valid"] == "True" for row in rows))

    def test_51_baco_full_lookup_size(self):
        lookup = json.loads((PROJECT / "tuner" / "expert_shell_lookup.json").read_text())
        self.assertEqual(len(lookup), 249)

    def test_52_baco_pool_excludes_rejects(self):
        pool = json.loads((PROJECT / "tuner" / "baco_tuning_pool.json").read_text())["members"]
        self.assertTrue(all(item["predicted_path"] != "reject" for item in pool))

    def test_53_baco_scenario_budget_split(self):
        scenario = json.loads((PROJECT / "tuner" / "baco_scenario.json").read_text())
        total = scenario["design_of_experiment"]["number_of_samples"] + scenario["optimization_iterations"]
        self.assertEqual(total, 6)


if __name__ == "__main__":
    unittest.main()
