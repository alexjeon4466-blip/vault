# Late sweep reconciliation for bounded harvests

Use this when any bounded harvest—news, multi-source, or a fixed public-community pool—has already been drafted but delegated source sweeps finish late. It also applies when a final live-source check shows that a previously public post disappeared during the same run.

## Core rule

A late sweep is not an appendix. Re-open the whole candidate pool and preserve the requested final cap. Replace weaker cards only when a late candidate has stronger source-grounded pressure; do not silently turn `20` into `25`.

## Distinguish redundant discovery from independent adjudication

Two lanes can read the same cached URLs without being redundant.

- A **discovery lane** finds posts and extracts title/date/body/comments. A completed direct sweep may supersede another discovery lane that would only reproduce the same pool.
- An **adjudication lane** independently rereads the bounded pool to challenge admissions, self-copy judgments, ethics, and the 3–4 writer-facing shortlist. It is non-redundant even when it reads the same files. Do not mark it `superseded by direct sweep` merely because direct collection already finished.
- Do not send a user-facing completion report while a known adjudication lane is still outstanding. If an artifact must be persisted for interruption safety, label it provisional internally and defer the completion claim. If a result arrives after an earlier report, reconcile it as a correction rather than pretending the first report was final.
- A lane may be superseded only when its **purpose as well as its source pool** is genuinely duplicated by completed work.

## Reconciliation sequence

1. **Account for every delegated lane.**
   - Record completed, timed-out, and failed lanes separately.
   - A timed-out lane with no summary contributes zero candidates and must not appear in pool counts.
   - Read complete saved summaries, not only truncated notifications.
2. **Compare against the current artifact.**
   - Identify late candidates whose action, relation, material, changing time, and ethical distance are stronger than specific weak cards.
   - Prefer one-for-one replacements over accumulation.
   - Typical replacement reasons: plan/promotion-only article, thin body evidence, duplicated engine, or weak person/relation/time.
3. **Verify only candidates that may enter the final set.**
   - Treat subagent summaries and cached bodies as leads, never as the final source gate.
   - Independently open each proposed replacement and verify HTTP accessibility, current title, page date, and body facts.
   - HTTP 200 plus a non-empty body is not enough: require the expected body-grounded action/evidence phrases. A post may have been edited into a generic closing message such as `감사합니다`, leaving the URL alive but the candidate evidence gone. Treat material title/body drift like deletion: use a verified same-pool alternate or lower the yield.
   - If an extractor reports a generic opened title (for example a board label) while the list contains the human title, keep the list title only as provisional metadata and resolve it against the current opened page/metadata before admission.
   - Do not spend another full sweep verifying candidates already rejected after comparison.
4. **Re-open the shortlist from the full reconciled pool.**
   - Do not protect the previous top 3–4.
   - Recheck existing-work/self-copy risk; a strong source can be demoted when its engine repeats a live lineage.
   - Keep the selection-pending count at the user’s cap.
5. **Synchronize artifacts.**
   - Update the harvest note, quick map, full cards, expanded shortlist, current verdict, index, and both local/domain logs.
   - Log the old→new replacements and explain any shortlist change.
   - Preserve collection date in the title/`created`; set `updated` to the reconciliation date.
6. **Run deterministic verification again.**
   - Card numbering exactly 1–N.
   - Final source URL set has N unique URLs.
   - Removed URLs are absent; replacement URLs are present.
   - Selection-pending count and expanded shortlist headings agree.
   - Prior-harvest URL overlap is zero unless explicitly documented.
   - Internal links resolve; Git whitespace check passes.
   - When automated extraction and independent reread disagree on `non-empty body` because one used a length threshold or removed extraction residue, preserve both labeled definitions (for example `initial length-filter N / independent substantive reread M`) instead of silently choosing the more favorable count.
7. **Run the last live-source gate after reconciliation.**
   - Reopen every accepted URL after all late results and replacements have been applied; require the contract's current public-access condition and a non-empty body, not only a cached extract.
   - A same-day public post can be deleted between collection and completion. On a real 404/deletion or newly empty body, replace it with an already verified alternate from the same approved pool or lower the actual yield. Do not keep it solely because the earlier cache was valid.
   - Re-open the full shortlist after this replacement even when the card number and site totals stay unchanged.
   - Rerun URL-set equality, numbering, per-site caps, live checks, selection table/card/shortlist agreement, internal links, index synchronization, and tests.
   - In append-only vault logs, add a `source-recheck`/correction entry; do not rewrite the earlier harvest or reconciliation history. Re-read the current log tail immediately before appending because another writer may have added entries meanwhile.

## Canonical/access edge case

If a direct publisher page returned HTTP 200 and usable body text during collection but repeated verification later triggers anti-bot 403:

- keep the publisher URL as canonical provenance;
- preserve the earlier status/body evidence;
- cross-check a public text renderer or explicit syndication copy for matching source URL, title, publication time, and key facts;
- document the boundary in the note rather than replacing the canonical with the renderer URL;
- never turn a transient bot response into a durable claim that the publisher is inaccessible.

## Reporting shape

Report the reconciliation as deltas:

- delegated lanes completed / timed out;
- candidates additionally reviewed;
- old cards → replacement cards;
- shortlist change and reason;
- final counts and verification results.

Do not reopen drafting or form selection merely because the source pool changed. Return to the user-attraction gate with the reconciled 3–4 options.
