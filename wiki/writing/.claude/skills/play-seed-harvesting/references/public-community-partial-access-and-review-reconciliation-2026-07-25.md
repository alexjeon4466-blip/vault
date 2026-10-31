# Partial-access community harvest and review reconciliation — 2026-07-25

Use this pattern when a fixed community-only harvest has **uneven access**: some list snapshots open but their post bodies later rate-limit or time out, while other approved sites yield large public-body caches that need an independent reread.

The durable result is not “those sites are broken.” It is a workflow for preserving scope, reporting actual yield, and finalizing only after late review and a live evidence gate.

## 1. Freeze the source contract first

Record before opening pages:

- approved list URLs and exact query parameters;
- excluded communities;
- per-site and overall caps;
- underfill validity;
- public-body requirement;
- no news/non-approved backfill;
- access timestamp and timezone.

A list snapshot is discovery evidence, not an accepted source card.

## 2. Use bounded, site-specific request pressure

- Use a separate session per site.
- Start with low concurrency, usually 1–4 workers per site. Do not assume that concurrency safe for one community is safe for another.
- When a site returns 429/430 or connections begin timing out after earlier success, stop that site lane instead of launching a high-concurrency replay.
- Keep already saved public material, but do not admit titles whose bodies were never opened.
- Record `body_opened_before_boundary` separately from the list count.

The reusable lesson is **bounded request pressure + early cache + honest underfill**, not a permanent claim about any site.

## 3. Snapshot counters before filtering rows away

Keep these distinct:

1. `listed_unique`
2. `title_filtered_queue`
3. `opened_attempted`
4. `same_day_rows_retained`
5. `body_strip_nonempty`
6. `body_len_ge_threshold`
7. `accepted_final`

If prior-day rows are discarded immediately after opening, calculate `opened_attempted` from the request queue before that discard. Never derive it from the retained same-day array.

When two rereads use different non-empty definitions, preserve both labels. For example, `body.strip() != ""` and `body_len >= 20` answer different questions; do not silently collapse them into one count.

## 4. Treat partial access as a per-site result

If a list opens but most bodies do not:

- report the list snapshot count;
- report how many bodies opened before the boundary;
- accept zero from that site unless a body-grounded candidate was actually verified;
- do not use search snippets, titles, or cached list furniture as substitute bodies;
- continue with the other already-approved sites;
- do not call the whole run incomplete merely because one site yielded zero.

## 5. Persist a provisional artifact without locking the count

For interruption safety, use a stable community-scoped filename such as:

```text
글감_채집_YYYY-MM-DD_공개커뮤니티.md
```

Avoid putting the provisional count in the filename. Late one-for-one replacements or underfill changes can then be patched in place without leaving a misleading orphan artifact.

Recommended provisional state:

- `status: provisional`;
- frontmatter contains only currently admitted direct URLs;
- source-access accounting is explicit;
- no index/log finalization yet;
- raw caches remain outside the vault and Git.

After reconciliation, change the status, rewrite the access/review receipt, and only then update index and append-only logs.

## 6. Independent rereads are adjudication lanes

An independent reread of the same cache is not a new source lane and its counts must not be added to the direct crawl.

For every proposed candidate:

1. compare it one-for-one against a current card from the same site;
2. challenge body sufficiency, privacy, ethics, repost/image dependence, product-claim dependence, and self-copy;
3. accept a replacement only when it is materially stronger;
4. allow all proposals from a site to be rejected;
5. reopen the full writing-first shortlist after any replacement.

Review is a challenge function, not an automatic promotion queue. Compare source-supported relation and time pressure, not novelty of topic alone.

## 7. Run the live evidence gate after reconciliation

For every final URL, re-open the current page and require:

- HTTP 200 and no deletion/login wall;
- current opened title;
- current publication date;
- exact canonical URL and board path;
- non-empty source-specific body selector;
- two independent normalized body phrases used by the card.

Save a machine-readable report outside the vault. For Clien, preserve `/park/`, `/kin/`, or the actual board path; never normalize every community post to `/park/`.

## 8. Finalize the vault only after the gate

Then perform:

1. frontmatter/card URL-set equality;
2. sequential numbering and caps;
3. privacy and excluded-domain scan;
4. wikilink resolution;
5. index insertion;
6. fresh-tail append to writing log and root log;
7. dashboard/data tests when affected;
8. scoped `git diff --check`;
9. explicit no-commit/no-push report when that is the standing workflow.

## Pitfalls

- Reporting retained same-day rows as all opened attempts.
- Calling different non-empty-body definitions a scraper discrepancy.
- Retrying a rate-limited site with more workers.
- Filling inaccessible-body slots from titles or news.
- Treating every independent-review proposal as accepted.
- Locking a provisional count into the filename.
- Updating append-only logs before the final live-source gate.
- Reporting HTTP 200 without checking title/date/body evidence.

## Minimal completion receipt

A concise receipt should include:

- per-site `listed / opened / substantive body / accepted` counts with definitions;
- access boundaries and actual underfill;
- completed review lanes and one-for-one replacements/rejections;
- final live evidence pass count;
- structural verifier result;
- wikilink/privacy/tests/whitespace result;
- raw-cache location and cleanup status;
- commit/push status.
