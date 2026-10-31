#!/usr/bin/env python3
"""Resumable public-community collector for A0 seed harvesting (stdlib only).

Stages, each idempotent and resumable from files under RUN_DIR/<site>/:

    robots    fetch robots.txt and judge the entry/read paths for the actual actor
    discover  date-targeted list paging until every window day is reached
    freeze    deterministic per-day queue, evenly spaced by post ID
    fetch     open queued posts body-only, one post at a time
    status    print accounting

Policy boundaries (see SKILL.md and the vault collection-pool decision):
  * --actor hermes  evaluates robots for the Hermes product token only.
  * --actor claude  evaluates every Anthropic token (Claude-User, ClaudeBot,
    Claude-Web, anthropic-ai, Claude-SearchBot); any applicable denial stops the site.
  * The User-Agent always names the real actor. No identity rotation, cookies,
    login, challenge solving, or redirect-following into other hosts.
  * robots.txt is fetched afresh on every invocation and every list/post URL is
    judged (path + query) right before it is requested. robots 429/430 stops the
    site like any other rate limit; other robots 4xx allow (RFC 9309).
  * A network failure while connecting *or* reading a body retries the whole
    request; whatever still fails is isolated to that post or that site.
  * A wall/deleted/empty/truncated/canonical-mismatch post is skipped and counted;
    only 403/429/430/451, a bot challenge, robots denial of a list page, repeated
    network failure, or repeated parser misses stop a site.
  * Body-only: post bodies are streamed and the connection is closed at the body
    element's end tag. Each profile declares a comment guard; a comment container
    met before that point excludes the post (comments_parsed=False is checked).
  * RUN_DIR must be outside any Git work tree (raw bodies stay out of the Vault).
"""

from __future__ import annotations

import argparse
import codecs
import functools
import hashlib
import http.client
import json
import random
import re
import sys
import time
import traceback
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator
from urllib.parse import parse_qs, urljoin, urlsplit

COLLECTOR_VERSION = "community-collector/1.0"
ACCESS_POLICY_VERSION = "2026-10-30-verified-baseline-v1"
KST = timezone(timedelta(hours=9))

ACTORS = {
    "hermes": {
        "user_agent": "HermesAgent-PublicResearch/1.0",
        "robots_tokens": ["hermesagent-publicresearch"],
    },
    "claude": {
        "user_agent": "Mozilla/5.0 (compatible; Claude-User; vault seed-harvest; no-login)",
        "robots_tokens": ["claude-user", "claudebot", "claude-web", "anthropic-ai", "claude-searchbot"],
    },
}

# --------------------------------------------------------------------------- DOM


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"}
RAW_TEXT = {"script", "style", "noscript", "template"}
# Comment guards fire only on elements that can hold comment text, not on <script id=commentTpl>,
# <link id=comment-css> or inline badges such as <span class=nocomment>.
GUARD_TAGS = {"div", "section", "article", "aside", "ul", "ol", "table", "tbody", "tr", "td", "dl", "form"}
BLOCK = {"p", "div", "br", "li", "tr", "blockquote", "h1", "h2", "h3", "h4", "section", "article"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag: str, attrs: dict[str, str], parent: "Node | None") -> None:
        self.tag = tag
        self.attrs = attrs
        self.children: list[Node | str] = []
        self.parent = parent

    @property
    def classes(self) -> set[str]:
        return set(self.attrs.get("class", "").split())

    def iter(self) -> Iterator["Node"]:
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.iter()

    def text(self, exclude: str | None = None, lines: bool = False) -> str:
        skip = set(select_all(self, exclude)) if exclude else set()
        parts: list[str] = []

        def walk(node: Node) -> None:
            for child in node.children:
                if isinstance(child, str):
                    parts.append(child)
                elif child.tag not in RAW_TEXT and child not in skip:
                    if lines and child.tag in BLOCK:
                        parts.append("\n")
                    walk(child)
                    if lines and child.tag in BLOCK:
                        parts.append("\n")

        walk(self)
        raw = "".join(parts)
        if lines:
            out = [" ".join(line.split()) for line in raw.splitlines()]
            return "\n".join(line for line in out if line)
        return " ".join(raw.split())

    def select(self, selector: str) -> list["Node"]:
        return select_all(self, selector)

    def select_one(self, selector: str) -> "Node | None":
        found = select_all(self, selector)
        return found[0] if found else None


_COMPOUND = re.compile(
    r"(?P<tag>[a-zA-Z][\w-]*|\*)?"
    r"(?P<rest>(?:#[\w-]+|\.[\w-]+|\[[^\]]+\])*)"
)
_PART = re.compile(r"#([\w-]+)|\.([\w-]+)|\[\s*([\w:-]+)\s*(?:([*^$]?=)\s*[\"']?([^\"'\]]*)[\"']?\s*)?\]")


def _parse_compound(text: str) -> tuple[str | None, list[tuple[str, str, str | None]]]:
    match = _COMPOUND.fullmatch(text)
    if not match:
        raise ValueError(f"unsupported selector part: {text!r}")
    tag = match.group("tag")
    tests: list[tuple[str, str, str | None]] = []
    for part in _PART.finditer(match.group("rest")):
        if part.group(1):
            tests.append(("id", part.group(1), None))
        elif part.group(2):
            tests.append(("class", part.group(2), None))
        else:
            tests.append((part.group(4) or "has", part.group(3), part.group(5)))
    return (None if tag in (None, "*") else tag.lower()), tests


def _matches(node: Node, compound: tuple[str | None, list[tuple[str, str, str | None]]]) -> bool:
    tag, tests = compound
    if tag and node.tag != tag:
        return False
    for op, name, value in tests:
        if op == "id":
            if node.attrs.get("id") != name:
                return False
        elif op == "class":
            if name not in node.classes:
                return False
        else:
            actual = node.attrs.get(name)
            if actual is None:
                return False
            if op == "=" and actual != value:
                return False
            if op == "*=" and (value or "") not in actual:
                return False
            if op == "^=" and not actual.startswith(value or ""):
                return False
            if op == "$=" and not actual.endswith(value or ""):
                return False
    return True


@functools.lru_cache(maxsize=256)
def _compile(selector: str) -> list[list[tuple[str | None, list[tuple[str, str, str | None]]]]]:
    return [[_parse_compound(p) for p in group.split()] for group in selector.split(",") if group.strip()]


def node_matches(node: Node, selector: str) -> bool:
    for chain in _compile(selector):
        if not _matches(node, chain[-1]):
            continue
        ancestor, i = node.parent, len(chain) - 2
        while i >= 0 and ancestor is not None:
            if _matches(ancestor, chain[i]):
                i -= 1
            ancestor = ancestor.parent
        if i < 0:
            return True
    return False


def select_all(root: Node, selector: str | None) -> list[Node]:
    if not selector:
        return []
    return [n for n in root.iter() if node_matches(n, selector)]


