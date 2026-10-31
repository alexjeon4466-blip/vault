#!/usr/bin/env python3
"""Strict-TDD tests for the standalone public community Scrapy spider."""

# Fixture HTML/text is synthetic; numeric URLs are parser inputs, not fetch targets.
from __future__ import annotations

import importlib.util
import inspect
import os
import sys
import tempfile
import unittest
from pathlib import Path

import scrapy
from scrapy.http import HtmlResponse


TARGET = Path(__file__).with_name("public-community-spider.py")
_TEST_TMP = tempfile.TemporaryDirectory(prefix="play-seed-tests-")
ARTIFACT_ROOT = Path(
    os.environ.get(
        "HERMES_SCRAPY_TEST_ROOT",
        _TEST_TMP.name,
    )
)


def load_target():
    spec = importlib.util.spec_from_file_location("public_community_spider", TARGET)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load target: {TARGET}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_response(url: str, html: str, status: int = 200) -> HtmlResponse:
    request = scrapy.Request(url=url)
    return HtmlResponse(
        url=url,
        request=request,
        body=html.encode("utf-8"),
        encoding="utf-8",
        status=status,
    )


def make_spider(module, site: str = "instiz", **overrides):
    arguments = {
        "site": site,
        "target_date": "2026-07-31",
        "output_root": str(ARTIFACT_ROOT.resolve()),
        "max_pages": "1",
    }
    arguments.update(overrides)
    return module.PublicCommunitySpider(**arguments)


REQUIRED_POST_FIELDS = {
    "site",
    "canonical_id",
    "canonical_url",
    "list_title",
    "opened_title",
    "page_date",
    "body",
    "comments",
    "http_status",
    "selector_counts",
}


class BootstrapContractTests(unittest.TestCase):
    def test_target_spider_exists_for_tdd_entry_point(self) -> None:
        self.assertTrue(
            TARGET.is_file(),
            f"RED expected: target spider is absent: {TARGET}",
        )


class RuntimeContractTests(unittest.TestCase):
    def test_spider_uses_scrapy_217_async_start_api(self) -> None:
        module = load_target()
        self.assertTrue(
            hasattr(module, "PublicCommunitySpider"),
            "RED expected: PublicCommunitySpider is not implemented",
        )
        spider_class = module.PublicCommunitySpider
        self.assertEqual(scrapy.__version__, "2.17.0")
        self.assertTrue(issubclass(spider_class, scrapy.Spider))
        self.assertTrue(inspect.isasyncgenfunction(spider_class.start))

    def test_custom_settings_enforce_conservative_access_policy(self) -> None:
        module = load_target()
        settings = getattr(module.PublicCommunitySpider, "custom_settings", {})
        self.assertTrue(settings, "RED expected: conservative settings are absent")
        self.assertIs(settings["ROBOTSTXT_OBEY"], True)
        self.assertEqual(settings["CONCURRENT_REQUESTS"], 1)
        self.assertEqual(settings["CONCURRENT_REQUESTS_PER_DOMAIN"], 1)
        self.assertGreaterEqual(settings["DOWNLOAD_DELAY"], 2.0)
        self.assertIs(settings["RANDOMIZE_DOWNLOAD_DELAY"], True)
        self.assertEqual(settings["DOWNLOAD_TIMEOUT"], 25)
        self.assertIs(settings["AUTOTHROTTLE_ENABLED"], True)
        self.assertEqual(settings["AUTOTHROTTLE_TARGET_CONCURRENCY"], 0.5)
        retry_codes = set(settings["RETRY_HTTP_CODES"])
        self.assertIn(408, retry_codes)
        self.assertTrue(set(range(500, 600)).issubset(retry_codes))
        self.assertTrue(retry_codes.isdisjoint({403, 429, 430}))


