# Public Community-First Play-Seed Harvest

This reference records the reusable details from the 2026-07-18 Korean public-community harvest correction. The parent `SKILL.md` contains the authoritative scope lock; this file holds operational detail.

## Trigger

Use this route when the user asks for `커뮤니티 채집`, names one or more communities, or explicitly distinguishes community posts from news/blog/RSS material.

## Scope contract before sourcing

Before opening any list, resolve the **current local contract**, not only the generic skill default. When the target vault has a durable decision note such as `wiki/writing/decisions/공개커뮤니티_채집풀_운영규칙_*.md`, read it first and preserve its exact list URLs, board IDs, query parameters, time window, and comment boundary. A historical `hitView` URL, a `freeboard` path, and an `bn=15` path are different pools; do not crawl a generic list first and correct the pool later.

Write the contract down before opening lists:

- fixed community names and list URLs;
- per-site maximum;
- overall maximum;
- whether fewer results are valid;
- explicit excluded sites;
- login/public-body requirement;
- whether comments are optional enrichment or required evidence;
- whether news may be used only for cross-checking.

Do not reuse a `다중소스20` template if its source mix conflicts with the contract.

## Packaged reference pool

This pool becomes the recipient's default only after adoption in `templates/collection-contract.md`; it is not evidence of current access:

| Role | Community | Public list / boundary |
|---|---|---|
| core | Instiz `일상` | `https://www.instiz.net/name` |
| core | Clien 모두의공원 | `https://www.clien.net/service/board/park` and `/service/board/park/<id>` only (the former `/service/group/community` entry is robots-denied for `*`) |
| supplemental B, rolling 24h, body-only | 82cook 자유게시판 `bn=15` | `https://www.82cook.com/entiz/enti.php?bn=15`; do not collect or adjudicate comments |
| supplemental B, rolling 24h, body-only | Ruliweb `고민상담 300147` | `https://bbs.ruliweb.com/community/board/300147`; exact query-free board for page 1, `?page=N` (no other query) for later list pages (2026-10-31 amendment), and `/community/board/300147/read/<id>` only; do not parse comments, replies, or JSON-LD comment bodies |

- Maximum 5 accepted cards per site.
- Maximum 20 total; 0–19 is valid when safety or quality filters reduce yield.
- New notes declare `community_pool_version: 2026-10-31`. `2026-08-29` notes remain valid with any Clien board.
- TodayHumor, FMKorea, and MLBPARK are inactive for current regular collection because current target bodies are not reproducibly available within the no-login/robots boundary. Historical notes remain valid under their historical contract.
- Bobaedream remains reserve B only and Inven 오픈이슈 is grade C (2026-10-31 re-evaluation); exclude Ppomppu, theqoo, and Ruliweb boards other than `300147`.
- Never fill missing slots with news or a non-approved community.

A newer user message overrides this table immediately.

## Community card admission

A post can qualify from its body alone when it contains a concrete person, action, relation, object, place, or changing time. Comments are not an admission ticket.

Use comments only when they add one of:

- material detail absent from the body;
- a new relationship cost;
- a concrete counterexample;
- a repeated lived action;
- a different authority or time horizon.

Treat comment experience, medical/legal/investment/product advice, and causal claims as unverified personal claims. Never generalize them as facts.

## Originality and repost handling

Classify every candidate as one of:

- original first-person post or question;
- original making/repair/use log;
- copied article or social post;
- image/video-only post;
- repeated cross-community repost.

A copied article or image/video-only post normally fails. Apply this source-originality boundary at A0 as well: `source-archive` is a handling lane, not permission to count a pure news copy as a community-origin yes. Distinguish a poster's substantive framing action or question from residue found only inside the copied article; retain the latter as an auditable source-scope exclusion, not as a sensitivity-based rejection. Rich comments do not automatically rescue a thin or transferred body, and comment novelty must never be used merely to fill a site quota. Use the narrow comment-thread exception only when the opened public post still supplies a minimally intelligible person/action/situation in its own body and the bounded comments add distinct lived scenes with new action, relation cost, or changing time. Label the body as reposted material and each comment contribution as unverified. If the body is only a news link, generic reaction, image-dependent caption, or board furniture, reject it even when the comments are interesting; harvest those commenters' experiences only through a separately public, body-grounded source. Deduplicate the same article, screenshot, or anecdote across sites.

