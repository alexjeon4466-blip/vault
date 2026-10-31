#!/usr/bin/env python3
"""Contract tests for the public-community A1 package verifier."""

# Fixture HTML/text is synthetic; numeric URLs are parser inputs, not fetch targets.
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TARGET = Path(__file__).with_name("verify-public-community-a1.py")
SCHEMA_VERSION = "public-community-a1/0.2"
POLICY_VERSION = "2026-08-15-a1-v0.2"


def valid_pass_record() -> dict:
    evidence_ids = ["ev-1", "ev-2"]
    line_specs = [
        (["anchor"], "A0 evidence #1 / 필요한 동안의 침묵과 뒤늦은 신호"),
        (["protected_core"], "도움은 필요한 시간에는 침묵하고 끝난 뒤에만 성공을 알린다."),
        (["source_distance"], "식별 맥락을 버리고 신호의 시간 순서만 남긴다."),
        (["performance_carrier", "tension_topology"], "침묵과 뒤늦은 소리가 필요 시간과 알림 시간을 어긋나게 한다."),
        (["time_rule"], "필요한 동안은 침묵하고 상황이 끝난 뒤 한 번 소리가 난다."),
        (["temporal_operation"], "시간 작용은 지연이다."),
        (["terminal_condition"], "성공 신호가 도움의 실패를 확정한다."),
        (["audience_route"], "관객은 침묵 뒤 소리로 시간차를 듣는다."),
    ]
    memo_lines = []
    for index, (line_types, text) in enumerate(line_specs, start=1):
        memo_lines.append(
            {
                "memo_line_id": f"L{index}",
                "line_types": line_types,
                "text": text,
                "support_evidence_ids": ["ev-1"],
                "transformation_note": "식별정보 없이 구조만 보존",
                "inference_class": "supported_abstraction",
            }
        )
    return {
        "a1_record_id": "a1-r1-v1",
        "source_id": "src-1",
        "source_version_id": "sha256:source-1",
        "residue_id": "res-1",
        "a0_evidence_ids": evidence_ids,
        "evidence_state": "valid",
        "safety_state": "clear",
        "source_handling": "clear",
        "structure_state": "proven",
        "novelty_state": "distinct",
        "workflow_state": "pass",
        "derived_permissions": [],
        "anchor": {
            "evidence_id": "ev-1",
            "mode": "pointer",
            "display": "A0 evidence #1 / 필요한 동안의 침묵과 뒤늦은 신호",
        },
        "proof": {
            "performance_carriers": ["sound"],
            "tension_topology": "time_misalignment",
            "time_rule": "during=silence; after=signal",
            "temporal_operations": ["delay"],
            "terminal_condition": "residual_pressure",
            "audience_route": "silence_then_sound",
        },
        "memo_lines": memo_lines,
        "review_state": {
            "structure": "pass",
            "lineage": "pass",
            "adjudication": "not_needed",
        },
        "failure_reasons": [],
        "merge": None,
    }


def valid_package() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "batch_id": "fixture-valid-pass",
        "a0_manifest": [
            {
                "source_id": "src-1",
                "source_version_id": "sha256:source-1",
                "residue_id": "res-1",
                "evidence_ids": ["ev-1", "ev-2"],
            }
        ],
        "final_card_residue_ids": ["res-1"],
        "records": [valid_pass_record()],
    }


