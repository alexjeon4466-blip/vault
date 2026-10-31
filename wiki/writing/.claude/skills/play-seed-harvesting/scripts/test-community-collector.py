#!/usr/bin/env python3
"""Offline regression tests for community-collector.py (stdlib only).

All HTML is synthetic and shaped after the observed DOM of each profile; numbers in
URLs are parser inputs, not fetch targets. No test opens a network connection.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

TARGET = Path(__file__).with_name("community-collector.py")
spec = importlib.util.spec_from_file_location("community_collector", TARGET)
cc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cc
spec.loader.exec_module(cc)

KST = cc.KST
FETCHED = datetime(2026, 10, 31, 12, 0, tzinfo=KST)


class FakeTransport:
    """url -> (status, headers, body) or callable(url) -> same, or an Exception."""

    def __init__(self, routes, default=(404, {}, b"")):
        self.routes = routes
        self.default = default
        self.calls: list[str] = []

    def get(self, url):
        self.calls.append(url)
        route = self.routes.get(url, self.default)
        if callable(route):
            route = route(url)
        if isinstance(route, Exception):
            raise route
        if isinstance(route, cc.Response):
            return route
        status, headers, body = route
        if isinstance(body, str):
            body = body.encode("utf-8")
        # deliver in small chunks to exercise incremental decoding
        chunks = [body[i:i + 7] for i in range(0, len(body), 7)] or [b""]
        return cc.Response(status, url, headers, iter(chunks))


def contract(hours=168, end=FETCHED):
    return {"actor": "hermes", "window_end": end.isoformat(),
            "window_start": (end - timedelta(hours=hours)).isoformat()}


def make_site(tmp, profile, transport, actor="hermes", hours=168, clock=lambda: FETCHED):
    c = contract(hours)
    c["actor"] = actor
    return cc.SiteRun(Path(tmp), cc.PROFILES[profile], actor, transport, c,
                      sleep=lambda s: None, clock=clock, min_delay=0)


OPEN_ROBOTS = (200, {}, "User-agent: *\nAllow: /\n")


class DateParsing(unittest.TestCase):
    def test_list_cells(self):
        cases = {
            "11:10": date(2026, 10, 31),
            "13:10": date(2026, 10, 30),  # later than fetch time (12:00) -> yesterday
            "10/27": date(2026, 10, 27),
            "06-26": date(2026, 6, 26),
            "12.25": date(2025, 12, 25),  # future month-day -> previous year
            "2026.10.30": date(2026, 10, 30),
            "26.10.29": date(2026, 10, 29),
            "2026-10-28 09:00:00": date(2026, 10, 28),
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(cc.parse_list_day(raw, FETCHED), expected)
        self.assertIsNone(cc.parse_list_day("조회 12", FETCHED))

    def test_post_timestamps(self):
        cases = {
            "2026-10-31T12:04:00+09:00": "2026-10-31T12:04:00+09:00",
            "2026.10.31\xa0(토) 12:04": "2026-10-31T12:04:00+09:00",
            "조회 81 | 추천 0 | 2026.10.31 (토) 12:04": "2026-10-31T12:04:00+09:00",
            "2026.10.31 (12:34:56)": "2026-10-31T12:34:56+09:00",
            "26.10.31 12:53": "2026-10-31T12:53:00+09:00",
            "2026-10-29 15:06:42": "2026-10-29T15:06:42+09:00",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(cc.parse_post_datetime(raw).isoformat(), expected)
        self.assertIsNone(cc.parse_post_datetime("2026.10.31"), "date-only is not a timestamp")


class Robots(unittest.TestCase):
    INSTIZ_LIKE = ("User-agent: GPTBot\nDisallow: /\n\nUser-agent: ClaudeBot\nUser-agent: anthropic-ai\n"
                   "Disallow: /\n")
    CLIEN_LIKE = ("User-agent: anthropic-ai\nDisallow: /\n\nUser-agent: *\nAllow:/service/board/\n"
                  "Disallow:/service/group/\nDisallow:/service/board/sold/\n")

    def test_hermes_is_judged_by_its_own_token(self):
        self.assertTrue(cc.judge_actor(self.INSTIZ_LIKE, 200, "hermes", "/name")["allowed"])

    def test_claude_respects_any_anthropic_named_denial(self):
        verdict = cc.judge_actor(self.INSTIZ_LIKE, 200, "claude", "/name")
        self.assertFalse(verdict["allowed"])
        self.assertIn("claudebot", verdict["basis"])
        self.assertFalse(cc.judge_actor(self.CLIEN_LIKE, 200, "claude", "/service/board/park")["allowed"])

    def test_longest_match_and_wildcard_group(self):
        self.assertTrue(cc.judge_actor(self.CLIEN_LIKE, 200, "hermes", "/service/board/park/1")["allowed"])
        self.assertFalse(cc.judge_actor(self.CLIEN_LIKE, 200, "hermes", "/service/group/community")["allowed"])
        self.assertFalse(cc.judge_actor(self.CLIEN_LIKE, 200, "hermes", "/service/board/sold/1")["allowed"])

    def test_rfc9309_status_semantics(self):
        self.assertTrue(cc.judge_actor(None, 404, "claude", "/x")["allowed"])
        self.assertFalse(cc.judge_actor(None, 503, "hermes", "/x")["allowed"])
        self.assertFalse(cc.judge_actor(None, "network tcp_connect", "hermes", "/x")["allowed"])

    def test_robots_denial_stops_only_that_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = FakeTransport({"https://www.instiz.net/robots.txt": (200, {}, self.INSTIZ_LIKE)})
            site = make_site(tmp, "instiz", t, actor="claude")
            with self.assertRaises(cc.SiteStopped) as ctx:
                site.discover(page_budget=5)
            self.assertEqual(ctx.exception.state, "robots_denied")
            self.assertEqual(t.calls, ["https://www.instiz.net/robots.txt"], "no list request after denial")
            self.assertFalse((Path(tmp) / "ruliweb").exists())

    # PGR21 (2026-10-31): robots.txt answered 200 with an Anubis challenge page, which parses as "no rules"
    def test_challenge_page_in_place_of_robots_stops_the_site(self):
        page = ('<!doctype html><html><head><title>Oh noes!</title></head><body>'
                '<script id="anubis_challenge" type="application/json">null</script></body></html>')
        with tempfile.TemporaryDirectory() as tmp:
            t = FakeTransport({"https://www.bobaedream.co.kr/robots.txt": (200, {}, page)})
            site = make_site(tmp, "bobaedream", t)
            with self.assertRaises(cc.SiteStopped) as ctx:
                site.discover(page_budget=3)
            self.assertEqual(ctx.exception.state, "challenge")
            self.assertEqual(t.calls, ["https://www.bobaedream.co.kr/robots.txt"])

    def test_plain_html_in_place_of_robots_is_recorded_and_parsed_as_no_rules(self):
        page = "<!DOCTYPE html><html><body><h1>Not found</h1></body></html>"
        with tempfile.TemporaryDirectory() as tmp:
            t = FakeTransport({"https://www.bobaedream.co.kr/robots.txt": (200, {}, page)})
            result = make_site(tmp, "bobaedream", t).robots()
            self.assertTrue(result["robots_html"])
            self.assertTrue(all(j["allowed"] for j in result["judgments"].values()))


class Selectors(unittest.TestCase):
    def test_compound_and_descendant(self):
        root = cc.parse_html('<div class="a b"><p id="x"><a href="/read.php?x" title="t">'
                             '<span class="cmt3">3</span>제목</a></p></div>')
        self.assertEqual(len(root.select("div.a.b p#x a[href*=read.php]")), 1)
        self.assertEqual(root.select_one("a").text(exclude="[class^=cmt]"), "제목")
        self.assertEqual(root.select("div.c"), [])


def ruliweb_list(rows):
    body = "".join(
        f'<tr class="table_body blocktarget"><td class="id">{i}</td><td class="subject"><div class="relative">'
        f'<a class="subject_link deco" href="https://bbs.ruliweb.com/community/board/300147/read/{i}?">'
        f'고민 {i} <span class="num_reply">(9)</span></a></div></td><td class="time">{d}</td></tr>'
        for i, d in rows)
    notice = ('<tr class="table_body notice"><td class="subject"><a class="subject_link" '
              'href="https://bbs.ruliweb.com/community/board/300147/read/1">공지</a></td>'
              '<td class="time">2026.01.01</td></tr>')
    return f"<html><body><table>{notice}{body}</table></body></html>"


class ListParsing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def parse(self, profile, html, url=None):
        site = make_site(self.tmp.name, profile, FakeTransport({}))
        return site.parse_list(html, url or site.p.list_url(1), FETCHED)

    def test_ruliweb(self):
        rows = self.parse("ruliweb", ruliweb_list([(30584842, "11:20"), (30584000, "2026.10.30")]))
        self.assertEqual([r["id"] for r in rows], ["30584842", "30584000"], "notice skipped")
        self.assertEqual(rows[0]["title"], "고민 30584842", "reply counter removed")
        self.assertEqual(rows[0]["day"], "2026-10-31")
        self.assertEqual(rows[1]["day"], "2026-10-30")

    def test_bobaedream_uses_full_title_attribute(self):
        html = ('<table><tr itemscope itemtype="http://schema.org/Article"><td class="num01">1</td>'
                '<td class="pl14"><a class="bsubject" href="/view?code=freeb&No=3448117&bm=1" '
                'title="잘리지 않은 긴 제목입니다">잘리지 않은 ..</a></td><td class="date">10/27</td></tr>'
                '<tr itemscope><td><a class="bsubject" href="/view?code=other&No=9">다른 게시판</a></td>'
                '<td class="date">13:10</td></tr></table>')
        rows = self.parse("bobaedream", html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://www.bobaedream.co.kr/view?code=freeb&No=3448117")
        self.assertEqual(rows[0]["title"], "잘리지 않은 긴 제목입니다")
        self.assertEqual(rows[0]["day"], "2026-10-27")

    def test_inven_skips_notice_and_category(self):
        html = ('<table><tr class="notice all"><td class="tit"><a class="subject-link" '
                'href="https://www.inven.co.kr/board/webzine/2097/272928">공지</a></td><td class="date">06-26</td></tr>'
                '<tr><td class="tit"><div><a class="subject-link" href="https://www.inven.co.kr/board/webzine/2097/2747181">'
                '<span class="category">[잡담]</span> 일상 이야기</a></div></td><td class="date">11:35</td></tr></table>')
        rows = self.parse("inven", html)
        self.assertEqual([(r["id"], r["title"], r["day"]) for r in rows],
                         [("2747181", "일상 이야기", "2026-10-31")])

    def test_82cook_requires_board_15(self):
        html = ('<table><tr><td class="title"><a href="read.php?bn=15&num=4253958">글 <span class="cmtN">3</span></a>'
                '</td><td class="regdate">2026/10/29</td></tr><tr><td class="title">'
                '<a href="read.php?bn=16&num=1">다른 게시판</a></td><td class="regdate">10:00:00</td></tr></table>')
        rows = self.parse("82cook", html, "https://www.82cook.com/entiz/enti.php?bn=15&page=1")
        self.assertEqual([(r["id"], r["title"], r["day"]) for r in rows], [("4253958", "글", "2026-10-29")])

    def test_instiz_category_filter_and_time_cell(self):
        html = ('<table><tr><td class="listsubject"><a href="/name/111?page=1"><span class="sbj">하루'
                '<span class="cmt2">2</span></span></a></td><td class="list_category">일상</td>'
                '<td class="listno regdate">10.27 l 조회</td></tr>'
                '<tr><td class="listsubject"><a href="/name/112"><span class="sbj">다른</span></a></td>'
                '<td class="list_category">이슈</td><td class="regdate">10.27</td></tr></table>')
        rows = self.parse("instiz", html)
        self.assertEqual([(r["id"], r["day"]) for r in rows], [("111", "2026-10-27")])

    def test_clien_board_path_only(self):
        html = ('<div class="list_item symph_row"><a class="list_subject" href="/service/board/park/190001">'
                '<span>공원 글</span></a><span class="timestamp">2026-10-30 21:00:00</span></div>'
                '<div class="list_item notice"><a class="list_subject" href="/service/board/park/1">공지</a></div>'
                '<div class="list_item"><a class="list_subject" href="/service/board/sold/5">판매</a>'
                '<span class="timestamp">2026-10-30 20:00:00</span></div>')
        rows = self.parse("clien", html)
        self.assertEqual([(r["id"], r["day"]) for r in rows], [("190001", "2026-10-30")])


def bobae_list(rows):
    return "<table>" + "".join(
        f'<tr itemscope><td class="pl14"><a class="bsubject" href="/view?code=freeb&No={i}" title="글 {i}">글</a>'
        f'</td><td class="date">{d}</td></tr>' for i, d in rows) + "</table>"


def bobae_post(body, published="2026.10.31&nbsp;(토) 11:04"):
    return ('<html><head><meta property="og:title" content="제목 | 보배드림 자유게시판">'
            '<title>x</title></head><body><div class="writerProfile"><dl><dt class="subject_len" title="원래 제목">'
            f'<strong>원래 제목<em>[3]</em></strong><span class="countGroup">조회 <em>81</em> | {published}</span>'
            f'</dt></dl></div><div class="bodyCont" itemprop="articleBody">{body}</div>'
            '<div id="cmt_list"><ul><li>SECRET_COMMENT 댓글 본문</li></ul></div></body></html>')


class PostFetching(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def site_with_queue(self, routes, ids=("1", "2", "3"), profile="bobaedream"):
        t = FakeTransport({"https://www.bobaedream.co.kr/robots.txt": OPEN_ROBOTS, **routes})
        site = make_site(self.tmp.name, profile, t)
        queue = [{"id": i, "url": site.p.read_url(i), "day": "2026-10-31", "title": f"t{i}"} for i in ids]
        cc.write_json(site.dir / "queue.json", {"receipt": {}, "queue": queue})
        return site, t

    def test_body_stream_stops_before_comments(self):
        site, _ = self.site_with_queue({
            "https://www.bobaedream.co.kr/view?code=freeb&No=1": (200, {"content-type": "text/html; charset=utf-8"},
                                                                  bobae_post("<p>첫 줄</p><p>둘째 줄</p>"))}, ids=("1",))
        site.fetch(max_posts=5)
        record = cc.read_jsonl(site.dir / "posts.jsonl")[0]
        self.assertEqual(record["state"], "eligible")
        self.assertEqual(record["body"], "첫 줄\n둘째 줄")
        self.assertEqual(record["opened_title"], "원래 제목")
        self.assertEqual(record["published_at"], "2026-10-31T11:04:00+09:00")
        self.assertTrue(record["stopped_at_body_close"])
        self.assertNotIn("SECRET_COMMENT", json.dumps(record, ensure_ascii=False))

    def test_wall_deleted_and_old_posts_are_skipped_not_site_stops(self):
        site, t = self.site_with_queue({
            "https://www.bobaedream.co.kr/view?code=freeb&No=1": (200, {}, bobae_post("회원에게만 공개된 글이에요")),
            "https://www.bobaedream.co.kr/view?code=freeb&No=2": (404, {}, ""),
            "https://www.bobaedream.co.kr/view?code=freeb&No=3": (200, {}, bobae_post("오래된 글", "2026.10.01 (목) 09:00")),
        })
        result = site.fetch(max_posts=5)
        self.assertIsNone(result["stop"])
        self.assertEqual(result["post_states"], {"members_only": 1, "deleted": 1, "outside_window": 1})

    def test_403_stops_site_and_records_receipt(self):
        site, t = self.site_with_queue({
            "https://www.bobaedream.co.kr/view?code=freeb&No=1": (200, {}, bobae_post("본문")),
            "https://www.bobaedream.co.kr/view?code=freeb&No=2": (403, {}, "Forbidden"),
        })
        with self.assertRaises(cc.SiteStopped):
            site.fetch(max_posts=5)
        self.assertEqual(site.stopped()["state"], "http_403")
        self.assertNotIn("https://www.bobaedream.co.kr/view?code=freeb&No=3", t.calls)
        with self.assertRaises(cc.SiteStopped):
            site.fetch(max_posts=5)  # a stopped site never resumes silently

    def test_challenge_page_is_a_site_stop(self):
        site, _ = self.site_with_queue({
            "https://www.bobaedream.co.kr/view?code=freeb&No=1": (
                403, {}, "<html><title>Just a moment...</title>cf-chl</html>")}, ids=("1",))
        with self.assertRaises(cc.SiteStopped):
            site.fetch(max_posts=5)
        self.assertEqual(site.stopped()["state"], "challenge")

    def test_network_errors_retry_then_stop_after_limit(self):
        err = cc.NetworkError("tcp_connect", "timed out")
        site, t = self.site_with_queue({site_url: err for site_url in [
            f"https://www.bobaedream.co.kr/view?code=freeb&No={i}" for i in (1, 2, 3)]})
        with self.assertRaises(cc.SiteStopped):
            site.fetch(max_posts=5)
        self.assertEqual(site.stopped()["state"], "network_unreachable")
        self.assertEqual(len([c for c in t.calls if "view" in c]), 9, "3 posts x (1 try + 2 retries)")

    def test_parser_drift_stops_after_consecutive_misses(self):
        page = (200, {}, "<html><body><div class='other'>새 레이아웃</div></body></html>")
        site, _ = self.site_with_queue({f"https://www.bobaedream.co.kr/view?code=freeb&No={i}": page
                                        for i in (1, 2, 3)})
        with self.assertRaises(cc.SiteStopped):
            site.fetch(max_posts=5)
        self.assertEqual(site.stopped()["state"], "parser_drift")

    # 2026-10-31 Hermes batch: clien stopped on selector_missing, and Claude may not open clien itself
    def test_selector_missing_records_structure_but_no_text(self):
        page = (200, {}, "<html><head><title>글 제목</title></head><body><div id='wrap' class='b a'>"
                         "<section class='post_view'><p>비밀 본문</p></section></div></body></html>")
        site, _ = self.site_with_queue({"https://www.bobaedream.co.kr/view?code=freeb&No=1": page})
        site.fetch(max_posts=1)
        record = cc.read_jsonl(site.dir / "posts.jsonl")[0]
        self.assertEqual(record["state"], "selector_missing")
        self.assertEqual(record["dom_outline"], ["2 div#wrap.a.b", "3 section.post_view"])
        self.assertEqual(record["page_title"], "글 제목")
        self.assertNotIn("비밀", str(record))

    def test_resume_skips_done_and_never_repeats_unresolved(self):
        site, t = self.site_with_queue({
            f"https://www.bobaedream.co.kr/view?code=freeb&No={i}": (200, {}, bobae_post(f"본문 {i}"))
            for i in (1, 2, 3)})
        cc.append_jsonl(site.dir / "started.jsonl", {"id": "1", "at": "x"})  # crashed before receipt
        site.fetch(max_posts=1)
        site.fetch(max_posts=5)
        opened = [c for c in t.calls if "view" in c]
        self.assertEqual(opened, ["https://www.bobaedream.co.kr/view?code=freeb&No=2",
                                  "https://www.bobaedream.co.kr/view?code=freeb&No=3"])
        self.assertEqual(site.accounting()["unresolved_attempts"], ["1"])

    def test_forbidden_container_before_body_is_boundary_error(self):
        html = ('<html><head><meta property="og:title" content="t"></head><body>'
                '<div class="comment_list">SECRET</div><div class="view_content">본문</div></body></html>')
        t = FakeTransport({"https://bbs.ruliweb.com/robots.txt": OPEN_ROBOTS,
                           "https://bbs.ruliweb.com/community/board/300147/read/7": (200, {}, html)})
        site = make_site(self.tmp.name, "ruliweb", t)
        cc.write_json(site.dir / "queue.json", {"receipt": {}, "queue": [
            {"id": "7", "url": site.p.read_url("7"), "day": "2026-10-31", "title": "t"}]})
        site.fetch(max_posts=1)
        record = cc.read_jsonl(site.dir / "posts.jsonl")[0]
        self.assertEqual(record["state"], "boundary_error")
        self.assertNotIn("SECRET", json.dumps(record))

    def test_ruliweb_mobile_canonical_is_declared_alias(self):
        html = ('<html><head><link rel="canonical" href="https://m.ruliweb.com/community/board/300147/read/7"/>'
                '<meta property="og:title" content="고민 제목"/></head><body><span class="regdate">'
                '2026.10.31 (10:00:00)</span><div class="view_content"><p>본문</p></div>'
                '<div class="comment_view">SECRET</div></body></html>')
        t = FakeTransport({"https://bbs.ruliweb.com/robots.txt": OPEN_ROBOTS,
                           "https://bbs.ruliweb.com/community/board/300147/read/7": (200, {}, html)})
        site = make_site(self.tmp.name, "ruliweb", t)
        cc.write_json(site.dir / "queue.json", {"receipt": {}, "queue": [
            {"id": "7", "url": site.p.read_url("7"), "day": "2026-10-31", "title": "t"}]})
        site.fetch(max_posts=1)
        record = cc.read_jsonl(site.dir / "posts.jsonl")[0]
        self.assertEqual((record["state"], record["canonical_identity"], record["opened_title"]),
                         ("eligible", "declared_alias", "고민 제목"))


class Discovery(unittest.TestCase):
    """Synthetic board: 300 posts/day, 30 rows/page, newest first => 10 pages/day."""

    PER_DAY, PER_PAGE = 300, 30

    def board(self, url):
        page = int(url.rsplit("=", 1)[1])
        rows = []
        for k in range(self.PER_PAGE):
            n = (page - 1) * self.PER_PAGE + k  # 0 = newest
            day = date(2026, 10, 31) - timedelta(days=n // self.PER_DAY)
            if day < date(2026, 10, 1):
                break
            cell = "11:00" if day == date(2026, 10, 31) else day.strftime("%m/%d")
            rows.append((100000 - n, cell))
        return (200, {}, bobae_list(rows))

    def run_discover(self, budget):
        # A paged profile (Bobaedream); Ruliweb is pinned to its query-free page 1 by the pool contract.
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        routes = {"https://www.bobaedream.co.kr/robots.txt": OPEN_ROBOTS}
        t = FakeTransport(routes)
        t.default = None
        t.get_orig = t.get

        def get(url):
            if url.startswith("https://www.bobaedream.co.kr/list?code=freeb&page="):
                t.routes[url] = self.board
            return t.get_orig(url)
        t.get = get
        site = make_site(tmp.name, "bobaedream", t, hours=168)
        receipt = site.discover(page_budget=budget)
        return site, t, receipt

    def test_every_window_day_is_reached_within_budget(self):
        site, t, receipt = self.run_discover(budget=24)
        days = receipt["in_window_days"]
        self.assertEqual(sorted(days), [f"2026-10-{d}" for d in range(24, 32)])
        self.assertTrue(all(count > 0 for count in days.values()), days)
        self.assertLessEqual(len(receipt["list_pages"]), 24)
        self.assertGreater(max(receipt["list_pages"]), 70, "reached a week back without walking every page")

    def test_freeze_is_deterministic_and_capped(self):
        site, _, _ = self.run_discover(budget=24)
        receipt = site.freeze(per_day_cap=4)
        self.assertTrue(all(v == 4 for v in receipt["by_day"].values()), receipt["by_day"])
        first = cc.read_json(site.dir / "queue.json")["queue"]
        (site.dir / "queue.json").unlink()
        site.freeze(per_day_cap=4)
        self.assertEqual(first, cc.read_json(site.dir / "queue.json")["queue"])

    # 2026-10-31 Hermes batch: 4 of 8 instiz picks were before the 24h window start on a partial day
    def test_freeze_drops_rows_whose_list_time_is_outside_the_window(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        site = make_site(tmp.name, "instiz", FakeTransport({}), hours=24)
        start = site.window_start.astimezone(cc.KST)
        before = (start - timedelta(hours=3)).strftime("%m.%d %H:%M")
        edge = start.strftime("%m.%d %H:%M")
        after = (start + timedelta(hours=1)).strftime("%m.%d %H:%M")
        day = start.date().isoformat()
        rows = [{"id": "1", "day": day, "date_raw": before}, {"id": "2", "day": day, "date_raw": edge},
                {"id": "3", "day": day, "date_raw": after}, {"id": "4", "day": day, "date_raw": "2026.10.30"}]
        cc.write_json(site.dir / "discovered.json", {"receipt": {}, "rows": rows})
        receipt = site.freeze(per_day_cap=10)
        queued = [r["id"] for r in cc.read_json(site.dir / "queue.json")["queue"]]
        self.assertEqual(queued, ["2", "3", "4"], "minute-edge and date-only rows stay; the post time decides")
        self.assertEqual(receipt["excluded_by_list_time"], 1)

    def test_unresolved_list_dates_are_interpolated_by_id(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        site = make_site(tmp.name, "ruliweb", FakeTransport({}))
        rows = [{"id": "10", "day": "2026-10-30", "day_source": "list"},
                {"id": "11", "day": None, "day_source": None},
                {"id": "12", "day": "2026-10-30", "day_source": "list"},
                {"id": "13", "day": None, "day_source": None},
                {"id": "14", "day": "2026-10-31", "day_source": "list"}]
        receipt = site._write_discovered({1: {"rows": rows}})
        self.assertEqual((receipt["date_interpolated"], receipt["date_unresolved"]), (1, 1))


def flaky_response(url, body, fail_after=1):
    """A 200 whose body stream times out after ``fail_after`` chunks (headers already received)."""

    def chunks():
        data = body.encode("utf-8")
        for i in range(fail_after):
            yield data[i * 7:(i + 1) * 7]
        raise cc.NetworkError("read_timeout", "timed out mid-body")
    return cc.Response(200, url, {}, chunks())


class ReviewRegressions(unittest.TestCase):
    """Reproductions from the 2026-10-31 independent review of community-collector.py."""

    POST1 = "https://www.bobaedream.co.kr/view?code=freeb&No=1"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def queued(self, routes, ids=("1",), profile="bobaedream", robots=OPEN_ROBOTS):
        host = cc.PROFILES[profile].host
        t = FakeTransport({f"https://{host}/robots.txt": robots, **routes})
        site = make_site(self.tmp.name, profile, t)
        queue = [{"id": i, "url": site.p.read_url(i), "day": "2026-10-31", "title": "t"} for i in ids]
        cc.write_json(site.dir / "queue.json", {"receipt": {}, "queue": queue})
        return site, t

    # 1. read-phase failures are retried and isolated
    def test_body_read_timeout_is_retried_as_one_request(self):
        attempts = []

        def route(url):
            attempts.append(url)
            if len(attempts) == 1:
                return flaky_response(url, bobae_post("본문"))
            return (200, {}, bobae_post("본문"))
        site, _ = self.queued({self.POST1: route})
        site.fetch(max_posts=1)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(cc.read_jsonl(site.dir / "posts.jsonl")[0]["state"], "eligible")
        stages = [r.get("stage") for r in cc.read_jsonl(site.dir / "requests.jsonl") if r["state"] == "network_error"]
        self.assertEqual(stages, ["read"])

    def test_list_read_failure_stops_only_that_site_and_main_continues(self):
        class Factory:
            def __init__(self, ua):
                self.calls = []

            def get(self, url):
                self.calls.append(url)
                if url.endswith("robots.txt"):
                    return cc.Response(200, url, {}, iter([b"User-agent: *\nAllow: /\n"]))
                if "bobaedream" in url:
                    return flaky_response(url, "<table></table>")
                return cc.Response(200, url, {}, iter([ruliweb_list([(5, "11:00")]).encode()]))
        run = Path(self.tmp.name) / "run"
        code = cc.main(["discover", "--run-dir", str(run), "--actor", "hermes", "--window-end", FETCHED.isoformat(),
                        "--page-budget", "2", "--delay", "2", "--site", "bobaedream", "--site", "ruliweb"],
                       transport_factory=Factory, sleep=lambda s: None)
        self.assertEqual(code, 2)
        self.assertEqual(cc.read_json(run / "bobaedream" / "stop.json")["state"], "network_unreachable")
        self.assertIsNone(cc.read_json(run / "ruliweb" / "stop.json"))
        self.assertEqual(cc.read_json(run / "ruliweb" / "discovered.json")["receipt"]["listed_unique"], 1)

    # 2. robots is judged per exact request URL; robots 429 is a rate-limit stop
    def test_robots_is_judged_for_each_post_url(self):
        robots = (200, {}, "User-agent: *\nDisallow: /view?code=freeb&No=7\n")
        site, t = self.queued({f"https://www.bobaedream.co.kr/view?code=freeb&No={i}": (200, {}, bobae_post("본문"))
                               for i in ("1", "7")}, ids=("1", "7"), robots=robots)
        result = site.fetch(max_posts=5)
        self.assertNotIn("https://www.bobaedream.co.kr/view?code=freeb&No=7", t.calls)
        self.assertEqual(result["post_states"], {"eligible": 1, "robots_denied": 1})

    def test_robots_429_stops_site_before_any_page_request(self):
        site, t = self.queued({}, robots=(429, {"retry-after": "60"}, ""))
        with self.assertRaises(cc.SiteStopped):
            site.discover(page_budget=3)
        self.assertEqual(site.stopped()["state"], "http_429")
        self.assertEqual(t.calls, ["https://www.bobaedream.co.kr/robots.txt"])
        self.assertFalse(cc.judge_actor(None, 429, "hermes", "/x")["allowed"])

    def test_robots_is_refetched_on_every_invocation(self):
        site, t = self.queued({self.POST1: (200, {}, bobae_post("본문"))})
        site.fetch(max_posts=1)
        again = make_site(self.tmp.name, "bobaedream", t)
        again.fetch(max_posts=1)
        self.assertEqual(t.calls.count("https://www.bobaedream.co.kr/robots.txt"), 2)
        self.assertEqual(len(cc.read_jsonl(again.dir / "robots_history.jsonl")), 1)

    # 3. incomplete or misidentified pages are not eligible
    def test_truncated_body_is_not_eligible(self):
        page = bobae_post("본문이 길게 이어지다가").split('</div><div id="cmt_list"')[0]
        site, _ = self.queued({self.POST1: (200, {}, page)})
        result = site.fetch(max_posts=1)
        record = cc.read_jsonl(site.dir / "posts.jsonl")[0]
        self.assertEqual((record["state"], record["stopped_at_body_close"]), ("truncated_body", False))
        self.assertEqual(result["eligible_bodies"], 0)

    def test_canonical_pointing_to_another_post_is_not_eligible(self):
        page = bobae_post("본문").replace(
            "<title>x</title>", '<title>x</title><link rel="canonical" href="/view?code=freeb&No=999">')
        site, _ = self.queued({self.POST1: (200, {}, page)})
        result = site.fetch(max_posts=1)
        record = cc.read_jsonl(site.dir / "posts.jsonl")[0]
        self.assertEqual((record["state"], record["canonical_identity"]), ("canonical_mismatch", "mismatch"))
        self.assertEqual(result["eligible_bodies"], 0)

    # 4. comments_parsed is a checked result backed by a per-profile guard
    def test_every_profile_declares_a_comment_guard(self):
        self.assertEqual([n for n, p in cc.PROFILES.items() if not p.comment_guard], [])

    def test_82cook_comment_before_body_is_boundary_error(self):
        page = ('<html><head><title>글 ::: 82cook.com</title></head><body>'
                '<div class="commentArea"><p>SECRET_COMMENT</p></div>'
                '<div id="articleBody">작성일 : 2026-10-31 10:00:00 본문</div></body></html>')
        url = "https://www.82cook.com/entiz/read.php?bn=15&num=1"
        site, _ = self.queued({url: (200, {}, page)}, profile="82cook")
        site.fetch(max_posts=1)
        record = cc.read_jsonl(site.dir / "posts.jsonl")[0]
        self.assertEqual((record["state"], record["comments_parsed"]), ("boundary_error", False))
        self.assertNotIn("SECRET_COMMENT", json.dumps(record, ensure_ascii=False))

    def test_instiz_comment_before_body_is_boundary_error(self):
        page = ('<html><body><table><tr><td class="comment_memo"><div class="comment_line">SECRET</div></td></tr>'
                '</table><div id="memo_content_1" class="memo_content">본문</div></body></html>')
        site, _ = self.queued({"https://www.instiz.net/name/1": (200, {}, page)}, profile="instiz")
        site.fetch(max_posts=1)
        self.assertEqual(cc.read_jsonl(site.dir / "posts.jsonl")[0]["state"], "boundary_error")

    # 5. list date selectors are tried in priority order, not DOM order
    def test_instiz_prefers_date_cell_over_earlier_number_cell(self):
        html = ('<table><tr><td class="listno">123</td><td class="listsubject"><a href="/name/111">'
                '<span class="sbj">하루</span></a></td><td class="list_category">일상</td>'
                '<td class="regdate">10.27</td></tr></table>')
        site = make_site(self.tmp.name, "instiz", FakeTransport({}))
        rows = site.parse_list(html, site.p.list_url(1), FETCHED)
        self.assertEqual((rows[0]["day"], rows[0]["date_raw"]), ("2026-10-27", "10.27"))

    # contract (2026-10-31 amendment): query-free page 1, then ``?page=N`` only
    def test_ruliweb_list_urls_follow_the_paging_contract(self):
        p = cc.PROFILES["ruliweb"]
        self.assertEqual(p.list_url(1), "https://bbs.ruliweb.com/community/board/300147")
        self.assertEqual(p.list_url(2), "https://bbs.ruliweb.com/community/board/300147?page=2")
        self.assertGreater(p.max_page, 1)
        site = make_site(self.tmp.name, "ruliweb", FakeTransport({}))
        with self.assertRaises(ValueError):
            site.fetch_list(p.max_page + 1)


class LocalServer:
    """One-shot raw socket server on 127.0.0.1; ``reply`` gets the accepted socket."""

    def __init__(self, reply):
        import socket
        import threading
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.url = f"http://127.0.0.1:{self.sock.getsockname()[1]}/x"

        def serve():
            conn, _ = self.sock.accept()
            conn.recv(4096)
            reply(conn)
            conn.close()
        self.thread = threading.Thread(target=serve, daemon=True)
        self.thread.start()

    def close(self):
        self.thread.join(5)
        self.sock.close()


class SecondReviewRegressions(unittest.TestCase):
    """Reproductions from the second independent review (2026-10-31)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def transport_error(self, reply):
        server = LocalServer(reply)
        self.addCleanup(server.close)
        with self.assertRaises(cc.NetworkError) as ctx:
            response = cc.UrllibTransport("test", timeout=5).get(server.url)
            b"".join(response.chunks)
        return ctx.exception

    def test_server_disconnect_before_response_is_a_network_error(self):
        self.assertEqual(self.transport_error(lambda conn: None).layer, "read")

    def test_garbage_status_line_is_a_network_error(self):
        self.transport_error(lambda conn: conn.sendall(b"NOT HTTP\r\n\r\n"))

    def test_short_body_against_content_length_is_a_network_error(self):
        err = self.transport_error(lambda conn: conn.sendall(
            b"HTTP/1.1 200 OK\r\nContent-Length: 1000\r\nConnection: close\r\n\r\nshort!"))
        self.assertEqual(err.layer, "read")

    def test_one_receipt_per_attempt(self):
        calls = []

        def route(url):
            calls.append(url)
            return flaky_response(url, bobae_post("본문")) if len(calls) == 1 else (200, {}, bobae_post("본문"))
        t = FakeTransport({"https://www.bobaedream.co.kr/robots.txt": OPEN_ROBOTS,
                           "https://www.bobaedream.co.kr/view?code=freeb&No=1": route})
        site = make_site(self.tmp.name, "bobaedream", t)
        site.open_post({"id": "1", "url": site.p.read_url("1"), "day": "2026-10-31"})
        posts = [r for r in cc.read_jsonl(site.dir / "requests.jsonl") if r["phase"] == "post"]
        self.assertEqual([(r["attempt"], r["state"]) for r in posts], [(1, "network_error"), (2, "response")])

    def test_comment_guard_ignores_scripts_links_and_inline_badges(self):
        page = ('<html><head><title>글 ::: 82cook.com</title><link id="comment-css" rel="stylesheet">'
                '<script id="commentTpl">tpl</script></head><body><li class="recent_comment">최근</li>'
                '<div id="articleBody">작성일 : 2026-10-31 10:00:00 본문 <span class="nocomment">x</span></div>'
                '</body></html>')
        builder = cc.TreeBuilder(watch=cc.PROFILES["82cook"].body, forbid=cc.PROFILES["82cook"].comment_guard)
        with self.assertRaises(cc.StopParsing):
            builder.feed(page)
        self.assertTrue(builder.closed)

    def test_canonical_trailing_slash_and_scheme_are_the_same_post(self):
        url = "https://bbs.ruliweb.com/community/board/300147/read/7"
        for canonical in (url + "/", url.replace("https", "http"), "/community/board/300147/read/7"):
            html = (f'<html><head><link rel="canonical" href="{canonical}"><meta property="og:title" content="t">'
                    '</head><body><span class="regdate">2026.10.31 (10:00:00)</span>'
                    '<div class="view_content"><p>본문</p></div></body></html>')
            t = FakeTransport({"https://bbs.ruliweb.com/robots.txt": OPEN_ROBOTS, url: (200, {}, html)})
            site = make_site(tempfile.mkdtemp(dir=self.tmp.name), "ruliweb", t)
            record = site.open_post({"id": "7", "url": url, "day": "2026-10-31"})
            self.assertEqual((record["canonical_identity"], record["state"]), ("exact", "eligible"), canonical)

    def test_late_meta_charset_is_honoured(self):
        filler = "<!-- " + "x" * 6000 + " -->"
        html = (f'<html><head>{filler}<meta charset="euc-kr"><title>x</title></head><body>'
                '<dl><dt class="subject_len" title="제목"><span class="countGroup">2026.10.31 (토) 11:04</span>'
                '</dt></dl><div class="bodyCont">한국어 본문입니다</div></body></html>').encode("euc-kr")
        t = FakeTransport({"https://www.bobaedream.co.kr/robots.txt": OPEN_ROBOTS,
                           "https://www.bobaedream.co.kr/view?code=freeb&No=1": (200, {}, html)})
        site = make_site(self.tmp.name, "bobaedream", t)
        record = site.open_post({"id": "1", "url": site.p.read_url("1"), "day": "2026-10-31"})
        self.assertEqual((record["state"], record["body"]), ("eligible", "한국어 본문입니다"))


class RunDirGuard(unittest.TestCase):
    def test_run_dir_inside_git_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".git").mkdir()
            with self.assertRaises(SystemExit):
                cc.main(["robots", "--run-dir", str(Path(tmp) / "run"), "--site", "ruliweb", "--actor", "claude"])

    def test_relative_run_dir_is_refused(self):
        with self.assertRaises(SystemExit):
            cc.main(["robots", "--run-dir", "relative/run", "--site", "ruliweb", "--actor", "claude"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
