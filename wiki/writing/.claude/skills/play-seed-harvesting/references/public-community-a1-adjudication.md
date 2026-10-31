# Public Community A0→A1 Adjudication Contract

This reference defines the A0-to-A1 contract for this distribution; no private Vault decision file is required. Load it only after a public-community run has a complete A0 residue manifest or when validating an A1 package.

## Responsibility boundary

- **A0** asks whether any reusable dramaturgical residue remains after the concrete incident is set aside.
- **A1** asks whether that inherited residue supports a 5–10-line, non-invented performance-rule memo.
- **captured/card** remains a separate later decision and must be a subset of A1 `pass`.
- A1 does not rerun A0 independence, rank items, set a pass quota, authorize a scene/form/B2, or change a crawler result.
- Every A1 record must set `derived_permissions: []`.

## Inputs and storage split

Use two outside-Vault stores connected only by opaque IDs.

1. **Source receipt store** — URL, public body, source timestamps/version hash, A0 evidence spans, access and handling receipts. Restrict exact/redacted quote access to the lineage lane.
2. **A1 package** — stable IDs, evidence IDs/hashes, structured proof, memo lines, review states, and workflow state. Do not copy raw bodies or removed identifier values here.

A1 identity is `(source_id, source_version_id, residue_id)`. URL is a versioned attribute, not the key. One source may have more than one residue record.

### Evidence lock before memo authorship

Run this as a lineage-owned gate before the author sees or writes a memo.

1. Confirm the two evidence IDs point to two different exact spans in the current public body.
2. Decide whether those spans semantically support the inherited A0 residue summary/types, not merely whether the strings occur in the body. Audit each modifier, prior state, and speech act separately: “old,” “already stored,” “after stopping,” “asks how,” and a named disposal action can be present in the full body yet absent from both selected spans. Record this as an evidence-selection gap, not absence of dramatic residue; do not silently trim the inherited summary or substitute spans to rescue it.
3. If either span or the inherited residue drifts, stop as `a0_recheck`. Selecting replacement evidence requires a versioned A0 decision; the memo author must never repair the lineage silently.
4. Only evidence-locked runnable records enter memo authorship.
5. Keep failure ownership distinct: invalid inherited evidence/residue → `a0_recheck`; valid residue plus invented memo action, causality, motive, timing, terminal behavior, or audience execution → `resting`.

For a correction-only request, version only the named failed A0 decisions, retaining source/residue identities and assigning fresh evidence IDs when rebinding spans. Freeze the reviewed proposal and preserve the old A0/A1 packages. Independently check that the new two spans support the entire revised summary/types; removing an unsupported clause may be better than enlarging excerpts. Publish corrections alongside the old reasons in the existing full-view ledger without duplicating the ledger or relabeling evidence repair as A1 pass. Keep memo authorship, resting-memo repair, and pool expansion held. When using a same-session verified snapshot without another fetch, bind its receipt/time/hash explicitly and do not claim a new current-access check.

A high masked-structure pass rate with a low source-open lineage pass rate is a calibration signal, not proof that lineage should be averaged away. Preserve both receipts and adjudicate whether the dispute belongs to A0 lineage, memo invention, or reviewer error before novelty review.

### A0-to-A1 handling map

| A0 label | A1 fields | Action |
|---|---|---|
| `clear` | `safety_state=clear`, `source_handling=clear` | Run both reviews. |
| `transform-only` | `safety_state=clear`, `source_handling=transform_only` | Run both reviews; exact anchor forbidden. |
| `source-archive` | `safety_state=clear`, `source_handling=archive_only` | Create the record but do not run the memo/reviews. |
| `blocked` | `safety_state=blocked`, `source_handling=prohibited` | Create the stop record; do not run the memo/reviews. |

Do not record removed names, locations, institutions, sums, diagnoses, or unique incident details. Record only removal categories. `blocked`, `not_run`, and `a0_recheck` stop records may set `anchor=null`, `proof=null`, and `memo_lines=[]`; their A0 manifest and restricted source receipt must still retain exactly two evidence IDs/spans for audit.

## Package shape

Top-level JSON:

```json
{
  "schema_version": "public-community-a1/0.2",
  "policy_version": "2026-08-15-a1-v0.2",
  "batch_id": "opaque-batch-id",
  "a0_manifest": [],
  "final_card_residue_ids": [],
  "records": []
}
```

Each `a0_manifest` item contains:

```json
{
  "source_id": "src-opaque",
  "source_version_id": "sha256:...",
  "residue_id": "res-opaque",
  "evidence_ids": ["ev-1", "ev-2"]
}
```

