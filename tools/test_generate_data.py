# -*- coding: utf-8 -*-
import unittest
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_data as g


class TestFrontmatter(unittest.TestCase):
    def test_scalar_and_list(self):
        text = (
            '---\n'
            'type: writing-note-evaluation\n'
            'title: "출처 확인 중인 위로 — 평가 완료"\n'
            'sources:\n'
            '  - "wiki/writing/notes/출처_확인_중인_위로.md"\n'
            '---\n\n# 본문\n'
        )
        fm = g.parse_frontmatter(text)
        self.assertEqual(fm["type"], "writing-note-evaluation")
        self.assertEqual(fm["sources"], ["wiki/writing/notes/출처_확인_중인_위로.md"])

    def test_no_frontmatter(self):
        self.assertEqual(g.parse_frontmatter("# 그냥 본문"), {})


class TestNormalizeSource(unittest.TestCase):
    def test_four_variants(self):
        key = "wiki/bookclub/books/궤도/00_책카드"
        self.assertEqual(g.normalize_source('"wiki/bookclub/books/궤도/00_책카드.md"'), key)
        self.assertEqual(g.normalize_source("wiki/bookclub/books/궤도/00_책카드.md"), key)
        self.assertEqual(g.normalize_source('"[[wiki/bookclub/books/궤도/00_책카드]]"'), key)
        self.assertEqual(g.normalize_source("[[wiki/bookclub/books/궤도/00_책카드|궤도]]"), key)

    def test_raw_path_with_space(self):
        self.assertEqual(
            g.normalize_source('"bookclub/석촌호수책모임/_혼모노_ 성해나.md"'),
            "bookclub/석촌호수책모임/_혼모노_ 성해나")


class TestVerdict(unittest.TestCase):
    def test_twin_variants(self):
        # 실측 변형 5종 (스펙 파싱 규칙 1)
        self.assertEqual(g.extract_verdict("- 판정: **유망★** / 채점: ..."), ("유망★", None))
        self.assertEqual(g.extract_verdict("- 판정: 유망★ (8축 만점) / 운반체 후보"), ("유망★", "8축 만점"))
        self.assertEqual(g.extract_verdict("- 판정: **유망★ — 집필 대기 큐 4순위**"), ("유망★", None))
        self.assertEqual(g.extract_verdict("- 판정: **유망** (소품 규격) / 채점"), ("유망", "소품 규격"))
        self.assertEqual(g.extract_verdict("- 판정: **병합** / 채점: A1○"), ("병합", None))
        self.assertIsNone(g.extract_verdict("판정 없음 본문")[0])

    def test_map_cell_variants(self):
        self.assertEqual(g.parse_verdict_cell("**유망★(흡수)**"), ("유망★", "흡수"))
        self.assertEqual(g.parse_verdict_cell("**병합(모체)**"), ("병합", "모체"))
        self.assertEqual(g.parse_verdict_cell("유망(소품)"), ("유망", "소품"))
        self.assertEqual(g.parse_verdict_cell("**진행 중**"), ("진행 중", None))
        self.assertEqual(g.parse_verdict_cell("**유망★**"), ("유망★", None))


class TestLineage(unittest.TestCase):
    def test_cut_at_punctuation(self):
        self.assertEqual(g.extract_lineage("- 계열: 결함/생존 (신규 — 노인과바다×고래 유입)."), "결함/생존")
        self.assertEqual(g.extract_lineage("- 계열: 진짜/출처 운반체 후보. **집필 후보 검토 대상.**"),
                         "진짜/출처 운반체 후보")
        self.assertEqual(g.extract_lineage("- 계열: 말/작별 · 노동 교차."), "말/작별 · 노동 교차")
        self.assertIsNone(g.extract_lineage("계열 언급 없음"))


