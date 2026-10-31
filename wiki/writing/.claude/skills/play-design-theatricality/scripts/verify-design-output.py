#!/usr/bin/env python3
"""Verify the durable structure of a play-design or theatricality-review note.

Checks only what the guardrail doctrine fixes as *shape*: the 13-item design order
(§20.2), the review template headings (§9), and the hard gates (§12.2) that must never
be silently passed. It deliberately does NOT judge design quality — that is a reading
task, not a parsing one.

Usage:
    verify-design-output.py <note.md> [--kind design|review|map|test]

Kind is inferred from frontmatter `type` when omitted, and only for the types the
storage convention actually puts in scope. Anything else exits 0 as SKIP rather than
being checked as a design — a scene body is not a malformed design document.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PRIMARY_MODES = {
    "사실주의",
    "양식화된사실주의",
    "단일무대약속",
    "주관시적표현주의",
    "메타의식게임",
    "부조리극",
}

EVIDENCE_LEVELS = {"R0", "R1", "H1", "R2", "R3", "R4"}

STATUS_VALUES = {"강한 통과", "통과", "조건부 통과", "강한 재설계 권고"}
NEXT_ACTIONS = {"유지", "도입부 냉독", "국소교정", "B2재설계", "별도형식계약"}

# references/출력_저장규약.md — the only artifacts this verifier fixes a shape for.
# There is deliberately no fallback: an unlisted `type` is skipped, not guessed at.
# A fallback meant every new type was silently graded against the design rules, which
# is how scene bodies (`draft-scene`) came to be reported as designs missing item 1.
TYPE_KINDS = {
    "draft-candidate": "design",
    "draft-candidate-map": "map",
    "dramaturgy-diagnostic": "review",
    "stage-test": "test",
}

# In the storage convention's table, but this file fixes no shape for a 구조표. Named
# here so it reports as unchecked rather than sharing the out-of-scope exit.
UNCHECKED_TYPES = {"structure-test"}

# §20.2 — the 13 fixed output items. Value is a keyword that must appear in the
# heading, kept short so wording may vary without breaking the check.
DESIGN_ITEMS = {
    1: "제목",
    2: "버린 표면",
    3: "라우터",
    4: "운반체",
    5: "구성",
    6: "촉발",
    7: "잔여",
    8: "종막",
    9: "카드",
    10: "도입",
    11: "점",
    12: "하드 실패",
    13: "약·물",
}

# §6 + §20.2 — the comparison map is a third artifact kind, not a design and not a review.
MAP_REQUIRED = {
    "독립성 5축": "§20.2: the five-axis independence comparison is missing",
    "증거 등급": "§6: the comparison table has no 증거 등급 column",
    "부채": "§6: the comparison table has no 설정·관람법 부채 column",
}

# §9 — review template sections.
REVIEW_SECTIONS = [
    "공통 연극성 판정",
    "냉관객 진입",
    "모드 번역 사건성",
    "언어 형식과 거칠음",
    "설정 이해 부채",
    "주 모드 적합성",
    "실패 유형",
    "판정",
]

GATE_MIN = 14
COLD_READER_MIN = 3  # R0 is the ceiling now; 격리 독자 3인 이상


if hasattr(sys.stdout, "reconfigure"):  # Korean paths on a cp949 console
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("note", type=Path)
    parser.add_argument("--kind", choices=["design", "review", "map", "test"])
    return parser.parse_args()


def frontmatter(text: str) -> str:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", text, flags=re.S)
    if not match:
        raise ValueError("missing or malformed YAML frontmatter fence")
    return match.group(1)


def field(fm: str, name: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(name)}:\s*(.+?)\s*$", fm)
    if not match:
        return None
    return match.group(1).strip().strip('"').strip("'")


def score(raw: str | None) -> int | None:
    """Read `17/20` or `17` into an int. Returns None when unparseable."""
    if raw is None:
        return None
    match = re.match(r"\s*(\d{1,3})\s*(?:/\s*20)?\s*\Z", raw)
    return int(match.group(1)) if match else None


def check_common(fm: str, errors: list[str]) -> None:
    for name in ("type", "status", "created", "updated", "visibility", "title"):
        if field(fm, name) is None:
            errors.append(f"frontmatter: missing `{name}`")

    status = field(fm, "status")
    if status is not None and status != "draft":
        errors.append(f"frontmatter: status must be `draft` on generated output, got `{status}`")

    evidence = field(fm, "_evidence_level")
    if evidence is None:
        errors.append("frontmatter: missing `_evidence_level` (R0 unless a real reader was used)")
    elif evidence not in EVIDENCE_LEVELS:
        errors.append(f"frontmatter: `_evidence_level` must be one of {sorted(EVIDENCE_LEVELS)}, got `{evidence}`")


def check_r0_labelling(fm: str, body: str, errors: list[str]) -> None:
    """§21 — `독립 리뷰` is earned by isolation, not by evidence grade.

    Separate agents or sessions with information isolation may use the term even at R0.
    One context reading in several voices may not.
    """
    if field(fm, "_evidence_level") != "R0" or "독립 리뷰" not in body:
        return
    isolated = "격리" in body and ("별도 에이전트" in body or "별도 세션" in body)
    if not isolated and "R0 다중 관점 검토" not in body:
        errors.append(
            "§21: R0 output calls itself `독립 리뷰` without documenting isolation "
            "(별도 에이전트/별도 세션 + 정보 격리). Use `R0 다중 관점 검토` instead."
        )


def check_gates(fm: str, body: str, errors: list[str]) -> None:
    """§12.2 — sub-14 scores may pass on total, but must never be shown as a plain pass."""
    common = score(field(fm, "_common_theatricality"))
    mode_fit = score(field(fm, "_mode_fit"))

    if common is None:
        errors.append("frontmatter: missing or unparseable `_common_theatricality` (expect `N/20`)")
    if mode_fit is None:
        errors.append("frontmatter: missing or unparseable `_mode_fit` (expect `N/20`)")

    for label, value in (("_common_theatricality", common), ("_mode_fit", mode_fit)):
        if value is None:
            continue
        if value > 20:
            errors.append(f"frontmatter: `{label}` is {value}, above the 20-point maximum")
        elif value < GATE_MIN and "조건부" not in body:
            errors.append(
                f"hard gate: `{label}` is {value} (<{GATE_MIN}) but the body never says 조건부"
            )


def check_design(fm: str, body: str, errors: list[str]) -> None:
    primary = field(fm, "_primary_mode")
    if primary is None:
        errors.append("frontmatter: missing `_primary_mode`")
    elif primary.replace(" ", "").replace("·", "") not in PRIMARY_MODES:
        errors.append(f"frontmatter: `_primary_mode` unknown: `{primary}`")

    secondary = field(fm, "_secondary_mode")
    if secondary is None:
        errors.append("frontmatter: missing `_secondary_mode` (use `해당없음` when there is none)")
    elif secondary != "해당없음":
        if secondary == primary:
            errors.append("frontmatter: `_secondary_mode` repeats `_primary_mode`")
        if "혼합" not in body and "보조 모드" not in body:
            errors.append("a secondary mode is declared but the body never contracts it (§19)")

    headings = re.findall(r"(?m)^##\s+(\d{1,2})\.\s*(.+?)\s*$", body)
    numbers = [int(number) for number, _ in headings]
    if numbers != sorted(numbers):
        errors.append(f"§20.2: the 13 items are out of order: {numbers}")

    seen = {int(number): title for number, title in headings}
    for index, keyword in DESIGN_ITEMS.items():
        if index not in seen:
            errors.append(f"§20.2: missing item {index} (expect a heading containing `{keyword}`)")
        elif keyword not in seen[index]:
            errors.append(
                f"§20.2: item {index} heading `{seen[index]}` does not contain `{keyword}`"
            )

    if "theatricality_entry_card" not in body:
        errors.append("§2: the required `theatricality_entry_card` block is absent")
    if "mode_boundary_router" not in body and "모드 경계 라우터" not in body:
        errors.append("§0.3: no mode boundary router output — the mode was not routed, only named")


def check_map(fm: str, body: str, errors: list[str]) -> None:
    linked = re.findall(r"(?m)^\s*-\s*\"?\[\[.+?\]\]\"?\s*$", fm[fm.find("has:"):] if "has:" in fm else "")
    if len(linked) < 2:
        errors.append("frontmatter: `has:` must link the design documents this map compares (2 or more)")

    for needle, message in MAP_REQUIRED.items():
        if needle not in body:
            errors.append(message)

    if not any(value in body for value in NEXT_ACTIONS):
        errors.append(f"§9: no 다음 행동 value found; expected one of {sorted(NEXT_ACTIONS)}")
    if not re.search(r"약속\s*=", body):
        errors.append("§21: the `[약·물]` line is missing")


def check_test(fm: str, body: str, errors: list[str]) -> None:
    """§5 — the one thing a cold-entry test must never do is invent the reader's answers.

    H1 is no longer called (decisions/냉관객시험_H1_비사용_2026-08-29), so R0 isolated
    reading is the ceiling. The bar is raised to compensate: three readers minimum, and
    the conclusion may only claim that no defect was detected.
    """
    if "cold_entry_test" not in body:
        errors.append("§5: the required `cold_entry_test` block is absent")
        return
    if "자유 회상" not in body:
        errors.append("§5: the free-recall questions are missing from the protocol")

    block = body[body.index("cold_entry_test") :]
    block = block[: block.find("```")] if "```" in block else block

    level = re.search(r"(?m)^\s*evidence_level:\s*(.+?)\s*$", block)
    if level is None:
        errors.append("§5: `cold_entry_test.evidence_level` is missing")
        return
    grade = level.group(1).strip()

    recalled = re.findall(
        r"(?m)^\s*(stage_code|repetition_compulsion_image_voice_or_role|"
        r"cost_exhaustion_fixation_or_residue|curiosity|blocking_rules|"
        r"viewing_method_learned):\s*(.+?)\s*$",
        block,
    )
    unrun = {"미실행", "미측정", "미판정", "해당없음"}
    filled = [name for name, value in recalled if value not in unrun]
    response = re.search(r"(?m)^\s*response:\s*(.+?)\s*$", block)

    if grade == "미실행":
        if filled:
            errors.append(
                "§5: the test is marked 미실행 but reader answers are filled in: "
                + ", ".join(filled)
                + " — never invent what a cold reader said"
            )
        if response is not None and response.group(1).strip() != "미판정":
            errors.append("§5: the test is 미실행 but `response` already carries a verdict")
    elif grade in EVIDENCE_LEVELS:
        if len(filled) < len(recalled):
            errors.append(
                f"§5: evidence is claimed as {grade} but some recall fields are still 미실행"
            )
        if response is None or response.group(1).strip() not in NEXT_ACTIONS:
            errors.append(f"§5: `response` must be one of {sorted(NEXT_ACTIONS)}")
        if grade == "R0":
            count = field(fm, "_cold_reader_count")
            if count is None or not count.isdigit() or int(count) < COLD_READER_MIN:
                errors.append(
                    f"frontmatter: R0 is the ceiling now, so `_cold_reader_count` must be "
                    f"{COLD_READER_MIN} or more; got `{count}`"
                )
            if "설계 결함이 검출되지 않았" not in body and "진입 확인" in body:
                errors.append(
                    "§5: an R0 pass may only claim `설계 결함이 검출되지 않았다`, not 관객 진입 확인"
                )
    else:
        errors.append(f"§5: `cold_entry_test.evidence_level` must be 미실행 or an evidence grade, got `{grade}`")


def check_review(body: str, errors: list[str]) -> None:
    for section in REVIEW_SECTIONS:
        if section not in body:
            errors.append(f"§9: review template section missing: `{section}`")

    if not re.search(r"약속\s*=", body):
        errors.append("§21: the `[약·물]` line is missing (약속= / 소유= / 상세=)")
    else:
        for key in ("소유", "상세"):
            if not re.search(rf"{key}\s*=", body):
                errors.append(f"§21: the `[약·물]` line has no `{key}=`")

    if not any(value in body for value in STATUS_VALUES):
        errors.append(f"§9: no 상태 value found; expected one of {sorted(STATUS_VALUES)}")
    if not any(value in body for value in NEXT_ACTIONS):
        errors.append(f"§9: no 다음 행동 value found; expected one of {sorted(NEXT_ACTIONS)}")


def main() -> int:
    args = parse_args()

    try:
        text = args.note.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"FAIL: cannot read {args.note}: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []

    try:
        fm = frontmatter(text)
    except ValueError as exc:
        print(f"FAIL: {args.note}: {exc}", file=sys.stderr)
        return 1

    body = text[text.index("\n---", 3) + 4 :]

    kind = args.kind
    if kind is None:
        doc_type = field(fm, "type") or ""
        kind = TYPE_KINDS.get(doc_type)
        if kind is None:
            # Exit 0: out of scope is not a defect. Pass --kind to check anyway.
            reason = "no-shape-rules" if doc_type in UNCHECKED_TYPES else "out-of-scope"
            print(f"SKIP: {args.note} | kind={reason} | type={doc_type or '(none)'}")
            return 0

    check_common(fm, errors)
    check_r0_labelling(fm, body, errors)
    if kind == "map":
        # Scores live in the per-design documents; a map that repeats them would drift.
        check_map(fm, body, errors)
    elif kind == "test":
        check_test(fm, body, errors)
    else:
        check_gates(fm, body, errors)
        if kind == "design":
            check_design(fm, body, errors)
        else:
            check_review(body, errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(f"PASS: {args.note} | kind={kind} | evidence={field(fm, '_evidence_level')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