class StopParsing(Exception):
    """Raised when the watched body element closes."""


class BoundaryError(Exception):
    """Raised when a forbidden container (e.g. comments) appears before the body."""


class TreeBuilder(HTMLParser):
    """Builds a tree until ``watch`` closes; any ``forbid`` match before that aborts the parse."""

    def __init__(self, watch: str | None = None, forbid: str | None = None) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {}, None)
        self.stack = [self.root]
        self.watch = watch
        self.forbid = forbid
        self.watched: Node | None = None
        self.closed = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        parent = self.stack[-1]
        node = Node(tag, {k: (v or "") for k, v in attrs}, parent)
        parent.children.append(node)
        if self.forbid and tag in GUARD_TAGS and node_matches(node, self.forbid):
            where = "inside" if self.watched is not None else "before"
            raise BoundaryError(f"comment container <{tag} {node.attrs}> {where} body")
        if self.watched is None and self.watch and node_matches(node, self.watch):
            self.watched = node
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                popped = self.stack[i:]
                del self.stack[i:]
                if self.watched is not None and self.watched in popped:
                    self.closed = True
                    raise StopParsing()
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def parse_html(text: str) -> Node:
    builder = TreeBuilder()
    builder.feed(text)
    builder.close()
    return builder.root


# ------------------------------------------------------------------------- dates


_FULL = re.compile(
    r"(?P<y>20\d{2}|\d{2})[.\-/](?P<m>\d{1,2})[.\-/](?P<d>\d{1,2})\.?"
    r"(?:\s*\([^)\d]{1,4}\))?\s*\(?(?:(?P<H>\d{1,2}):(?P<M>\d{2})(?::(?P<S>\d{2}))?)?"
)
_MONTH_DAY = re.compile(r"(?<!\d)(?P<m>\d{1,2})[.\-/](?P<d>\d{1,2})(?![.\-/]?\d)")
_TIME = re.compile(r"(?<![\d.\-/])(?P<H>\d{1,2}):(?P<M>\d{2})(?::(?P<S>\d{2}))?(?![\d])")


def parse_post_datetime(raw: str | None) -> datetime | None:
    """Parse a post's own timestamp. Naive values are KST."""

    if not raw:
        return None
    text = raw.strip()
    try:
        value = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return value if value.tzinfo else value.replace(tzinfo=KST)
    except ValueError:
        pass
    m = _FULL.search(text)
    if not m or m.group("H") is None:
        return None
    year = int(m.group("y"))
    year += 2000 if year < 100 else 0
    try:
        return datetime(year, int(m.group("m")), int(m.group("d")), int(m.group("H")),
                        int(m.group("M")), int(m.group("S") or 0), tzinfo=KST)
    except ValueError:
        return None


def parse_list_day(raw: str | None, fetched_at: datetime) -> date | None:
    """Resolve a list cell (``13:10``, ``10/27``, ``2026.10.30``...) to a KST day."""

    if not raw:
        return None
    text = " ".join(raw.split())
    local = fetched_at.astimezone(KST)
    m = _FULL.search(text)
    if m:
        year = int(m.group("y"))
        year += 2000 if year < 100 else 0
        try:
            return date(year, int(m.group("m")), int(m.group("d")))
        except ValueError:
            return None
    m = _MONTH_DAY.search(text)
    if m:
        try:
            day = date(local.year, int(m.group("m")), int(m.group("d")))
        except ValueError:
            return None
        return day.replace(year=day.year - 1) if day > local.date() else day
    m = _TIME.search(text)
    if m:
        stamp = local.replace(hour=int(m.group("H")), minute=int(m.group("M")),
                              second=int(m.group("S") or 0), microsecond=0)
        return (local.date() - timedelta(days=1)) if stamp > local + timedelta(minutes=5) else local.date()
    return None


# ---------------------------------------------------------------------- profiles


@dataclass
class Profile:
    name: str
    label: str
    host: str
    list_url: Callable[[int], str]
    read_url: Callable[[str], str]
    row: str
    link: str
    id_from_url: Callable[[str], str | None]
    row_date: tuple[str, ...]  # tried in order; the first cell that parses to a day wins
    body: str
    title_sources: list[str]
    date_sources: list[str]
    skip_row: str | None = None
    title_exclude: str | None = None
    title_strip: str | None = None
    require_text: dict[str, str] = field(default_factory=dict)
    comment_guard: str | None = None  # comment containers; a match before the body closes skips the post
    wall_markers: tuple[str, ...] = ("회원에게만 공개", "로그인 후 이용", "로그인이 필요", "회원만 볼 수")
    deleted_markers: tuple[str, ...] = ("삭제된 게시물", "존재하지 않는 게시물", "삭제되었거나")
    canonical_aliases: tuple[str, ...] = ()
    max_page: int = 500
    live_verified: str = ""
    note: str = ""


def _query_id(key: str, path: str, extra: dict[str, str] | None = None) -> Callable[[str], str | None]:
    def get(url: str) -> str | None:
        parts = urlsplit(url)
        if parts.path != path:
            return None
        q = parse_qs(parts.query)
        for k, v in (extra or {}).items():
            if q.get(k) != [v]:
                return None
        value = q.get(key, [""])
        return value[0] if len(value) == 1 and value[0].isdecimal() else None
    return get


def _path_id(pattern: str) -> Callable[[str], str | None]:
    rx = re.compile(pattern)

    def get(url: str) -> str | None:
        m = rx.fullmatch(urlsplit(url).path)
        return m.group(1) if m else None
    return get


