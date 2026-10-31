# Scrapy Local Community Crawler — Unimplemented Design Targets

> **2026-10-31 vault note:** the runnable collector is now `scripts/community-collector.py` (stdlib, resumable, actor-aware robots, date-targeted discovery, per-post skip, body-only streaming; offline suite `scripts/test-community-collector.py`). Its list/body parsers are separate from this Scrapy spider's, so a selector fix must be made in both if the spider is still used. This document remains the historical Scrapy design contract.

**Distribution status:** the bundled code implements construction, fixed profiles, list parsing and body parsing only. `start()` is an empty async generator. Scheduling, live collection, date-window enforcement, close receipts, accounting files and resume orchestration are NOT implemented. The specifications below are design targets, not shipped behavior or completed acceptance tests. Do not use `runspider` as a working collection recipe. See `references/portable-setup.md`.

This design does not register Scrapy as a Hermes `web_search`/`web_extract` provider.

## Grounding and pinned runtime

- Upstream: <https://github.com/scrapy/scrapy>
- Runtime: `Scrapy==2.17.0` from PyPI, isolated with `uv tool`.
- License: BSD-3-Clause.
- Python: Scrapy 2.17.0 requires Python 3.10+.
- This is a version-pinned test dependency, not a claim of current security support. Reassess upstream security notices before live deployment.
- Official 2.17.0 source docs govern `JOBDIR`, retry settings, AutoThrottle, robots.txt, timeouts, concurrency, and feed exports.

Always invoke the pinned runtime through:

```bash
uv tool run --from 'Scrapy==2.17.0' scrapy ...
```

Use the explicit pinned runtime rather than assuming the PATH-selected Scrapy version.

## Scope and non-goals

Scrapy owns:

- per-site HTTP scheduling;
- list and body requests;
- source-specific CSS selectors;
- request deduplication;
- clean-stop resume through one unique `JOBDIR` per site/run;
- conservative retry, timeout, concurrency, and AutoThrottle settings;
- raw HTML, JSONL records, diagnostics, and accounting outside the Vault.

Scrapy does not own:

- search-engine discovery;
- remote egress or anti-bot bypass;
- login, cookies obtained from a user account, CAPTCHA solving, proxy rotation, or robots.txt evasion;
- ethical admission, dramatic expansion, shortlist selection, or Vault publication;
- claims that an HTTP 200 or non-empty selector is evidence enough.

A local DNS/TCP/TLS/site-edge failure remains a failure. The crawler must preserve the boundary rather than label it a parser defect or silently substitute another source.

## Architecture

Add two skill-local files:

1. `scripts/public-community-spider.py`
   - standalone `scrapy runspider` entry point;
   - four explicit profiles: `instiz`, `clien`, `82cook`, `ruliweb`;
   - list parsing and body parsing remain profile-specific;
   - one item per opened post with canonical ID, list/open titles, page date, body, bounded comments, response status, selector counts, and artifact paths;
   - writes raw list/body HTML and a machine-readable close receipt.
2. `scripts/test-public-community-spider.py`
   - fixture-driven parser and accounting tests;
   - no live community request is required for the unit suite.

Keep the profile table data-only where possible. Shared code may normalize whitespace, canonical IDs, response receipts, evidence phrases, and accounting, but it must not pretend the four DOMs are one schema.

The Instiz profile is limited to the login-free `https://www.instiz.net/name?page=N` list and query-free `https://www.instiz.net/name/<id>` bodies. Its current parser contract is `td.listsubject a[href]` → numeric `/name/<id>`, title `.sbj` or `.texthead_notice` without nested `cmtN` counters, opened title `#nowsubject` under the same badge rule, date `meta[property="article:published_time"]@content`, body `#memo_content_1.memo_content`, and bounded comments `.comment_memo .comment_line`. A crawler item remains `accepted=0` until separate body, ethics, privacy, and self-copy review; school, workplace, age, family, relationship, and location clues require removal or strong transformation.

## Proposed command contract — not a working collector

```bash
uv tool run --from 'Scrapy==2.17.0' scrapy runspider \
  scripts/public-community-spider.py \
  -a site=clien \
  -a target_date=YYYY-MM-DD \
  -a output_root=/absolute/path/out \
  -a max_pages=2 \
  -s JOBDIR=/absolute/path/out/clien/job \
  -O /absolute/path/out/clien/items.jsonl:jsonlines
```

