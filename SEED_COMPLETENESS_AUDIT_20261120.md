# IRG AI reference seed completeness audit — 2026-11-20

## Audit target

Repository: `Aaronpqking/IRG_AI_REFERENCE_REPO`  
Audited main-tree snapshot before corrections: `dab00546463c19455111aafa788c0d6fd2faaf3e`

Objective: ensure the public reference repository becomes a self-contained, evidence-grounded historical reference for Codex without relying on inaccessible external storage, placeholder completion, inferred implementation, or stale project-state summaries.

## Executive result

**Status: IN_PROGRESS — integrity controls improved, seed not complete.**

The repository already contains meaningful synthesis, exact ADR transfers, historical lessons/implementation ledgers, selected frozen evaluation artifacts, and several late-history reports. It is not yet complete because multiple intended source/report/research folders contain no substantive evidence beyond structural placeholders.

No current evidence supports declaring the reference seed complete.

## 1. File-integrity audit

### Confirmed substantive files

The repository contains non-empty current/reference documents, all 19 historical ADRs, historical lessons and implementation history, selected frozen evaluation contracts/manifests, two historical evaluator reports, scale/ablation syntheses, and validation/test tooling.

### Empty files

The pre-audit tree contains multiple zero-byte `.gitkeep` files. They are structural placeholders, not evidence. No substantive zero-byte file was identified in the enumerated tree.

**Correction:** the validator now emits `EMPTY_PLACEHOLDER` blockers for zero-byte `.gitkeep` files and `EMPTY_SUBSTANTIVE_FILE` errors for any other zero-byte file. Placeholder presence therefore cannot be interpreted as completion.

### Empty required reference areas at audited snapshot

The following intended areas contained no substantive file at the audited main snapshot:

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

These are now explicit completion blockers in `scripts/validate_reference_seed.py`.

## 2. Codex-portability audit

### Defect found

Current/reference documentation contained direct external storage URLs. Those links are not suitable as required evidence because Codex or a future isolated implementation agent may not have access.

### Correction

On the audit branch:

- `SOURCE_MANIFEST.md` now uses local paths, source artifact names, hashes, byte counts, and visibility status rather than external links.
- `evaluation/FROZEN_TRANSFER_LEDGER.json` no longer requires external URLs.
- `evaluation/EXPERIMENT_ADDENDUM_20261120.md` uses local historical report paths.
- `evaluation/INTEGRITY_FINDINGS_20261120.md` describes withheld/private evidence through cryptographic identity without requiring external archive access.
- the validator rejects direct Drive/Docs URLs in current/synthesized reference files.

Exact historical transfer files are not rewritten merely because their original text may mention external systems; current reference logic must not depend on those mentions.

## 3. Direct V1-code grounding audit

### Current weakness

The current synthesized architecture documents correctly distinguish historical runtime, research, and clean-build targets, but most curated legacy implementation source has not yet landed under `source_reference/`.

That means statements such as:

- identity extraction behavior;
- document applicability;
- hybrid retrieval/fusion;
- source serialization;
- evidence context;
- runtime contract boundaries;
- structural owner/configuration/procedure mechanisms;

cannot yet all be traced by Codex from the reference synthesis directly to local historical implementation source.

### Completion requirement

Before completion, populate the curated source areas with the selected historical implementation files defined by the seed manifest. Preserve original code intact except for any required public-repository redaction that does not change logic; any redaction must be explicitly recorded.

Do not create rewritten “representative” code in place of historical source.

## 4. Test grounding audit

The current `tests_reference/` contains reference-seed tests, but not yet the full curated set of historical behavior-defining tests.

Required historical coverage still includes:

- exact identifier resolution;
- product/document applicability;
- wrong-product suppression;
- retrieval policy;
- hybrid retrieval;
- retrieval/evaluation parity;
- context/source serialization;
- citation validation;
- execution trace/debug behavior;
- core/hexagonal boundaries;
- hardcoding controls;
- corpus promotion;
- structural owner/configuration/procedure milestones;
- late canonical/direct-RAG/fresh-holdout evaluators.

Completion requires local tests or a documented reason an original test cannot be published.

