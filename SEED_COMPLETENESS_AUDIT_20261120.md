# IRG AI reference seed completeness audit — 2026-11-20

## Audit target

Repository: `Aaronpqking/IRG_AI_REFERENCE_REPO`  
Audited main-tree snapshot: `33b412f85f66cbf30e28b2c8a1782632a7054870`

Objective: ensure the public reference repository becomes a self-contained, evidence-grounded historical reference for Codex without relying on inaccessible external storage, placeholder completion, inferred implementation, or stale project-state summaries.

## Executive result

**Status: IN_PROGRESS — integrity controls improved, seed not complete.**

The repository already contains meaningful synthesis, exact ADR transfers, historical lessons/implementation ledgers, selected frozen evaluation artifacts, and several late-history reports. It is not yet complete because multiple intended source/report/research folders contain no substantive evidence beyond structural placeholders.

No current evidence supports declaring the reference seed complete.

## 1. File-integrity audit

The audited tree contains 114 files, of which 81 are substantive and 33 are zero-byte `.gitkeep` placeholders.

No non-`.gitkeep` zero-byte substantive file was identified in the enumerated tree.

The validator now treats every empty `.gitkeep` as an explicit completion blocker and any other zero-byte file as an integrity error. Placeholders therefore cannot be mistaken for completed seeding.

### Required areas still without substantive evidence

- `source_reference/identity/`
- `source_reference/retrieval/`
- `source_reference/context/`
- `source_reference/contracts/`
- `source_reference/structural/`
- `source_snapshot/`
- `research/structural/`
- `reports/reference/v1/`
- `reports/reference/v1_5/`
- `reports/reference/corpus/`
- `reports/reference/structural/`

These remain hard completion blockers.

## 2. Codex-portability audit

Current/reference documentation must not require access to external storage.

Corrections already present on `main`:

- `SOURCE_MANIFEST.md` uses local paths, source names, hashes, byte counts, and status rather than external-source URLs.
- `evaluation/FROZEN_TRANSFER_LEDGER.json` is repository-local and hash-based.
- `evaluation/EXPERIMENT_ADDENDUM_20261120.md` points to local historical reports.
- `evaluation/INTEGRITY_FINDINGS_20261120.md` describes withheld/private evidence through cryptographic identity.
- `scripts/validate_reference_seed.py` rejects direct Drive/Docs URLs in current/synthesized reference files.

Exact historical transfer files are not rewritten solely because their original historical text may mention outside systems. Current reference logic, however, must never depend on those references.

## 3. Direct V1-code grounding audit

The synthesized architecture correctly separates historical runtime, research, and clean-build targets, but curated historical implementation source has not yet landed under `source_reference/`.

Until that source is local, Codex cannot independently trace several current principles to the exact legacy implementation, including:

- identifier extraction and normalization;
- product/document applicability;
- hybrid retrieval and fusion;
- source/evidence serialization;
- context assembly;
- runtime contract boundaries;
- owner/configuration/procedure structural mechanisms.

Completion requires the original historical source files selected in the seed manifest. Do not create rewritten “representative” code in place of the historical implementation.

Any necessary public-repository redaction must be recorded and must not alter the logic being preserved.

## 4. Historical test grounding audit

`tests_reference/` currently contains seed-integrity tests, but not the full curated set of historical behavior-defining tests.

Completion still requires coverage for:

- exact identifier resolution;
- product/document applicability;
- wrong-product protection;
- retrieval policy;
- hybrid retrieval;
- retrieval/evaluation parity;
- context/source serialization;
- citation validation;
- execution trace/debug behavior;
- architecture boundaries;
- hardcoding controls;
- corpus promotion;
- structural owner/configuration/procedure milestones;
- late canonical/direct-RAG/fresh-holdout evaluation.

If an original test cannot be published, record the exact reason rather than replacing it with a synthetic test that changes semantics.

## 5. Latest project-history coverage

The current reference state now includes late October and November findings that materially supersede older summaries.

### October reconstruction

- 26/26 downstream parity.
- Answerable subset: exact-gold Recall@10 21/21.
- Sufficient context: 19/21, with P1 5/6 and P2 14/15.
- Critical wrong-product/revision errors: 0.
- P1: 80 logical docs, 48,447 views, 46,462 vectors.
- P2: 437 logical docs, 107 physical sources, 216,921 views, 163,268 vectors.

