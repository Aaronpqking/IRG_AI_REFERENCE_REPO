# ADR-006 - Exact Identifier Precedence

Status: Accepted

## Context

Broad Boolean product search can produce ambiguous candidates when model/MPN/UPC identifiers are present.

## Decision

Run exact normalized identifier lookup before broad stored-procedure discovery.

## Alternatives considered

Only broad Boolean stored-procedure search, or post-filtering broad results.

## Consequences

Exact product questions get a distinct lane. Broad fallback remains active when exact lookup returns no rows.

## Invariants

Exact lookup must be parameterized, bounded, read-only, and traceable.

## Evidence

`src/adapters/product_mysql.py`, `src/product_discovery.py`, `src/query_identity.py`.

## Related tests/files

`tests/test_two_lane_product_discovery.py`, `tests/test_identifier_retrieval.py`, `tests/test_product_db_contract.py`.

## Supersedes / Superseded by

Supersedes broad-only product search behavior. Superseded by: none.
