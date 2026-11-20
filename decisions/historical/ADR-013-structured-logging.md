# ADR-013 - Structured Logging

Status: Accepted

## Context

Operational diagnosis needs request IDs, pipeline stages, failure categories, and sanitized payloads.

## Decision

Use structured logging events and request context for API and chat pipeline diagnostics.

## Alternatives considered

Plain print traces or ad hoc exception dumps.

## Consequences

Logs are easier to correlate and safer to inspect. Debug payloads remain gated and sanitized.

## Invariants

Do not log credentials or unsanitized records. Carry request IDs through API, pipeline, diagnostics, and metadata.

## Evidence

`src/structured_logging.py`, `src/api_server.py`, `src/conversation_loop.py`, `src/debug_contract.py`.

## Related tests/files

`tests/test_production_debug_contract.py`, `docs/LOGGING_POLICY.md`.

## Supersedes / Superseded by

Supersedes print-based runtime diagnosis. Superseded by: none.