class TestTable(unittest.TestCase):
    def test_split_row_with_wikilink_pipe(self):
        # 위키링크 내부 |는 셀 구분자가 아니다 (배치 1~6 실측 형식)
        cells = g.split_row("| [[wiki/writing/notes/3_8초_지연_scored|3.8초 지연]] | △ △ △ | **병합** |")
        self.assertEqual(len(cells), 3)
        self.assertEqual(cells[0], "[[wiki/writing/notes/3_8초_지연_scored|3.8초 지연]]")

    def test_stem_from_cell(self):
        self.assertEqual(g.stem_from_cell("[[wiki/writing/notes/3_8초_지연_scored|3.8초 지연]]"), "3_8초_지연")
        self.assertEqual(g.stem_from_cell("[[wiki/writing/notes/그늘은_예약할_수_없습니다|그늘]]"), "그늘은_예약할_수_없습니다")
        self.assertEqual(g.stem_from_cell("**출처_확인_중인_위로**"), "출처_확인_중인_위로")

    def test_extract_tables(self):
        text = ("앞 문장\n\n| 글감 | 판정 |\n|---|---|\n| 왜요 | 유망 |\n| 흼_설명회 | 병합 |\n\n뒤 문장\n")
        tables = g.extract_tables(text)
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0][0], ["글감", "판정"])   # 헤더 행
        self.assertEqual(len(tables[0]), 3)                  # 구분선 제외 헤더+데이터 2


def make_vault(files):
    """dict{상대경로: 내용} → 임시 vault 루트 Path. 호출자가 TemporaryDirectory 관리."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return tmp, root


TWIN = ('---\ntype: writing-note-evaluation\nsources:\n  - "wiki/writing/notes/왜요.md"\n---\n'
        '# 왜요 — 평가 완료\n- 판정: **유망** (소품 규격) / 채점: A1○\n- 계열: 말/작별 · 노동 교차.\n')
FAKE_TWIN = ('---\ntype: writing-note\n---\n# 1차 개명 원본\n- 판정: **유망** 처방이 본문에 있음\n')

NOTE_WITH_BOOK = ('---\ntype: writing-note\nsources:\n'
                  '  - "wiki/bookclub/books/혼모노/00_책카드.md"\n'
                  '  - "bookclub/석촌호수책모임/_혼모노_ 성해나.md"\n---\n# 노트\n')
DEVICE_MAP = ('---\ntype: writing-map\nsources:\n'
              '  - "bookclub/석촌호수책모임/_혼모노_ 성해나.md"\n'
              '  - "wiki/bookclub/books/혼모노/00_책카드.md"\n---\n# 지도\n')


class TestScanTwins(unittest.TestCase):
    def test_type_gate_and_extraction(self):
        tmp, root = make_vault({
            "wiki/writing/notes/왜요_scored.md": TWIN,
            "wiki/writing/notes/관심_지도_scored.md": FAKE_TWIN,   # type이 달라 무시돼야 함
        })
        with tmp:
            unparsed = []
            twins = g.scan_twins(root, unparsed)
            self.assertIn("왜요", twins)
            self.assertNotIn("관심_지도", twins)      # 이중 계상 방지 (스펙 파싱 규칙 1)
            self.assertEqual(twins["왜요"]["verdict"], "유망")
            self.assertEqual(twins["왜요"]["lineage"], "말/작별 · 노동 교차")
            self.assertEqual(twins["왜요"]["path"], "wiki/writing/notes/왜요")
            self.assertEqual(unparsed, [])

    def test_missing_verdict_goes_unparsed(self):
        broken = '---\ntype: writing-note-evaluation\n---\n# 깨진 쌍둥이\n판정 줄이 없다\n'
        tmp, root = make_vault({"wiki/writing/notes/깨짐_scored.md": broken})
        with tmp:
            unparsed = []
            twins = g.scan_twins(root, unparsed)
            self.assertNotIn("깨짐", twins)
            self.assertEqual(len(unparsed), 1)
            self.assertIn("판정", unparsed[0]["reason"])


TRIAGE_FIXTURE = """# 글감 트리아지 지도

## 배치 1 — notes 1~20 (2026-07-04)

