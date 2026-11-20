# ADR-010 - Remove Answer-Permission Flags

Status: Accepted

## Context

Historical docs referenced answer-permission flags and role-gated technical-answer authorization.

## Decision

Treat active answer-permission flags as superseded. Current runtime uses response class, evidence status, grounding validation mode, final response disposition, citation validation, and response origin.

## Alternatives considered

Retain answer permission as a first-class gate.

## Consequences

Docs and evals must not describe hidden permission flags as current runtime behavior.

## Invariants

Grounding diagnostics may observe or enforce final response disposition; product roles do not authorize answers.

## Evidence

`src/conversation_loop.py`, `src/final_response_disposition.py`, `src/grounding_mode.py`, `docs/IMPLEMENTATION_HISTORY.md`.

## Related tests/files

`tests/test_production_debug_contract.py`, `tests/test_identity_resolution_evidence_gate.py`.

## Supersedes / Superseded by

Supersedes historical answer-permission docs and role-authorization gates. Superseded by: none.
