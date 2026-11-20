# ADR-012 - Observe-First Grounding

Status: Accepted

## Context

Grounding validation can be operationally useful before it is safe to mutate customer-visible answers.

## Decision

Default `GROUNDING_VALIDATION_MODE` to `observe`; support `off` and experimental `enforce`.

## Alternatives considered

Always enforce validation or disable validation entirely.

## Consequences

Diagnostics can surface grounding/citation failures without changing normal delivery unless enforce mode is selected.

## Invariants

Observe mode records findings; enforce mode may downgrade unsafe final responses.

## Evidence

`src/bootstrap/settings.py`, `src/grounding_mode.py`, `src/conversation_loop.py`.

## Related tests/files

`tests/test_citation_validation.py`, `tests/test_production_debug_contract.py`.

## Supersedes / Superseded by

Supersedes hard-coded post-model behavior. Superseded by: none.
