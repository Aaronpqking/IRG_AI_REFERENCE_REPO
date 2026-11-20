# P0 reference seed verification ledger — 2026-11-20

## Completed and measured

- Reference architecture, provenance policy, navigation, claim registry, and intellectual-state synthesis are present.
- All 19 historical ADRs plus their original README are present.
- Historical `LESSONS_LEARNED.md` and `IMPLEMENTATION_HISTORY.md` are present as substantive local files.
- Eight frozen contract/manifest source files and two associated historical reports were transferred byte-for-byte and recorded with source SHA-256 and byte counts.
- Master population identity: 244 JSONL scenarios, SHA-256 `4b561ffea79edc97c270cda38fbd0e5351615c0acd8d8be4eab291a3d504bd8e`.
- Historical triage identity: 615 JSONL records, SHA-256 `8dc936cb0d7c600fdad13592f45f2b564ff8c0b41e9050294373f19432a25e2d`.
- Those two raw populations are deliberately withheld from the public repository because they contain historical user-conversation wording.
- [FROZEN_TRANSFER_LEDGER](evaluation/FROZEN_TRANSFER_LEDGER.json) records local paths, source artifact names, byte counts, hashes, visibility status, and IRG-X001.
- [INTEGRITY_FINDINGS](evaluation/INTEGRITY_FINDINGS_20261120.md) records frozen binding checks.
- [CURRENT_REFERENCE_STATE](CURRENT_REFERENCE_STATE.md) now includes the latest known October/November project-history findings, including the 2026-11-18 R2 ledger, with explicit `HISTORY_REPORTED_UNVERIFIED` status where local run packages remain absent.
- The validator distinguishes evidence integrity from seed completion and flags external-storage dependencies, empty placeholders, and required reference areas without substantive files.

## Outstanding P0 blocks

1. **IRG-X001:** evaluator manifest binds master-regression manifest SHA-256 `9ddf9eaf...`; repository-local manifest hashes to `fa6b6291...`. Recover the evaluator-bound revision from directly bound historical evidence. Do not rewrite either frozen artifact to force a pass.
2. **Private frozen population reproduction:** two historical populations are hash-verified but intentionally not public. Qualification requiring them must use separately authorized copies that match the recorded hashes.
3. **Curated source/test seeding:** legacy implementation source and behavior-defining tests are being seeded. Until `source_reference/*`, `source_snapshot/`, and the curated behavior-test set contain substantive local files, code-level reference coverage is incomplete.
4. **Milestone report seeding:** `reports/reference/v1`, `v1_5`, `corpus`, and `structural` remain incomplete until their selected direct historical reports are local.
5. **Structural research seeding:** `research/structural/` is not complete until the selected structural mechanisms/reports are present.
6. **Late October/November provenance:** the P1/P2 reconstruction, 40-case scale comparison, 17-case full-view ablation, November alias audit, and R2 P0–P7 ledger require their original bound run artifacts before their status can move beyond history-reported evidence.
7. **R2 evaluation:** latest authoritative project-history state reports P1 only 6/150 with 0 accepted gates; P5/P6 0/5 sufficiency; SLO/p95 not established.
8. **Completion-mode CI:** `python scripts/validate_reference_seed.py --strict` must pass before the reference seed is declared complete.

## Public-repository guardrails

Do not upload:
- credentials or secrets;
- customer/employee records;
- private conversations;
- operational databases;
- unsanitized traces;
- private frozen question populations;
- generated vector stores;
- raw corpus material unless separately approved.

Do not use external storage links as required evidence for current/reference documents. A current claim must be understandable from repository-local evidence plus explicit claim status.

## Status

**REFERENCE_SEED_IN_PROGRESS / INTEGRITY_GUARDED / NOT COMPLETE.**

No production database, provider, corpus, vector index, deployment, release state, or clean-build implementation is changed by this reference audit.

## Addendum — historical archive source recovery and evaluator approval (2026-11-20)
- Original `irg_ai-main` folder contains historical `src/`, `tests/`, and `src/v2_evaluator/` trees. Eleven selected serving/test files (421,897 bytes) have direct SHA-256 and AST parse evidence; Git-commit and October runtime equivalence remain unbound.
- Ten of ten evaluator source/test hashes **exactly match** `V2_EVALUATOR_MANIFEST_v1.json`. The dependency manifest, derived population, fixture and focused test evidence also match their declared hashes.
- Independently recovered owner approval `V2_EVALUATOR_APPROVAL_v1.json` binds the existing manifest and derived population to frozen **implementation approval**. It explicitly leaves qualification `NOT_EXECUTED` and execution unauthorized.
- The three distinct master-manifest digests in [IRG-X001 lineage](evaluation/IRG_X001_MANIFEST_LINEAGE_20261120.md) remain unequal. Do not claim full qualification or quietly substitute revisions.
- Public metadata is in [EVALUATOR_PROVENANCE_LEDGER](evaluation/EVALUATOR_PROVENANCE_LEDGER.json) and [SOURCE_BINDINGS](source_reference/SOURCE_BINDINGS_20261120.json). Original code, private questions, and raw derived-case data stay out of this public repository.

