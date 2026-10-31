# Google News RSS canonical URL recovery and interrupted-harvest resume

Use this when a broad harvest has Google News RSS `news.google.com/rss/articles/...` links or the session stops after source collection but before the Obsidian artifact is written.

## High-recall RSS collection

Google News query terms behave roughly like an AND filter. Long thematic phrases can collapse a harvest to only a handful of items. For a news-only harvest:

1. Use many one- or two-term lanes such as `주민 when:3d`, `도서관 when:3d`, `수리 정비 when:3d`, `여객선 주민 when:3d` instead of a few four- or five-term queries.
2. Pool the feeds, normalize titles to letters/numbers/Hangul, and deduplicate before opening articles.
3. Apply title-level exclusions only as a first pass. Final inclusion requires publisher-body verification.
4. Group wire copies, alerts, and follow-ups as one article family; retain one verified canonical source rather than counting the same event repeatedly.
5. Keep news yield separate from community yield. Never use one source class to fill another class's quota.

## Canonical URL recovery

Do not preserve Google wrapper URLs when a public publisher URL can be recovered. A normal redirect request may remain on Google News.

1. Parse the final path segment from `https://news.google.com/rss/articles/<SLUG>?...`. The `garturlreq` RPC needs this **article slug/base64 token**, not the entire wrapper URL.
2. GET `https://news.google.com/articles/<SLUG>` with a browser user agent.
3. Extract `data-n-a-sg` (signature) and `data-n-a-ts` (timestamp) from the returned HTML.
4. POST to `https://news.google.com/_/DotsSplashUi/data/batchexecute` with RPC id `Fbv4je` and a `garturlreq` payload containing `<SLUG>`, timestamp, and signature.
5. Parse the `garturlres` response for the publisher URL and unescape response artifacts before saving.
6. Fetch the publisher page and verify title, publisher, publication date, and source facts from metadata/body. An RSS date alone is not sufficient; old articles can resurface with misleading feed dates.

Treat a successful decode as URL discovery, not fact verification. For a bounded batch, the maintained `googlenewsdecoder` package can be used ephemerally:

```bash
uv run --with googlenewsdecoder --with trafilatura python harvest_probe.py
```

### Exact-headline fallback when wrapper decoding is throttled

Do not repeatedly hammer Google wrapper pages. Switch discovery routes while preserving the same verification contract:

1. Search the exact quoted headline through Naver News search and score external anchor text against the normalized headline. Prefer the direct publisher link over portals.
2. If Naver has no strong match, query Bing News RSS:
   `https://www.bing.com/news/search?q=%22<HEADLINE>%22&format=rss`.
3. Bing RSS often returns `news/apiclick.aspx?...&url=<PUBLISHER_URL>`; parse and URL-decode the `url` query parameter.
4. Reject weak title matches rather than guessing from a similar headline.
5. Open the recovered page and verify its publication date and body facts exactly as with an RPC-decoded URL.

### Article-body extraction and public-mirror fallback

Useful fallbacks, in order:

1. publisher HTML plus `trafilatura` or known article selectors;
2. source-specific blocks such as `article`, `[itemprop=articleBody]`, `.article_body`, `.news_article`, `.paragraph`, or the largest plausible content block;
3. canonical/OG/`article:published_time`/JSON-LD metadata;
4. publisher AMP URL, embedded application state, or a public article JSON endpoint;
5. a public syndication copy to locate and cross-check the original publisher page;
6. `https://r.jina.ai/http://<publisher-url>` as a verification mirror when the canonical page is client-rendered or temporarily bot-challenged.

A public text mirror is corroboration, not the saved canonical source. Keep the publisher URL in the card. If completion-time rechecking finds a previously verified canonical page bot-challenged, record the exception transparently and require the mirror to reproduce the source URL, exact title, publication time, and substantive body. If that identity chain cannot be proved, exclude the candidate.

A `200` response is not sufficient: rendered pages may yield an empty extractor result while the article text sits in embedded state, and a wrapper may remain on Google with `200`. If only a photo shell or headline is available, exclude it rather than inventing facts.

### Explicit prior-engine exclusion ledger

When the user supplies already-used engines, write a short rejection ledger before searching (for example: `closed shop`, `elevator rescue`, `generic bus-route change`). Compare candidates by **dramatic engine**, not only by topic words. A transport article can survive a `bus route` exclusion only when its active engine is materially different—such as a festival timetable that opens and closes stations, a shelter/last-mile construction sequence, or another time-producing public-space condition. Record borderline exclusions so an easy headline does not silently reintroduce an old play.

## Public SNS lane

For Mastodon, collect from public tag timelines through the instance API, preserve the direct status URL and UTC timestamp, and mark untitled posts as `제목 없음(본문 첫 문장/행동 설명)`. Extract only transferable action/material/time structure; do not reproduce account identity or private biography in the dramatic hypothesis.

## Resume after interruption

Treat the run as incomplete until the durable artifact exists.

1. Check whether the intended note, index entry, and log entry already exist before repeating research.
2. Reuse any verified temporary source pools, but re-open canonical sources needed for the final cards.
3. Distinguish states explicitly:
   - `source pool collected`
   - `20 cards selected`
   - `3–4 cards research-expanded`
   - `note/index/log written`
   - `verified`
4. On resume, continue from the first missing state rather than rerunning every lane.
5. Before completion, verify:
   - candidate headings and quick-map rows are exactly 1–20;
   - every card has one public URL, source pressure/protected core, time fuel, and provisional judgment;
   - expansion headings match the intended 3–4 cards;
   - all direct URLs currently return a public response;
   - internal wikilinks resolve;
   - placeholders and trailing spaces are zero;
   - project tests and `git diff --check` pass when relevant.

Keep source-pool JSON outside the vault or remove it after verification; the durable source of truth is the final note with canonical URLs.