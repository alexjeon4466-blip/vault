#!/usr/bin/env python3
"""Deterministic structural checks for a community-only harvest note.

This does not replace source-specific live title/date/body verification.
It checks the saved artifact's provenance sets, numbering, caps, and scope.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse

CURRENT_POOL_VERSION = "2026-08-29"
PREVIOUS_POOL_VERSION = "2026-08-15"
ACTIVE_HOSTS = {
    "www.instiz.net": "Instiz",
    "instiz.net": "Instiz",
    "www.clien.net": "Clien",
    "clien.net": "Clien",
    "www.82cook.com": "82cook",
    "82cook.com": "82cook",
    "bbs.ruliweb.com": "RuliwebAdvice",
}
PREVIOUS_ACTIVE_HOSTS = {
    **{host: site for host, site in ACTIVE_HOSTS.items() if site != "RuliwebAdvice"},
    "www.todayhumor.co.kr": "TodayHumor",
    "todayhumor.co.kr": "TodayHumor",
    "todayhumor.com": "TodayHumor",
}
LEGACY_HOSTS = {
    "www.fmkorea.com": "FMKorea",
    "fmkorea.com": "FMKorea",
    "mlbpark.donga.com": "MLBPARK",
}
CURRENT_EXCLUDED_HOST_PARTS = (
    "bobaedream", "todayhumor", "fmkorea", "mlbpark", "ppomppu", "theqoo"
)
PREVIOUS_EXCLUDED_HOST_PARTS = (
    "bobaedream", "ruliweb", "fmkorea", "mlbpark", "ppomppu", "theqoo"
)


def frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---", 4)
    return text[4:end] if end >= 0 else ""


def list_field(block: str, key: str) -> list[str]:
    lines = block.splitlines()
    values: list[str] = []
    active = False
    for line in lines:
        if re.match(rf"^{re.escape(key)}:\s*$", line):
            active = True
            continue
        if active:
            match = re.match(r'^\s+-\s+["\']?(.*?)["\']?\s*$', line)
            if match:
                values.append(match.group(1))
                continue
            if re.match(r"^[A-Za-z_][\w-]*:\s*", line):
                break
    return values


def scalar_field(block: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*[\"']?([^\n\"']+)", block)
    return match.group(1).strip() if match else None


def _single_query_value(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    if values is None or len(values) != 1:
        return None
    return values[0]


def approved_site(url: str, *, policy_mode: str) -> str | None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    query = parse_qs(parsed.query, keep_blank_values=True)

    hosts = (
        ACTIVE_HOSTS
        if policy_mode == "current"
        else PREVIOUS_ACTIVE_HOSTS
        if policy_mode == PREVIOUS_POOL_VERSION
        else {**PREVIOUS_ACTIVE_HOSTS, **ACTIVE_HOSTS}
    )
    site = hosts.get(host)
    if site == "Instiz":
        return site if re.fullmatch(r"/name/\d+/?", parsed.path) else None
    if site == "Clien":
        return site if re.fullmatch(r"/service/board/[^/]+/\d+/?", parsed.path) else None
    if site == "TodayHumor":
        if host == "todayhumor.com":
            return site if parsed.path in {"", "/"} and re.fullmatch(
                r"freeboard_\d+", parsed.query
            ) else None
        table = _single_query_value(query, "table")
        number = _single_query_value(query, "no")
        return site if (
            parsed.path == "/board/view.php"
            and table == "freeboard"
            and number is not None
            and number.isdecimal()
        ) else None
    if site == "82cook":
        board = _single_query_value(query, "bn")
        number = _single_query_value(query, "num")
        return site if (
            parsed.path == "/entiz/read.php"
            and board == "15"
            and number is not None
            and number.isdecimal()
        ) else None
    if site == "RuliwebAdvice":
        return site if (
            not parsed.query
            and re.fullmatch(
                r"/community/board/300147/read/\d+/?", parsed.path
            )
        ) else None

    if policy_mode == "legacy-compatible":
        return LEGACY_HOSTS.get(host)
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("note", type=Path)
    parser.add_argument("--max-total", type=int, default=20)
    parser.add_argument("--max-per-site", type=int, default=5)
    args = parser.parse_args()

    text = args.note.read_text(encoding="utf-8")
    fm = frontmatter(text)
    errors: list[str] = []

    pool_version = scalar_field(fm, "community_pool_version")
    if pool_version is None:
        policy_mode = "legacy-compatible"
    elif pool_version == CURRENT_POOL_VERSION:
        policy_mode = "current"
    elif pool_version == PREVIOUS_POOL_VERSION:
        policy_mode = PREVIOUS_POOL_VERSION
    else:
        policy_mode = "unknown"
        errors.append(
            "community_pool_version must be "
            f"{CURRENT_POOL_VERSION!r} for current harvest notes"
        )

    sources = list_field(fm, "sources")
    source_set = set(sources)
    card_urls = re.findall(
        r"(?m)^- \*\*원문:\*\* .*? / (https?://\S+)\s*$", text
    )
    card_set = set(card_urls)
    numbers = [
        int(match.group(1) or match.group(2))
        for match in re.finditer(
            r"(?m)^## (?:(\d+)\.|\[후보\s+(\d+)\])", text
        )
    ]

    if scalar_field(fm, "source_scope") != "community-only":
        errors.append("frontmatter source_scope must be community-only")
    if card_urls and not sources:
        errors.append("frontmatter sources is empty or unparsable while cards exist")
    if len(sources) != len(source_set):
        errors.append("frontmatter sources contains duplicates")
    if len(card_urls) != len(card_set):
        errors.append("card source URLs contain duplicates")
    if source_set != card_set:
        errors.append(
            "frontmatter/card URL sets differ: "
            f"frontmatter_only={sorted(source_set-card_set)}, "
            f"cards_only={sorted(card_set-source_set)}"
        )
    if numbers != list(range(1, len(card_urls) + 1)):
        errors.append(f"card numbering is not sequential: {numbers}")
    if len(card_urls) > args.max_total:
        errors.append(f"total {len(card_urls)} exceeds cap {args.max_total}")

    counts: Counter[str] = Counter()
    unapproved_urls: list[str] = []
    for url in sources:
        site = approved_site(url, policy_mode=policy_mode)
        if site:
            counts[site] += 1
        else:
            unapproved_urls.append(url)
    if unapproved_urls:
        errors.append(f"unapproved source URLs: {sorted(set(unapproved_urls))}")
    for site, count in counts.items():
        if count > args.max_per_site:
            errors.append(f"{site} count {count} exceeds cap {args.max_per_site}")

    all_urls = re.findall(r"https?://[^\s)\]>]+", text)
    excluded_host_parts = (
        CURRENT_EXCLUDED_HOST_PARTS
        if policy_mode == "current"
        else PREVIOUS_EXCLUDED_HOST_PARTS
        if policy_mode == PREVIOUS_POOL_VERSION
        else ()
    )
    excluded_hits = sorted({
        host_part
        for url in all_urls
        for host_part in excluded_host_parts
        if host_part in ((urlparse(url).hostname or "").lower())
    })
    if excluded_hits:
        errors.append(f"excluded-site URL found: {excluded_hits}")

    report = {
        "note": str(args.note),
        "sources": len(sources),
        "cards": len(card_urls),
        "source_card_sets_equal": source_set == card_set,
        "sequential": numbers == list(range(1, len(card_urls) + 1)),
        "community_pool_version": pool_version,
        "policy_mode": policy_mode,
        "site_counts": dict(sorted(counts.items())),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