### Standard/full-view unseen P2

- 20 planned, 19 executed, 17 valid unseen.
- Sufficient context: 3/17 both arms.
- Sufficient evidence@10: 5/17 both arms.
- Critical wrong-product errors: 0.
- Full-view wins/losses: 0/0.
- 10,868 extra contextualized views changed ranking stages but did not rescue a failed case.

### Expanded scale comparison

- Exact gold: 16/40 current vs 13/40 October.
- Narrative: 3/10 current vs 0/10 October.
- These denominators are not interchangeable with the bounded reconstruction population.

### November alias/canonical audit

- 19/19 alias failures reproduced, including 13/13 cart cases.
- 1,502 canonical documents vs 935 physical revisions.
- 567 excess canonical records.
- 1,110 duplicate references across 298 products.

### C1 inactive safety candidate

- 4,943 relationships.
- 52 unsupported post/cart grants removed.
- 40/40 reviewed positives preserved.
- 9/9 revocations preserved.
- 4,903 unrelated relationships unchanged.
- No production change.

### Latest authoritative project-history R2 state — 2026-11-18

- P0 recovery scope deferred: 183 logical / 177 physical.
- P1: 6/150 latest baseline; 0 accepted gates.
- P2: 49/49 literals and 19/19 controls; ≥98% identity target still unproven.
- P3 scopes 83 / 38 / 561 / 67; mean document reduction 90.85%.
- P4 canonical reduction 18.92%–51.62%; fine exclusions 0; lexical competition reduction 0%; dense reduction 0%–6.22%.
- P5/P6 sufficient context: 0/5.
- P7: 35 valid; cold 141.935 s; repeat 28.175 s; parity 35/35; SLO/p95 unestablished.

Earlier 2026-11-16 R2 observations are progression evidence and are superseded by the 2026-11-18 ledger where inconsistent.

## 6. Current intellectual consequence

The latest evidence rejects a common shortcut:

> Document-level candidate reduction is not evidence-level competition reduction, evidence sufficiency, or answerability.

The clean build must measure the stages separately:

`identity → document authority → evidence competition → candidate retrieval → selected evidence → serialized context → sufficiency → response → citation`

Likewise, rank movement or view proliferation is not promotion evidence unless it improves the downstream stage that matters.

## 7. No-assumption rule

Every synthesized claim must carry one of these states where applicable:

- `LOCAL_SOURCE_VERIFIED`
- `LOCAL_REPORT_VERIFIED`
- `HISTORY_REPORTED_UNVERIFIED`
- `SYNTHESIS`
- `PROPOSED`
- `INVALID`
- `BLOCKED`
- `SUPERSEDED`

Do not:

- infer runtime behavior from filenames;
- infer implementation from architecture prose when source should be available;
- convert project-history recollection into verified runtime evidence;
- merge metrics from incompatible populations;
- rewrite frozen evidence to eliminate a mismatch.

## 8. Completion gates

The reference seed may be declared complete only when all are true:

1. `python scripts/validate_reference_seed.py --strict` passes.
2. Required reference directories contain substantive evidence rather than placeholders.
3. No substantive zero-byte files exist.
4. Current/synthesized reference documents contain no required external-storage URL.
5. Curated historical source is local and traceable from the synthesis.
6. Curated historical behavior tests are local.
7. Required V1, V1.5, corpus, structural, scale, ablation, and audit reports are local or explicitly classified unavailable with reason.
8. Current reference state includes the latest dated project-history findings.
9. History-only results remain provisional until bound artifacts are local.
10. IRG-X001 remains visible unless directly reconciled.
11. Public-repository privacy review passes.
12. `SOURCE_MANIFEST.md` accounts for every substantive seeded artifact class.

## 9. Current verdict

**NOT COMPLETE.**

Progress is valid and materially improved, but direct historical source, behavior tests, milestone reports, structural research, and late-run provenance are still incomplete.

Do not declare completion from folder existence, `.gitkeep` files, document titles, or passing non-strict seed-integrity CI.
