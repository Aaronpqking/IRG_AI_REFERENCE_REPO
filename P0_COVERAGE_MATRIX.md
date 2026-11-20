# P0 seed coverage reconciliation — 2026-11-20

Coverage audited against the 2026-11-20 supplied **IRG AI Reference Repository Seed Manifest**, using the full original manifest (not a subset of selected filenames). This is a **document-delivery accounting**, not a measure of release readiness or empirical confidence.

| P0 destination | Delivery | Specific gap / interpretation |
|---|---|---|
| `README.md` | IMPLEMENTED | Reference-only orientation, no runtime coupling |
| `REFERENCE_POLICY.md` | IMPLEMENTED | Claim-level authority precedence |
| `REFERENCE_INDEX.md` | IMPLEMENTED | Codex navigation and evidence escalation |
| `SOURCE_MANIFEST.md` | PARTIAL | Original transfers linked; item-level full manifest still expanding |
| `CURRENT_REFERENCE_STATE.md` | PARTIAL | Snapshot synthesized; late-run verification pending |
| `timeline/BUILD_TIMELINE.md` | PARTIAL | Chronology synthesized; original milestone hash joins incomplete |
| `architecture/ARCHITECTURE_EVOLUTION.md` | PARTIAL | Historical implementation and research distinguished; executable source checkout missing |
| `architecture/DURABLE_ARCHITECTURE_PRINCIPLES.md` | IMPLEMENTED | Reference principles; not runtime promotion |
| `architecture/TARGET_REFERENCE_PIPELINE.md` | IMPLEMENTED | Explicit proposed five-part pipeline |
| `evaluation/EVALUATION_EVOLUTION.md` | IMPLEMENTED | Stage-specific chronology |
| `evaluation/METRIC_DEFINITIONS.md` | PARTIAL | Normalized metric glossary; 77 frozen metric definitions transferred but comparison pending |
| `evaluation/EMPIRICAL_FINDINGS.md` | PARTIAL | V1.9.35 direct report added; October P2 originals missing |
| `evaluation/EXPERIMENT_REGISTER.md` | PARTIAL | Initial experiment entries plus verified invalidated research; no exhaustive run inventory |
| `evaluation/FAILURE_REGISTER.md` | PARTIAL | Normalized taxonomy; original defects/tests incomplete |
| `evaluation/frozen/` | PARTIAL | 8 original contracts + 2 associated reports copied exactly; 244+615 record sets hash-verified but withheld; IRG-X001 open |
| `governance/GOVERNANCE_PRINCIPLES.md` | IMPLEMENTED | Core controls synthesized |
| `governance/SOURCE_AUTHORITY.md` | PARTIAL | Fact-specific reference; explicit nonactivated original policy preserved |
| `governance/EVALUATION_INTEGRITY.md` | IMPLEMENTED | Denominator, contamination and integrity gates |
| `governance/EXPERIMENT_PROMOTION_POLICY.md` | IMPLEMENTED | Versioned JSON promotion contract available |
| `governance/AUTONOMY_BOUNDARIES.md` | IMPLEMENTED | Read-only operators and approval boundaries |
| `decisions/historical/` | IMPLEMENTED | 19 original ADRs plus original README copied |
| `decisions/ADR_INDEX.md` | IMPLEMENTED | 19 dispositions with historical vs clean-build status |
| `lessons/LESSONS_LEARNED.md` | IMPLEMENTED | Original 65,467-byte historical lessons transferred intact |
| `lessons/IMPLEMENTATION_HISTORY.md` | IMPLEMENTED | Original historical implementation ledger copied intact |
| `lessons/CLEAN_LAB_CARRY_FORWARD.md` | IMPLEMENTED | Clean inheritance map with conditional gates |
| `reports/reference/evaluation/EVALUATION_RESULTS_CROSSWALK.md` | PARTIAL | Main populations separated, full original milestones missing |
| `reports/reference/scale/CORPUS_SCALE_EVOLUTION.md` | PARTIAL | Historical scale counts, original structural manifests missing |
| `reports/reference/scale/EXPANDED_CORPUS_SCALE_TEST.md` | PARTIAL | Historical 40/10 results synthesized, late immutable ledgers missing |
| `reports/reference/ablations/STANDARD_VS_FULL_VIEW_P2_ABLATION.md` | PARTIAL | Late paired 17-case research reported, original October run missing |
| `reports/reference/audits/CLEAN_LAB_AUDIT_SYNTHESIS.md` | PARTIAL | Historical audit synthesis, selected detailed audits not yet transferred; directly checked source available separately |

## Summary
- Total named P0 destinations/groups: **30**.
- Implemented at the document/directory level: **15**.
- Partial due to missing bound original evidence, source snapshots, run artifacts or coverage: **15**.
- Full-P0 empirical qualification: **BLOCKED** by unresolved IRG-X001, historical source revision binding and late experimental provenance.

## High-priority completion sequence
1. Resolve evaluator/master manifest hash mismatch **IRG-X001** from original bound source revision; do not change the frozen manifest to force a pass.
2. Verify 11 discovered original archived source/test files against the exact historical Git commit; do not publish private source bodies.
3. Verify late October P1/P2 and scale report run IDs, frozen cases and metadata; leave current reported statistics at `HISTORY_REPORTED_UNVERIFIED` until then.
4. Expand evaluation crosswalk to all required milestone runs; separate invalid, blocked, fresh holdout and development metrics.
5. Audit detailed original architecture/codebase reports and update accepted/rejected mechanisms based on direct source.
6. Complete privacy review of all material before any further public transfer.

## Constraints
A copied ADR is historical evidence, not executable proof. A transferred frozen manifest is not a completed evaluation. The 244-case population and 615-row triage are hash-verified in Drive and withheld from the public repository. Seed integrity CI is independent of strict qualification.

See [P0_SEED_LEDGER.md](P0_SEED_LEDGER.md), [evaluation/FROZEN_TRANSFER_LEDGER.json](evaluation/FROZEN_TRANSFER_LEDGER.json), and [evaluation/INTEGRITY_FINDINGS_20261120.md](evaluation/INTEGRITY_FINDINGS_20261120.md).

## Updated provenance vs local-implementation classification
Historical source and evaluator bytes have been directly SHA-256 verified in private Drive, but **no historical implementation modules were deposited in the required local source subdirectories**. The source register is an evidence inventory, not substantive curated code. Required local test semantics and all strict completion gates remain incomplete. Source use in Codex must follow [REFERENCE_PORTABILITY_POLICY](governance/REFERENCE_PORTABILITY_POLICY.md). The existing 15/30 implemented/partial count is document-level inventory only; this update makes no upward completion-count claim.

## Rereview verification — 2026-11-20
All 11 records in `source_reference/SOURCE_BINDINGS_20261120.json` were independently re-fetched from the private historical archive during rereview. Byte counts and SHA-256 values matched the local ledger **11/11**. This verifies provenance identity only; the source is still not repository-local, commit-bound, or a substitute for curated local V1 code/tests.

## Original identity reference transfer (2026-11-20)
The selected identity-source slice is now materially populated: 5 exact historical implementation modules in `source_reference/identity/` and 3 exact historical identity tests in `tests_reference/historical/identity/`, with 8/8 equal original/local SHA-256 fingerprints and 138,849 bytes. This counts as **local exact source transfer** for that selected subset, not complete implementation coverage, source revision equivalence, or a passing historical behavior-test suite. Other required source and report families remain incomplete; `IRG-X001` persists and strict completion is blocked.