## Crawl and cache discipline

For overlapping rolling windows, deduplicate against the preceding matching source batch's outside-Vault body manifest as well as Vault notes. A0 bodies are intentionally not all published in Vault, so a Vault-only URL search cannot establish novelty. Preserve current reacquisition counts, list repeated canonical URLs and body-hash agreement separately, and report non-repeated bodies/A0 yes without silently removing them from source accounting. Do not overwrite or re-adjudicate a repeated record's prior A1 or evidence-correction history through the new A0 batch.

1. Inspect the user-provided list URL first. For fast-moving same-day lists, record the access timestamp/timezone and snapshot the visible post IDs/URLs before opening candidates; otherwise page reshuffling can make later counts or row references irreproducible.
2. Save candidate title, canonical post URL, publication date, body extract, and bounded comment samples locally before synthesis. Deduplicate `opened` by canonical post ID rather than by page number or title, because the same post can move between list pages while the run is in progress.
3. Preserve A0 residue before topic judgment. Politics, grief, family, money, illness, law, violence, a short sentence, or a charged image are not automatic failures. Record the independently reusable question, irony, action, role contradiction, object, sound, interrupted time, or voice rhythm, then assign `clear`, `transform-only`, `source-archive`, or `blocked` separately.
4. Page within the approved site if the first screen is topic-skewed; do not substitute a different source.
5. On a rate-limit response, stop repeated requests, use already saved public material, and report that site's actual yield.
6. Persist the sanitized Obsidian artifact before lengthy prose synthesis so connection/context interruptions do not erase the deliverable.

## A0→A1 adjudication boundary

A0 capture and A1 writing eligibility answer different questions. Preserve the complete A0 yes residue manifest first. Only when the user approves A1, load `references/public-community-a1-adjudication.md` and build a separate outside-Vault package for every A0 yes `residue_id`.

- Do not run A1 inside the crawler or infer it from `accepted` counters.
- Do not send URL, site, title, anchor line, source handling, or old captured/resting labels to the masked structure lane.
- Do send the restricted body plus both A0 evidence spans to the separate lineage lane.
- Keep exact/redacted/pointer anchor rendering distinct from the masked review input.
- Attempt a 5–10-line memo only for runnable clear/transform-only records; retain a completed memo only when both final reviews pass.
- Preserve blocked, archive-only, A0 recheck, resting, merge, and pass as separate states.
- Run `python scripts/verify-public-community-a1.py <outside-vault-package.json>` and require `final_card_residue_ids ⊆ pass residue_ids`.

A1 never sets a pass quota and never authorizes a scene, form, length, B2, or full-pool rollout. A verified pilot precedes any full-pool application.

Do not persist environment-specific claims such as a site or tool being permanently broken. The durable lesson is to cache early, stop on rate limits, and preserve actual yield.

## Extraction sanity probes

These are diagnostic hints, not permanent scraper contracts. Reinspect the current HTML before each automated run.

