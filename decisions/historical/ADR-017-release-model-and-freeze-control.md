# ADR-017: Release Model and Freeze Control

Status: Accepted

Date: 2026-07-31

## Context

The accepted V1 runtime commit, its final closeout commit, the current committed
branch head, and the integrated V1.5 dirty tree are distinct states. Treating
the dirty tree as a release would lose path ownership, artifact identity,
rollback clarity, and the difference between engineering proof and production
readiness.

## Decision

1. Preserve V1 as the historical PDF/manual baseline. Do not rewrite its final
   closeout.
2. Freeze V1.5 only from an explicit staging allowlist reviewed before commit.
3. Exclude secrets, ignored local data, temporary files, generated evaluation
   outputs, unrelated work, and V2-only implementation.
4. Record the staged manifest, exclusions, uncertainties, cached diff,
   configuration, artifact fingerprints, verification, proposed message/tags,
   and rollback ref before creating a release commit.
5. Use annotated immutable tags. Never move a release tag.
6. Keep business milestones separate from conventional versions: V1=`0.1.0`,
   V1.5=`0.2.0`, V2=`0.3.0`, V2.5=`0.9.0`, V3=`1.0.0`.
7. Close V1.5 as `PASS_WITH_WATCH` and an internal-pilot candidate, not as
   production ready.
8. Gate V2, V2.5, and V3 with the numerical contracts in
   `V2_PRODUCT_CONTRACT.md` and `ROADMAP_TO_INTERNAL_PRODUCTION.md`.

## Consequences

The V1.5 release commit can be reproduced and rolled back without silently
including generated or unrelated state. Remaining work is visible in one WATCH
register. Future changes target an explicit milestone instead of modifying the
meaning of a closed release.

## Reversal condition

Supersede this ADR only with an approved release-management system that retains
the same historical, artifact, review, gate, and rollback guarantees.