## Isolated offline evaluator replay (2026-11-20)
Original SHA-bound evaluator code was assembled in a private temporary workspace. **17/17** core tests passed; a combined subset completed **20 passed and 3 deliberately deselected**. The three deselections concern original frozen master-manifest closure, full bound-file closure and exact builder reproduction; they remain qualification blockers rather than silent passes. See [replay report](evaluation/EVALUATOR_ISOLATED_OFFLINE_REPLAY_20261120.md). No external provider/database/vector calls or serving changes occurred.

## P0 portability control update (2026-11-20)
- [Portability policy](governance/REFERENCE_PORTABILITY_POLICY.md) formalizes the updated rule: Google Drive is an origin/discovery source, **not a Codex runtime dependency**. The 11-file source register and 10-file evaluator binding are `EXTERNALLY_VERIFIED_NOT_LOCAL`, so they **do not close** the required `source_reference/*`, `source_snapshot/`, or curated historical `tests_reference/` folders.
- Added the new synthesis and provenance audit documents to the validator's external-storage-URL check; no required Drive link is allowed in these current documents.
- `V2_EVALUATOR_APPROVAL_v1.json` explicitly limits its own scope and does **not** authorize Git publication by itself. The pending public PR requires separate privacy/publication review before merge.
- Read-only archive folder enumeration found one available `V2_MASTER_REGRESSION_MANIFEST_v1.json` and one evaluator-version artifact folder. No second original master-manifest body was found there; `IRG-X001` remains unresolved.

## 11/11 source-binding rereview (2026-11-20)
The 11 source/test records currently listed in `source_reference/SOURCE_BINDINGS_20261120.json` were independently re-fetched from the historical archive during this rereview. Their byte lengths and SHA-256 hashes matched **11/11**. This confirms that the binding ledger represents real historical files, not invented placeholders. It does **not** close local-source completion because the files are still absent from the public repository and are not bound to the exact historical Git revision.

The latest project-history addition is the 2026-11-19 read-only G2/R1/R0 comparison. It is recorded as `HISTORY_REPORTED_UNVERIFIED` until its original local run/comparison package is transferred.

## Identity-family implementation slice — 2026-11-20
A targeted, original-byte identity source review covered 5 Python implementation files and 3 behavior-test files. All 8 were parseable, 8 original-byte fingerprints computed (0 comparisons to a preexisting frozen digest), and 24 historical `test_*` definitions located (not executed). A heuristic secrets/path scan found no obvious literal credential assignments, email addresses or absolute user paths, but this is **not** a publication approval. Original bytes remain private; no source family is promoted to local completion. See [publication review](governance/publication_reviews/IDENTITY_SOURCE_REVIEW_20261120.md). This bounded audit does not change IRG-X001, release qualification or late R2 evidence status.

## User-approved original identity publication (2026-11-20)
Five original identity implementation modules plus three original identity behavior-test modules are now locally present as byte-identical copies (**8/8 local digest matches; 138,849 bytes**). Previously publication-blocked status in this ledger's earlier dated section is superseded for those eight artifacts only. Public review: **user-approved**, additional static source scan completed, no redactions. The source checkout is not yet mapped to an exact Git commit; historical behavior tests have not been executed and downstream completeness remains blocked. See [exact-file register](governance/publication_reviews/IDENTITY_SOURCE_TRIAGE_20261120.json).

## Postapproval reconciliation — 2026-11-20
Five original identity modules and three historical tests (138,849 bytes; eight equal SHA-256 source/local digests) were published in approved PR #14. Five previously empty historical report/research families gained substantive locally readable curated summaries and local provenance through merged PRs #15–#19. The conflicted combined PR #10 was closed unmerged. No frozen original run package was promoted or replayed; no source commit or live runtime equivalence established. The selected identity and five report areas are now **populated**, while all other required reference areas, original report transfer, behavior-suite qualification, `IRG-X001`, and strict P0 remain unresolved. Preserved November 19 project-history authority from PR #11 is unchanged.
