# Publisher-site search fallback for Korean news canonicals

Use this after a Korean news RSS sweep when wrapper decoding is rate-limited, a search backend is unavailable, or a syndication page is easier to find than the publisher page. The durable lesson is the fallback sequence, not any one provider failure.

## Workflow

1. Preserve the RSS title, publisher label, feed timestamp, and wrapper URL as discovery metadata only.
2. Search the named publisher's public site with the exact headline or a distinctive 6–12-word stem. Common NDSoft-style routes are:
   - `/news/articleList.html?sc_area=A&sc_word=<encoded query>`
   - `/news/articleView.html?idxno=<id>` once the list exposes an ID.
   Other publishers may expose `/search`, `/detailSearch`, date archives, latest-article lists, or RSS feeds.
3. Read the publisher search/list page. These pages often expose the direct article ID, publication time, author, and a long body excerpt even when general web search is weak.
4. Open the direct publisher article and verify all four: exact title, publisher, page publication date/time, and 2–4 source facts from the body.
5. Keep Bing/Google News results, MSN/portal copies, and RSS timestamps as discovery aids. Do not cite a syndicated copy when the publisher canonical is publicly recoverable.
6. If only a syndication page is available, label it as such and preserve the access boundary; do not infer a publisher URL from the slug.

## Useful secondary routes

### Exact-title Naver news search

A public Naver news search can expose both portal and direct publisher anchors:

```text
https://search.naver.com/search.naver?where=news&query=<exact headline>
```

Strip a trailing ` - publisher` suffix from an RSS title, search the remaining headline, and compare normalized anchor text to the target. Prefer a direct publisher hostname over search/profile/section links. A Naver-hosted article is acceptable only when it is the publisher's public distribution page and the title, date, and body are verified. Do not accept the highest-similarity anchor blindly; recommendation cards and same-topic follow-ups can reuse most of the words.

### Bing News RSS

Bing News RSS (`https://www.bing.com/news/search?q=<query>&format=rss`) may expose a publisher URL inside the `url=` parameter of an `apiclick.aspx` link. Decode that parameter, then verify the destination. It may point to MSN rather than the originating publisher, so treat it as a lead, not final provenance.

## Repeated-request anti-bot edge case

A publisher page may return 200 with a complete body during collection and later return 403 after repeated verification requests. In that case:

1. Keep the verified publisher URL as canonical.
2. Preserve the earlier HTTP status, title/date, and body evidence.
3. Cross-check a public text renderer or explicit syndication page for matching source URL, title, publication time, and 2–4 key facts.
4. Record the current access boundary transparently; do not replace the canonical with the renderer URL merely to make a live-status assertion pass.
5. Do not convert a transient response into a persistent claim that the publisher is inaccessible.

If the canonical never yielded a body, use a syndication page only with an explicit label and access-boundary note.

## Verification

- Final URL is a direct public publisher page when recoverable.
- Page date, not feed date alone, establishes freshness.
- Body facts are read from the canonical page or an explicitly labelled public syndication copy.
- No Google News wrapper, tracking redirect, or guessed slug is presented as canonical.