Each evidence ID identifies one of the two different exact body spans in the restricted source receipt. Two spans are not two independent sources.

Each A1 record contains:

```json
{
  "a1_record_id": "a1-res-opaque-v1",
  "source_id": "src-opaque",
  "source_version_id": "sha256:...",
  "residue_id": "res-opaque",
  "a0_evidence_ids": ["ev-1", "ev-2"],
  "evidence_state": "valid",
  "safety_state": "clear",
  "source_handling": "transform_only",
  "structure_state": "proven",
  "novelty_state": "distinct",
  "workflow_state": "pass",
  "derived_permissions": [],
  "anchor": {
    "evidence_id": "ev-1",
    "mode": "pointer",
    "display": "A0 evidence #1 / 필요한 동안의 침묵과 뒤늦은 신호"
  },
  "proof": {
    "performance_carriers": ["sound"],
    "tension_topology": "time_misalignment",
    "time_rule": "during=silence; after=signal",
    "temporal_operations": ["delay"],
    "terminal_condition": "residual_pressure",
    "audience_route": "silence_then_sound"
  },
  "memo_lines": [],
  "review_state": {
    "structure": "pass",
    "lineage": "pass",
    "adjudication": "not_needed"
  },
  "failure_reasons": [],
  "merge": null
}
```

## Anchor rule

The rendered memo's first line is the A0 anchor, but the structure reviewer never sees it.

- `exact` — only for `source_handling=clear`, low-risk, minimal, non-identifying quotation.
- `redacted` — irreversibly mask direct and quasi-identifiers while preserving the relation/action link.
- `pointer` — show only the A0 evidence ID and structural role when quotation is risky or substantial relative to a short post.

The anchor must reference one of the existing two A0 evidence IDs. Selecting a new span requires a new versioned A0 decision; do not silently replace evidence.

Audit the anchor's rendered line as rigorously as the later memo lines. A pointer label such as “before clicking” can require both locked spans even when its anchor.evidence_id points to the first span; put every necessary locked ID in that line's support_evidence_ids. A neutral pointer is safer than a compressed temporal claim with incomplete attribution. Preserve attribution-only failures separately from speculative-content failures; neither is silently promoted.

## Memo and proof contract

A `pass` or `merge` record has 5–10 rendered `memo_lines`. The union of `line_types` must contain:

- `anchor`
- `protected_core`
- `source_distance`
- `performance_carrier`
- `tension_topology`
- `time_rule`
- `temporal_operation`
- `terminal_condition`
- `audience_route`

A line may carry more than one type. Every line contains:

```json
{
  "memo_line_id": "L2",
  "line_types": ["performance_carrier", "tension_topology"],
  "text": "침묵과 뒤늦은 소리가 두 시간을 어긋나게 한다.",
  "support_evidence_ids": ["ev-1", "ev-2"],
  "transformation_note": "식별 맥락을 버리고 시간 순서만 보존",
  "inference_class": "supported_abstraction"
}
```

Allowed inference classes are `supported_abstraction` and `entailed`. A speculative line is never part of the saved memo. If deleting a speculative proposal collapses the carrier, time rule, operation, or terminal condition, set `structure_state=insufficient` and `workflow_state=resting`.

For `resting` without a retained draft, preserve a neutral `pointer` anchor to an already-locked manifest evidence ID while keeping `proof=null` and `memo_lines=[]`. The v0.2 validator requires an anchor for resting records; null-anchor exceptions apply to `blocked`, `not_run`, and `a0_recheck`. Never fabricate a draft, change the state, or weaken validation merely to satisfy this serialization requirement. Test the builder's no-draft resting path against the dedicated A1 validator, not only its local fixture.

### Temporal and terminal breadth

`temporal_operations` may include transition, accumulation/wear, repetition-with-difference, delay, stasis/duration, return, redistribution, dispersal, disappearance, or audience perceptual reframing.

Treat every added operation enum as an evidence claim, not decoration. A broken object and remaining fragments do not by themselves establish dispersal over time; a supported shift in what a voice names may establish transition only. Review the prose and its linked proof together. If an extra enum fails lineage, preserve that failure as memo/proof-owned `resting`, not an A0 error; do not silently delete the enum after review and promote the old draft.

`terminal_condition` may be residual pressure, closure/exhaustion, cutoff, return, stillness, residual image, role transfer, or audience-only difference. A single irreversible change and an open ending are not universal requirements.

