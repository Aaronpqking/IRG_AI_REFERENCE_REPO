# ADR-016 - SQL Stored Procedure and Direct Query

Status: Accepted

## Context

The product read model needs both broad discovery and exact identifier lookup.

## Decision

Use stored procedures for broad product discovery and direct parameterized SQL for exact identifier lookup and procedure/server metadata verification.

## Alternatives considered

Stored procedures only, direct SQL only, or broad Boolean search without exact lookup.

## Consequences

The actual architecture is mixed. Docs must not describe stored procedures as the only product-data access path.

## Invariants

All product SQL must be read-only, parameterized where values are supplied, bounded, allowlisted, and traceable without exposing credentials.

## Evidence

`src/adapters/product_mysql.py`, `src/product_db_contract.py`, `src/scripts/inspect_flamy_product_source.py`.

## Related tests/files

`tests/test_product_db_contract.py`, `tests/test_two_lane_product_discovery.py`.

## Supersedes / Superseded by

Supersedes stored-procedure-only product DB architecture claims. Superseded by: none.