| 글감 | A1 A2 A3 | B1 B2 B3 B4 B5 | 판정 | 가장 약한 축 / 한 줄 사유 | 계열(가) |
|---|---|---|---|---|---|
| [[wiki/writing/notes/3_8초_지연_scored|3.8초 지연]] | △ △ △ | ✕ ✕ ✕ ✕ ○ | **병합** | 독백 | 통신/지연 |
| [[wiki/writing/notes/거울을_옮기는_사람|거울을 옮기는 사람]] | — | — | **진행 중** | 활성 | 돌봄/반복 |

### 배치 1 대상 아님 (메타/작업 파일 — 개명·채점 제외)

- [[wiki/writing/notes/수많은_일인칭]] — 메타
- 설명란_부족 — 진행 중 원고

### 배치 1에서 보이기 시작한 계열

| 계열 | 글감 수 | 비고 |
|---|---|---|
| 통신/지연 | 1 | 초기 |

## 배치 12 — 신규 노트 101~106 (2026-07-04, 최종 잔여분)

| 글감 | 판정 | 한 줄 사유 | 계열 |
|---|---|---|---|
| 왜요 | 유망(소품) | 한 단어 | 말/작별·노동 |
| 주정으로_처리하지_마세요 | **유망★** | 자기강화 루프 | 기록-발언 운반체 후보 |

## 전체 트리아지 완료 (2026-07-04)

| 구분 | notes | draft-candidates | 합계 |
|---|---|---|---|
| 유망★ | 13 | 8 | **21** |
"""


class TestTriageMap(unittest.TestCase):
    def test_parse(self):
        unparsed = []
        r = g.parse_triage_map(TRIAGE_FIXTURE, unparsed)
        e = r["entries"]
        # 배치 1 (6열 위키링크 형식)
        self.assertEqual(e["3_8초_지연"]["verdict"], "병합")
        self.assertEqual(e["3_8초_지연"]["lineage"], "통신/지연")
        self.assertEqual(e["3_8초_지연"]["batch"], 1)
        self.assertEqual(e["거울을_옮기는_사람"]["verdict"], "진행 중")
        # 배치 12 (4열 플레인 형식)
        self.assertEqual(e["왜요"]["verdict"], "유망")
        self.assertEqual(e["왜요"]["qualifier"], "소품")
        self.assertEqual(e["주정으로_처리하지_마세요"]["verdict"], "유망★")
        self.assertEqual(e["주정으로_처리하지_마세요"]["batch"], 12)
        # 오탐 배제: 집계표(판정 열 없음)와 계열 보조표의 행이 글감으로 오인되지 않음
        self.assertNotIn("유망★", e)
        self.assertNotIn("통신/지연", e)
        # 대상 아님 수집 (위키링크·플레인 양쪽)
        self.assertIn("수많은_일인칭", r["excluded"])
        self.assertIn("설명란_부족", r["excluded"])

    def test_excluded_multi_name_bullet(self):
        text = (
            "## 배치 5 — notes (2026-07-04)\n\n"
            "### 배치 5 대상 아님 (기법 노트 — 개명·채점 제외)\n\n"
            "- `좋은_마찰을_무대에_남기는_법`, `침묵을_설명하지_않고_들리게_하는_법` — 기법 노트\n"
            "- 설명란_부족 — 진행 중 원고\n"
        )
        r = g.parse_triage_map(text, [])
        self.assertIn("좋은_마찰을_무대에_남기는_법", r["excluded"])
        self.assertIn("침묵을_설명하지_않고_들리게_하는_법", r["excluded"])
        self.assertIn("설명란_부족", r["excluded"])


LINEAGE_FIXTURE = """# 글감 계열·병합 지도

## 계열 지도

### 1. 기록 — 유류품/애도

| 역할 | 글감 | 상태 |
|---|---|---|
| 운반체 | [[wiki/writing/draft-candidates/폐기_전_확인_초고후보_scored|폐기 전 확인]] ★ | 조립 |
| 독립 가능 | [[wiki/writing/notes/라벨_없음_scored|라벨 없음]] ★ | 설계 |
| 비트 | 고작이라는_말 | 부품 |

### 3. 기록 — 보정 체인

