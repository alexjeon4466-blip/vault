#!/usr/bin/env python3
"""Standalone Scrapy entry point for bounded public-community crawling."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import scrapy


PROFILES: dict[str, dict[str, Any]] = {
    "instiz": {
        "list_url": "https://www.instiz.net/name?page={page}",
        "allowed_hosts": ("www.instiz.net", "instiz.net"),
    },
    "clien": {
        "list_url": "https://www.clien.net/service/board/park?od=T31&po={page0}",
        "allowed_hosts": ("www.clien.net", "clien.net"),
    },
    "ruliweb": {
        "list_url": "https://bbs.ruliweb.com/community/board/300147",
        "allowed_hosts": ("bbs.ruliweb.com",),
        "supplemental": True,
        "body_only": True,
    },
    "82cook": {
        "list_url": "https://www.82cook.com/entiz/enti.php?bn=15&page={page}",
        "allowed_hosts": ("www.82cook.com", "82cook.com"),
        "window": "rolling_24h",
        "body_only": True,
    },
}


def _normalize_text(value: str | None) -> str:
    """Collapse all HTML/line-break whitespace to one space."""

    return " ".join((value or "").split())


def _selector_text(selector: Any) -> str:
    """Return normalized text from an element and all descendants."""

    return _normalize_text(" ".join(selector.xpath(".//text()").getall()))


def _first_text(selectors: Any) -> str:
    for selector in selectors:
        text = _selector_text(selector)
        if text:
            return text
    return ""


def _first_text_without_comment_badges(selectors: Any) -> str:
    """Read an Instiz list title without nested ``cmtN`` badges."""

    for selector in selectors:
        text = _normalize_text(
            " ".join(
                selector.xpath(
                    ".//text()[not(ancestor::span["
                    "starts-with(normalize-space(@class), 'cmt')])]"
                ).getall()
            )
        )
        if text:
            return text
    return ""


def _single_query_value(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    if values is None or len(values) != 1:
        return None
    return values[0]


class PublicCommunitySpider(scrapy.Spider):
    """Bounded crawler for the fixed public-community source pool."""

    name = "public_community"
    COMMENT_LIMIT = 20
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "USER_AGENT": (
            "Mozilla/5.0 (compatible; HermesPublicCommunityCrawler/1.0; "
            "public-research; no-login)"
        ),
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 2.0,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "DOWNLOAD_TIMEOUT": 25,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 2.0,
        "AUTOTHROTTLE_MAX_DELAY": 30.0,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 0.5,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 1,
        "RETRY_HTTP_CODES": [408, *range(500, 600)],
        "COOKIES_ENABLED": False,
        "TELNETCONSOLE_ENABLED": False,
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def __init__(
        self,
        site: str | None = None,
        target_date: str | None = None,
        output_root: str | None = None,
        max_pages: str | int = 1,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        if site not in PROFILES:
            supported = ", ".join(PROFILES)
            raise ValueError(f"unsupported site {site!r}; choose one of: {supported}")
        self.site = site
        self.profile = PROFILES[site]

        if not isinstance(target_date, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}", target_date
        ):
            raise ValueError("target_date must be a real YYYY-MM-DD date")
        try:
            parsed_target_date = date.fromisoformat(target_date)
        except ValueError as exc:
            raise ValueError("target_date must be a real YYYY-MM-DD date") from exc
        self.target_date = parsed_target_date.isoformat()

        if output_root is None:
            raise ValueError("output_root is required")
        root = Path(output_root).expanduser()
        if not root.is_absolute():
            raise ValueError("output_root must be absolute")
        self.output_root = root.resolve()

        if isinstance(max_pages, bool):
            raise ValueError("max_pages must be an integer from 1 to 10")
        if isinstance(max_pages, int):
            parsed_max_pages = max_pages
        elif isinstance(max_pages, str) and re.fullmatch(r"\d+", max_pages):
            parsed_max_pages = int(max_pages)
        else:
            raise ValueError("max_pages must be an integer from 1 to 10")
        if not 1 <= parsed_max_pages <= 10:
            raise ValueError("max_pages must be an integer from 1 to 10")
        self.max_pages = parsed_max_pages

        self.target_date_arg = target_date
        self.output_root_arg = output_root
        self.max_pages_arg = max_pages
        self.allowed_domains = list(self.profile["allowed_hosts"])

    def extract_list_candidates(self, response: Any) -> list[dict[str, str]]:
        """Extract canonical post identities from one site's list response."""

        if self.site == "instiz":
            anchors = response.css("td.listsubject a[href]")
        elif self.site == "clien":
            anchors = response.css("a.list_subject[href]")
        elif self.site == "ruliweb":
            anchors = response.css(
                "a[href*='/community/board/300147/read/']"
            )
        else:  # 82cook
            anchors = response.css("#column2 a[href*='read.php']")

        candidates: list[dict[str, str]] = []
        candidate_indexes: dict[str, int] = {}

        for anchor in anchors:
            href = anchor.attrib.get("href")
            if not href:
                continue
            parsed = urlparse(urljoin(response.url, href))
            if (
                parsed.scheme not in {"http", "https"}
                or parsed.hostname not in self.profile["allowed_hosts"]
            ):
                continue

            canonical_id: str | None = None
            canonical_url: str | None = None
            query = parse_qs(parsed.query, keep_blank_values=True)

            if self.site == "instiz":
                match = re.fullmatch(r"/name/(\d+)/?", parsed.path)
                if match:
                    canonical_id = match.group(1)
                    canonical_url = f"https://www.instiz.net/name/{canonical_id}"

            elif self.site == "clien":
                match = re.fullmatch(
                    r"/service/board/([^/]+)/([0-9]+)", parsed.path
                )
                if match:
                    board, number = match.groups()
                    canonical_id = f"{board}/{number}"
                    canonical_url = (
                        "https://www.clien.net/service/board/"
                        f"{canonical_id}"
                    )

            elif self.site == "ruliweb":
                match = re.fullmatch(
                    r"/community/board/300147/read/(\d+)/?", parsed.path
                )
                if match and not parsed.query:
                    canonical_id = match.group(1)
                    canonical_url = (
                        "https://bbs.ruliweb.com/community/board/300147/read/"
                        f"{canonical_id}"
                    )

            elif self.site == "82cook":
                board = _single_query_value(query, "bn")
                number = _single_query_value(query, "num")
                if (
                    parsed.path == "/entiz/read.php"
                    and board == "15"
                    and number is not None
                    and number.isdecimal()
                ):
                    canonical_id = number
                    canonical_url = (
                        "https://www.82cook.com/entiz/read.php"
                        f"?bn=15&num={canonical_id}"
                    )

            if canonical_id is None or canonical_url is None:
                continue

            if self.site == "82cook":
                row_text = (
                    _first_text(anchor.xpath("ancestor::tr[1]"))
                    or _selector_text(anchor)
                )
                if "공지" in row_text:
                    continue

            if self.site == "instiz":
                title = _first_text_without_comment_badges(
                    anchor.css("div.sbj, span.texthead_notice")
                )
            else:
                title = _selector_text(anchor)
            if not title:
                continue
            existing_index = candidate_indexes.get(canonical_id)
            if existing_index is None:
                candidate_indexes[canonical_id] = len(candidates)
                candidates.append(
                    {
                        "site": self.site,
                        "canonical_id": canonical_id,
                        "canonical_url": canonical_url,
                        "list_title": title,
                    }
                )
            elif (
                candidates[existing_index]["list_title"].isdecimal()
                and not title.isdecimal()
            ):
                candidates[existing_index]["list_title"] = title

        return candidates

    def extract_post_record(
        self, response: Any, candidate: dict[str, str]
    ) -> dict[str, Any]:
        """Extract a normalized post record without scheduling more requests."""

        canonical_id = _normalize_text(candidate.get("canonical_id"))
        list_title = _normalize_text(candidate.get("list_title"))

        if self.site == "instiz":
            title_nodes = response.css("span#nowsubject")
            date_nodes = response.css(
                'meta[property="article:published_time"][content]'
            )
            body_nodes = response.css("div#memo_content_1.memo_content")
            comment_nodes = response.css("td.comment_memo div.comment_line")
            opened_title = (
                _first_text_without_comment_badges(title_nodes) or list_title
            )
            page_date = (
                _normalize_text(date_nodes[0].attrib.get("content"))
                if date_nodes
                else ""
            )

        elif self.site == "clien":
            title_nodes = response.css("h3.post_subject")
            date_nodes = response.css("div.post_author span.date")
            body_nodes = response.css("div.post_article")
            comment_nodes = response.css("div.comment_row div.comment_view")
            opened_title = _first_text(title_nodes) or list_title
            page_date = _first_text(date_nodes)

        elif self.site == "ruliweb":
            title_nodes = response.css('meta[property="og:title"][content]')
            date_nodes = response.css("span.regdate")
            body_nodes = response.css("div.view_content")
            comment_nodes = response.css(".__hermes_comments_disabled__")
            opened_title = (
                _normalize_text(title_nodes[0].attrib.get("content"))
                if title_nodes
                else list_title
            )
            page_date = _first_text(date_nodes)

        else:  # 82cook, body-only by contract
            title_nodes = response.css("#column2 h1, .bbs_view_header h1")
            date_nodes = response.xpath(
                '//text()[contains(., "작성일") and '
                'not(ancestor::*[contains(@class, "comment") or '
                'contains(@id, "comment")])]'
            )
            body_nodes = response.css("#articleBody")
            comment_nodes = response.css(".__hermes_comments_disabled__")
            opened_title_candidate = _first_text(title_nodes)
            opened_title = (
                list_title
                if opened_title_candidate in {"", "자유게시판"}
                else opened_title_candidate
            )
            page_text = _normalize_text(" ".join(date_nodes.getall()))
            date_match = re.search(
                r"작성일\s*:\s*(20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
                page_text,
            )
            page_date = (
                _normalize_text(date_match.group(1)) if date_match else ""
            )

        comments = [
            text
            for text in (_selector_text(node) for node in comment_nodes)
            if text
        ][: self.COMMENT_LIMIT]
        body = _first_text(body_nodes)
        members_only_body = self.site == "instiz" and (
            "회원에게만 공개된 글이에요" in body
            or "로그인 후 이용해 주세요" in body
        )

        return {
            "site": self.site,
            "canonical_id": canonical_id,
            "canonical_url": candidate.get("canonical_url", ""),
            "list_title": list_title,
            "opened_title": opened_title,
            "page_date": page_date,
            "body": body,
            "public_body_eligible": bool(body) and not members_only_body,
            "access_exclusion_reason": (
                "members_only_body_wall" if members_only_body else None
            ),
            "comments": comments,
            "http_status": response.status,
            "selector_counts": {
                "title": len(title_nodes),
                "date": len(date_nodes),
                "body": len(body_nodes),
                "comments": len(comment_nodes),
            },
        }

    async def start(self) -> AsyncIterator[Any]:
        if False:  # Keep this a real async generator until start requests are added.
            yield None