- **Ruliweb `고민상담 300147`:** use only the query-free list `https://bbs.ruliweb.com/community/board/300147` (later list pages: `?page=N` and no other query, 2026-10-31 amendment) and exact `/community/board/300147/read/<id>` originals. Never request `cate=` or other disallowed query routes and never admit general board `300143`. Require matching canonical, visible original time, and self-contained `.view_content` text. Parse the original container with a bounded stream and stop at its matching end tag before comments; do not inspect page-wide text, JSON-LD, comment/reply containers, or rich-result comment payloads. This is a slow supplemental B lane: underfill is expected, and medical, death, sexual, debt, crime, family/workplace/social-graph identifying, image-dependent, or document-dependent rows require exclusion or strong handling separation.
- **82cook 자유게시판:** require `/entiz/read.php?bn=15&num=<id>` discovered from the public `enti.php?bn=15` list. On current list markup, use `td.title a[href*="read.php"]` for the human title; the first matching row link may be a `.photolink` whose text is only a numeric board number. The opened-page selectors `#column2 h1, .bbs_view_header h1` may return the generic board label `자유게시판`; never overwrite a verified list title with that generic label. Use `#articleBody` for body and parse visible `작성일 : YYYY-MM-DD HH:MM:SS`. This lane is body-only: do not extract, retain, reread, or cite comments.
- **Instiz `일상`:** use the public `https://www.instiz.net/name?page=N` list only. Require a numeric `/name/<id>` path under `td.listsubject a[href]`, then canonicalize to query-free `https://www.instiz.net/name/<id>`. General rows carry the title in `.sbj`; popular rows may use `.texthead_notice`. In both places, remove nested `span.cmtN` counters and do not absorb `.list_subtitle` date/view metadata. On the opened page use `#nowsubject` under the same counter-removal rule, `#memo_content_1.memo_content` for the body, `meta[property="article:published_time"]@content` for the timestamp, `.comment_memo .comment_line` for bounded public comments, and `link[rel="canonical"]` for identity. The body selector itself can contain a members-only placeholder such as `회원에게만 공개된 글이에요 / 로그인 후 이용해 주세요`; treat that as a login wall, not as a non-empty public body or an A0 `no`. Preserve the opened attempt in access accounting but exclude it from the public-body/A0 population. When this exclusion is reconciled after the crawl, update both the overall collection receipt and the per-site `nonempty/public_body_eligible` summary (while retaining the pre-filter selector count); otherwise the final site-count equality gate can falsely disagree with the correctly filtered population. Shared chrome can contain generic login text even when the body is public, so distinguish a phrase inside the selected body from unrelated page chrome and judge the boundary from the canonical/title/date/body selectors and final host rather than a login word alone. Do not request category/search routes disallowed by current robots rules, use a session, or infer access from snippets. Daily-life posts can expose school, workplace, age, family, relationship, or location clues; keep `accepted=0` until separate privacy and ethics review and remove or strongly transform those details before durable use.
- **Clien:** the body has appeared at `.post_article`; comment rows commonly appear under `.comment_row`/`.comment_view`. Community group pages mix several boards, so preserve the exact opened board path (`park`, `kin`, or another public board) in both frontmatter and card URL. Never normalize every accepted post to `/park/` merely because the group listing was the entry point.

After extraction, compare opened-page title, exact canonical URL/board path, date, non-empty body length, and bounded comment count. A selector returning text is not enough if it captured navigation, a recommendation count, ads, another board, or a reply duplicate.

### Crawl-accounting discipline

Keep distinct counters for `listed`, `title-filtered`, `opened`, `non-empty body`, and `accepted`. If a topic-skewed first pass leads to a manual reread of later rows, report it as `initial opened N + additional reread M` unless the union was deterministically deduplicated. Do not publish a precise inspected/non-empty total assembled from overlapping automated and manual passes. When an extractor's length threshold and an independent substantive reread disagree about whether short bodies are non-empty, retain both labeled counts and their definitions; do not overwrite one count or present the discrepancy as a scraper failure.

### Late-sweep reconciliation and source-expiry gate

Treat every delegated or parallel lane as an auditable lane with one final state: `completed`, `timed out`, `failed`, or `superseded by direct sweep`. A timeout with no summary contributes no candidate or count. A completed direct **discovery** sweep may supersede another discovery lane over the same pool, but it does not supersede an independent **adjudication** reread whose purpose is to challenge admission, self-copy, ethics, or the shortlist. Lane purpose and source coverage must both be redundant before using `superseded`. Do not issue a user-facing completion report while a known non-redundant adjudication lane is outstanding; persist a provisional artifact for interruption safety if needed, then wait for reconciliation.

Do not treat an artifact as final while a non-redundant source lane is still outstanding. If an asynchronous result arrives after a provisional artifact or response:

