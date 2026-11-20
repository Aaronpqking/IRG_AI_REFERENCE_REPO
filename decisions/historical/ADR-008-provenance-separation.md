# ADR-008 - Provenance Separation

Status: Accepted

## Context

Candidate discovery explains how products were found; answer sources explain what supported the delivered answer.

## Decision

Keep `candidate_basis` separate from `answer_sources`.

## Alternatives considered

Expose all candidates as sources or omit discovery provenance.

## Consequences

Frontend and evaluation can show source cards without confusing discovery candidates with cited answer evidence.

## Invariants

Citation validation uses answer sources. Candidate basis is diagnostic/discovery provenance.

## Evidence

`src/chat_contracts.py`, `src/chat_service.py`, `src/source_serialization.py`, `src/citation_validation.py`.

## Related tests/files

`tests/test_answer_contract.py`, `tests/test_citation_validation.py`, `tests/test_frontend_source_contract.py`.

## Supersedes / Superseded by

Supersedes source-list-only response contracts. Superseded by: none.
