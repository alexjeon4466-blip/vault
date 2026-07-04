# -*- coding: utf-8 -*-
import unittest
from pathlib import Path
import sys
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


if __name__ == "__main__":
    unittest.main()