`tension_topology` may be interpersonal, body-environment, person-object/rule, layers of one voice, signal-noise, chorus-internal, multiple times, stage-audience information, or an unlocated sensory conflict. Do not invent two abstract opponents merely to fill a field.

## Independent review lanes

### 1. Structure review — masked

Hide:

- line 1 anchor;
- URL, site, title, body, and source handling;
- current `captured/resting` label and existing-card status;
- A0 evidence wording.

Show memo lines 2–10 and the structured proof only. Decide whether a performance carrier, tension topology, time rule/operation, terminal condition, and audience route stand without source context.

### 2. Lineage review — source-open

Show the restricted source receipt, the two A0 evidence spans, anchor mode/display, proof, and all memo lines. For every line decide whether it is supported abstraction, entailed, or speculative; check identifier re-entry, invented causality, anchor risk, and A0 lineage.

Bind reviewer inputs to actual upstream content, not only claimed hashes: compare source-open drafts and masked proof/memo projections against the exact `draft-memos` rows and manifest identities through their opaque-ID maps. A mutation to reviewer text with unchanged upstream hashes must fail; updating a map's input hash must not legitimize a different projection.

Both final reviews must be `pass` for `structure_state=proven`. A disagreement is not averaged. Re-adjudicate the disputed field and preserve both original review receipts; the final package records only the reconciled state.

When a lineage reviewer supports a memo line only by adding the other already-locked evidence ID, reconcile the author's line-level and corresponding proof attribution explicitly. Archive the prior author, projections, and review receipts; change only the justified support-ID arrays, regenerate exact downstream projections while preserving opaque candidate identities, and obtain bounded independent reconfirmation in every affected lane. Prove that source bodies, selected spans, inherited summaries, and memo/proof text did not change. Rebind reviewer hashes only after that reconfirmation; a parent hash rewrite alone is not a fresh independent review. Any need for a new span or a changed inherited summary remains versioned A0 work, not attribution repair.

## Workflow derivation precedence

Apply in this exact order:

1. safety blocked or handling prohibited → `blocked`
2. handling archive_only → `not_run`
3. A0 evidence/residue error → `a0_recheck`
4. evidence invalid/unverifiable → `not_run`
5. structure insufficient or novelty unresolved → `resting`
6. duplicate/merge_candidate with a valid active pass target → `merge`
7. all pass conditions satisfied → `pass`

A missing merge target yields `resting` plus `merge_target_missing`. Merge metadata requires `merge_target`, `shared_engine`, `retained_difference`, and `merge_gain`. Targets must be active pass records; self-reference and cycles fail validation.

## Controlled failure reasons

Prefer these codes over free prose:

- `evidence_invalid`
- `evidence_unverifiable`
- `a0_evidence_error`
- `a0_residue_misclassified`
- `anchor_risk`
- `invented_fact_required`
- `carrier_not_operational`
- `time_rule_not_supported`
- `terminal_condition_not_supported`
- `audience_route_not_executable`
- `novelty_unresolved`
- `merge_target_missing`
- `duplicate_engine`
- `archive_only`
- `safety_blocked`

Free explanation may accompany a code but cannot replace it.

## Validator

Run from the skill directory:

```bash
python scripts/verify-public-community-a1.py "<PRIVATE_ARTIFACT_ROOT>/a1-package.json"
python scripts/test-verify-public-community-a1.py
```

The validator checks:

- schema/policy versions;
- A0 manifest and A1 residue-set equality;
- stable and unique record/residue/line IDs;
- source/version/evidence lineage;
- state enums and deterministic workflow precedence;
- exact anchor prohibition for transform-only;
- 5–10-line proven memo contract and required line types;
- no speculative or unsupported memo lines;
- independent structure/lineage pass for `pass` and `merge`;
- final-card subset of pass;
- merge target fields, active target, self-reference, and cycles.

It does not semantically prove a paraphrase, detect every quasi-identifier, or replace the two human/agent review lanes.

For aggregate international A0/A1 summaries and full-view ledgers, use their contract-specific document/projection validators; the generic Korean community-card note validator expects `community-only` and numbered cards, so applying it to aggregate section headings yields a schema mismatch rather than a content defect. Do not relabel an aggregate as a card note to get a green result.

Audit-bundle payload scans must distinguish exact boolean negative-control receipts from forbidden response content. Permit a known rejection-check key only at its receipt path with a strict boolean value; strings, mappings, numeric lookalikes, actual response-body flags, and nested payloads must remain rejected. Retain a regression proving the receipt exception cannot hide real comment or answer content.

## Judge calibration: error taxonomy, TPR/TNR, and independent test sets