Required arguments: `site`, `target_date`, and absolute `output_root`. `max_pages` is bounded and defaults to a conservative probe. Unknown sites, relative output paths, reused cross-site `JOBDIR` values, and unsupported dates fail before network I/O.

## Per-site output contract

Every run writes under `output_root/<site>/`:

```text
manifest.json
lists/*.html
posts/*.html
items.jsonl
request_queue.jsonl
request_receipts.jsonl
accounting.json
diagnostics.jsonl
job/                  # Scrapy JOBDIR, unique to this site/run
```

The output root must be outside the Vault and Git. Raw identifiers stay there. Durable notes may carry only canonical public URLs and sanitized evidence.

Accounting keeps these layers separate:

- `list_requests_attempted`
- `list_responses_ok`
- `listed_unique`
- `title_filtered_out`
- `opened_attempted`
- `opened_ok`
- `same_day_rows_retained`
- `nonempty_body`
- `accepted` (always left for the later human/LLM evidence gate)
- status/exception counts and final access boundary

## Access policy and settings

Default settings are intentionally conservative:

- `ROBOTSTXT_OBEY=True`;
- descriptive browser-compatible user agent, no identity spoofing claim;
- `CONCURRENT_REQUESTS_PER_DOMAIN=1`;
- `DOWNLOAD_DELAY>=2.0` seconds;
- `RANDOMIZE_DOWNLOAD_DELAY=True`;
- `DOWNLOAD_TIMEOUT=25` seconds;
- `AUTOTHROTTLE_ENABLED=True`;
- `AUTOTHROTTLE_TARGET_CONCURRENCY=0.5`;
- bounded retry for connection/timeouts and transient 408/5xx only;
- first explicit 403/429/430 closes that site with an access-boundary receipt; do not amplify the queue;
- no redirect from an approved host to login, consent, or unrelated hosts is admitted as body evidence.

Scrapy retry is not described as exponential backoff. Site-level relaunch, when justified, is orchestrated outside the spider with bounded exponential backoff plus jitter and the same site-specific `JOBDIR`; `Retry-After` wins. A retry must never broaden domains, dates, pages, or source class.

## Resume rules

Official Scrapy 2.17.0 `JOBDIR` persists scheduled requests, duplicate filtering, and spider state after a clean stop. One job directory must never be shared by different spiders or runs.

On resume:

1. preserve the original list snapshots and run manifest;
2. reuse only the same site/run `JOBDIR`;
3. compute unopened canonical IDs from persisted receipts;
4. append JSONL receipts and deduplicate by canonical ID during reconciliation;
5. do not add prior counters a second time;
6. label a later list fetch as a supplemental sweep, not as the original boundary.

Cookies can expire and are not part of this public crawl contract.

## Data flow and evidence gate

1. Snapshot the approved list response before parsing it.
2. Record every unique canonical ID in `request_queue.jsonl` before body date filtering.
3. Open bounded body requests and save raw HTML before extraction.
4. Extract with the known source-specific selectors from the direct-crawl reference.
5. Reject or flag wrong-page, login-wall, empty-body, redirect-host, and selector-mismatch cases.
6. Emit machine records; do not auto-accept dramatic cards.
7. Reopen accepted URLs later and apply title/date/body plus two-phrase live evidence verification.

## Error model

Classify failures at the narrowest observed layer:

- DNS
- TCP connect
- TLS handshake/certificate
- redirect/final host
- HTTP status or rate limit
- robots.txt denial
- list selector zero
- body selector zero/wrong page
- date/parser mismatch
- interrupted/dirty stop

Do not collapse these into “site blocked.” Each site closes independently and preserves its own receipt.

## Test and acceptance contract

Before use:

1. fixture tests prove each profile’s canonical ID, title, date, and body extraction;
2. duplicate links produce one queue item;
3. list/body counters remain distinct around date filtering;
4. 403/429/430 records an access boundary and closes the site;
5. relative output paths and invalid profile names fail before request scheduling;
6. a local HTTP fixture proves raw artifacts, JSONL output, `accounting.json`, and clean `JOBDIR` resume;
7. one bounded public smoke run proves the actual 2.17.0 runtime path;
8. an Instiz smoke proves robots allowance plus login-free list/body access, numeric canonical identity, publication metadata, non-empty body extraction, and `accepted=0` before manual ethics review.

No commit, push, Vault publication, login, or source-pool expansion is implied by this integration.
