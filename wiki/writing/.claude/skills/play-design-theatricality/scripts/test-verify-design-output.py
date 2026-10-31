#!/usr/bin/env python3
"""Tests for verify-design-output.py.

Every failing case here is a real way a generated note goes wrong: a hard gate shown
as a plain pass, a mode named but never routed, items reordered, a review with no
verdict. A verifier that only accepts good input is a rubber stamp, so most of these
assert rejection.

Run: python test-verify-design-output.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

VERIFIER = Path(__file__).with_name("verify-design-output.py")

if hasattr(sys.stdout, "reconfigure"):  # Korean labels on a cp949 console
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DESIGN_FRONTMATTER = """---
type: draft-candidate
status: draft
created: 2026-08-29
updated: 2026-08-29
visibility: private
title: "테스트 설계 A"
_primary_mode: 단일무대약속
_secondary_mode: 해당없음
_evidence_level: R0
_common_theatricality: 17/20
_mode_fit: 16/20
_generated_by: play-design-theatricality
---
"""

DESIGN_ITEMS = [
    "## 1. 제목과 한 줄 현재 상황",
    "## 2. 채집 노트에서 가져온 것과 버린 표면",
    "## 3. 모드 경계 라우터와 모드 계약",
    "## 4. 핵심 무대 경험과 주 사건 운반체",
    "## 5. 인물·관계 구성",
    "## 6. 촉발 사건",
    "## 7. 장면별 기능과 후속 잔여",
    "## 8. 종막의 무대 상태",
    "## 9. 설계 카드",
    "## 10. 가장 위험한 도입 블록",
    "## 11. 100점표 매핑",
    "## 12. 모드 적합성과 하드 실패 확인",
    "## 13. [약·물] 한 줄",
]

DESIGN_BLOCKS = """
```yaml
mode_boundary_router:
  selected_primary_mode: 단일 무대 약속
```

```yaml
theatricality_entry_card:
  mode_contract:
    primary_mode: 단일 무대 약속
```
"""


def design_note(items: list[str] | None = None, frontmatter: str | None = None, extra: str = "") -> str:
    body = "\n\n".join(f"{heading}\n\n내용." for heading in (items or DESIGN_ITEMS))
    return (frontmatter or DESIGN_FRONTMATTER) + "\n# 테스트 설계 A\n\n" + body + "\n" + DESIGN_BLOCKS + extra


REVIEW_NOTE = """---
type: dramaturgy-diagnostic
status: draft
created: 2026-08-29
updated: 2026-08-29
visibility: private
title: "테스트 판정"
_evidence_level: R0
_common_theatricality: 15/20
_mode_fit: 16/20
---

## 공통 연극성 판정

### A. 냉관객 진입·관람법 — 15/20

### B. 모드 번역 사건성 — 8/10

### 언어 형식과 거칠음

### 설정 이해 부채

### 주 모드 적합성

### 실패 유형

### 판정

- 상태: 통과
- 다음 행동: 도입부 냉독
- [약·물] 약속=허용 / 소유=본문 / 상세=OFF
"""


MAP_NOTE = """---
type: draft-candidate-map
status: draft
created: 2026-08-29
updated: 2026-08-29
visibility: private
title: "테스트 3안 비교"
has:
  - "[[wiki/writing/draft-candidates/테스트_설계A]]"
  - "[[wiki/writing/draft-candidates/테스트_설계B]]"
  - "[[wiki/writing/draft-candidates/테스트_설계C]]"
_evidence_level: R0
_design_count: 3
---

## 독립성 5축

| 축 | A | B | C |
|---|---|---|---|
| 중심 관계 | 가 | 나 | 다 |

## 설계안 비교

| 설계안 | 공통 연극성 20 | 설정·관람법 부채 | 증거 등급 | 판정 |
|---|---:|---|---|---|
| A | 18 | 낮음 | R0 | 강한 통과 |

## 판정과 다음 행동