Use this section when changing evidence selection, memo prompts, reviewers, models, or rubrics. It adds an evaluation sidecar, not new package fields, state enums, source permissions, or rollout authorization. Keep evaluation traces and split manifests outside Vault/Git; a user-facing A1 ledger still follows the main skill's full-view rule.

### 1. Establish a reference judgment without circularity

- Freeze the task, rubric version, positive-label meaning, reviewer inputs, and error costs before comparison. The user's writing criteria remain authoritative; no universal literary-quality score or target pass rate is imported.
- Use explicit human/domain-expert adjudication as the reference. Another unvalidated LLM, the tested judge's own explanation, or a majority of agents is not automatically ground truth. Without expert-confirmed labels, report provisional agreement/disagreement, not validated TPR/TNR.
- Keep original structure, lineage, and reconciliation receipts alongside the reference verdict and a detailed critique. For a pass, explain what evidence makes it valid; for a failure, identify the precise unsupported field/span, invented leap, or omitted criterion. Preserve unresolved reference disputes as unresolved.

### 2. Discover errors before imposing categories

1. Open-code real traces: record the last successful stage, first failing stage, evidence IDs, expected versus observed decision, and a plain-language explanation. Separate a source/memo defect from a judge failing to detect it.
2. Group related critiques into a small, actionable taxonomy (aim for fewer than ten parent groups, not a mandatory cap). Reuse the controlled failure reasons above as leaf codes; do not replace them with a generic rejection label.
3. Useful initial parent groups are access/version mismatch; A0 evidence/residue mismatch; memo invention; missing performance/time/audience support; reviewer input or rubric error; novelty/merge error; handling/privacy error; and infrastructure/incomplete run. Add or merge groups only from observed traces.
4. Count by stage and source/handling stratum. Give a primary cause per record for non-overlapping totals; if secondary causes are counted, mark the table as multi-label. Do not average structure/lineage disagreement away.
5. Preserve the ownership boundary: inherited evidence/residue defect → `a0_recheck`; valid inheritance plus speculative memo → `resting`. Reviewer mistakes require corrected review receipts, not silent rewriting of the source or memo.

Minimal sidecar fields: opaque record/group ID, source-version/evidence pointers, split, stratum, rubric/model/prompt versions, reference label and critique, judge decision/abstention, failure stage, primary/secondary error codes, and adjudication status. No raw personal details are needed in this sidecar.

### 3. Report confusion counts with an explicit positive label

Evaluate structure and lineage separately on their eligible, expert-labeled records. For each lane, **positive means the lane's criterion is satisfied**; negative means it is not. Do not use `positive` to mean defect in one table and valid in another.

| Reference | Judge pass | Judge fail |
|---|---|---|
| Satisfied | TP | FN — valid work rejected |
| Not satisfied | FP — unsupported work admitted | TN |

- Compute `TPR = TP / (TP + FN)` and `TNR = TN / (TN + FP)` with code, displaying numerator and denominator. Also show FP/FN counts; when unsupported admissions matter, optionally report precision `TP / (TP + FP)`.
- A zero denominator is `N/A`, never zero or perfect. Show class support, sample design and uncertainty; small samples are diagnostic, not proof of reliability. Compute any confidence intervals with a stated method, not intuition.
- Keep `blocked`, `not_run`, `a0_recheck`, pending, timeouts and unresolved reference labels visible in coverage/state tables. Do not force them into binary fail. Their correctness may be evaluated in a separately specified routing/state-classification task.
- For an eligible reference-labeled record where the judge abstains, fails to execute or remains unresolved, report it separately and include it in the coverage denominator. TPR/TNR on decided records must be labeled conditional on coverage; never hide abstentions to improve rates.
- Keep `merge` distinct. If evaluating a composite endpoint, freeze its eligible set and label mapping before the run; do not silently turn `merge` into a selected card or fold every non-pass workflow state into a negative class.
- Distinguish missed dramatic possibilities (FN) from invented or unsafe admissions (FP); neither error justifies weakening the other lane. Report handling/privacy failures separately from dramatic yield.

### 4. Split by source lineage, not by rows

