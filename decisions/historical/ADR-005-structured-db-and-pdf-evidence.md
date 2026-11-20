# ADR-005 - Structured DB and PDF Evidence

Status: Accepted

## Context

Product identity and catalog context come from the product read model. Technical facts come from approved PDF chunks.

## Decision

Keep structured database evidence and vectorized PDF evidence as separate source classes in context, provenance, and frontend rendering.

## Alternatives considered

Vectorizing all product facts as PDF-like evidence or treating database facts as file sources.

## Consequences

Database sources can support identity/catalog claims without fake page links. PDF sources remain required for technical claims.

## Invariants

Do not attribute database facts to manuals. Do not use catalog fields to prove unverified compatibility.

## Evidence

`src/unified_answer_context.py`, `src/product_applicability.py`, `src/source_serialization.py`, `src/product_db_contract.py`.

## Related tests/files

`tests/test_frontend_source_contract.py`, `tests/test_production_debug_contract.py`, `tests/test_product_db_contract.py`.

## Supersedes / Superseded by

Supersedes PDF-only architecture claims. Superseded by: none.