- 다음 행동: 도입부 냉독
- [약·물] 약속=허용 / 소유=본문 / 상세=OFF
"""


TEST_NOTE = """---
type: stage-test
status: draft
created: 2026-08-29
updated: 2026-08-29
visibility: private
title: "테스트 냉관객 시험"
_evidence_level: R0
_cold_reader_count: 3
---

## 자유 회상 질문

1. 무엇이 반복되거나 달라질 때 주의해야 한다고 느꼈는가?

## 결과 기록

```yaml
cold_entry_test:
  target_text: wiki/writing/drafts/테스트_도입부.md
  evidence_level: 미실행
  primary_mode: 단일 무대 약속
  recalled_viewing_code_if_applicable:
    stage_code: 미실행
    repetition_compulsion_image_voice_or_role: 미실행
    cost_exhaustion_fixation_or_residue: 미실행
  curiosity: 미실행
  blocking_rules: 미실행
  viewing_method_learned: 미실행
  theatricality_score_before: 19/20
  theatricality_score_after: 미측정
  response: 미판정
```
"""


SCENE_NOTE = """---
type: draft-scene
status: draft
created: 2026-08-29
updated: 2026-08-29
visibility: private
title: "담가두면 돌아옵니다 — 도입부"
---

## 도입부

무대. 번호표를 든 사람이 서 있다.