- Maintain separate **few-shot/training**, **development/calibration**, and **held-out test** roles. Freeze an ID manifest, source/evidence versions, deduplication groups, rubric, prompts, models, endpoint mapping, and acceptance criteria before opening the test results.
- Put all residues, versions, paraphrases, near-duplicates, and shared-incident variants of a source in one split. Two spans from one body are not independent examples. Check group overlap before scoring.
- Use development records for prompt/rubric repair and error-category discovery. Do not present those same records as independent test evidence. The existing twelve-record pilot is calibration unless a separate untouched holdout was explicitly designated before its inspection.
- Select split sizes based on available independent groups and positive/negative coverage, not copied percentage rules. If too few independent groups exist, report that a credible held-out estimate is unavailable and keep the run diagnostic.
- Once test results inform a prompt, rubric, evidence policy, model selection, or threshold, that set is consumed for development; obtain a new untouched test set for the next independence claim. Keep the old set as regression coverage.
- Report stratified calibration results by stratum. Do not extrapolate their pass rate to the full A0 population. Population estimates require a separately specified representative sampling design (or justified weights), not merely high TPR/TNR. No automatic prevalence correction is authorized.
- Release decisions require the existing user gate. Regression tests prove known-contract stability, not semantic correctness or market demand; a test pass cannot promote A1 records, change source pools, or authorize full rollout.

### Attribution and selected adaptation

Adapted, in original wording and narrowed to this workflow, from RefoundAI's `lenny-skills` at commit `13598cc54e09399bc1bc1398b0fca284110efb2f`: [ai-evals](https://github.com/RefoundAI/lenny-skills/blob/13598cc54e09399bc1bc1398b0fca284110efb2f/skills/ai-evals/SKILL.md) and [evaluation artifacts](https://github.com/RefoundAI/lenny-skills/blob/13598cc54e09399bc1bc1398b0fca284110efb2f/skills/ai-evals/references/artifacts.md), especially Open Coding/Axial Coding, LLM-as-a-Judge Playbook, Transition Failure Matrix, and Golden Dataset Construction. The compilation attributes these evaluation methods to Hamel Husain, Shreya Shankar, and Lenny's Podcast/Newsletter contributors. This is not independent verification of every upstream quote. Do not import fixed split percentages, generic accuracy targets, blanket binary workflow states, or commercial metrics as creative admission criteria. Upstream distinguishes MIT file structure/organization from the rights in underlying attributed content; do not treat it as blanket permission to redistribute source material.

## Twelve-record pilot before full rollout

Do not apply the new contract to the full A0 pool first. Build an outside-Vault stratified pilot:

- 5 `clear`;
- 5 `transform-only`;
- 2 legacy `blocked` stop records;
- mask existing captured/resting labels from the structure lane;
- include all four active sites where the bounded pool permits;
- seek transition, repetition/voice, stasis/object/time, non-human carrier, audience reframing, and closed-terminal examples.

For the ten runnable records, write the memo before self-copy comparison, run masked structure and source-open lineage reviews independently, then reconcile. Report state counts, review disagreement, invented-fact failures, and form coverage. Do not optimize to a target pass count. Keep crawler/source audit stores, machine records, failed drafts, exact-evidence ledgers, and review receipts outside Vault/Git. The private-workshop full-view convention, when approved by the recipient, supersedes aggregate-only user visibility: publish every A1 pilot entry, including resting/a0_recheck/blocked/not_run, in a private `wiki/writing/seeds/harvests/` full-view ledger with the public original (targeted identifier masking where needed), canonical URL/time, theatrical residue, clearly separated AI extension, judgment reason, and next writer question. Source-hidden applies only to the independent structure-review lane. Do not silently rewrite upstream A0 evidence or commit/push originals.

Keep the user-document rendering mode explicit and verify it separately from record coverage. A ledger with every source URL and a short excerpt is not a full-original ledger: label it as linked-original/excerpt rendering, report the limitation, and do not claim that a 12/12 section count proves full-body reproduction. Where quotation/reproduction constraints prevent the requested original rendering, preserve all verdicts and writer-facing reasons with compliant excerpts and source links rather than silently dropping records or overstating completion.

Full-pool rollout requires a separate user decision after the pilot is verified.

When an approved rollout accompanies correction-only work, keep historical A1 verdicts and latest A0 repair status as separate axes. Preserve the old A1 package exactly; label repaired records `A0 corrected / A1 retry pending` in the user ledger until a new memo/review is authorized. Do not count them as either newly passed A1 records or still-unrepaired A0 failures. Expand the existing canonical ledger with stable numbering and archive its prior rendering outside Vault rather than creating a competing ledger. Verify both historical and current-user totals against the same record set.

Report carrier and temporal-operation concentration after expansion. Many soundly supported voice-delivery memos do not prove broad theatrical form coverage or artistic novelty. Distinguish a shared delivery template from an identical source-specific dramatic engine, and state the bounded scope of the self-copy comparison.