PROFILES: dict[str, Profile] = {
    "instiz": Profile(
        name="instiz", label="인스티즈 일상", host="www.instiz.net",
        list_url=lambda p: f"https://www.instiz.net/name?page={p}",
        read_url=lambda i: f"https://www.instiz.net/name/{i}",
        row="tr", link="td.listsubject a[href]", id_from_url=_path_id(r"/name/(\d+)/?"),
        row_date=(".regdate", "td.listno"), skip_row=".texthead_notice",
        title_exclude="[class^=cmt], .list_subtitle",
        require_text={".list_category": "일상"},
        body="div#memo_content_1", comment_guard=".comment_memo, .comment_line",
        title_sources=["css:#nowsubject", "meta:og:title"],
        date_sources=["meta:article:published_time"],
        note="Selectors from the Hermes 2026-10-31 collector; list date cell unverified by Claude.",
    ),
    "clien": Profile(
        name="clien", label="클리앙 모두의공원", host="www.clien.net",
        list_url=lambda p: f"https://www.clien.net/service/board/park?od=T31&po={p - 1}",
        read_url=lambda i: f"https://www.clien.net/service/board/park/{i}",
        row="div.list_item", link="a.list_subject[href]",
        id_from_url=_path_id(r"/service/board/park/(\d+)"),
        row_date=("span.timestamp", ".list_time"), skip_row=".notice",
        body="div.post_article", comment_guard="div.comment_row, div.comment_view",
        title_sources=["css:h3.post_subject", "meta:og:title"],
        date_sources=["css:div.post_author span.date", "css:.post_date"],
        note="Pool 2026-10-31 entry; replaces the robots-denied /service/group/community. Hermes lane only.",
    ),
    "82cook": Profile(
        name="82cook", label="82cook 자유게시판", host="www.82cook.com",
        list_url=lambda p: f"https://www.82cook.com/entiz/enti.php?bn=15&page={p}",
        read_url=lambda i: f"https://www.82cook.com/entiz/read.php?bn=15&num={i}",
        row="tr", link="td.title a[href*=read.php]",
        id_from_url=_query_id("num", "/entiz/read.php", {"bn": "15"}),
        row_date=("td.regdate",), skip_row=".notice",
        title_exclude=".cmtN, .comment, .reply",
        body="#articleBody",
        # the Scrapy spider excludes any ancestor whose class/id contains "comment" for 82cook
        comment_guard="[class*=comment], [id*=comment]",
        title_sources=["title"], title_strip=r"\s*:::\s*82cook\.com.*$",
        date_sources=["regex:작성일\\s*:\\s*(\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}:\\d{2})"],
        note="Host intermittently unreachable at TCP level from this PC; retried with backoff.",
    ),
    "ruliweb": Profile(
        name="ruliweb", label="루리웹 고민상담", host="bbs.ruliweb.com",
        # Pool contract (2026-10-31 amendment): page 1 is the query-free board path;
        # later pages add ``?page=N`` and nothing else.
        list_url=lambda p: "https://bbs.ruliweb.com/community/board/300147" if p == 1 else
        f"https://bbs.ruliweb.com/community/board/300147?page={p}",
        read_url=lambda i: f"https://bbs.ruliweb.com/community/board/300147/read/{i}",
        row="tr.table_body", link="a.subject_link[href]",
        id_from_url=_path_id(r"/community/board/300147/read/(\d+)"),
        row_date=("td.time",), skip_row=".notice, .best",
        title_exclude=".num_reply",
        body="div.view_content",
        comment_guard="div.comment_view, div.comment_list, div.comment_wrapper, #comment_list",
        title_sources=["meta:og:title"],
        date_sources=["meta:article:published_time", "css:span.regdate"],
        canonical_aliases=("https://m.ruliweb.com/community/board/300147/read/{id}",),
        live_verified="2026-10-31 list+post (Claude probe)",
    ),
    "bobaedream": Profile(
        name="bobaedream", label="보배드림 자유게시판", host="www.bobaedream.co.kr",
        list_url=lambda p: f"https://www.bobaedream.co.kr/list?code=freeb&page={p}",
        read_url=lambda i: f"https://www.bobaedream.co.kr/view?code=freeb&No={i}",
        row="tr[itemscope]", link="a.bsubject[href]",
        id_from_url=_query_id("No", "/view", {"code": "freeb"}),
        row_date=("td.date",), skip_row=".notice",
        body="div.bodyCont", comment_guard="#cmt_list",
        title_sources=["attr:dt.subject_len:title", "css:dt.subject_len strong", "meta:og:title"],
        title_strip=r"\s*\|\s*보배드림.*$",
        date_sources=["css:span.countGroup"],
        live_verified="2026-10-31 list+post (Claude probe)",
        note="Reserve B (2026-10-31 re-evaluation); not in the approved pool.",
    ),
    "inven": Profile(
        name="inven", label="인벤 오픈이슈갤러리", host="www.inven.co.kr",
        list_url=lambda p: f"https://www.inven.co.kr/board/webzine/2097?p={p}",
        read_url=lambda i: f"https://www.inven.co.kr/board/webzine/2097/{i}",
        row="tr", link="td.tit a.subject-link[href]",
        id_from_url=_path_id(r"/board/webzine/2097/(\d+)"),
        row_date=("td.date",), skip_row=".notice",
        title_exclude=".category",
        body="#powerbbsContent", comment_guard="#powerbbsCmt2",
        title_sources=["css:.articleTitle h1", "meta:og:title"],
        date_sources=["css:.articleDate"],
        live_verified="2026-10-31 list+post (Claude probe)",
        note="Grade C (2026-10-31): link/repost heavy; not in the approved pool.",
    ),
}


# ------------------------------------------------------------------------ robots