기록이 좋아질수록 사람이 사라지는 극. **운반체 없음 → 신규 극 후보.**

| 역할 | 글감 | 상태 |
|---|---|---|
| 체인 순서 | 잡음이_제거되었습니다 | 부품 |

## 병합 후보 요약

| # | 병합 극 | 재료 | 다음 행동 |
|---|---|---|---|
| A | 유류품 인계극 | 한_장짜리_보고서 + 그건_관련이 | 차별화 확인 후 2단계 처방 |
| H | 공동 수리 극 | 상호_번역_작업대 ★ × 공동_수리_허가 | 재해석 후 2부 구조 설계 |
"""


class TestLineageMap(unittest.TestCase):
    def test_lineages(self):
        unparsed = []
        r = g.parse_lineage_map(LINEAGE_FIXTURE, unparsed)
        by_name = {x["name"]: x for x in r["lineages"]}
        rec = by_name["기록 — 유류품/애도"]
        self.assertEqual(rec["carrier"], "폐기 전 확인")
        self.assertEqual(rec["stars"], 2)
        self.assertEqual(rec["members"], 2)     # 부품 제외
        self.assertEqual(rec["parts"], 1)
        self.assertEqual(rec["state"], "조립")   # 운반체의 상태
        self.assertIsNone(by_name["기록 — 보정 체인"]["carrier"])  # 운반체 없음 선언

    def test_mergers_only_from_summary_table(self):
        unparsed = []
        r = g.parse_lineage_map(LINEAGE_FIXTURE, unparsed)
        ids = [m["id"] for m in r["mergers"]]
        self.assertEqual(ids, ["A", "H"])
        self.assertEqual(r["mergers"][1]["nextAction"], "재해석 후 2부 구조 설계")

    def test_kanban_cards(self):
        unparsed = []
        r = g.parse_lineage_map(LINEAGE_FIXTURE, unparsed)
        titles = {(c["title"], c["state"]) for c in r["cards"]}
        self.assertIn(("폐기 전 확인", "조립"), titles)
        self.assertIn(("라벨 없음", "설계"), titles)          # ★라서 설계 카드 포함
        self.assertNotIn(("고작이라는_말", "부품"), titles)   # 부품은 카드 아님

    def test_headerless_role_table(self):
        text = ("### 24. 공동 작업 (신규)\n\n"
                "| 독립 가능 | 귀환_좌표_변경(관제팀) | 설계 |\n"
                "|---|---|---|\n"
                "| 부품 | 관측만으로는_구조가_아닙니다 | 부품 |\n")
        r = g.parse_lineage_map(text, [])
        rec = [x for x in r["lineages"] if x["name"].startswith("공동 작업")][0]
        self.assertEqual(rec["members"], 1)
        self.assertEqual(rec["parts"], 1)

    def test_stars_counted_from_rows_only(self):
        text = ("### 19. 노동 — 몸/비용 (신규) — ★ 3편 밀집\n\n"
                "| 역할 | 글감 | 상태 |\n"
                "|---|---|---|\n"
                "| 운반체 | 교대자를_찾으셔야_합니다 ★ (휴식의 비용 전가 — 메모) | 설계 |\n"
                "| 독립 강자 | 시간을_견딘_것은_누구입니까 ★ | 설계 |\n")
        r = g.parse_lineage_map(text, [])
        rec = r["lineages"][0]
        self.assertEqual(rec["stars"], 2)          # 헤더의 ★는 세지 않음
        self.assertEqual(rec["carrier"], "교대자를_찾으셔야_합니다")   # 괄호 주석 제거


class TestBooks(unittest.TestCase):
    def _root(self):
        return make_vault({
            "wiki/bookclub/books/혼모노/00_책카드.md": "---\ntype: book-card\n---\n# 혼모노\n",
            "wiki/bookclub/books/궤도/00_책카드.md": "---\ntype: book-card\n---\n# 궤도\n",
            "wiki/writing/notes/바나나맛_진짜.md": NOTE_WITH_BOOK,
            "wiki/writing/notes/바나나맛_진짜_scored.md": TWIN,  # sources 스캔에서 제외돼야 함
            "wiki/writing/maps/혼모노_원본_창작장치_지도.md": DEVICE_MAP,
            "bookclub/석촌호수책모임/_혼모노_ 성해나.md": "로우 데이터",
            "bookclub/석촌호수책모임/모임기록.md": "로우 데이터 2",
            "bookclub/석촌호수책모임/표지.webp": "binary-ish",   # md 아님 → rawTotal 제외
        })

    def test_book_linkage(self):
        tmp, root = self._root()
        with tmp:
            sources = g.scan_note_sources(root)
            self.assertIn("바나나맛_진짜", sources)
            self.assertNotIn("바나나맛_진짜_scored", sources)
            verdicts = {"바나나맛_진짜": {"verdict": "유망★", "lineage": "진짜/출처"}}
            r = g.scan_books(root, sources, lambda s: verdicts.get(s))
            self.assertEqual(r["rawTotal"], 2)          # .md만
            self.assertEqual(r["deviceMapTotal"], 1)
            by_title = {b["title"]: b for b in r["books"]}
            self.assertEqual(by_title["혼모노"]["derivedNotes"], 1)
            self.assertEqual(by_title["혼모노"]["stars"], 1)
            self.assertEqual(by_title["혼모노"]["rawNotes"], 1)   # 장치 지도 교량
            self.assertEqual(by_title["혼모노"]["lineages"], ["진짜/출처"])
            self.assertEqual(by_title["궤도"]["derivedNotes"], 0)  # 미채굴


class TestUnscoredAndActions(unittest.TestCase):
    def test_unscored(self):
        tmp, root = make_vault({
            "wiki/writing/notes/새_글감.md": "---\ntype: writing-note\n---\n# 새 글감\n",
            "wiki/writing/notes/왜요.md": "---\ntype: writing-note\n---\n# 왜요\n",
            "wiki/writing/notes/왜요_scored.md": TWIN,
            "wiki/writing/notes/수많은_일인칭.md": "---\ntype: writing-note\n---\n# 메타\n",
            "wiki/writing/notes/글감_트리아지_지도.md": "---\ntype: writing-note\n---\n# 지도\n",
        })
        with tmp:
            r = g.compute_unscored(root, twins={"왜요": {}}, entries={},
                                   excluded={"수많은_일인칭"})
            titles = [x["title"] for x in r]
            self.assertEqual(titles, ["새_글감"])   # 쌍둥이·제외·지도 자신 전부 빠짐

    def test_next_actions_rules(self):
        unscored = [{"title": "n%d" % i, "link": None} for i in range(12)]
        lineages = [{"name": "기록 — 보정 체인", "carrier": None, "stars": 1,
                     "members": 3, "parts": 5, "state": "설계"}]
        cards = [{"title": "라벨 없음", "lineage": "기록", "star": True,
                  "state": "설계", "link": None}]
        acts = g.compute_next_actions(unscored, lineages, cards)
        self.assertEqual(len(acts), 3)
        self.assertIn("12편 대기", acts[0]["text"])
        self.assertIn("보정 체인", acts[1]["text"])
        self.assertIn("라벨 없음", acts[2]["text"])

    def test_next_actions_empty(self):
        acts = g.compute_next_actions([], [], [])
        self.assertEqual(len(acts), 1)
        self.assertIn("계속 쓰세요", acts[0]["text"])


class TestWriter(unittest.TestCase):
    def test_write_utf8_and_shape(self):
        tmp = tempfile.TemporaryDirectory()
        with tmp:
            out = Path(tmp.name) / "data.js"
            g.write_data_js({"generated": "지금", "한글": ["값"]}, out)
            raw = out.read_bytes()
            text = raw.decode("utf-8")                    # cp949였다면 여기서 깨짐/예외
            self.assertTrue(text.startswith("window.VAULT_DATA = {"))
            self.assertTrue(text.rstrip().endswith(";"))
            self.assertIn('"한글"', text)                  # ensure_ascii=False


if __name__ == "__main__":
    unittest.main()
