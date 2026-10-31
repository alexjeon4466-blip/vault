#!/usr/bin/env python3
"""Verify the durable structure of a public-community harvest note.

This intentionally checks local note structure only. Live HTTP evidence belongs in a
separate verifier so a network outage cannot masquerade as a malformed note.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

SITE_DOMAINS = {
    "인스티즈": ("instiz.net",),
    "클리앙": ("clien.net",),
    "FMKorea": ("fmkorea.com",),
    "에펨코리아": ("fmkorea.com",),
    "MLBPARK": ("mlbpark.donga.com",),
    "엠엘비파크": ("mlbpark.donga.com",),
    "82cook": ("82cook.com",),
    "루리웹": ("ruliweb.com",),
    "Ruliweb": ("ruliweb.com",),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("note", type=Path)
    parser.add_argument("--expected-count", type=int, required=True)
    parser.add_argument(
        "--site-count",
        action="append",
        default=[],
        metavar="SITE=COUNT",
        help="Repeat for every source site that should have accepted cards.",
    )
    return parser.parse_args()


def frontmatter(text: str) -> str:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", text, flags=re.S)
    if not match:
        raise ValueError("missing or malformed YAML frontmatter fence")
    return match.group(1)


def source_urls(fm: str) -> list[str]:
    lines = fm.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "sources:") + 1
    except StopIteration as exc:
        raise ValueError("frontmatter has no sources list") from exc
    urls: list[str] = []
    for line in lines[start:]:
        if line and not line.startswith((" ", "\t")):
            break
        match = re.match(r"\s*-\s*[\"']?(https?://[^\"']+?)[\"']?\s*$", line)
        if match:
            urls.append(match.group(1))
    return urls


def parse_site_counts(items: list[str]) -> dict[str, int]:
    parsed: dict[str, int] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"invalid --site-count {item!r}; expected SITE=COUNT")
        label, raw_count = item.rsplit("=", 1)
        label = label.strip()
        if not label:
            raise ValueError("site label cannot be empty")
        parsed[label] = int(raw_count)
    return parsed


def source_site(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    for label, domains in SITE_DOMAINS.items():
        if any(host == domain or host.endswith("." + domain) for domain in domains):
            return label
    return host


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    if not args.note.is_file():
        print(f"ERROR: note not found: {args.note}", file=sys.stderr)
        return 2

    text = args.note.read_text(encoding="utf-8")
    try:
        fm = frontmatter(text)
        urls = source_urls(fm)
        expected_sites = parse_site_counts(args.site_count)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    card_headings = re.findall(r"(?m)^##\s+\d+\.\s+\S.*$", text)
    source_rows = re.findall(r"(?m)^- \*\*원문:\*\*\s+.+https?://\S+\s*$", text)

    if len(card_headings) != args.expected_count:
        errors.append(f"card headings: expected {args.expected_count}, got {len(card_headings)}")
    if len(source_rows) != args.expected_count:
        errors.append(f"source rows: expected {args.expected_count}, got {len(source_rows)}")
    if len(urls) != args.expected_count:
        errors.append(f"frontmatter sources: expected {args.expected_count}, got {len(urls)}")
    if len(set(urls)) != len(urls):
        errors.append("frontmatter sources contain duplicate URLs")

    observed = Counter(source_site(url) for url in urls)
    for label, expected in expected_sites.items():
        domains = SITE_DOMAINS.get(label)
        if domains is None:
            errors.append(f"unknown site label in --site-count: {label}")
            continue
        count = sum(
            1
            for url in urls
            if any(
                (urlparse(url).hostname or "").lower() == domain
                or (urlparse(url).hostname or "").lower().endswith("." + domain)
                for domain in domains
            )
        )
        if count != expected:
            errors.append(f"site {label}: expected {expected}, got {count}")

    expected_total = sum(expected_sites.values())
    if expected_sites and expected_total != args.expected_count:
        errors.append(
            f"site-count total {expected_total} does not equal expected-count {args.expected_count}"
        )

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    display = ", ".join(f"{label}={count}" for label, count in expected_sites.items())
    print(
        f"PASS: {args.note} | cards={len(card_headings)} | sources={len(urls)}"
        + (f" | {display}" if display else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
