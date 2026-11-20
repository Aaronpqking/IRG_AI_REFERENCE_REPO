# Architecture Decision Records

Verified ADR set through the 2026-08-05 V2 corpus promotion.

| ADR | Status | Decision |
|---|---|---|
| `ADR-001-thin-hexagonal-architecture.md` | Accepted | Keep routes thin and isolate SDK/database/filesystem details behind ports and adapters. |
| `ADR-002-composition-roots.md` | Accepted | Use `src/bootstrap/composition.py` as the primary runtime composition root. |
| `ADR-003-versioned-runtime-contracts.md` | Accepted | Preserve `hexagonal.v1`, `context.v1`, `sources.v2`, and `phase0.v1` contracts. |
| `ADR-004-qdrant-rebuildability.md` | Accepted | Treat Qdrant as rebuildable index state over local chunk artifacts. |
| `ADR-005-structured-db-and-pdf-evidence.md` | Accepted | Keep structured product DB evidence distinct from vectorized PDF evidence. |
| `ADR-006-exact-identifier-precedence.md` | Accepted | Run exact normalized identifier lookup before broad discovery. |
| `ADR-007-identity-locking-and-followups.md` | Accepted | Reuse bounded conversation product context for follow-up questions. |
| `ADR-008-provenance-separation.md` | Accepted | Keep answer sources separate from candidate discovery provenance. |
| `ADR-009-model-consistency.md` | Accepted | Successful answer paths call the configured chat model; deterministic responses are runtime failures or validation disposition. |
| `ADR-010-remove-answer-permission-flags.md` | Accepted | Supersede active answer-permission flags with response class, evidence status, and grounding disposition. |
| `ADR-011-descriptive-product-roles.md` | Accepted | Treat product roles as descriptive/applicability context, not hidden authorization gates. |
| `ADR-012-observe-first-grounding.md` | Accepted | Default grounding validation to observe mode. |
| `ADR-013-structured-logging.md` | Accepted | Use structured request/pipeline events with request IDs and sanitized diagnostics. |
| `ADR-014-failure-taxonomy.md` | Accepted | Report failures by pipeline stage and evaluation category. |
| `ADR-015-api-cli-eval-parity.md` | Accepted | Keep API, CLI, and production-path evaluation on shared service composition. |
| `ADR-016-sql-stored-procedure-and-direct-query.md` | Accepted | Use stored procedures for broad product discovery and direct parameterized SQL for exact lookup/metadata verification. |
| `ADR-017-release-model-and-freeze-control.md` | Accepted | Preserve V1 history, freeze V1.5 only from a reviewed allowlisted tree, and use explicit V2/V2.5/V3 numerical gates. |
| `ADR-018-v2-conversation-and-multi-subject-context.md` | Accepted | Use ten recent persisted messages as context, preserve the literal current question, retrieve fresh evidence, and retain evidence ownership for every requested subject. |
| `ADR-019-governed-corpus-promotion-and-rollback.md` | Accepted | Promote only a frozen, validated collection copy; preserve the prior active collection as rollback authority and do not re-embed during promotion. |

Historical `docs/decisions.md` is retained as a V1-era ledger and includes superseded claims. This directory is the current ADR surface.