class ValidationContractTests(unittest.TestCase):
    def test_only_four_production_profiles_are_admitted(self) -> None:
        module = load_target()
        profiles = getattr(module, "PROFILES", {})
        self.assertEqual(
            set(profiles), {"instiz", "clien", "82cook", "ruliweb"}
        )
        with self.assertRaisesRegex(ValueError, "unsupported site"):
            module.PublicCommunitySpider(
                site="unapproved",
                target_date="2026-07-31",
                output_root=str(ARTIFACT_ROOT.resolve()),
                max_pages="1",
            )

    def test_target_date_is_required(self) -> None:
        module = load_target()
        with self.assertRaisesRegex(ValueError, "target_date"):
            make_spider(module, target_date=None)

    def test_target_date_requires_a_real_zero_padded_calendar_date(self) -> None:
        module = load_target()
        for invalid in ("2026-7-31", "31-07-2026", "2026-02-30", "not-a-date"):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "target_date"):
                    make_spider(module, target_date=invalid)

    def test_valid_target_date_is_retained_as_iso_text(self) -> None:
        module = load_target()
        spider = make_spider(module, target_date="2024-02-29")
        self.assertEqual(spider.target_date, "2024-02-29")

    def test_output_root_is_required(self) -> None:
        module = load_target()
        with self.assertRaisesRegex(ValueError, "output_root"):
            make_spider(module, output_root=None)

    def test_output_root_must_be_absolute(self) -> None:
        module = load_target()
        with self.assertRaisesRegex(ValueError, "output_root.*absolute"):
            make_spider(module, output_root="relative/crawl-output")

    def test_constructor_does_not_create_the_absolute_output_root(self) -> None:
        module = load_target()
        absent_root = ARTIFACT_ROOT / f"not-created-by-spider-{os.getpid()}"
        self.assertFalse(absent_root.exists())
        spider = make_spider(module, output_root=str(absent_root.resolve()))
        self.assertEqual(spider.output_root, absent_root.resolve())
        self.assertFalse(absent_root.exists())

    def test_max_pages_accepts_integer_text_at_both_bounds(self) -> None:
        module = load_target()
        self.assertEqual(make_spider(module, max_pages="1").max_pages, 1)
        self.assertEqual(make_spider(module, max_pages="10").max_pages, 10)

    def test_max_pages_rejects_non_integer_or_out_of_range_values(self) -> None:
        module = load_target()
        for invalid in (None, "many", "1.5", "0", 0, "11", 11):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "max_pages"):
                    make_spider(module, max_pages=invalid)


