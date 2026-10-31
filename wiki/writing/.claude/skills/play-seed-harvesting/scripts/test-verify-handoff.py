#!/usr/bin/env python3
"""Offline tests for verify-handoff.py (synthetic batch folders, no network)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("vh", HERE / "verify-handoff.py")
vh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def post(site: str, i: str, body: str = "본문", **extra) -> dict:
    row = {"site": site, "id": i, "url": f"https://example.test/{i}", "state": "eligible",
           "body": body, "body_sha256": sha(body)}
    row.update(extra)
    return row


class HandoffTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.batch = Path(self.tmp.name) / "2026-11-01_kr"
        self.collector = Path(self.tmp.name) / "collector.py"
        self.collector.write_text("# collector\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def kr_batch(self, rows=None, sites=None, actor="hermes", collector_sha=None):
        dump(self.batch / "contract.json", {"actor": actor, "window_start": "s", "window_end": "e"})
        dump(self.batch / "HANDOFF.json", {
            "batch": self.batch.name, "actor": "hermes", "finished_at": "t",
            "sites": sites or {"ruliweb": "done"},
            "collector_sha256": collector_sha or hashlib.sha256(self.collector.read_bytes()).hexdigest()})
        rows = rows if rows is not None else [post("ruliweb", "1"), post("ruliweb", "2")]
        site = self.batch / "ruliweb"
        site.mkdir(parents=True, exist_ok=True)
        (site / "posts.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                                          encoding="utf-8")
        dump(site / "accounting.json", {"eligible_bodies": sum(r.get("state") == "eligible" for r in rows),
                                        "unresolved_attempts": []})

    def run_verify(self):
        return vh.verify(self.batch, self.collector, {})

    def test_clean_korean_batch_passes(self):
        self.kr_batch()
        report = self.run_verify()
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["eligible_total"], 2)
        self.assertNotIn("본문", json.dumps(report, ensure_ascii=False), "verify.json never carries bodies")

    def test_unfinished_batch_is_not_read(self):
        self.batch.mkdir(parents=True)
        report = self.run_verify()
        self.assertFalse(report["ok"])
        self.assertIn("HANDOFF.json missing", report["errors"][0])

    def test_tampered_body_fails(self):
        bad = post("ruliweb", "1")
        bad["body"] = "고쳐진 본문"
        self.kr_batch(rows=[bad])
        report = self.run_verify()
        self.assertFalse(report["ok"])
        self.assertEqual(report["sites"]["ruliweb"]["hash_mismatch"], 1)

    def test_claude_actor_contract_fails(self):
        self.kr_batch(actor="claude")
        self.assertTrue(any("contract.json actor" in e for e in self.run_verify()["errors"]))

    def test_other_collector_version_fails(self):
        self.kr_batch(collector_sha="0" * 64)
        self.assertTrue(any("collector_sha256" in e for e in vh.verify(self.batch, self.collector, {})["errors"]))

    # 2026-10-31_kr_r2: the shared collector was committed again while Hermes was running
    def test_committed_older_version_passes_with_warning(self):
        self.kr_batch(collector_sha="a" * 64)
        report = vh.verify(self.batch, self.collector, {"a" * 64: "ed31a5e"})
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["collector"], "committed ed31a5e")
        self.assertTrue(any("not the current file" in w for w in report["warnings"]))

    def test_this_skill_collector_history_is_readable(self):
        history = vh.committed_versions(vh.COLLECTOR)
        self.assertTrue(history, "the vault collector has committed versions in Git")

    def test_stop_must_agree_with_handoff(self):
        self.kr_batch()
        dump(self.batch / "ruliweb" / "stop.json", {"state": "challenge", "detail": "x"})
        self.assertTrue(any("stop.json says" in e for e in self.run_verify()["errors"]))
        self.kr_batch(sites={"ruliweb": "stopped:challenge after 3 pages"})
        self.assertTrue(self.run_verify()["ok"])

    def test_listed_site_without_folder_fails(self):
        self.kr_batch(sites={"ruliweb": "done", "clien": "done"})
        self.assertTrue(any("clien: folder missing" in e for e in self.run_verify()["errors"]))

    def test_accounting_disagreement_fails(self):
        self.kr_batch()
        dump(self.batch / "ruliweb" / "accounting.json", {"eligible_bodies": 5})
        self.assertTrue(any("accounting.json says 5" in e for e in self.run_verify()["errors"]))

    def test_comment_material_fails(self):
        self.kr_batch(rows=[post("ruliweb", "1", comments=["댓글"])])
        self.assertTrue(any("comment material" in e for e in self.run_verify()["errors"]))

    def test_list_date_problems_are_warnings(self):
        self.kr_batch()
        dump(self.batch / "ruliweb" / "discovered.json",
             {"receipt": {"date_unresolved": 2, "in_window_days": {"2026-10-31": 0, "2026-11-01": 3}}})
        report = self.run_verify()
        self.assertTrue(report["ok"])
        self.assertTrue(any("date_unresolved=2" in w for w in report["warnings"]))
        self.assertTrue(any("2026-10-31" in w for w in report["warnings"]))

    def test_japanese_batch_requires_lane_fields(self):
        dump(self.batch / "HANDOFF.json", {"batch": "jp", "actor": "hermes", "finished_at": "t",
                                           "sites": {"mamastar": "done"}, "collector_sha256": "hermes jp v2"})
        good = {"url": "u1", "title": "t", "posted_at": "p", "fetched_at": "f", "state": "eligible",
                "lane": "freshness", "lane_signal": {"answers": 3}, "body": "本文", "body_sha256": sha("本文")}
        bad = {k: v for k, v in good.items() if k != "lane_signal"} | {"url": "u2"}
        site = self.batch / "mamastar"
        site.mkdir(parents=True)
        (site / "posts.jsonl").write_text(json.dumps(good) + "\n" + json.dumps(bad) + "\n", encoding="utf-8")
        report = self.run_verify()
        self.assertEqual(report["kind"], "external")
        self.assertEqual(report["errors"], ["mamastar:u2: missing lane_signal"])

    def test_cli_writes_verify_json_and_exit_code(self):
        self.kr_batch()
        self.assertEqual(vh.main([str(self.batch), "--collector", str(self.collector)]), 0)
        self.assertTrue(json.loads((self.batch / "claude" / "verify.json").read_text(encoding="utf-8"))["ok"])


if __name__ == "__main__":
    unittest.main()
