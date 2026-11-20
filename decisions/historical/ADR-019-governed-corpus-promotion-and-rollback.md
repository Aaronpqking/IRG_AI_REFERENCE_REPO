# ADR-019 - Governed Corpus Promotion and Rollback

Status: Accepted

Date: 2026-08-05

## Context

A larger corpus is not ready merely because it was embedded successfully or
because source and destination point counts match. Retrieval identity,
manufacturer isolation, answer fidelity, citation alignment, collection
configuration, rollback, and runtime configuration must agree on one frozen
artifact identity.

## Decision

1. Freeze corpus authority with manifest/chunk hashes and a governed staging
   collection before quality evaluation.
2. Require retrieval, identity, contamination, answer, citation, hardcoding,
   and bypass gates before promotion review.
3. Promote by creating an exact named collection copy from the validated
   staging snapshot. Do not rebuild or re-embed during promotion.
4. Verify point IDs, vector schema, payload indexes, configuration, selected
   payload/vector parity, health, and an ordinary retrieval smoke before the
   runtime switch is accepted.
5. Change the existing runtime collection setting explicitly and reload only
   the affected service.
6. Preserve the previous active collection unchanged as recorded rollback
   authority. Do not move an alias or delete rollback state as part of
   promotion.

## Alternatives considered

- Rebuild the active collection in place.
- Re-embed during promotion.
- Switch an unverified alias without a named rollback collection.
- Promote from point-count parity alone.

## Consequences

The promoted collection has a reproducible lineage and immediate rollback
target. Intermediate failed evaluations remain historical evidence; later
repairs supersede their current recommendation only through new immutable
artifacts. Promotion proves normal V2 operation, not V2.5 pilot or V3 production
readiness.

## Invariants

- Manifest and chunk hashes identify the evaluated corpus.
- Promotion creates no new corpus embeddings.
- The previous active collection remains intact until a later retention
  decision.
- Active configuration names the promoted collection directly.
- Production-readiness claims remain governed by the versioned roadmap.

## Evidence

`reports/V2_S2G_PROMOTION_READINESS.md`,
`reports/V2_S2H_CONTROLLED_PROMOTION_REVIEW.md`,
`reports/V2_S2H_PROMOTION_RESULT.md`,
`reports/V2_S2H_ROLLBACK_RECORD.md`.

## Related tests/files

`src/scripts/build_v2_staging_index.py`,
`src/scripts/validate_v2_staging_index.py`,
`tests/test_build_v2_staging_index.py`,
`tests/test_validate_v2_staging_index.py`.

## Supersedes / Superseded by

Supersedes ad hoc collection switching and in-place promotion assumptions.
Superseded by: none.