남자: 아직 들고 계시네요.
"""


def run(text: str, *args: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        note = Path(tmp) / "note.md"
        note.write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(VERIFIER), str(note), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )


def expect_pass(label: str, text: str, *args: str) -> bool:
    result = run(text, *args)
    if result.returncode == 0:
        print(f"ok   {label}")
        return True
    print(f"FAIL {label}: expected pass, got:\n{result.stderr.strip()}")
    return False


def expect_skip(label: str, text: str, needle: str, *args: str) -> bool:
    """Out of scope must exit 0 and say so — not pass quietly, not fail loudly."""
    result = run(text, *args)
    if result.returncode != 0:
        print(f"FAIL {label}: expected skip, got:\n{result.stderr.strip()}")
        return False
    if not result.stdout.startswith("SKIP:") or needle not in result.stdout:
        print(f"FAIL {label}: skipped without saying why:\n{result.stdout.strip()}")
        return False
    print(f"ok   {label}")
    return True


def expect_fail(label: str, text: str, needle: str, *args: str) -> bool:
    result = run(text, *args)
    if result.returncode == 0:
        print(f"FAIL {label}: expected rejection, but it passed")
        return False
    if needle not in result.stderr:
        print(f"FAIL {label}: rejected for the wrong reason:\n{result.stderr.strip()}")
        return False
    print(f"ok   {label}")
    return True


def main() -> int:
    results = [
        expect_pass("valid design", design_note()),
        expect_pass("valid review", REVIEW_NOTE),
        # A sub-14 score presented without 조건부 is the failure the gate exists to stop.
        expect_fail(
            "sub-14 mode fit shown as a plain pass",
            design_note(frontmatter=DESIGN_FRONTMATTER.replace("_mode_fit: 16/20", "_mode_fit: 11/20")),
            "hard gate",
        ),
        expect_pass(
            "sub-14 mode fit marked 조건부",
            design_note(
                frontmatter=DESIGN_FRONTMATTER.replace("_mode_fit: 16/20", "_mode_fit: 11/20"),
                extra="\n모드 적합성 조건부. 다른 모드로 재라우팅한다.\n",
            ),
        ),
        expect_fail(
            "score above the 20-point maximum",
            design_note(frontmatter=DESIGN_FRONTMATTER.replace("_mode_fit: 16/20", "_mode_fit: 24/20")),
            "above the 20-point maximum",
        ),
        expect_fail(
            "mode named but never routed",
            design_note().replace("mode_boundary_router:", "notes:").replace("모드 경계 라우터", "모드 선택"),
            "not routed, only named",
        ),
        expect_fail(
            "required design card absent",
            design_note().replace("theatricality_entry_card", "some_other_card"),
            "theatricality_entry_card",
        ),
        expect_fail(
            "13 items out of order",
            design_note(items=DESIGN_ITEMS[:6] + [DESIGN_ITEMS[7], DESIGN_ITEMS[6]] + DESIGN_ITEMS[8:]),
            "out of order",
        ),
        expect_fail(
            "dropped final [약·물] item",
            design_note(items=DESIGN_ITEMS[:12]),
            "missing item 13",
        ),
        expect_fail(
            "unknown primary mode",
            design_note(frontmatter=DESIGN_FRONTMATTER.replace("단일무대약속", "리얼리즘풍")),
            "_primary_mode` unknown",
        ),
        expect_fail(
            "secondary mode declared but never contracted",
            design_note(
                frontmatter=DESIGN_FRONTMATTER.replace("_secondary_mode: 해당없음", "_secondary_mode: 부조리극")
            ).replace("보조 모드", "x").replace("혼합", "x"),
            "never contracts it",
        ),
        expect_fail(
            "R0 review promoted to status stable",
            design_note(frontmatter=DESIGN_FRONTMATTER.replace("status: draft", "status: stable")),
            "must be `draft`",
        ),
        expect_fail(
            "evidence level omitted",
            design_note(frontmatter=DESIGN_FRONTMATTER.replace("_evidence_level: R0\n", "")),
            "_evidence_level",
        ),
        expect_fail(
            "review without a verdict",
            REVIEW_NOTE.replace("- 상태: 통과\n", ""),
            "no 상태 value",
        ),
        expect_fail(
            "review without the [약·물] line",
            REVIEW_NOTE.replace("- [약·물] 약속=허용 / 소유=본문 / 상세=OFF\n", ""),
            "약·물",
        ),
        expect_fail("no frontmatter", "# 제목만 있는 문서\n", "frontmatter"),
        # A comparison map is a third artifact kind — checking it as a design
        # rejected a correct document on the skill's first real run.
        expect_pass("valid comparison map", MAP_NOTE),
        expect_fail(
            "map that links fewer than two designs",
            MAP_NOTE.replace(
                '  - "[[wiki/writing/draft-candidates/테스트_설계B]]"\n'
                '  - "[[wiki/writing/draft-candidates/테스트_설계C]]"\n',
                "",
            ),
            "must link the design documents",
        ),
        expect_fail(
            "map without the five-axis comparison",
            MAP_NOTE.replace("## 독립성 5축", "## 세 안 요약"),
            "five-axis independence",
        ),
        expect_fail(
            "map without an evidence-grade column",
            MAP_NOTE.replace("| 증거 등급 ", "| 비고 "),
            "증거 등급",
        ),
        expect_fail(
            "map with no next action",
            MAP_NOTE.replace("- 다음 행동: 도입부 냉독\n", ""),
            "no 다음 행동",
        ),
        # §21: one context read in several voices is not an independent review.
        expect_fail(
            "R0 output calling itself an independent review",
            MAP_NOTE.replace("## 판정과 다음 행동", "## 판정과 다음 행동\n\n독립 리뷰 3실을 돌렸다."),
            "without documenting isolation",
        ),
        # Isolation, not evidence grade, is what earns the term (§21).
        expect_pass(
            "R0 independent review that documents isolation",
            MAP_NOTE.replace(
                "## 판정과 다음 행동",
                "## 판정과 다음 행동\n\n격리된 별도 에이전트 3인에게 패킷만 준 독립 리뷰다.",
            ),
        ),
        expect_pass(
            "R0 output labelled as multi-perspective review",
            MAP_NOTE.replace(
                "## 판정과 다음 행동",
                "## 판정과 다음 행동\n\n독립 리뷰가 아니라 R0 다중 관점 검토다.",
            ),
        ),
        # §5: the worst thing this pipeline can produce is a reader response nobody gave.
        expect_pass("unrun cold-entry test, honestly empty", TEST_NOTE),
        expect_fail(
            "unrun test with invented reader answers",
            TEST_NOTE.replace(
                "    stage_code: 미실행", "    stage_code: 번호가 넘어가는 것을 보았다"
            ),
            "never invent what a cold reader said",
        ),
        expect_fail(
            "unrun test that already carries a verdict",
            TEST_NOTE.replace("response: 미판정", "response: 유지"),
            "already carries a verdict",
        ),
        expect_fail(
            "claimed H1 evidence with recall fields left unrun",
            TEST_NOTE.replace("evidence_level: 미실행", "evidence_level: H1"),
            "some recall fields are still 미실행",
        ),
        expect_fail(
            "cold-entry test with no cold_entry_test block",
            TEST_NOTE.replace("cold_entry_test:", "notes:"),
            "`cold_entry_test` block is absent",
        ),
        expect_fail(
            "cold-entry test with no free-recall questions",
            TEST_NOTE.replace("## 자유 회상 질문", "## 물어볼 것"),
            "free-recall questions are missing",
        ),
        # H1 is no longer called, so R0 is the ceiling and the bar rises to compensate.
        expect_pass(
            "completed R0 test with three isolated readers",
            TEST_NOTE.replace("evidence_level: 미실행", "evidence_level: R0")
            .replace("    stage_code: 미실행", "    stage_code: 번호표 교환 — 3/3")
            .replace(
                "    repetition_compulsion_image_voice_or_role: 미실행",
                "    repetition_compulsion_image_voice_or_role: 보려다 멈추는 동작 — 3/3",
            )
            .replace(
                "    cost_exhaustion_fixation_or_residue: 미실행",
                "    cost_exhaustion_fixation_or_residue: 수신되지 않은 사과 — 3/3",
            )
            .replace("  curiosity: 미실행", "  curiosity: 열의 침묵")
            .replace("  blocking_rules: 미실행", "  blocking_rules: 왜 열에게 갔는가 3/3")
            .replace("  viewing_method_learned: 미실행", "  viewing_method_learned: 손과 숫자를 보라")
            .replace("  theatricality_score_after: 미측정", "  theatricality_score_after: 19/20")
            .replace("  response: 미판정", "  response: 국소교정"),
        ),
        expect_fail(
            "completed R0 test with only two readers",
            TEST_NOTE.replace("_cold_reader_count: 3", "_cold_reader_count: 2")
            .replace("evidence_level: 미실행", "evidence_level: R0")
            .replace("    stage_code: 미실행", "    stage_code: 번호표 교환 — 2/2")
            .replace(
                "    repetition_compulsion_image_voice_or_role: 미실행",
                "    repetition_compulsion_image_voice_or_role: 보려다 멈추는 동작",
            )
            .replace(
                "    cost_exhaustion_fixation_or_residue: 미실행",
                "    cost_exhaustion_fixation_or_residue: 수신되지 않은 사과",
            )
            .replace("  curiosity: 미실행", "  curiosity: 열의 침묵")
            .replace("  blocking_rules: 미실행", "  blocking_rules: 없음")
            .replace("  viewing_method_learned: 미실행", "  viewing_method_learned: 손과 숫자")
            .replace("  response: 미판정", "  response: 유지"),
            "`_cold_reader_count` must be 3 or more",
        ),
        # The classifier used to fall back to `design` for every unlisted type, so a
        # scene body was reported as a design missing all 13 items. Out of scope is
        # not a defect: skip, exit 0, and name the reason.
        expect_skip("scene body is out of scope, not a broken design", SCENE_NOTE, "out-of-scope"),
        expect_skip(
            "an unregistered type is skipped rather than graded as a design",
            SCENE_NOTE.replace("type: draft-scene", "type: some-future-type"),
            "out-of-scope",
        ),
        # In the storage convention's table, but no shape is fixed for it here.
        expect_skip(
            "structure-test reports as unchecked, not as a design",
            SCENE_NOTE.replace("type: draft-scene", "type: structure-test"),
            "no-shape-rules",
        ),
        # The escape hatch: inference is strict, an explicit --kind still forces it.
        expect_fail(
            "--kind forces design rules onto a scene body",
            SCENE_NOTE,
            "missing item 1",
            "--kind",
            "design",
        ),
        # The four in-scope types must still route to their own checkers.
        expect_pass("draft-candidate still routes to the design checker", design_note()),
    ]

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