def run_verifier(package: dict) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as directory:
        package_path = Path(directory) / "a1-package.json"
        package_path.write_text(
            json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        completed = subprocess.run(
            [sys.executable, str(TARGET), str(package_path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    report = json.loads(completed.stdout) if completed.stdout.strip() else {
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    return completed.returncode, report


class ValidPackageTests(unittest.TestCase):
    def test_accepts_valid_pass_package(self) -> None:
        returncode, report = run_verifier(valid_package())
        self.assertEqual(returncode, 0, report)
        self.assertEqual(report["workflow_counts"], {"pass": 1})
        self.assertEqual(report["errors"], [])

    def test_accepts_blocked_stop_record_without_a1_anchor_or_memo(self) -> None:
        package = valid_package()
        record = package["records"][0]
        record["safety_state"] = "blocked"
        record["source_handling"] = "prohibited"
        record["structure_state"] = "not_run"
        record["novelty_state"] = "unresolved"
        record["workflow_state"] = "blocked"
        record["anchor"] = None
        record["proof"] = None
        record["memo_lines"] = []
        record["review_state"] = {
            "structure": "not_run",
            "lineage": "not_run",
            "adjudication": "not_needed",
        }
        record["failure_reasons"] = ["safety_blocked"]
        package["final_card_residue_ids"] = []

        returncode, report = run_verifier(package)
        self.assertEqual(returncode, 0, report)
        self.assertEqual(report["workflow_counts"], {"blocked": 1})
        self.assertEqual(report["errors"], [])


class SetInvariantTests(unittest.TestCase):
    def test_rejects_a0_manifest_and_a1_record_residue_mismatch(self) -> None:
        package = valid_package()
        package["records"][0]["residue_id"] = "res-not-in-a0"
        returncode, report = run_verifier(package)
        self.assertEqual(returncode, 1, report)
        self.assertTrue(
            any("A0/A1 residue sets differ" in error for error in report["errors"]),
            report,
        )


class PassContractTests(unittest.TestCase):
    def test_rejects_invalid_pass_proof(self) -> None:
        cases = []

        speculative = valid_package()
        speculative["records"][0]["memo_lines"][1]["inference_class"] = "speculative"
        cases.append(("speculative", speculative, "speculative memo line"))

        permissions = valid_package()
        permissions["records"][0]["derived_permissions"] = ["card"]
        cases.append(("permissions", permissions, "derived_permissions must be empty"))

        exact_transform = valid_package()
        exact_transform["records"][0]["source_handling"] = "transform_only"
        exact_transform["records"][0]["anchor"]["mode"] = "exact"
        cases.append(("exact_transform", exact_transform, "transform_only cannot use exact anchor"))

        short_memo = valid_package()
        short_memo["records"][0]["memo_lines"] = short_memo["records"][0]["memo_lines"][:4]
        cases.append(("short_memo", short_memo, "pass memo must have 5-10 lines"))

        missing_type = valid_package()
        missing_type["records"][0]["memo_lines"][5]["line_types"] = ["time_rule"]
        cases.append(("missing_type", missing_type, "missing memo line types"))

        failed_review = valid_package()
        failed_review["records"][0]["review_state"]["lineage"] = "fail"
        cases.append(("failed_review", failed_review, "pass requires structure and lineage reviews"))

        one_evidence = valid_package()
        one_evidence["a0_manifest"][0]["evidence_ids"] = ["ev-1"]
        one_evidence["records"][0]["a0_evidence_ids"] = ["ev-1"]
        cases.append(("one_evidence", one_evidence, "exactly two A0 evidence ids required"))

        empty_support = valid_package()
        empty_support["records"][0]["memo_lines"][2]["support_evidence_ids"] = []
        cases.append(("empty_support", empty_support, "memo line requires evidence support"))

        for label, package, expected in cases:
            with self.subTest(label=label):
                returncode, report = run_verifier(package)
                self.assertEqual(returncode, 1, report)
                self.assertTrue(
                    any(expected in error for error in report["errors"]), report
                )


    def test_rejects_non_proven_record_that_retains_completed_memo(self) -> None:
        cases = []

        blocked = valid_package()
        blocked_record = blocked["records"][0]
        blocked_record["safety_state"] = "blocked"
        blocked_record["source_handling"] = "prohibited"
        blocked_record["structure_state"] = "not_run"
        blocked_record["novelty_state"] = "unresolved"
        blocked_record["workflow_state"] = "blocked"
        blocked["final_card_residue_ids"] = []
        cases.append(("blocked", blocked))

        resting = valid_package()
        resting_record = resting["records"][0]
        resting_record["structure_state"] = "insufficient"
        resting_record["novelty_state"] = "unresolved"
        resting_record["workflow_state"] = "resting"
        resting["final_card_residue_ids"] = []
        cases.append(("resting", resting))

        for label, package in cases:
            with self.subTest(label=label):
                returncode, report = run_verifier(package)
                self.assertEqual(returncode, 1, report)
                self.assertTrue(
                    any("only pass or merge may retain memo/proof" in error for error in report["errors"]),
                    report,
                )

    def test_rejects_global_permission_or_anchor_risk_in_non_proven_state(self) -> None:
        permissions = valid_package()
        record = permissions["records"][0]
        record["safety_state"] = "blocked"
        record["source_handling"] = "prohibited"
        record["structure_state"] = "not_run"
        record["novelty_state"] = "unresolved"
        record["workflow_state"] = "blocked"
        record["derived_permissions"] = ["card"]
        record["anchor"] = None
        record["proof"] = None
        record["memo_lines"] = []
        permissions["final_card_residue_ids"] = []

        returncode, report = run_verifier(permissions)
        self.assertEqual(returncode, 1, report)
        self.assertTrue(
            any("derived_permissions must be empty" in error for error in report["errors"]),
            report,
        )

        exact_transform = valid_package()
        record = exact_transform["records"][0]
        record["source_handling"] = "transform_only"
        record["structure_state"] = "insufficient"
        record["novelty_state"] = "unresolved"
        record["workflow_state"] = "resting"
        record["anchor"]["mode"] = "exact"
        record["proof"] = None
        record["memo_lines"] = []
        exact_transform["final_card_residue_ids"] = []

        returncode, report = run_verifier(exact_transform)
        self.assertEqual(returncode, 1, report)
        self.assertTrue(
            any("transform_only cannot use exact anchor" in error for error in report["errors"]),
            report,
        )


class WorkflowDerivationTests(unittest.TestCase):
    def test_rejects_workflow_state_that_violates_precedence(self) -> None:
        cases = []

        blocked = valid_package()
        blocked["records"][0]["safety_state"] = "blocked"
        cases.append(("blocked", blocked, "blocked"))

        archived = valid_package()
        archived["records"][0]["source_handling"] = "archive_only"
        cases.append(("archive_only", archived, "not_run"))

        a0_recheck = valid_package()
        a0_recheck["records"][0]["evidence_state"] = "invalid"
        a0_recheck["records"][0]["structure_state"] = "a0_recheck"
        cases.append(("a0_recheck", a0_recheck, "a0_recheck"))

        unverifiable = valid_package()
        unverifiable["records"][0]["evidence_state"] = "unverifiable"
        cases.append(("unverifiable", unverifiable, "not_run"))

        insufficient = valid_package()
        insufficient["records"][0]["structure_state"] = "insufficient"
        cases.append(("insufficient", insufficient, "resting"))

        unresolved = valid_package()
        unresolved["records"][0]["novelty_state"] = "unresolved"
        cases.append(("unresolved", unresolved, "resting"))

        for label, package, expected in cases:
            with self.subTest(label=label):
                returncode, report = run_verifier(package)
                self.assertEqual(returncode, 1, report)
                self.assertTrue(
                    any(
                        f"workflow_state must be {expected}" in error
                        for error in report["errors"]
                    ),
                    report,
                )

    def test_rejects_final_card_outside_pass_subset(self) -> None:
        package = valid_package()
        record = package["records"][0]
        record["structure_state"] = "insufficient"
        record["workflow_state"] = "resting"
        returncode, report = run_verifier(package)
        self.assertEqual(returncode, 1, report)
        self.assertTrue(
            any("final cards must be a subset of pass" in error for error in report["errors"]),
            report,
        )


class AuditIntegrityTests(unittest.TestCase):
    def test_rejects_broken_ids_lineage_evidence_and_enums(self) -> None:
        cases = []

        duplicate_id = valid_package()
        second = copy.deepcopy(duplicate_id["records"][0])
        second["residue_id"] = "res-2"
        second["source_id"] = "src-2"
        second["source_version_id"] = "sha256:source-2"
        duplicate_id["records"].append(second)
        duplicate_id["a0_manifest"].append(
            {
                "source_id": "src-2",
                "source_version_id": "sha256:source-2",
                "residue_id": "res-2",
                "evidence_ids": ["ev-1", "ev-2"],
            }
        )
        cases.append(("duplicate_id", duplicate_id, "duplicate a1_record_id"))

        bad_lineage = valid_package()
        bad_lineage["records"][0]["source_version_id"] = "sha256:other"
        cases.append(("bad_lineage", bad_lineage, "record lineage does not match A0 manifest"))

        bad_evidence = valid_package()
        bad_evidence["records"][0]["anchor"]["evidence_id"] = "ev-unknown"
        cases.append(("bad_evidence", bad_evidence, "unknown anchor evidence"))

        bad_enum = valid_package()
        bad_enum["records"][0]["evidence_state"] = "maybe"
        cases.append(("bad_enum", bad_enum, "invalid evidence_state"))

        missing_record_id = valid_package()
        del missing_record_id["records"][0]["a1_record_id"]
        cases.append(("missing_record_id", missing_record_id, "missing required record field: a1_record_id"))

        for label, package, expected in cases:
            with self.subTest(label=label):
                returncode, report = run_verifier(package)
                self.assertEqual(returncode, 1, report)
                self.assertTrue(
                    any(expected in error for error in report["errors"]), report
                )

    def test_rejects_merge_cycle(self) -> None:
        package = valid_package()
        first = package["records"][0]
        first["a1_record_id"] = "a1-r1-v1"
        first["novelty_state"] = "merge_candidate"
        first["workflow_state"] = "merge"
        first["merge"] = {
            "merge_target": "a1-r2-v1",
            "shared_engine": "same time rule",
            "retained_difference": "different carrier",
            "merge_gain": "one comparison record",
        }

        second = copy.deepcopy(first)
        second["a1_record_id"] = "a1-r2-v1"
        second["source_id"] = "src-2"
        second["source_version_id"] = "sha256:source-2"
        second["residue_id"] = "res-2"
        second["merge"]["merge_target"] = "a1-r1-v1"
        package["records"].append(second)
        package["a0_manifest"].append(
            {
                "source_id": "src-2",
                "source_version_id": "sha256:source-2",
                "residue_id": "res-2",
                "evidence_ids": ["ev-1", "ev-2"],
            }
        )
        package["final_card_residue_ids"] = []

        returncode, report = run_verifier(package)
        self.assertEqual(returncode, 1, report)
        self.assertTrue(any("merge cycle" in error for error in report["errors"]), report)

    def test_rejects_merge_that_skips_proven_memo_contract(self) -> None:
        package = valid_package()
        target = package["records"][0]
        target["a1_record_id"] = "a1-target-v1"

        merged = copy.deepcopy(target)
        merged["a1_record_id"] = "a1-merge-v1"
        merged["source_id"] = "src-2"
        merged["source_version_id"] = "sha256:source-2"
        merged["residue_id"] = "res-2"
        merged["novelty_state"] = "merge_candidate"
        merged["workflow_state"] = "merge"
        merged["memo_lines"] = []
        merged["merge"] = {
            "merge_target": "a1-target-v1",
            "shared_engine": "same time rule",
            "retained_difference": "different carrier",
            "merge_gain": "one comparison record",
        }
        package["records"].append(merged)
        package["a0_manifest"].append(
            {
                "source_id": "src-2",
                "source_version_id": "sha256:source-2",
                "residue_id": "res-2",
                "evidence_ids": ["ev-1", "ev-2"],
            }
        )
        package["final_card_residue_ids"] = ["res-1"]

        returncode, report = run_verifier(package)
        self.assertEqual(returncode, 1, report)
        self.assertTrue(
            any("proven memo must have 5-10 lines" in error for error in report["errors"]),
            report,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