## 5. Latest project-history coverage audit

The earlier current-reference snapshot was materially incomplete because it did not include the latest November R2 findings.

### October evidence retained

- October reconstruction: 26/26 downstream parity.
- On the answerable subset: exact-gold Recall@10 21/21; sufficient context 19/21; wrong-product/revision 0.
- P1: 80 logical docs, 48,447 views, 46,462 vectors.
- P2: 437 logical docs, 107 physical sources, 216,921 views, 163,268 vectors.
- P2 standard/full unseen: 17 valid; context 3/17 both; evidence@10 5/17 both; 0 critical wrong-product; 0 full-view wins.
- 40-case scale comparison: 16/40 current versus 13/40 October; narrative 3/10 versus 0/10.

### November evidence added

November alias/canonical audit history:

- 19/19 alias failures reproduced, including 13/13 cart cases.
- 1,502 canonical docs versus 935 physical revisions.
- 567 excess canonical records.
- 1,110 duplicate references across 298 products.

C1 inactive safety candidate:

- 4,943 relationships;
- 52 unsupported post/cart grants removed;
- 40/40 reviewed positives preserved;
- 9/9 revocations preserved;
- 4,903 unrelated relationships unchanged;
- no production change.

### Latest R2 authoritative project-history state — 2026-11-18

- P0 recovery scope deferred: 183 logical / 177 physical.
- P1: 6/150 latest baseline, 0 accepted gates.
- P2: 49/49 literals, 19/19 controls; ≥98% identity target still unproven.
- P3 scopes 83 / 38 / 561 / 67; mean document reduction 90.85%.
- P4 canonical reduction 18.92%–51.62%; fine exclusions 0; lexical competition reduction 0%; dense reduction 0%–6.22%.
- P5/P6 sufficient context: 0/5.
- P7: 35 valid; cold 141.935 s; repeat 28.175 s; parity 35/35; SLO/p95 unestablished.

### Intellectual consequence

This supersedes any simpler claim that metadata/document narrowing is sufficient retrieval repair.

Current reference principle:

> Document-level candidate reduction must not be treated as evidence-level competition reduction, evidence sufficiency, or answerability.

The full chain must be measured separately:

`identity → document authority → evidence competition → candidate retrieval → selected evidence → serialized context → sufficiency → response → citation`

## 6. No-assumption rule

Current and future synthesized files must distinguish:

- `LOCAL_SOURCE_VERIFIED`
- `LOCAL_REPORT_VERIFIED`
- `HISTORY_REPORTED_UNVERIFIED`
- `SYNTHESIS`
- `PROPOSED`
- `INVALID`
- `BLOCKED`
- `SUPERSEDED`

Do not convert project-history recollection into “verified runtime behavior” without the bound local artifact.

Do not infer a code path from an architecture diagram when the historical source is available or expected to be seeded.

Do not infer the latest state from filenames such as `FINAL`, `CURRENT`, `V2`, or `PRODUCTION`.

## 7. Completion gates

The reference seed may be declared complete only when all are true:

1. `python scripts/validate_reference_seed.py --strict` returns PASS.
2. Required reference directories contain substantive evidence, not placeholders.
3. No substantive zero-byte files exist.
4. Current/synthesized reference documents contain no required external-storage URL.
5. Curated V1 source is local and traceable from reference synthesis.
6. Curated historical behavior tests are local.
7. Required V1, V1.5, corpus, structural, scale, ablation, and audit milestone reports are local or explicitly classified unavailable with reason.
8. Current reference state includes the latest dated project-history findings.
9. History-only results retain provisional status until bound artifacts are local.
10. IRG-X001 remains a visible blocker unless directly reconciled.
11. Public-repository privacy review passes.
12. `SOURCE_MANIFEST.md` accounts for every substantive seeded artifact class.

## 8. Current completion verdict

**NOT COMPLETE.**

The seed is progressing correctly in governance/evaluation/ADR/lessons coverage, but source, historical tests, milestone reports, structural research, and late-run provenance remain materially incomplete.

The validator and current-reference corrections on `audit/seed-completeness-20261120` are intended to prevent those gaps from being mistaken for completion.
