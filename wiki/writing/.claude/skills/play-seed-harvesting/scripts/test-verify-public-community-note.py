#!/usr/bin/env python3
"""Contract tests for the public-community note verifier."""

# Fixture HTML/text is synthetic; numeric URLs are parser inputs, not fetch targets.
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TARGET = Path(__file__).with_name("verify-public-community-note.py")
CURRENT_POOL_VERSION = "2026-10-31"
BOARD_AGNOSTIC_POOL_VERSION = "2026-08-29"
PREVIOUS_POOL_VERSION = "2026-08-15"


def make_note(urls: list[str], *, pool_version: str | None) -> str:
    version = (
        f"community_pool_version: {pool_version}\n" if pool_version is not None else ""
    )
    sources = "\n".join(f'  - "{url}"' for url in urls)
    cards = "\n\n".join(
        f"## {index}. 카드 {index}\n- **원문:** 제목 / {url}"
        for index, url in enumerate(urls, start=1)
    )
    return (
        "---\n"
        "type: writing-note\n"
        "status: working\n"
        "source_scope: community-only\n"
        f"{version}"
        "sources:\n"
        f"{sources}\n"
        "---\n\n"
        "# 검증 표본\n\n"
        f"{cards}\n"
    )


def run_verifier(urls: list[str], *, pool_version: str | None) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as directory:
        note = Path(directory) / "note.md"
        note.write_text(make_note(urls, pool_version=pool_version), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(TARGET), str(note)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    return completed.returncode, json.loads(completed.stdout)


class CurrentPoolContractTests(unittest.TestCase):
    def test_current_pool_accepts_only_core_and_supplemental_paths(self) -> None:
        urls = [
            "https://www.instiz.net/name/7001",
            "https://www.clien.net/service/board/park/9001",
            "https://www.82cook.com/entiz/read.php?bn=15&num=92000001",
            "https://bbs.ruliweb.com/community/board/300147/read/91000001",
        ]
        returncode, report = run_verifier(urls, pool_version=CURRENT_POOL_VERSION)
        self.assertEqual(returncode, 0, report)
        self.assertEqual(
            report["site_counts"],
            {"82cook": 1, "Clien": 1, "Instiz": 1, "RuliwebAdvice": 1},
        )
        self.assertEqual(report["policy_mode"], "current")

    def test_current_pool_rejects_retired_todayhumor_and_other_ruliweb_board(self) -> None:
        urls = [
            "https://www.todayhumor.co.kr/board/view.php?table=freeboard&no=93000001",
            "https://bbs.ruliweb.com/community/board/300143/read/91000003",
        ]
        returncode, report = run_verifier(urls, pool_version=CURRENT_POOL_VERSION)
        self.assertEqual(returncode, 1)
        self.assertTrue(
            any("unapproved source URLs" in error for error in report["errors"]),
            report,
        )

    def test_previous_pool_version_keeps_todayhumor_historical_notes_valid(self) -> None:
        urls = [
            "https://www.todayhumor.co.kr/board/view.php?table=freeboard&no=93000001",
            "https://www.82cook.com/entiz/read.php?bn=15&num=92000001",
        ]
        returncode, report = run_verifier(urls, pool_version=PREVIOUS_POOL_VERSION)
        self.assertEqual(returncode, 0, report)
        self.assertEqual(report["policy_mode"], "2026-08-15")

    def test_current_pool_rejects_retired_fmkorea_and_mlbpark_sources(self) -> None:
        urls = [
            "https://www.fmkorea.com/123456",
            "https://mlbpark.donga.com/mp/b.php?b=bullpen&m=view&id=8001",
        ]
        returncode, report = run_verifier(urls, pool_version=CURRENT_POOL_VERSION)
        self.assertEqual(returncode, 1)
        self.assertTrue(
            any("unapproved source URLs" in error for error in report["errors"]),
            report,
        )


    def test_current_pool_pins_clien_to_park_board(self) -> None:
        urls = ["https://www.clien.net/service/board/kin/9002"]
        returncode, report = run_verifier(urls, pool_version=CURRENT_POOL_VERSION)
        self.assertEqual(returncode, 1)
        self.assertTrue(
            any("unapproved source URLs" in error for error in report["errors"]),
            report,
        )

    def test_current_pool_keeps_bobaedream_and_inven_out(self) -> None:
        urls = [
            "https://www.bobaedream.co.kr/view?code=freeb&No=3448117",
            "https://www.inven.co.kr/board/webzine/2097/2747181",
        ]
        returncode, report = run_verifier(urls, pool_version=CURRENT_POOL_VERSION)
        self.assertEqual(returncode, 1)
        self.assertTrue(
            any("unapproved source URLs" in error for error in report["errors"]),
            report,
        )

    def test_2026_08_29_notes_keep_any_clien_board_valid(self) -> None:
        urls = [
            "https://www.clien.net/service/board/kin/9002",
            "https://bbs.ruliweb.com/community/board/300147/read/91000001",
        ]
        returncode, report = run_verifier(urls, pool_version=BOARD_AGNOSTIC_POOL_VERSION)
        self.assertEqual(returncode, 0, report)
        self.assertEqual(report["policy_mode"], "2026-08-29")


class LegacyCompatibilityTests(unittest.TestCase):
    def test_notes_without_pool_version_keep_historical_fmkorea_and_mlbpark_valid(self) -> None:
        urls = [
            "https://www.fmkorea.com/123456",
            "https://mlbpark.donga.com/mp/b.php?b=bullpen&m=view&id=8001",
        ]
        returncode, report = run_verifier(urls, pool_version=None)
        self.assertEqual(returncode, 0, report)
        self.assertEqual(report["policy_mode"], "legacy-compatible")


if __name__ == "__main__":
    unittest.main(verbosity=2)