class ListParserContractTests(unittest.TestCase):
    def test_ruliweb_requires_advice_read_links_and_deduplicates_id(self) -> None:
        module = load_target()
        spider = make_spider(module, site="ruliweb")
        response = make_response(
            "https://bbs.ruliweb.com/community/board/300147",
            """
            <html><body>
              <a class="subject" href="/community/board/300147/read/91000001"> 파서 시험 제목 A </a>
              <a href="https://bbs.ruliweb.com/community/board/300147/read/91000001">중복 제목</a>
              <a href="/community/board/300143/read/91000003">다른 게시판</a>
              <a href="/community/board/300147/read/not-a-number">숫자 ID 아님</a>
              <a href="/community/board/300147/read/91000002?cate=1">금지 query</a>
            </body></html>
            """,
        )
        self.assertEqual(
            spider.extract_list_candidates(response),
            [
                {
                    "site": "ruliweb",
                    "canonical_id": "91000001",
                    "canonical_url": "https://bbs.ruliweb.com/community/board/300147/read/91000001",
                    "list_title": "파서 시험 제목 A",
                }
            ],
        )

    def test_instiz_uses_subject_text_and_removes_query_and_comment_count(self) -> None:
        module = load_target()
        spider = make_spider(module, site="instiz")
        response = make_response(
            "https://www.instiz.net/name",
            """
            <html><body>
              <table>
                <tr><td class="listsubject r7001">
                  <a href="/name/7001?page=1&amp;category=1">
                    <div class="sbj"> 사람 냄새 나는 제목 <span class="cmt2">12</span></div>
                    <div class="list_subtitle">07.31 · 12:03</div>
                  </a>
                </td></tr>
                <tr><td class="listsubject r7001">
                  <a href="https://www.instiz.net/name/7001?category=1&amp;green=1">
                    <span class="texthead_notice">중복 인기 제목 <span class="cmt3">33</span></span>
                  </a>
                </td></tr>
                <tr><td class="listsubject r7002">
                  <a href="/name/not-a-number"><div class="sbj">숫자 ID 아님</div></a>
                </td></tr>
                <tr><td class="listsubject r7003">
                  <a href="/pt/7003"><div class="sbj">다른 게시판</div></a>
                </td></tr>
              </table>
              <a href="/name/7999"><div class="sbj">제목 셀 바깥 링크</div></a>
            </body></html>
            """,
        )
        self.assertEqual(
            spider.extract_list_candidates(response),
            [
                {
                    "site": "instiz",
                    "canonical_id": "7001",
                    "canonical_url": "https://www.instiz.net/name/7001",
                    "list_title": "사람 냄새 나는 제목",
                }
            ],
        )

    def test_clien_requires_exact_board_path_and_preserves_board_in_id(self) -> None:
        module = load_target()
        spider = make_spider(module, site="clien")
        response = make_response(
            "https://www.clien.net/service/group/community?od=T31&po=0",
            """
            <html><body>
              <a class="list_subject" href="/service/board/park/9001?od=T31"> 클리앙 제목 </a>
              <a class="list_subject" href="/service/board/park/9001?po=1">중복 제목</a>
              <a class="list_subject" href="/service/board/park/9001/reply">경로가 더 김</a>
              <a class="other" href="/service/board/park/9002">다른 앵커</a>
              <a class="list_subject" href="/service/board/park/not-a-number">숫자 ID 아님</a>
            </body></html>
            """,
        )
        self.assertEqual(
            spider.extract_list_candidates(response),
            [
                {
                    "site": "clien",
                    "canonical_id": "park/9001",
                    "canonical_url": "https://www.clien.net/service/board/park/9001",
                    "list_title": "클리앙 제목",
                }
            ],
        )

    def test_82cook_requires_bn15_read_links_and_deduplicates_id(self) -> None:
        module = load_target()
        spider = make_spider(module, site="82cook")
        response = make_response(
            "https://www.82cook.com/entiz/enti.php?bn=15",
            """
            <html><body>
              <div id="column2">
                <table><tr><td><a href="/entiz/read.php?bn=15&amp;num=1945163&amp;page=1">테스트용 게시판 공지</a></td></tr></table>
                <a href="/entiz/read.php?bn=15&amp;num=92000001&amp;page=1"> 파서 시험 제목 B </a>
                <a href="/entiz/read.php?num=92000001&amp;bn=15">중복 제목</a>
                <a href="/entiz/read.php?bn=10&amp;num=92000002">다른 게시판</a>
                <a href="/entiz/enti.php?bn=15&amp;num=92000003">목록 링크</a>
                <a href="/entiz/read.php?bn=15&amp;num=not-a-number">숫자 ID 아님</a>
              </div>
            </body></html>
            """,
        )
        self.assertEqual(
            spider.extract_list_candidates(response),
            [
                {
                    "site": "82cook",
                    "canonical_id": "92000001",
                    "canonical_url": (
                        "https://www.82cook.com/entiz/read.php"
                        "?bn=15&num=92000001"
                    ),
                    "list_title": "파서 시험 제목 B",
                }
            ],
        )


