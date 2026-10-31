#!/usr/bin/env python3
"""Detect drift between this skill's section pointers and the guardrail doctrine.

The skill deliberately stores no doctrine — only pointers like "§20.2" and "§12.2".
When the guardrail document is revised those pointers can go stale silently. This
script fails loudly instead.

It checks structure and named blocks, never wording, so the doctrine stays free to
change its prose.

Usage:
    verify-doctrine-anchors.py [--doc <path>]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

DOC_RELPATH = Path("wiki/writing/aesthetics/희곡_설계_연극성_가드레일.md")

# section number -> keyword that must appear in that section's heading
SECTIONS = {
    "0.2": "모드 선택",
    "0.3": "모드 경계 라우터",
    "0.4": "빠른 사용 경로",
    "1": "핵심 원칙",
    "2": "필수 설계 카드",
    "3": "반복 실패 유형",
    "4": "공통 연극성",
    "5": "냉관객 시험",
    "6": "운용 순서",
    "8": "실행문",
    "9": "리뷰 출력 템플릿",
    "12": "모드별 평가 운용",
    "12.1": "100점표",
    "12.2": "모드 적합성",
    "13": "사실주의",
    "14": "양식화된 사실주의",
    "15": "단일 무대 약속",
    "16": "주관·시적·표현주의",
    "17": "메타·의식·게임",
    "18": "부조리극",
    "19": "혼합 모드 규칙",
    "20": "복수 설계 실행문",
    "20.2": "실행 키트",
    "21": "독립 리뷰 프로토콜",
}

# YAML block names the skill and the output verifier depend on by name
BLOCKS = (
    "theatricality_entry_card",
    "mode_boundary_router",
    "cold_entry_test",
    "hybrid_mode_contract",
    "run_config",
)

MODULE_SECTIONS = range(13, 19)
FAILURE_TYPES = [f"F{n}" for n in range(1, 11)]


if hasattr(sys.stdout, "reconfigure"):  # Korean paths on a cp949 console
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", type=Path, help="override the guardrail document path")
    return parser.parse_args()


def vault_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def headings(text: str) -> dict[str, str]:
    """Map `0.3` / `12` -> heading text, for `## 12. Title` and `### 0.3 Title` forms."""
    found: dict[str, str] = {}
    for match in re.finditer(r"(?m)^#{2,4}\s+(\d+(?:\.\d+)?)\.?\s+(.+?)\s*$", text):
        found[match.group(1)] = match.group(2)
    return found


def main() -> int:
    args = parse_args()

    if args.doc is not None:
        doc = args.doc
    else:
        try:
            doc = vault_root() / DOC_RELPATH
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("FAIL: not inside a git repository; pass --doc explicitly", file=sys.stderr)
            return 1

    try:
        text = doc.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"FAIL: cannot read guardrail document {doc}: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    found = headings(text)

    for number, keyword in SECTIONS.items():
        if number not in found:
            errors.append(f"§{number} is gone from the guardrail document")
        elif keyword not in found[number]:
            errors.append(f"§{number} heading is now `{found[number]}` — expected it to contain `{keyword}`")

    for block in BLOCKS:
        if block not in text:
            errors.append(f"named YAML block `{block}` is gone — verify-design-output.py depends on it")

    for failure in FAILURE_TYPES:
        if not re.search(rf"(?m)^###\s+{failure}\.", text):
            errors.append(f"failure type {failure} is gone from §3")

    for number in MODULE_SECTIONS:
        if not re.search(rf"(?m)^###\s+{number}\.\d+\s+.*하드 실패", text):
            errors.append(f"§{number} no longer declares a 하드 실패 subsection")

    if "최대 13점" not in text:
        errors.append("§12.2 no longer caps mode fit at 13 on a live hard failure — SKILL.md states it does")
    if "14점 미만" not in text:
        errors.append("§12.2 no longer uses the 14-point conditional threshold — SKILL.md states it does")

    version = re.search(r'(?m)^reference_version:\s*"?([\d.]+)"?', text)
    updated = re.search(r"(?m)^updated:\s*(\S+)", text)

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(
            "\nFix SKILL.md and references/ to match the current doctrine, then report the drift.",
            file=sys.stderr,
        )
        return 1

    print(
        f"PASS: {doc.name} | version={version.group(1) if version else '?'}"
        f" | updated={updated.group(1) if updated else '?'}"
        f" | sections={len(SECTIONS)} anchors intact"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
