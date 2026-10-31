#!/usr/bin/env python3
"""Mechanical check of a Hermes → Claude harvest handoff before any A0 judgment.

Contract: wiki/writing/decisions/Hermes_Claude_글감채집_협업체계_2026-10-31.md (1단계).

    python -B scripts/verify-handoff.py "$SEED_HARVEST_RUNS/<batch>"

Checks, without opening the network:
  * HANDOFF.json exists (the batch is finished) and names actor ``hermes``.
  * Korean batches (``contract.json`` present): the run contract's actor is hermes and the
    collector hash in HANDOFF.json matches the collector in this skill.
  * Every site listed in HANDOFF.json has a folder, its done/stopped status agrees with stop.json,
    and the eligible count agrees with accounting.json when that exists.
  * Every record carrying a body has the required fields and its body_sha256 matches the body.

Writes ``<batch>/claude/verify.json`` (counts and problems only, never body text) and exits
0 when there are no errors, 1 otherwise. Warnings do not fail the check.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
COLLECTOR = HERE / "community-collector.py"
KR_FIELDS = ("site", "id", "url", "state", "body", "body_sha256")
JP_FIELDS = ("url", "title", "posted_at", "fetched_at", "state", "lane", "lane_signal", "body", "body_sha256")
COMMENT_KEYS = ("comments", "replies", "answers", "res", "trackbacks")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.parent.name}/posts.jsonl:{n}: invalid JSON ({exc.msg})")
    return rows


def verify(batch: Path, collector: Path = COLLECTOR) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    report: dict[str, Any] = {"batch": batch.name, "checked_at": datetime.now().astimezone().isoformat(),
                              "errors": errors, "warnings": warnings, "sites": {}}
    handoff = read_json(batch / "HANDOFF.json")
    if handoff is None:
        errors.append("HANDOFF.json missing: the batch is not finished, do not read it yet")
        report["ok"] = False
        return report
    if handoff.get("actor") != "hermes":
        errors.append(f"HANDOFF actor is {handoff.get('actor')!r}, expected 'hermes'")
    sites = handoff.get("sites")
    if not isinstance(sites, dict) or not sites:
        errors.append("HANDOFF.json has no sites")
        sites = {}

    contract = read_json(batch / "contract.json")
    kind = "kr-collector" if contract else "external"
    report["kind"] = kind
    if contract:
        if contract.get("actor") != "hermes":
            errors.append(f"contract.json actor is {contract.get('actor')!r}, expected 'hermes'")
        expected = sha256_file(collector)
        if handoff.get("collector_sha256") != expected:
            errors.append("collector_sha256 differs from this skill's community-collector.py "
                          "(Hermes ran another collector version or a copy)")
        report["window"] = [contract.get("window_start"), contract.get("window_end")]
    fields = KR_FIELDS if contract else JP_FIELDS

    for name, status in sites.items():
        site_dir = batch / name
        info: dict[str, Any] = {"handoff_status": status}
        report["sites"][name] = info
        if not site_dir.is_dir():
            errors.append(f"{name}: folder missing")
            continue
        stop = read_json(site_dir / "stop.json")
        if stop and not str(status).startswith(f"stopped:{stop.get('state')}"):
            errors.append(f"{name}: stop.json says {stop.get('state')!r} but HANDOFF says {status!r}")
        if not stop and str(status).startswith("stopped"):
            warnings.append(f"{name}: HANDOFF says {status!r} but there is no stop.json")
        rows = read_jsonl(site_dir / "posts.jsonl", errors)
        eligible = bad_hash = 0
        for row in rows:
            if "body" not in row:
                continue  # collector writes body-less records for skipped posts
            label = f"{name}:{row.get('id') or row.get('url')}"
            missing = [f for f in fields if f not in row]
            if missing:
                errors.append(f"{label}: missing {', '.join(missing)}")
            leaked = [k for k in COMMENT_KEYS if row.get(k)]
            if leaked:
                errors.append(f"{label}: carries comment material ({', '.join(leaked)})")
            if row.get("body_sha256") != sha256_text(str(row.get("body", ""))):
                bad_hash += 1
                errors.append(f"{label}: body_sha256 does not match the body")
            if row.get("state") == "eligible":
                eligible += 1
        info.update(records=len(rows), eligible=eligible, hash_mismatch=bad_hash)
        accounting = read_json(site_dir / "accounting.json")
        if accounting is not None:
            info["accounting_eligible"] = accounting.get("eligible_bodies")
            if accounting.get("eligible_bodies") != eligible:
                errors.append(f"{name}: {eligible} eligible bodies but accounting.json says "
                              f"{accounting.get('eligible_bodies')} (run status again, then hand off)")
            if accounting.get("unresolved_attempts"):
                warnings.append(f"{name}: {len(accounting['unresolved_attempts'])} unresolved attempts")
        elif contract:
            warnings.append(f"{name}: accounting.json missing")
        if contract and (site_dir / "discovered.json").exists():
            receipt = (read_json(site_dir / "discovered.json") or {}).get("receipt") or {}
            if receipt.get("date_unresolved"):
                warnings.append(f"{name}: date_unresolved={receipt['date_unresolved']} (list date selector)")
            empty = [d for d, c in (receipt.get("in_window_days") or {}).items() if not c]
            if empty:
                warnings.append(f"{name}: no posts found for {', '.join(empty)} (shortfall, do not backfill)")
    report["eligible_total"] = sum(s.get("eligible", 0) for s in report["sites"].values())
    report["ok"] = not errors
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("batch", help="batch folder under $SEED_HARVEST_RUNS")
    parser.add_argument("--collector", default=str(COLLECTOR), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    batch = Path(args.batch).expanduser().resolve()
    if not batch.is_dir():
        print(f"not a folder: {batch}", file=sys.stderr)
        return 2
    report = verify(batch, Path(args.collector))
    out = batch / "claude" / "verify.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("batch", "ok", "eligible_total") if k in report}, ensure_ascii=False))
    for line in report["errors"]:
        print("ERROR", line)
    for line in report["warnings"]:
        print("WARN ", line)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