class PostParserContractTests(unittest.TestCase):
    def assert_required_record_fields(self, record: dict) -> None:
        self.assertTrue(REQUIRED_POST_FIELDS.issubset(record), record)
        self.assertIsInstance(record["comments"], list)
        self.assertIsInstance(record["selector_counts"], dict)

    def test_ruliweb_extracts_advice_body_but_never_comments(self) -> None:
        module = load_target()
        spider = make_spider(module, site="ruliweb")
        candidate = {
            "site": "ruliweb",
            "canonical_id": "91000001",
            "canonical_url": "https://bbs.ruliweb.com/community/board/300147/read/91000001",
            "list_title": "  목록의 제목  ",
        }
        response = make_response(
            candidate["canonical_url"],
            """
            <html><body>
              <meta property="og:title" content="파서 시험 제목 A">
              <span class="regdate">2026.08.29 (14:07:48)</span>
              <div class="view_content"> 첫째 줄이고\n <b>둘째 줄이다</b> </div>
              <script type="application/ld+json">{"comment":"수집하면 안 되는 댓글"}</script>
              <div class="comment_view">댓글은 계약 밖</div>
            </body></html>
            """,
        )
        record = spider.extract_post_record(response, candidate)
        self.assert_required_record_fields(record)
        self.assertEqual(record["list_title"], "목록의 제목")
        self.assertEqual(record["opened_title"], "파서 시험 제목 A")
        self.assertEqual(record["page_date"], "2026.08.29 (14:07:48)")
        self.assertEqual(record["body"], "첫째 줄이고 둘째 줄이다")
        self.assertEqual(record["comments"], [])
        self.assertEqual(record["http_status"], 200)
        self.assertEqual(record["selector_counts"]["body"], 1)
        self.assertEqual(record["selector_counts"]["comments"], 0)

    def test_instiz_extracts_public_body_metadata_and_bounds_comments(self) -> None:
        module = load_target()
        spider = make_spider(module, site="instiz")
        candidate = {
            "site": "instiz",
            "canonical_id": "7001",
            "canonical_url": "https://www.instiz.net/name/7001",
            "list_title": "인스티즈 목록 제목",
        }
        comments = "".join(
            f'<td class="comment_memo"><div class="comment_line"> 댓글 {number} </div></td>'
            for number in range(1, spider.COMMENT_LIMIT + 4)
        )
        response = make_response(
            candidate["canonical_url"],
            f"""
            <html><head>
              <link rel="canonical" href="https://www.instiz.net/name/7001">
              <meta property="article:published_time" content="2026-07-31T12:03:04+09:00">
            </head><body>
              <span id="nowsubject">
                열린 <span>인스티즈 제목</span> <span class="cmt3">99</span>
              </span>
              <div id="memo_content_1" class="memo_content"> 첫 줄\n <em>둘째 줄</em> </div>
              <table>{comments}</table>
            </body></html>
            """,
        )
        record = spider.extract_post_record(response, candidate)
        self.assert_required_record_fields(record)
        self.assertEqual(record["opened_title"], "열린 인스티즈 제목")
        self.assertEqual(record["page_date"], "2026-07-31T12:03:04+09:00")
        self.assertEqual(record["body"], "첫 줄 둘째 줄")
        self.assertEqual(len(record["comments"]), spider.COMMENT_LIMIT)
        self.assertEqual(record["comments"][0], "댓글 1")
        self.assertEqual(
            record["comments"][-1], f"댓글 {spider.COMMENT_LIMIT}"
        )
        self.assertEqual(
            record["selector_counts"]["comments"], spider.COMMENT_LIMIT + 3
        )
        self.assertEqual(record["selector_counts"]["title"], 1)
        self.assertEqual(record["selector_counts"]["date"], 1)
        self.assertEqual(record["selector_counts"]["body"], 1)
        self.assertTrue(record["public_body_eligible"])
        self.assertIsNone(record["access_exclusion_reason"])

    def test_instiz_members_only_placeholder_is_not_public_body(self) -> None:
        module = load_target()
        spider = make_spider(module, site="instiz")
        candidate = {
            "site": "instiz",
            "canonical_id": "7002",
            "canonical_url": "https://www.instiz.net/name/7002",
            "list_title": "목록에는 보이는 제목",
        }
        response = make_response(
            candidate["canonical_url"],
            """
            <html><head>
              <meta property="article:published_time" content="2026-07-31T12:03:04+09:00">
            </head><body>
              <span id="nowsubject">목록에는 보이는 제목</span>
              <div id="memo_content_1" class="memo_content">
                죄송해요, 회원에게만 공개된 글이에요 로그인 후 이용해 주세요
              </div>
            </body></html>
            """,
        )
        record = spider.extract_post_record(response, candidate)
        self.assertFalse(record["public_body_eligible"])
        self.assertEqual(
            record["access_exclusion_reason"], "members_only_body_wall"
        )

    def test_clien_extracts_subject_article_date_and_comment_views(self) -> None:
        module = load_target()
        spider = make_spider(module, site="clien")
        candidate = {
            "site": "clien",
            "canonical_id": "park/9001",
            "canonical_url": "https://www.clien.net/service/board/park/9001",
            "list_title": "클리앙 목록 제목",
        }
        response = make_response(
            candidate["canonical_url"],
            """
            <html><body>
              <h3 class="post_subject"> 클리앙 <span>열린 제목</span> </h3>
              <div class="post_author"><span class="date">2026-07-31 14:05</span></div>
              <div class="post_article"> 글의 <p>중심 장면</p> </div>
              <div class="comment_row"><div class="comment_view"> 첫 댓글 </div></div>
              <div class="comment_row"><div class="comment_view"> 둘째\n댓글 </div></div>
              <div class="comment_view">행 바깥 댓글은 제외</div>
            </body></html>
            """,
        )
        record = spider.extract_post_record(response, candidate)
        self.assert_required_record_fields(record)
        self.assertEqual(record["opened_title"], "클리앙 열린 제목")
        self.assertEqual(record["page_date"], "2026-07-31 14:05")
        self.assertEqual(record["body"], "글의 중심 장면")
        self.assertEqual(record["comments"], ["첫 댓글", "둘째 댓글"])
        self.assertEqual(record["selector_counts"]["title"], 1)
        self.assertEqual(record["selector_counts"]["body"], 1)

    def test_82cook_extracts_body_but_never_comments(self) -> None:
        module = load_target()
        spider = make_spider(module, site="82cook")
        candidate = {
            "site": "82cook",
            "canonical_id": "92000001",
            "canonical_url": (
                "https://www.82cook.com/entiz/read.php?bn=15&num=92000001"
            ),
            "list_title": " 82cook 목록 제목 ",
        }
        response = make_response(
            candidate["canonical_url"],
            """
            <html><body>
              <div class="bbs_view_comment">작성일 : 2099-01-01 00:00:00 수집하면 안 되는 댓글</div>
              <div id="column2"><h1> 파서 시험 제목 B </h1></div>
              <div class="bbs_view_header">작성일 : 2026-08-15 09:15:18</div>
              <div id="articleBody"> 첫째 줄\n <strong>둘째 줄이다</strong> </div>
              <div class="bbs_view_comment">수집하면 안 되는 댓글</div>
            </body></html>
            """,
        )
        record = spider.extract_post_record(response, candidate)
        self.assert_required_record_fields(record)
        self.assertEqual(record["list_title"], "82cook 목록 제목")
        self.assertEqual(record["opened_title"], "파서 시험 제목 B")
        self.assertEqual(record["page_date"], "2026-08-15 09:15:18")
        self.assertEqual(record["body"], "첫째 줄 둘째 줄이다")
        self.assertEqual(record["comments"], [])
        self.assertEqual(record["selector_counts"]["date"], 1)
        self.assertEqual(record["selector_counts"]["comments"], 0)

    def test_82cook_generic_opened_board_label_preserves_list_title(self) -> None:
        module = load_target()
        spider = make_spider(module, site="82cook")
        candidate = {
            "site": "82cook",
            "canonical_id": "92000004",
            "canonical_url": (
                "https://www.82cook.com/entiz/read.php?bn=15&num=92000004"
            ),
            "list_title": "목록에서 확인한 실제 제목",
        }
        response = make_response(
            candidate["canonical_url"],
            """
            <html><body>
              <div id="column2"><h1>자유게시판</h1></div>
              <div>작성일 : 2026-08-19 21:32:40</div>
              <div id="articleBody">공개 원글 본문</div>
            </body></html>
            """,
        )
        record = spider.extract_post_record(response, candidate)
        self.assertEqual(record["opened_title"], "목록에서 확인한 실제 제목")
        self.assertTrue(record["public_body_eligible"])
        self.assertIsNone(record["access_exclusion_reason"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