def parse_robots(text: str) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    last_was_agent = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (s.strip() for s in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if current is None or not last_was_agent:
                current = {"agents": [], "rules": []}
                groups.append(current)
            current["agents"].append(value.lower())
            last_was_agent = True
        elif key in ("allow", "disallow") and current is not None:
            current["rules"].append((key, value))
            last_was_agent = False
        else:
            last_was_agent = False
    return groups


def _rule_matches(pattern: str, path: str) -> bool:
    rx = re.escape(pattern).replace(r"\*", ".*")
    if rx.endswith(r"\$"):
        rx = rx[:-2] + "$"
    return re.match(rx, path) is not None


def judge_token(groups: list[dict[str, Any]], token: str, path: str) -> dict[str, Any]:
    named = [g for g in groups if any(a != "*" and (a == token or token.startswith(a)) for a in g["agents"])]
    chosen = named or [g for g in groups if "*" in g["agents"]]
    best: tuple[int, bool, str] | None = None
    for group in chosen:
        for kind, value in group["rules"]:
            if value and _rule_matches(value, path):
                score = (len(value), kind == "allow", f"{kind}:{value}")
                if best is None or score[:2] > best[:2]:
                    best = score
    return {"token": token, "group": "named" if named else ("*" if chosen else "none"),
            "allowed": True if best is None else best[1], "rule": best[2] if best else None}


def judge_actor(robots_text: str | None, status: int | str, actor: str, path: str) -> dict[str, Any]:
    """RFC 9309 status semantics plus the actor's token policy."""

    if isinstance(status, int) and 400 <= status < 500 and status not in RATE_LIMIT_STATUS:
        return {"allowed": True, "basis": f"robots HTTP {status}: unavailable, RFC 9309 allows", "tokens": []}
    if status != 200:
        return {"allowed": False, "basis": f"robots unreachable ({status}): treated as full disallow", "tokens": []}
    groups = parse_robots(robots_text or "")
    tokens = [judge_token(groups, t, path) for t in ACTORS[actor]["robots_tokens"]]
    allowed = all(t["allowed"] for t in tokens)
    denied = [t["token"] for t in tokens if not t["allowed"]]
    return {"allowed": allowed, "tokens": tokens,
            "basis": "all actor tokens allowed" if allowed else f"denied for {', '.join(denied)}"}


# ----------------------------------------------------------------------- network


@dataclass
class Response:
    status: int
    url: str
    headers: dict[str, str]
    chunks: Iterable[bytes]
    close: Callable[[], None] = lambda: None


class NetworkError(Exception):
    def __init__(self, layer: str, detail: str) -> None:
        super().__init__(f"{layer}: {detail}")
        self.layer = layer
        self.detail = detail


def _read_layer(exc: BaseException) -> str:
    return "read_timeout" if isinstance(exc, TimeoutError) else "read"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


class UrllibTransport:
    def __init__(self, user_agent: str, timeout: float = 20.0) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self.opener = urllib.request.build_opener(_NoRedirect)

    def get(self, url: str) -> Response:
        request = urllib.request.Request(url, headers={
            "User-Agent": self.user_agent, "Accept-Language": "ko,en;q=0.5"})
        try:
            raw = self.opener.open(request, timeout=self.timeout)
        except urllib.error.HTTPError as exc:
            try:
                body = exc.read(300_000) if exc.fp else b""
            except (OSError, http.client.HTTPException) as read_exc:
                raise NetworkError(_read_layer(read_exc), str(read_exc)) from read_exc
            return Response(exc.code, url, {k.lower(): v for k, v in (exc.headers or {}).items()}, [body])
        except urllib.error.URLError as exc:
            reason = exc.reason
            layer = "tcp_connect" if isinstance(reason, (TimeoutError, OSError)) else "url"
            if "ssl" in type(reason).__name__.lower() or "certificate" in str(reason).lower():
                layer = "tls"
            if "getaddrinfo" in str(reason) or "Name or service" in str(reason):
                layer = "dns"
            raise NetworkError(layer, str(reason)) from exc
        except (OSError, http.client.HTTPException) as exc:
            # urllib wraps only OSErrors from sending; getresponse() errors such as
            # RemoteDisconnected, ConnectionResetError or BadStatusLine arrive raw.
            raise NetworkError(_read_layer(exc), f"{type(exc).__name__}: {exc}") from exc
        expected = raw.headers.get("content-length")

        def chunks() -> Iterator[bytes]:
            received = 0
            try:
                while True:
                    try:
                        piece = raw.read(4096)
                    except (OSError, http.client.HTTPException) as exc:
                        raise NetworkError(_read_layer(exc), f"{type(exc).__name__}: {exc}") from exc
                    if not piece:
                        if expected and expected.isdecimal() and received < int(expected):
                            raise NetworkError("read", f"short body: {received} of {expected} bytes")
                        return
                    received += len(piece)
                    yield piece
            finally:
                raw.close()

        return Response(raw.status, raw.url, {k.lower(): v for k, v in raw.headers.items()}, chunks(), raw.close)


CHALLENGE = re.compile(r"just a moment|cf-chl|challenge-platform|captcha|ddos-guard|attention required"
                       r"|anubis_challenge|/\.within\.website/", re.I)
HTML_DOC = re.compile(r"^\s*(?:<!doctype html|<html|<head|<body)", re.I)


def sniff_encoding(headers: dict[str, str], head: bytes) -> str:
    m = re.search(r"charset=([\w-]+)", headers.get("content-type", ""), re.I)
    if not m:
        m2 = re.search(rb"charset=[\"']?([\w-]+)", head[:20000], re.I)
        name = m2.group(1).decode("ascii") if m2 else "utf-8"
    else:
        name = m.group(1)
    try:
        codecs.lookup(name)
        return name
    except LookupError:
        return "utf-8"


# ----------------------------------------------------------------------- storage


def now() -> datetime:
    return datetime.now(KST)


def read_json(path: Path, default: Any = None) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, default=str) + "\n")


def read_jsonl(path: Path) -> list[Any]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def inside_git_worktree(path: Path) -> Path | None:
    for parent in [path, *path.parents]:
        if (parent / ".git").exists():
            return parent
    return None


# ------------------------------------------------------------------------ engine


SITE_STOP_STATUS = {403: "http_403", 429: "http_429", 430: "http_430", 451: "http_451"}
RATE_LIMIT_STATUS = (429, 430)


class SiteStopped(Exception):
    def __init__(self, state: str, detail: str) -> None:
        super().__init__(f"{state}: {detail}")
        self.state = state
        self.detail = detail


