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


if __name__ == "__main__":
    unittest.main()
