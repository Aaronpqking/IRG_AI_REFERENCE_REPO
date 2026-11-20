# Historical ADR inventory and clean-lab disposition — 2026-11-20

This inventory maps all **19 original historical decisions**, copied without modification into [historical/](historical/), to a **recommended** clean-build posture. Original accepted status does not imply that a decision remains activated or should be reproduced. Dispositions are proposals until independently accepted against bound code/tests and current holdout.

| ADR | Historical decision | Clean-build disposition | Later evidence / caveat |
|---|---|---|---|
| 001 | [Thin hexagonal architecture](historical/ADR-001-thin-hexagonal-architecture.md) | KEEP | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 002 | [Composition roots](historical/ADR-002-composition-roots.md) | KEEP | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 003 | [Versioned runtime contracts](historical/ADR-003-versioned-runtime-contracts.md) | KEEP | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 004 | [Qdrant rebuildability](historical/ADR-004-qdrant-rebuildability.md) | KEEP_CONCEPT | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 005 | [Structured DB and PDF evidence](historical/ADR-005-structured-db-and-pdf-evidence.md) | KEEP | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 006 | [Exact identifier precedence](historical/ADR-006-exact-identifier-precedence.md) | KEEP | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 007 | [Identity locking and follow-ups](historical/ADR-007-identity-locking-and-followups.md) | KEEP_CONCEPT | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 008 | [Provenance separation](historical/ADR-008-provenance-separation.md) | KEEP | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 009 | [Model consistency](historical/ADR-009-model-consistency.md) | REASSESS | Historical model-called successful path; later sufficiency/clarify/abstain work requires explicit decision-policy reassessment. |
| 010 | [Remove answer-permission flags](historical/ADR-010-remove-answer-permission-flags.md) | KEEP | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 011 | [Descriptive product roles](historical/ADR-011-descriptive-product-roles.md) | SUPERSEDED | Accepted as descriptive-only in original ADR; later project history reports roles removed from active paths. Preserve original, exclude role permission logic. |
| 012 | [Observe-first grounding](historical/ADR-012-observe-first-grounding.md) | KEEP | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 013 | [Structured logging](historical/ADR-013-structured-logging.md) | KEEP | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 014 | [Failure taxonomy](historical/ADR-014-failure-taxonomy.md) | KEEP | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 015 | [API/CLI/eval parity](historical/ADR-015-api-cli-eval-parity.md) | KEEP | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 016 | [SQL stored procedure and direct query](historical/ADR-016-sql-stored-procedure-and-direct-query.md) | IRG_SPECIFIC | Implementation-specific SQL mix; retain generic read-only bounded data authority, not hardwired MySQL procedures. |
| 017 | [Release model and freeze control](historical/ADR-017-release-model-and-freeze-control.md) | KEEP_CONCEPT | Historical accepted design; clean-build adoption requires bound tests and renewed qualification. |
| 018 | [V2 conversation and multi-subject context](historical/ADR-018-v2-conversation-and-multi-subject-context.md) | DEFER | Multi-subject continuity was historical, but clean V1 scope is smaller; retain concept, defer feature until justified. |
| 019 | [Governed corpus promotion and rollback](historical/ADR-019-governed-corpus-promotion-and-rollback.md) | KEEP | Promotion/rollback governance remains essential but bound source artifacts must be imported. |

## Disposition vocabulary
KEEP: retain architecture invariant subject to tests; KEEP_CONCEPT: retain principle, reimplement differently; IRG_SPECIFIC: isolate product domain; SUPERSEDED: preserve only for lineage; REASSESS: new downstream measurement required; DEFER: not a clean V1 default.

## Conflict emphasis
**ADR-011:** Original was accepted descriptive product-role context. Later project-history runtime analysis reports the entire product-role infrastructure was removed. Both statements can be true at different times. Do not treat the archived ADR as current serving authority.

**ADR-009:** Historical preference for model calls on successful answer paths must be reconciled with the newer evidence sufficiency and valid-answer suppression dilemma. Do not conclude automatic model generation is always correct.

**ADR-018:** Historical multi-subject conversation continuity can be reused as bounded context principles without inheriting the full V2 scope immediately.

## Provenance
Google Drive original ADR folder contains 19 ADRs and its README. Copied to `decisions/historical/`; provenance per filename is the source Drive folder. No original ADR was edited to reflect later outcomes.
