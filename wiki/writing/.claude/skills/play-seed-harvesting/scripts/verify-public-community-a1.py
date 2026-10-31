#!/usr/bin/env python3
"""Validate an outside-Vault public-community A1 adjudication package."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

SCHEMA_VERSION = "public-community-a1/0.2"
POLICY_VERSION = "2026-08-15-a1-v0.2"
REQUIRED_PASS_LINE_TYPES = {
    "anchor",
    "protected_core",
    "source_distance",
    "performance_carrier",
    "tension_topology",
    "time_rule",
    "temporal_operation",
    "terminal_condition",
    "audience_route",
}
ENUMS = {
    "evidence_state": {"valid", "unverifiable", "invalid"},
    "safety_state": {"clear", "blocked"},
    "source_handling": {"clear", "transform_only", "archive_only", "prohibited"},
    "structure_state": {"proven", "insufficient", "not_run", "a0_recheck"},
    "novelty_state": {"distinct", "drift_warning", "merge_candidate", "duplicate", "unresolved"},
    "workflow_state": {"pass", "resting", "merge", "not_run", "blocked", "a0_recheck"},
}
INFERENCE_CLASSES = {"supported_abstraction", "entailed"}
ANCHOR_MODES = {"exact", "redacted", "pointer"}


def duplicates(values: list[object]) -> list[object]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def validate_proven_record(record: dict) -> list[str]:
    record_id = record.get("a1_record_id", "<missing-record-id>")
    workflow = record.get("workflow_state")
    contract_label = "pass" if workflow == "pass" else "proven"
    errors: list[str] = []
    if record.get("derived_permissions") != []:
        errors.append(f"{record_id}: derived_permissions must be empty")

    anchor = record.get("anchor") or {}
    if record.get("source_handling") == "transform_only" and anchor.get("mode") == "exact":
        errors.append(f"{record_id}: transform_only cannot use exact anchor")

    memo_lines = record.get("memo_lines") or []
    if not 5 <= len(memo_lines) <= 10:
        errors.append(f"{record_id}: {contract_label} memo must have 5-10 lines")

    observed_types = {
        line_type
        for line in memo_lines
        for line_type in (line.get("line_types") or [])
    }
    missing_types = sorted(REQUIRED_PASS_LINE_TYPES - observed_types)
    if missing_types:
        errors.append(f"{record_id}: missing memo line types: {missing_types}")

    if any(line.get("inference_class") == "speculative" for line in memo_lines):
        errors.append(f"{record_id}: speculative memo line is forbidden for pass")

    reviews = record.get("review_state") or {}
    if reviews.get("structure") != "pass" or reviews.get("lineage") != "pass":
        errors.append(f"{record_id}: pass requires structure and lineage reviews")
    return errors


def validate_audit_integrity(manifest: list[dict], records: list[dict]) -> list[str]:
    errors: list[str] = []
    record_ids = [record.get("a1_record_id") for record in records]
    residue_ids = [record.get("residue_id") for record in records]
    duplicate_record_ids = duplicates(record_ids)
    duplicate_residue_ids = duplicates(residue_ids)
    if duplicate_record_ids:
        errors.append(f"duplicate a1_record_id: {duplicate_record_ids}")
    if duplicate_residue_ids:
        errors.append(f"duplicate A1 residue_id: {duplicate_residue_ids}")

    manifest_residue_ids = [item.get("residue_id") for item in manifest]
    duplicate_manifest_ids = duplicates(manifest_residue_ids)
    if duplicate_manifest_ids:
        errors.append(f"duplicate A0 residue_id: {duplicate_manifest_ids}")
    # 2026-10-31 amendment: one of the two A0 spans may be the post title, never both.
    for item in manifest:
        kinds = item.get("evidence_kinds") or {}
        evidence_ids = item.get("evidence_ids") or []
        if evidence_ids and all(kinds.get(eid) == "title" for eid in evidence_ids):
            errors.append(f"{item.get('residue_id')}: both A0 evidence spans are title spans; one must be body")
    manifest_by_residue = {
        item.get("residue_id"): item
        for item in manifest
        if item.get("residue_id") is not None
    }
    record_by_id = {
        record.get("a1_record_id"): record
        for record in records
        if record.get("a1_record_id") is not None
    }

    for record in records:
        record_id = record.get("a1_record_id", "<missing-record-id>")
        for required_field in ("a1_record_id", "source_id", "source_version_id", "residue_id"):
            if not record.get(required_field):
                errors.append(f"{record_id}: missing required record field: {required_field}")
        if record.get("derived_permissions") != []:
            errors.append(f"{record_id}: derived_permissions must be empty")
        if (
            record.get("source_handling") == "transform_only"
            and (record.get("anchor") or {}).get("mode") == "exact"
        ):
            errors.append(f"{record_id}: transform_only cannot use exact anchor")
        for field, allowed in ENUMS.items():
            if record.get(field) not in allowed:
                errors.append(f"{record_id}: invalid {field}: {record.get(field)!r}")

        manifest_item = manifest_by_residue.get(record.get("residue_id"))
        if manifest_item is not None:
            lineage = (record.get("source_id"), record.get("source_version_id"))
            expected_lineage = (
                manifest_item.get("source_id"),
                manifest_item.get("source_version_id"),
            )
            if lineage != expected_lineage:
                errors.append(f"{record_id}: record lineage does not match A0 manifest")
            expected_evidence = set(manifest_item.get("evidence_ids") or [])
            if set(record.get("a0_evidence_ids") or []) != expected_evidence:
                errors.append(f"{record_id}: A0 evidence ids do not match manifest")
        else:
            expected_evidence = set(record.get("a0_evidence_ids") or [])

        if len(expected_evidence) != 2:
            errors.append(f"{record_id}: exactly two A0 evidence ids required")

        anchor = record.get("anchor")
        anchor_required = record.get("workflow_state") not in {"blocked", "not_run", "a0_recheck"}
        if anchor_required or anchor is not None:
            anchor = anchor or {}
            if anchor.get("mode") not in ANCHOR_MODES:
                errors.append(f"{record_id}: invalid anchor mode: {anchor.get('mode')!r}")
            if anchor.get("evidence_id") not in expected_evidence:
                errors.append(f"{record_id}: unknown anchor evidence: {anchor.get('evidence_id')!r}")

        memo_lines = record.get("memo_lines") or []
        if record.get("workflow_state") not in {"pass", "merge"}:
            if memo_lines or record.get("proof") is not None:
                errors.append(f"{record_id}: only pass or merge may retain memo/proof")
        memo_line_ids = [line.get("memo_line_id") for line in memo_lines]
        duplicate_line_ids = duplicates(memo_line_ids)
        if duplicate_line_ids:
            errors.append(f"{record_id}: duplicate memo_line_id: {duplicate_line_ids}")
        if memo_lines and "anchor" not in (memo_lines[0].get("line_types") or []):
            errors.append(f"{record_id}: first memo line must be anchor")
        for line in memo_lines:
            support_ids = set(line.get("support_evidence_ids") or [])
            if not support_ids:
                errors.append(
                    f"{record_id}/{line.get('memo_line_id')}: memo line requires evidence support"
                )
            if line.get("inference_class") not in INFERENCE_CLASSES:
                errors.append(
                    f"{record_id}/{line.get('memo_line_id')}: invalid inference_class: "
                    f"{line.get('inference_class')!r}"
                )
            unknown_support = support_ids - expected_evidence
            if unknown_support:
                errors.append(
                    f"{record_id}/{line.get('memo_line_id')}: unknown support evidence: "
                    f"{sorted(unknown_support)}"
                )

        if record.get("workflow_state") == "merge":
            merge = record.get("merge") or {}
            required = {"merge_target", "shared_engine", "retained_difference", "merge_gain"}
            missing = sorted(field for field in required if not merge.get(field))
            if missing:
                errors.append(f"{record_id}: missing merge fields: {missing}")
            target = merge.get("merge_target")
            if target == record_id:
                errors.append(f"{record_id}: merge target cannot be self")
            elif target not in record_by_id:
                errors.append(f"{record_id}: merge target does not exist: {target!r}")
            elif record_by_id[target].get("workflow_state") != "pass":
                errors.append(f"{record_id}: merge target must be an active pass record")

    merge_edges = {
        record_id: (record.get("merge") or {}).get("merge_target")
        for record_id, record in record_by_id.items()
        if record.get("workflow_state") == "merge"
    }
    for start in merge_edges:
        seen: set[str] = set()
        current = start
        while current in merge_edges:
            if current in seen:
                errors.append(f"merge cycle detected from {start}")
                break
            seen.add(current)
            current = merge_edges[current]
    return errors


def derive_workflow_state(record: dict, record_ids: set[str]) -> str:
    if record.get("safety_state") == "blocked" or record.get("source_handling") == "prohibited":
        return "blocked"
    if record.get("source_handling") == "archive_only":
        return "not_run"
    if record.get("structure_state") == "a0_recheck":
        return "a0_recheck"
    if record.get("evidence_state") in {"unverifiable", "invalid"}:
        return "not_run"
    if record.get("structure_state") == "insufficient" or record.get("novelty_state") == "unresolved":
        return "resting"
    if record.get("novelty_state") in {"duplicate", "merge_candidate"}:
        merge = record.get("merge") or {}
        target = merge.get("merge_target")
        if target in record_ids and target != record.get("a1_record_id"):
            return "merge"
        return "resting"
    return "pass"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()

    data = json.loads(args.package.read_text(encoding="utf-8"))
    errors: list[str] = []
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if data.get("policy_version") != POLICY_VERSION:
        errors.append(f"policy_version must be {POLICY_VERSION}")

    records = data.get("records", [])
    manifest = data.get("a0_manifest", [])
    a0_residue_ids = [item.get("residue_id") for item in manifest]
    a1_residue_ids = [record.get("residue_id") for record in records]
    if set(a0_residue_ids) != set(a1_residue_ids):
        errors.append(
            "A0/A1 residue sets differ: "
            f"a0_only={sorted(set(a0_residue_ids) - set(a1_residue_ids))}, "
            f"a1_only={sorted(set(a1_residue_ids) - set(a0_residue_ids))}"
        )

    errors.extend(validate_audit_integrity(manifest, records))

    record_ids = {
        record.get("a1_record_id") for record in records if record.get("a1_record_id")
    }
    for record in records:
        expected_workflow = derive_workflow_state(record, record_ids)
        if record.get("workflow_state") != expected_workflow:
            errors.append(
                f"{record.get('a1_record_id', '<missing-record-id>')}: "
                f"workflow_state must be {expected_workflow}"
            )
        if record.get("workflow_state") in {"pass", "merge"}:
            errors.extend(validate_proven_record(record))

    pass_residue_ids = {
        record.get("residue_id")
        for record in records
        if record.get("workflow_state") == "pass"
    }
    final_card_residue_ids = set(data.get("final_card_residue_ids", []))
    if not final_card_residue_ids <= pass_residue_ids:
        errors.append(
            "final cards must be a subset of pass: "
            f"outside_pass={sorted(final_card_residue_ids - pass_residue_ids)}"
        )

    workflow_counts = Counter(record.get("workflow_state") for record in records)
    report = {
        "package": str(args.package),
        "records": len(records),
        "workflow_counts": dict(sorted(workflow_counts.items())),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