class SiteRun:
    def __init__(self, run_dir: Path, profile: Profile, actor: str, transport: Any,
                 contract: dict[str, Any], sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], datetime] = now, min_delay: float = 2.0) -> None:
        self.dir = run_dir / profile.name
        self.p = profile
        self.actor = actor
        self.transport = transport
        self.contract = contract
        self.sleep = sleep
        self.clock = clock
        self.min_delay = min_delay
        self.last_request = 0.0
        self._robots: dict[str, Any] | None = None
        self.window_start = datetime.fromisoformat(contract["window_start"])
        self.window_end = datetime.fromisoformat(contract["window_end"])

    # -- receipts -----------------------------------------------------------
    def stopped(self) -> dict[str, Any] | None:
        return read_json(self.dir / "stop.json")

    def stop(self, state: str, detail: str, **extra: Any) -> None:
        write_json(self.dir / "stop.json", {"state": state, "detail": detail, "at": self.clock(), **extra})
        raise SiteStopped(state, detail)

    def _pace(self) -> None:
        if self.last_request:
            wait = self.min_delay + random.uniform(0, 1.0) - (time.monotonic() - self.last_request)
            if wait > 0:
                self.sleep(wait)
        self.last_request = time.monotonic()

    def request(self, url: str, phase: str, consume: Callable[[Response], Any] = lambda r: b"".join(r.chunks),
                retries: int = 2) -> Any:
        """One logical request with network backoff, from connect through consuming the body.

        ``consume`` reads the response; a NetworkError while connecting *or* while reading
        retries the whole request. HTTP statuses are handed to ``consume`` unchanged.
        """

        backoff = [5.0, 15.0, 45.0]
        for attempt in range(retries + 1):
            self._pace()
            receipt = {"url": url, "phase": phase, "attempt": attempt + 1, "at": self.clock(),
                       "user_agent": ACTORS[self.actor]["user_agent"], "cookies": False}
            response: Response | None = None
            try:
                response = self.transport.get(url)
                receipt.update(state="response", status=response.status, final_url=response.url,
                               retry_after=response.headers.get("retry-after"))
                return consume(response)
            except NetworkError as exc:
                stage = "read" if response is not None else "connect"
                receipt.update(state="network_error", stage=stage, layer=exc.layer, detail=exc.detail)
                if attempt == retries:
                    raise
                self.sleep(backoff[attempt] + random.uniform(0, 2.0))
            finally:
                append_jsonl(self.dir / "requests.jsonl", receipt)  # exactly one receipt per attempt
                if response is not None:
                    response.close()
        raise AssertionError("unreachable")

    def robots_allows(self, url: str) -> dict[str, Any]:
        """Judge the exact request URL (path + query) against this run's robots receipt."""

        result = self.robots()
        parts = urlsplit(url)
        return judge_actor(result["text"], result["status"], self.actor,
                           (parts.path or "/") + (f"?{parts.query}" if parts.query else ""))

    def _check_site_status(self, response: Response, head: bytes, url: str) -> None:
        text = head[:20000].decode("utf-8", "replace")
        if response.status in SITE_STOP_STATUS:
            state = "challenge" if CHALLENGE.search(text) else SITE_STOP_STATUS[response.status]
            self.stop(state, f"HTTP {response.status} at {url}", retry_after=response.headers.get("retry-after"))
        if response.status == 503 and CHALLENGE.search(text):
            self.stop("challenge", f"HTTP 503 challenge at {url}")
        if response.status == 200 and CHALLENGE.search(text) and "<title>just a moment" in text.lower():
            self.stop("challenge", f"challenge page at {url}")

    # -- robots -------------------------------------------------------------
    def robots(self) -> dict[str, Any]:
        """Fetch robots.txt once per invocation (never reused across invocations, even on resume)."""

        if self._robots is not None:
            return self._robots
        previous = read_json(self.dir / "robots.json")
        if previous:
            append_jsonl(self.dir / "robots_history.jsonl", {k: v for k, v in previous.items() if k != "text"})
        url = f"https://{self.p.host}/robots.txt"
        status: int | str
        text = ""
        try:
            response, body = self.request(url, "robots", lambda r: (r, b"".join(r.chunks)))
            status = response.status
            hops = 0
            while status in (301, 302, 303, 307, 308) and hops < 5:
                target = urljoin(url, response.headers.get("location", ""))
                if urlsplit(target).hostname not in (self.p.host, self.p.host.removeprefix("www.")):
                    status = f"redirect to other host {target}"
                    break
                response, body = self.request(target, "robots", lambda r: (r, b"".join(r.chunks)))
                status, hops = response.status, hops + 1
            if status == 200:
                text = body.decode(sniff_encoding(response.headers, body), "replace")
        except NetworkError as exc:
            status = f"network {exc.layer}"
        # An HTML page where robots.txt should be has no rules, so it would read as "allow everything".
        # A bot challenge there (PGR21's Anubis page, 2026-10-31) is an access wall, not a permission.
        robots_html = status == 200 and bool(HTML_DOC.match(text))
        if robots_html and CHALLENGE.search(text):
            write_json(self.dir / "robots.json", {"url": url, "status": status, "fetched_at": self.clock(),
                                                  "actor": self.actor, "robots_html": True, "judgments": {},
                                                  "text": text[:2000]})
            self.stop("challenge", f"robots.txt returned a bot challenge page at {url}")
        if status in RATE_LIMIT_STATUS:
            write_json(self.dir / "robots.json", {"url": url, "status": status, "fetched_at": self.clock(),
                                                  "actor": self.actor, "judgments": {}, "text": ""})
            self.stop(SITE_STOP_STATUS[status], f"robots.txt HTTP {status}: rate limited",
                      retry_after=response.headers.get("retry-after"))
        paths = {"list": urlsplit(self.p.list_url(1)), "read": urlsplit(self.p.read_url("1"))}
        judgments = {k: judge_actor(text, status, self.actor, v.path + (f"?{v.query}" if v.query else ""))
                     for k, v in paths.items()}
        result = {"url": url, "status": status, "fetched_at": self.clock(), "actor": self.actor,
                  "tokens": ACTORS[self.actor]["robots_tokens"],
                  # HTML without a challenge (e.g. a soft 404) carries no rules: RFC 9309 parsing allows.
                  "robots_html": robots_html,
                  "content_signal": sorted(set(re.findall(r"(?im)^content-signal:\s*(.+)$", text))),
                  "anthropic_named": sorted({a for g in parse_robots(text) for a in g["agents"]
                                             if re.search(r"claude|anthropic", a)}),
                  "judgments": judgments, "text": text}
        write_json(self.dir / "robots.json", result)
        self._robots = result
        if not all(j["allowed"] for j in judgments.values()):
            denied = "; ".join(f"{k}: {j['basis']}" for k, j in judgments.items() if not j["allowed"])
            self.stop("robots_denied" if status == 200 else "robots_unreachable", denied)
        return result

    def require_robots(self) -> None:
        if self.stopped():
            raise SiteStopped(self.stopped()["state"], self.stopped()["detail"])
        result = self.robots()
        if not all(j["allowed"] for j in result["judgments"].values()):
            raise SiteStopped("robots_denied", "robots judgment denies this actor")

    # -- discover -----------------------------------------------------------
    def window_days(self) -> list[date]:
        first, last = self.window_start.astimezone(KST).date(), self.window_end.astimezone(KST).date()
        return [first + timedelta(days=i) for i in range((last - first).days + 1)]

    def parse_list(self, html: str, url: str, fetched_at: datetime) -> list[dict[str, Any]]:
        root = parse_html(html)
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for position, row in enumerate(root.select(self.p.row)):
            if self.p.skip_row and (node_matches(row, self.p.skip_row) or row.select_one(self.p.skip_row)):
                continue
            if any((n := row.select_one(sel)) is not None and n.text() != want
                   for sel, want in self.p.require_text.items()):
                continue
            link = row.select_one(self.p.link)
            if link is None:
                continue
            href = urljoin(url, link.attrs.get("href", ""))
            if urlsplit(href).hostname not in (self.p.host, self.p.host.removeprefix("www.")):
                continue
            post_id = self.p.id_from_url(href)
            if not post_id or post_id in seen:
                continue
            seen.add(post_id)
            raw, day = "", None
            for selector in self.p.row_date:
                cell = row.select_one(selector)
                if cell is None:
                    continue
                text = cell.text()
                if self.p.name == "instiz":
                    text = text.split(" l ")[0]
                raw = raw or text
                if (day := parse_list_day(text, fetched_at)) is not None:
                    raw = text
                    break
            rows.append({"id": post_id, "url": self.p.read_url(post_id),
                         "title": link.attrs.get("title") or link.text(exclude=self.p.title_exclude),
                         "date_raw": raw, "day": day.isoformat() if day else None,
                         "day_source": "list" if day else None, "position": position})
        return rows

    def fetch_list(self, page: int) -> dict[str, Any]:
        pages = {snap["page"]: snap for snap in read_jsonl(self.dir / "lists.jsonl")}
        if page in pages:
            return pages[page]
        if not 1 <= page <= self.p.max_page:
            raise ValueError(f"{self.p.name}: list page {page} outside the profile's approved range")
        url = self.p.list_url(page)
        verdict = self.robots_allows(url)
        if not verdict["allowed"]:
            self.stop("robots_denied", f"list page {page} {url}: {verdict['basis']}")
        try:
            response, body = self.request(url, "list", lambda r: (r, b"".join(r.chunks)))
        except NetworkError as exc:
            self.stop("network_unreachable", f"list page {page}: {exc}")
        self._check_site_status(response, body, url)
        fetched_at = self.clock()
        snap: dict[str, Any] = {"page": page, "url": url, "status": response.status, "fetched_at": fetched_at,
                                "rows": []}
        if response.status in (301, 302, 303, 307, 308):
            self.stop("redirect_boundary", f"list redirected to {response.headers.get('location')}")
        if response.status == 200:
            snap["rows"] = self.parse_list(body.decode(sniff_encoding(response.headers, body), "replace"),
                                           url, fetched_at)
        append_jsonl(self.dir / "lists.jsonl", snap)
        return snap

    @staticmethod
    def _bounds(snap: dict[str, Any]) -> tuple[str, str] | None:
        days = [r["day"] for r in snap["rows"] if r["day"]]
        return (max(days), min(days)) if days else None

    def discover(self, page_budget: int, extra_per_day: int = 1) -> dict[str, Any]:
        self.require_robots()
        days = [d.isoformat() for d in self.window_days()]
        fetched = {s["page"]: s for s in read_jsonl(self.dir / "lists.jsonl")}

        def budget_left() -> bool:
            return len(fetched) < page_budget

        def get(page: int) -> dict[str, Any]:
            fetched[page] = self.fetch_list(page)
            return fetched[page]

        get(1)
        empty_after: int | None = None
        # Phase 1: reach every window day at least once (gallop + interpolation).
        guard = 0
        while budget_left() and guard < page_budget * 3:
            guard += 1
            known = sorted((p, self._bounds(s)) for p, s in fetched.items())
            nonempty = [(p, b) for p, b in known if b]
            for p, s in fetched.items():
                if not s["rows"] and s["status"] == 200:
                    empty_after = p if empty_after is None else min(empty_after, p)
            covered = {r["day"] for s in fetched.values() for r in s["rows"] if r["day"]}
            target = None
            for day in sorted(days, reverse=True):
                if day in covered:
                    continue
                newer = [(p, b) for p, b in nonempty if b[1] > day]
                older = [(p, b) for p, b in nonempty if b[0] < day]
                left = max(newer, default=None)
                right = min(older, default=None)
                if left is None:
                    continue  # nothing newer than the day was seen: it lies above page 1 or inside a gap
                if right and right[0] - left[0] <= 1:
                    continue  # adjacent pages straddle the day: no posts that day
                if any(b[0] > day > b[1] for _, b in nonempty):
                    continue  # one page spans across the day without listing it: no posts that day
                target = (day, left, right)
                break
            if target is None:
                break
            day, left, right = target
            ceiling = min(self.p.max_page, empty_after - 1 if empty_after else self.p.max_page)
            if right is None:
                page = min(ceiling, max(left[0] * 2, left[0] + 1))
                if page <= left[0] or page in fetched:
                    break
            else:
                lo, hi = left[0], right[0]
                span = (date.fromisoformat(left[1][1]) - date.fromisoformat(right[1][0])).days or 1
                frac = (date.fromisoformat(left[1][1]) - date.fromisoformat(day)).days / span
                page = lo + max(1, min(hi - lo - 1, round((hi - lo) * frac)))
                if page in fetched:
                    page = next((q for q in range(lo + 1, hi) if q not in fetched), None)
                    if page is None:
                        continue
            get(page)
        # Phase 2: widen each day's sample with pages inside that day's range.
        for _ in range(extra_per_day):
            for day in sorted(days, reverse=True):
                if not budget_left():
                    break
                pages_with = sorted(p for p, s in fetched.items() if any(r["day"] == day for r in s["rows"]))
                if not pages_with:
                    continue
                newer = [p for p, s in fetched.items() if (b := self._bounds(s)) and b[1] > day]
                older = [p for p, s in fetched.items() if (b := self._bounds(s)) and b[0] < day]
                lo = max([p for p in newer if p < pages_with[0]], default=pages_with[0])
                hi = min([p for p in older if p > pages_with[-1]], default=pages_with[-1])
                gaps = [(b - a, a, b) for a, b in zip([lo, *pages_with], [*pages_with, hi]) if b - a > 1]
                if gaps:
                    _, a, b = max(gaps)
                    get((a + b) // 2)
        return self._write_discovered(fetched)

    def _write_discovered(self, fetched: dict[int, dict[str, Any]]) -> dict[str, Any]:
        rows: dict[str, dict[str, Any]] = {}
        for page in sorted(fetched):
            for row in fetched[page]["rows"]:
                rows.setdefault(row["id"], {**row, "page": page})
        ordered = sorted(rows.values(), key=lambda r: int(r["id"]))
        # Interpolate missing list dates from neighbouring IDs with the same resolved day.
        resolved = [r for r in ordered if r["day"]]
        for row in ordered:
            if row["day"]:
                continue
            lower = max((r for r in resolved if int(r["id"]) < int(row["id"])), key=lambda r: int(r["id"]), default=None)
            upper = min((r for r in resolved if int(r["id"]) > int(row["id"])), key=lambda r: int(r["id"]), default=None)
            if lower and upper and lower["day"] == upper["day"]:
                row.update(day=lower["day"], day_source="id_interpolated")
        days = {d.isoformat() for d in self.window_days()}
        receipt = {
            "list_pages": sorted(fetched), "listed_unique": len(ordered),
            "date_from_list": sum(r["day_source"] == "list" for r in ordered),
            "date_interpolated": sum(r["day_source"] == "id_interpolated" for r in ordered),
            "date_unresolved": sum(r["day"] is None for r in ordered),
            "in_window_days": {d: sum(r["day"] == d for r in ordered) for d in sorted(days)},
        }
        write_json(self.dir / "discovered.json", {"receipt": receipt, "rows": ordered})
        return receipt

    # -- freeze -------------------------------------------------------------
    def freeze(self, per_day_cap: int) -> dict[str, Any]:
        if (self.dir / "queue.json").exists():
            return read_json(self.dir / "queue.json")["receipt"]
        data = read_json(self.dir / "discovered.json")
        if data is None:
            raise SystemExit(f"{self.p.name}: run discover first")
        days = [d.isoformat() for d in self.window_days()]
        queue: list[dict[str, Any]] = []
        by_day: dict[str, int] = {}
        for day in days:
            group = sorted((r for r in data["rows"] if r["day"] == day), key=lambda r: int(r["id"]))
            k = min(per_day_cap, len(group))
            if k == 1:
                picks = [group[len(group) // 2]]
            else:
                picks = [group[round(i * (len(group) - 1) / (k - 1))] for i in range(k)] if k else []
            picks = list({r["id"]: r for r in picks}.values())
            by_day[day] = len(picks)
            queue.extend(picks)
        receipt = {"frozen_at": self.clock(), "per_day_cap": per_day_cap, "queued": len(queue), "by_day": by_day,
                   "selection": "per window day, evenly spaced by post ID; titles not used; no replenishment"}
        write_json(self.dir / "queue.json", {"receipt": receipt, "queue": queue})
        return receipt

    # -- fetch --------------------------------------------------------------
    def extract_post(self, root: Node, head_text: str, list_row: dict[str, Any]) -> dict[str, Any]:
        def meta(prop: str) -> str | None:
            for node in root.select("meta"):
                if node.attrs.get("property") == prop or node.attrs.get("name") == prop:
                    return node.attrs.get("content")
            return None

        def source(spec: str, exclude: str | None = None) -> str | None:
            kind, _, arg = spec.partition(":")
            if kind == "meta":
                return meta(arg)
            if kind == "css":
                node = root.select_one(arg)
                return node.text(exclude=exclude) if node else None
            if kind == "attr":
                sel, _, attr = arg.rpartition(":")
                node = root.select_one(sel)
                return node.attrs.get(attr) if node else None
            if kind == "title":
                node = root.select_one("title")
                return node.text() if node else None
            if kind == "regex":
                m = re.search(arg, head_text)
                return m.group(1) if m else None
            raise ValueError(spec)

        title = next((t for s in self.p.title_sources if (t := source(s, self.p.title_exclude))), "")
        if self.p.title_strip:
            title = re.sub(self.p.title_strip, "", title).strip()
        published_raw = None
        published = None
        for spec in self.p.date_sources:
            raw = source(spec)
            if raw and (value := parse_post_datetime(raw)):
                published_raw, published = raw, value
                break
        canonical = next((n.attrs.get("href") for n in root.select("link[rel=canonical]")), None)
        return {"opened_title": " ".join(title.split()), "list_title": list_row.get("title"),
                "published_raw": published_raw, "published_at": published.isoformat() if published else None,
                "canonical": canonical}

    def open_post(self, row: dict[str, Any]) -> dict[str, Any]:
        url = row["url"]
        base: dict[str, Any] = {"site": self.p.name, "id": row["id"], "url": url, "list_day": row["day"],
                                "attempted_at": self.clock(), "comment_guard": self.p.comment_guard}
        verdict = self.robots_allows(url)
        if not verdict["allowed"]:
            return {**base, "state": "robots_denied", "detail": verdict["basis"]}
        return self.request(url, "post", lambda response: self._read_post(response, row, dict(base)))

    def _read_post(self, response: Response, row: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
        url = row["url"]
        record.update(status=response.status, final_url=response.url)
        if response.status in (301, 302, 303, 307, 308):
            location = response.headers.get("location", "")
            record["state"] = "members_only" if re.search(r"login|member|signin", location, re.I) else "redirect"
            record["location"] = location
            return record
        if response.status in (404, 410):
            record["state"] = "deleted"
            return record
        iterator = iter(response.chunks)
        first = next(iterator, b"")
        # Buffer enough to see a late <meta charset> (and, for errors, a challenge page).
        while len(first) < 20000 and (piece := next(iterator, None)) is not None:
            first += piece
        self._check_site_status(response, first, url)
        if response.status != 200:
            record["state"] = f"http_{response.status}"
            return record
        decoder = codecs.getincrementaldecoder(sniff_encoding(response.headers, first))("replace")
        builder = TreeBuilder(watch=self.p.body, forbid=self.p.comment_guard)
        received = 0
        try:
            for chunk in _chain(first, iterator):
                received += len(chunk)
                if received > 3_000_000:
                    raise BoundaryError("byte ceiling")
                builder.feed(decoder.decode(chunk))
            builder.feed(decoder.decode(b"", final=True))
        except StopParsing:
            pass
        except BoundaryError as exc:
            # Parsing stopped at the forbidden start tag: none of its text was read.
            record.update(state="boundary_error", detail=str(exc), bytes_read=received,
                          comments_parsed=False)
            return record
        # Every comment-guard match anywhere before the parse stopped raises above, so with a
        # guard this is a checked result. Without one it is unknown, not False.
        record.update(bytes_read=received, stopped_at_body_close=builder.closed,
                      comments_parsed=False if self.p.comment_guard else None)
        root = builder.root
        head_text = root.text()
        if builder.watched is None:
            page_text = head_text
            if any(m in page_text for m in self.p.wall_markers):
                record["state"] = "members_only"
            elif any(m in page_text for m in self.p.deleted_markers):
                record["state"] = "deleted"
            else:
                record["state"] = "selector_missing"
            return record
        body = builder.watched.text(lines=True)
        record.update(self.extract_post(root, head_text, row))
        record.update(body=body, body_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest())
        if record.get("canonical"):
            canonical = _norm_url(urljoin(url, record["canonical"]))
            aliases = {_norm_url(a.format(id=row["id"])) for a in self.p.canonical_aliases}
            record["canonical_identity"] = "exact" if canonical == _norm_url(url) else (
                "declared_alias" if canonical in aliases else "mismatch")
        if any(m in body for m in self.p.wall_markers):
            record["state"] = "members_only"
        elif not builder.closed:
            record["state"] = "truncated_body"  # response ended before the body element closed
        elif not body.strip():
            record["state"] = "empty_body"
        elif body.count("\ufffd") > 2:
            record["state"] = "encoding_error"  # charset guessed wrong; text is not the original
        elif record.get("canonical_identity") == "mismatch":
            record["state"] = "canonical_mismatch"  # page declares itself to be a different post
        elif not record["published_at"]:
            record["state"] = "date_missing"
        elif not self.window_start <= datetime.fromisoformat(record["published_at"]) <= self.window_end:
            record["state"] = "outside_window"
        else:
            record["state"] = "eligible"
        return record

    def fetch(self, max_posts: int, parser_drift_limit: int = 3, network_limit: int = 3) -> dict[str, Any]:
        self.require_robots()
        queue = read_json(self.dir / "queue.json")
        if queue is None:
            raise SystemExit(f"{self.p.name}: run freeze first")
        started = {r["id"] for r in read_jsonl(self.dir / "started.jsonl")}
        done = {r["id"] for r in read_jsonl(self.dir / "posts.jsonl")}
        unresolved = started - done
        misses = network_failures = opened = 0
        for row in queue["queue"]:
            if row["id"] in done or opened >= max_posts:
                continue
            if row["id"] in unresolved:
                continue  # attempted earlier without a completion receipt: never repeat silently
            append_jsonl(self.dir / "started.jsonl", {"id": row["id"], "at": self.clock()})
            try:
                record = self.open_post(row)
                network_failures = 0
            except NetworkError as exc:
                record = {"site": self.p.name, "id": row["id"], "url": row["url"], "state": "network_error",
                          "layer": exc.layer, "detail": exc.detail, "attempted_at": self.clock()}
                network_failures += 1
            except SiteStopped:
                append_jsonl(self.dir / "posts.jsonl", {"site": self.p.name, "id": row["id"], "url": row["url"],
                                                        "state": "site_stopped", "attempted_at": self.clock()})
                raise
            append_jsonl(self.dir / "posts.jsonl", record)
            opened += 1
            misses = misses + 1 if record["state"] in ("selector_missing", "boundary_error") else 0
            if misses >= parser_drift_limit:
                self.stop("parser_drift", f"{misses} consecutive posts without body selector {self.p.body!r} "
                                          f"or tripping comment guard {self.p.comment_guard!r}")
            if network_failures >= network_limit:
                self.stop("network_unreachable", f"{network_failures} consecutive network failures")
        return self.accounting()

    # -- accounting ----------------------------------------------------------
    def accounting(self) -> dict[str, Any]:
        discovered = read_json(self.dir / "discovered.json", {}) or {}
        queue = read_json(self.dir / "queue.json", {}) or {}
        posts = {r["id"]: r for r in read_jsonl(self.dir / "posts.jsonl")}
        started = {r["id"] for r in read_jsonl(self.dir / "started.jsonl")}
        states: dict[str, int] = {}
        for record in posts.values():
            states[record["state"]] = states.get(record["state"], 0) + 1
        requests = read_jsonl(self.dir / "requests.jsonl")
        result = {
            "site": self.p.name, "actor": self.actor, "stop": self.stopped(),
            "requests_total": len(requests),
            "network_errors": sum(r["state"] == "network_error" for r in requests),
            "list_pages": len(read_jsonl(self.dir / "lists.jsonl")),
            "discover": discovered.get("receipt"),
            "queued": len(queue.get("queue", [])),
            "opened_attempted": len(started),
            "unresolved_attempts": sorted(started - set(posts)),
            "post_states": states,
            "eligible_bodies": states.get("eligible", 0),
            "accepted": 0,
            "note": "accepted stays 0: A0 judgment, ethics and evidence gates happen after collection",
        }
        write_json(self.dir / "accounting.json", result)
        return result


def _norm_url(url: str) -> str:
    """Scheme, host case and a trailing slash do not change which post a URL names."""

    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/"
    return f"{(parts.hostname or '').lower()}{path}" + (f"?{parts.query}" if parts.query else "")


def _chain(first: bytes, rest: Iterator[bytes]) -> Iterator[bytes]:
    yield first
    yield from rest


# --------------------------------------------------------------------------- CLI


def load_contract(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.run_dir).expanduser()
    if not run_dir.is_absolute():
        raise SystemExit("--run-dir must be absolute")
    repo = inside_git_worktree(run_dir.resolve())
    if repo is not None:
        raise SystemExit(f"--run-dir is inside Git work tree {repo}; raw bodies must stay outside Vault/Git")
    path = run_dir / "contract.json"
    existing = read_json(path)
    if existing:
        for key in ("actor",):
            if getattr(args, key, None) and getattr(args, key) != existing[key]:
                raise SystemExit(f"run contract has {key}={existing[key]!r}; start a new --run-dir to change it")
        return existing
    if not args.actor:
        raise SystemExit("--actor is required for a new run")
    end = datetime.fromisoformat(args.window_end) if args.window_end else now()
    end = end if end.tzinfo else end.replace(tzinfo=KST)
    contract = {
        "collector_version": COLLECTOR_VERSION, "access_policy_version": ACCESS_POLICY_VERSION,
        "actor": args.actor, "user_agent": ACTORS[args.actor]["user_agent"],
        "robots_tokens": ACTORS[args.actor]["robots_tokens"],
        "window_end": end.isoformat(), "window_start": (end - timedelta(hours=args.window_hours)).isoformat(),
        "window_hours": args.window_hours, "created_at": now(),
        "comments": "body-only; parse stops at the body end tag; profile comment guards exclude posts that hit comments first",
    }
    write_json(path, contract)
    return contract


def main(argv: list[str] | None = None, transport_factory: Callable[[str], Any] = UrllibTransport,
         sleep: Callable[[float], None] = time.sleep) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["robots", "discover", "freeze", "fetch", "all", "status", "profiles"])
    parser.add_argument("--run-dir", help="absolute directory outside Vault/Git")
    parser.add_argument("--site", action="append", help="profile name; repeatable")
    parser.add_argument("--actor", choices=sorted(ACTORS))
    parser.add_argument("--window-end", help="ISO timestamp; default now (KST)")
    parser.add_argument("--window-hours", type=int, default=24)
    parser.add_argument("--page-budget", type=int, default=24, help="max list pages per site")
    parser.add_argument("--per-day-cap", type=int, default=4)
    parser.add_argument("--max-posts", type=int, default=40, help="max post opens per site per invocation")
    parser.add_argument("--delay", type=float, default=2.5, help="seconds between requests (min 2.0)")
    args = parser.parse_args(argv)

    if args.stage == "profiles":
        for p in PROFILES.values():
            print(f"{p.name:11s} {p.label} | live: {p.live_verified or 'unverified'} | {p.note}")
        return 0
    if not args.run_dir or not args.site:
        parser.error("--run-dir and --site are required")
    unknown = [s for s in args.site if s not in PROFILES]
    if unknown:
        parser.error(f"unknown site(s): {unknown}; see `profiles`")
    contract = load_contract(args)
    transport = transport_factory(contract["user_agent"])
    exit_code = 0
    for name in args.site:
        site = SiteRun(Path(args.run_dir), PROFILES[name], contract["actor"], transport, contract,
                       sleep=sleep, min_delay=max(2.0, args.delay))
        try:
            if args.stage in ("robots", "all"):
                site.require_robots()
            if args.stage in ("discover", "all"):
                print(name, "discover", json.dumps(site.discover(args.page_budget), ensure_ascii=False))
            if args.stage in ("freeze", "all"):
                print(name, "freeze", json.dumps(site.freeze(args.per_day_cap), ensure_ascii=False, default=str))
            if args.stage in ("fetch", "all"):
                site.fetch(args.max_posts)
        except SiteStopped as exc:
            print(name, "STOPPED", exc.state, exc.detail)
            exit_code = 2
        except Exception as exc:  # isolate: one site's failure never prevents the next site
            state = "network_unreachable" if isinstance(exc, NetworkError) else "collector_error"
            trace = traceback.format_exc()
            try:
                site.stop(state, f"{type(exc).__name__}: {exc}",
                          traceback=None if isinstance(exc, NetworkError) else trace)
            except SiteStopped:
                pass
            print(name, "STOPPED", state, f"{type(exc).__name__}: {exc}")
            if state == "collector_error":
                print(trace, file=sys.stderr)  # a collector bug, not a site fault
            exit_code = 2
        print(name, "status", json.dumps(site.accounting(), ensure_ascii=False, default=str))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
