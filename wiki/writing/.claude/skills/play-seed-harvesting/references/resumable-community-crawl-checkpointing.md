# Resumable Community Crawl Checkpointing

Use this when a community-only harvest spans several public sites, many pages, or access-sensitive endpoints. The goal is to keep one source failure from erasing or corrupting the rest of the run.

## Per-site isolation

Treat each approved community as an independent bounded job. Do not make one monolithic loop whose first uncaught list/body failure prevents later sites from running.

For each site, persist outside the Vault:

1. `list-snapshot.<site>.html/json` — access time, exact list URL/query, visible canonical IDs and provisional titles.
2. `request-queue.<site>.json` — deduplicated canonical IDs selected for body opening.
3. `opened.<site>.json` or NDJSON — title, canonical URL, date, body, bounded comments only where the site contract permits them, HTTP/extraction result. For a body-only lane such as 82cook, store no comments and make that boundary explicit.
4. `accounting.<site>.json` — `listed_unique`, `title_filtered_out`, `opened_attempted`, `same_day_rows_retained`, `nonempty_body`, `accepted`, and the final boundary.

Write each site's receipt immediately when that site finishes or stops. A later site's failure must not overwrite earlier receipts.

## Conservative request ramp

- Begin with serial or low concurrency (normally 1–4 workers per site).
- Increase only after a small probe shows stable public responses.
- On the first explicit rate-limit response, stop that site rather than allowing already queued workers to amplify it.
- Keep sessions, queues, and stop conditions site-local.
- A timeout/limit is an access boundary for this run, not a durable claim that the community is unavailable.

## Week-scale bounded samples

- When the user widens the window to a week, separate time-window eligibility from exhaustive coverage. Discover dated list slices adaptively, preserve the page gaps, then freeze a chronological date-stratified original queue before opening bodies. Keep exact boundary-day timestamps: a date-only row can fall outside the rolling window, and excluded rows do not license unannounced backfill.
- Preserve the tested, user-approved access baseline (`2026-10-30-verified-baseline-v1`) and actual request identity. Evaluate the raw applicable-UA/wildcard path rules; do not generalize a different named AI bot's prohibition to this collector or require all provider bots to allow it. Do not rotate/misrepresent identity to evade an applicable restriction, and honor independently applicable explicit site-wide rules. Distinguish HTTP 404 (absent robots rules) from 5xx/network-unreachable robots. A new real restriction needs exact changed evidence; an agent's extra caution must not change the baseline. Remove inherited agent-only conservative gates from NEW run contracts/code, never from historical receipts.
- When a robots fetch alone returns 403 without policy text, distinguish retrieval failure from an explicit rule. A bounded alternate retrieval of the exact robots document may clarify the policy; preserve both receipts and do not treat this as permission to open blocked bodies, switch boards, rotate UA, or bypass authentication. Record which rule applies to the approved entry path separately from provider-specific AI groups.
- Keep acquisition-time A0 checks distinct from final-card freshness reopens. A0-only completion does not prove currently live A1/card eligibility; report missing extraction/timestamp evidence separately from A0 no.
- For an A0-only note with illustrative residues and `final_cards: 0`, use an A0-specific validator for source/decision identity and order, deterministic frozen-queue reconstruction, body hashes, date bounds, two disjoint exact spans per yes, note source/example URL equality, and navigation links. The card-note validator recognizes a different card grammar; do not reformat A0 examples as approved cards merely to satisfy it.
- During parent rereading, preserve modality and attribution: a planned move is not an actual storage gap, ticket booking is not completed attendance, a hobby does not prove a motive to enjoy or an obligation to finish, and a pronoun-only quote does not carry its antecedent. Expand the two locked A0 spans to include necessary support or narrow the residue summary; preserve the collector version and log the correction before A1.
- Before ending a resumable run, copy the external evidence package from auto-pruned scratch into a profile-owned private artifact directory outside Vault/Git and verify hashes. Keep semantic corrections in a versioned reconciled ledger rather than overwriting collector judgments.

## Correct counters around date filtering

Snapshot `opened_attempted` from the request queue before discarding prior-day or out-of-scope rows. Then record `same_day_rows_retained` separately. Never infer attempt count from a date-filtered saved array.

Distinguish:

- list rows seen;
- unique canonical IDs;
- title-filter queue size;
- request attempts;
- successful opened pages;
- same-day retained rows;
- non-empty bodies;
- accepted cards.

## Resume without double counting

On interruption:

1. Load the saved list snapshot and opened records.
2. Compute unopened IDs by canonical ID, not page position or title.
3. Resume only the unfinished site's queue.
4. Do not re-add counts from already completed sites.
5. If the list is fast-moving, preserve the original snapshot as the run boundary; later pages are a labeled supplemental sweep.

## Bounded original queues and final reopens

- When original opening is deliberately budgeted, declare the budget and deterministic queue selection before requests. Preserve the full discovered queue and separate unattempted originals from HTTP/access failures; a budget stop is not an access failure or proof of exhaustive window collection. Describe A0 coverage as the whole **collected-body population**, not every post published in the window.
- Adapt cloned validators to reproduce the declared bounded selection exactly, not merely to accept an arbitrary subset. Preserve identity, order, timestamp, original-body boundary, and unopened-count checks; replace historical batch/date constants without carrying semantic judgments forward.
- Preserve requested URL, final response URL, and declared canonical separately when a page declares a mobile-host canonical. Never rewrite the source token to force equality or request the alternate host without its own scope/access permission. For A0, if the approved original was actually fetched and exact board/read/ID paths agree, record the host mismatch as an explicit identity warning rather than claiming literal canonical equality; stricter final-card admission remains a separate gate. A diagnostic repeat of the same approved original counts as an additional HTTP attempt, not another unique body.
- Persist a request-start receipt before each final reopen and a completion receipt afterward. Stop only the affected site after repeated connection failures, retaining other site results. If a process is interrupted before its completion receipt, label that attempt unresolved instead of claiming it was never requested or inventing a response.
- Distinguish a title re-read on the original page from a list title carried into a body reopen. Exact body/date/evidence equality does not independently reverify a carried title.
- Persist bounded original-extraction metadata (requested/final URL, literal declared canonical, opened title, visible publication time, stream-stop state) before raising an identity exception. Otherwise a missing failure receipt forces another request just to diagnose a canonical alias. Never silently rewrite a mobile canonical into the requested desktop URL; preserve both and report literal-host equality separately from same-board/post-path identity. If the contract requires exact canonical-host equality, hold the record instead of waiving that gate.

## Provisional Vault artifact

When independent review or a late lane is still outstanding, use a stable community-scoped filename without a final count, for example:

`글감_채집_YYYY-MM-DD_공개커뮤니티.md`

Mark it `provisional`, preserve current source sets, and state which reconciliation remains. Do not update index or append-only logs as though the run were final. After all non-redundant review lanes finish:

1. reconcile replacements one-for-one;
2. rerun the full writer-facing shortlist;
3. change the note status from provisional;
4. run live title/date/body/evidence checks;
5. only then update index/logs and report the final count.

This prevents count-bearing filenames and historical logs from becoming wrong when late review changes the pool.