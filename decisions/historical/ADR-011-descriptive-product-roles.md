# ADR-011 - Descriptive Product Roles

Status: Accepted

## Context

Product role data helps explain whether a resolved subject is an appliance, base, mount, or related/supporting product.

## Decision

Use product roles as descriptive/applicability context only, not as answer authorization.

## Alternatives considered

Role-based permission gates or removing role context entirely.

## Consequences

Answers can explain relationship/applicability constraints while preserving evidence-first behavior.

## Invariants

Technical claims still require PDF evidence; role labels cannot prove compatibility.

## Evidence

`src/product_roles.py`, `src/multi_source_retrieval.py`, `src/answer_synthesis_policy.py`.

## Related tests/files

`tests/test_product_roles.py`, `tests/test_production_debug_contract.py`.

## Supersedes / Superseded by

Supersedes role-derived technical permission. Superseded by: none.
