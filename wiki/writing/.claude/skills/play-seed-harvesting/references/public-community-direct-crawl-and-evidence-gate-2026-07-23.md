# Direct Community Crawl and Evidence Gate — 2026-07-23

This reference records a reusable direct-crawl pattern for public Korean community harvests when browser extraction is unavailable, list pages are fast-moving, or topic skew requires deeper paging. The parent `SKILL.md` and `public-community-first-harvest.md` remain authoritative for scope and ethics.

## Use this pattern when

- the fixed community contract is already known;
- public HTML is available without login;
- list snapshots must be reproducible near the end of a fast-moving day;
- a site is heavily skewed toward politics, finance, sports, images, or reposts;
- the final artifact needs exact title/date/body evidence rather than URL-count checks alone.

## 1. Snapshot lists before opening posts

Use a separate HTTP session per site with a normal browser user agent and Korean language preference. Save raw list HTML outside the vault before opening candidates.

Canonical list-key rules used successfully:

- Instiz `일상`: numeric post ID from exact `/name/<id>` paths under `td.listsubject a[href]`; remove list queries such as `page`, `category`, and `green` only after validating the path and host. Read the human title from `.sbj` or `.texthead_notice` while excluding nested `span.cmtN` counters and `.list_subtitle` metadata.
- Clien: exact `/service/board/<board>/<id>` path from `a.list_subject`; preserve the board name and remove query strings only after opening.
- Ruliweb `고민상담 300147`: require query-free `/community/board/300147/read/<id>` paths discovered from the exact public board; do not request `cate=` or general board `300143`.
- 82cook 자유게시판: require `/entiz/read.php`, `bn=15`, and numeric `num`; normalize to `https://www.82cook.com/entiz/read.php?bn=15&num=<id>`.

For a same-day run, choose page depth by **date coverage and topic yield**, not a fixed page count. If the first Clien pages are dominated by one topic, continue through later pages within the approved `community` list and record the supplemental page range separately. Deduplicate the union by canonical post ID.

## 2. Keep crawl layers separate

Never collapse these counters:

1. `listed_unique`
2. `title_filtered_out`
3. `opened_attempted`
4. `opened_ok`
5. `nonempty_body`
6. `accepted`

A title filter is only a triage queue. It does **not** prove that the skipped body was read, and it must not be reported as a body-inspection count. When supplemental pages are disjoint and post-ID deduplication is deterministic, their list/open counts may be summed; otherwise report each pass separately.

When opened pages are date-filtered before their records are persisted, snapshot `opened_attempted` from the request queue **before** dropping prior-day rows. Record a separate `same_day_rows_retained` count. Never derive the attempt count from the retained array; that silently undercounts every successfully opened prior-day page.

The 2026-07-23 run demonstrated why this matters: a community could expose hundreds of same-day rows while only a bounded subset was opened after title filtering. The artifact reported both the total list snapshot and the smaller body-open count rather than claiming a full-body census.

## 3. Cache opened posts outside the vault

For every opened candidate save a JSON record containing:

- site and canonical post ID;
- list title and opened-page title;
- exact canonical URL/board path;
- opened-page date metadata;
- body text and body length;
- a bounded public-comment sample only when the site contract permits comments; for 82cook, store no comments and record the body-only boundary;
- HTTP status and extraction errors.

Keep HTML and comment JSON under a temporary directory outside the vault and Git. The final note must contain no nickname, partial IP, account handle, precise address, vehicle number, or family identifier.

## 4. Opened-page extraction and cross-check

Use source-specific selectors, but always cross-check selector output against the opened page title and metadata:

- Instiz `일상` title: `#nowsubject` with nested `span.cmtN` counters removed; body: `#memo_content_1.memo_content`; date: `meta[property="article:published_time"]@content`; comments: `.comment_memo .comment_line`; canonical: query-free `link[rel="canonical"]` matching `/name/<id>`. If the selected body contains the members-only placeholder `회원에게만 공개된 글이에요 / 로그인 후 이용해 주세요`, preserve the opened attempt but exclude that row from the public-body and A0 populations; selector non-empty is not public evidence. Generic login text in unrelated page chrome is not itself a wall, so make this test on the selected body. Comments remain bounded enrichment and every candidate requires manual privacy review.
- Clien title: `h3.post_subject`; body: `.post_article`; comments: `.comment_row .comment_view`. Remove a trailing reply count only after comparing with the list title.
- Ruliweb `고민상담 300147`: title from safe page metadata/opened heading, body only from `.view_content`, visible original time from the opened page, and matching canonical under `/community/board/300147/read/<id>`. Use bounded original-container streaming and stop at its closing tag before comments; never parse page-wide text, JSON-LD comments, or reply containers.
- 82cook 자유게시판 `bn=15`: on the list use `td.title a[href*="read.php"]` for the human title; a row's first matching `read.php` link may be a `.photolink` whose text is only a numeric board number. Opened-page `#column2 h1, .bbs_view_header h1` may now return the generic board label `자유게시판`, so preserve the verified list title rather than overwriting it with that label. Body: `#articleBody`; visible date: `작성일 : YYYY-MM-DD HH:MM:SS`, with the verified header selector `#readHead .readRight`. Do not rely on `.bbs_view_header` for the date without confirming its current DOM match. Comments are contractually excluded even when present in the response.

A non-empty selector is not enough. Reject or repair extraction when it captured a board badge, recommendation count, navigation text, another board, or an image/video placeholder without an independent text body.

## 5. Selection discipline

- Treat title filtering as rejection of obvious lanes, not automatic acceptance of the remainder.
- A body can qualify without comments when it contains a concrete person, action, relation, object, place, or changing time.
- Image/repost bodies may qualify only when bounded public comments add a distinct lived scene; otherwise reject.
- Underfill is valid. A site with zero accepted cards must remain zero rather than donating its quota to another source.
- Re-read the final cross-site pool for writer curiosity and self-copy; place at most 3–4 in `selection pending`.

## 6. Final live evidence gate

Immediately before completion, reopen every accepted URL and verify:

1. HTTP 200 and no login/deletion wall;
2. opened title matches the saved title;
3. publication date matches the saved date;
4. source-specific body selector is non-empty;
5. preferably **two independent normalized body phrases** from the saved card are still present in the live body. For a genuinely tiny body, one distinctive phrase may suffice, but record that exception.

Normalizing whitespace before phrase comparison avoids false failures without weakening provenance. Two phrases are preferred because they catch wrong-but-nonempty selectors and plausible wrong pages better than a generic body-length check.

Store a machine-readable verification report outside the vault with per-URL title/date/body/evidence booleans. Run the structural note verifier separately; neither gate replaces the other.

## 7. Parallel and late-review accounting

A delegated reread of the same cached posts is a **review lane**, not a new source lane. Do not add its inspected counts to the direct crawl. If the direct crawl already covers the fixed pool, mark an unfinished duplicate review as `superseded by direct sweep` rather than blocking indefinitely.

If a completed late review proposes a replacement before final delivery, compare it one-for-one against the current bounded pool and reopen the full writing-first shortlist. If the review was explicitly superseded as duplicate and contributed no unique source coverage, do not double-count it or append its candidates automatically.

## 8. Verification receipt

A complete receipt should report:

- site-by-site listed/opened/non-empty/accepted layers;
- frontmatter/card URL set equality;
- sequential numbering and site caps;
- final live URL/title/date/body/evidence pass count;
- wikilink and privacy scans;
- relevant vault tests and `git diff --check`;
- raw-cache location and cleanup boundary;
- no-commit/no-push status when that is the standing workflow.
