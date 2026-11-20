# ADR-015 - API, CLI, and Evaluation Parity

Status: Accepted

## Context

The system has user-facing API, developer CLI, and evaluation workflows that must not drift.

## Decision

Use shared `ChatService` and composition roots for API, CLI, and production-path evaluation.

## Alternatives considered

Separate bespoke evaluation path or frontend-local chat behavior.

## Consequences

Evaluation can verify actual production chat behavior while keeping eval data isolated.

## Invariants

Frontend chat calls the Python backend. Production-path eval uses isolated stores and the same service turn contract.

## Evidence

`src/api_server.py`, `src/scripts/conversation_cli.py`, `src/scripts/run_unified_answering_eval.py`, `frontend/utils/api/irgAiClient.js`.

## Related tests/files

`tests/test_api_server.py`, `tests/test_conversation_cli.py`, `tests/test_production_debug_contract.py`.

## Supersedes / Superseded by

Supersedes docs claiming no Python HTTP API or frontend backend call. Superseded by: none.