1. Read the complete late result, not only its truncated notification.
2. Compare every proposed candidate against the current bounded pool one-for-one; do not merely append until the cap is exceeded.
3. Prefer same-site replacements for weaker or inaccessible cards so site quotas and source diversity remain explicit.
4. After any replacement, reopen the **entire** writing-first shortlist. A replaced card can displace a previous top candidate even when the total and site counts stay unchanged.
5. Record completed, timed-out, and superseded lanes in the artifact so the final count has an audit trail.

Make the live-source check the last network-dependent gate immediately before completion, after all late-sweep reconciliation. Same-day community posts can be deleted or materially edited between initial collection and final verification. HTTP 200 and a non-empty selector do not prove the candidate survived: require the current title/date plus the body-grounded action or two normalized evidence phrases used by the card. A URL whose body was replaced by a generic closing message such as `감사합니다`, whose title/body now describes another post, or whose evidence phrases disappeared has expired for this run even though the page still opens. If an accepted URL now returns 404, a login wall, an empty body, or material content drift:

- replace it with an already verified alternate from the same approved site, or lower the actual yield;
- never keep the inaccessible card merely because its body was cached earlier when the contract requires a currently public body;
- rerun frontmatter/card URL set equality, sequential numbering, per-site totals, HTTP/non-empty-body checks for **all** accepted cards, shortlist/table/card status agreement, wikilink checks, and vault tests;
- update the mutable index summary, but add a new correction/reconciliation entry to append-only logs rather than rewriting the earlier log history.

A count that stayed constant is not evidence that reconciliation was unnecessary: replacements can change the strongest four cards while leaving totals unchanged.

## Privacy and raw-cache hygiene

Raw HTML/comment caches may contain nicknames, partial IPs, locations, vehicle numbers, family details, or other identifiers.

- Never copy those identifiers into the final note.
- Sanitize before writing to the vault.
- Keep temporary raw caches outside the vault and Git.
- Remove agent-created raw caches after verification only through an approved deletion action; if approval is absent, report the exact cleanup boundary instead of pretending deletion succeeded.

## Output shape

Use a filename that says `공개커뮤니티` or otherwise makes community-only scope explicit. Include:

- fixed pool and excluded sites;
- inspected and accepted count per site;
- actual total, even when below the maximum;
- one source URL per card;
- body fact vs comment contribution;
- ethical/factual boundary;
- duplicate/repost note;
- at most 3–4 writing-first expansions, with zero valid;
- top rejection reasons.

If an earlier mixed-source artifact was mistakenly presented as the requested community result, preserve it as historical material but add a scope-correction note and create a separate community-only artifact. Do not silently overwrite provenance.

## Verification

- final card numbers are sequential;
- source lines and unique URLs equal the actual total;
- the set of frontmatter `sources` is exactly equal to the set of card source URLs (not merely the same count);
- source-specific live checks confirm HTTP success, opened title, publication date, and non-empty body for every accepted card;
- each accepted summary retains at least one body-grounded evidence phrase or action that can be found in the live page/cache;
- exact Instiz `/name/<id>`, Clien board paths, 82cook `bn=15` post IDs/dates, and query-free Ruliweb `/community/board/300147/read/<id>` identities survive canonicalization;
- no site exceeds its maximum;
- total does not exceed the overall maximum;
- no excluded-site URL appears;
- no news URL counts as a separate card;
- no raw IP, `@` handle, or nickname survives outside an exact public source title when provenance requires it;
- frontmatter and wikilinks resolve;
- index/decision/log links are present when the vault workflow requires them;
- dashboard tests and `git diff --check` pass when affected;
- when A1 is in scope, A0/A1 residue sets are equal, every final card residue is A1 pass, proven memos have 5–10 supported lines, both reviews pass, and merge references are acyclic;
- raw-cache cleanup status is reported honestly.

A count-only validator can miss a wrong-but-plausible URL, such as a Clien `/kin/` post rewritten to `/park/`, or an MLBPARK recommendation count mistaken for a date. Treat cross-field set equality plus live source-specific metadata checks as the completion gate.
