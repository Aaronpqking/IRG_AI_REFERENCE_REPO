# ADR-001 - Thin Hexagonal Architecture

Status: Accepted

## Context

The repository has explicit ports in `src/ports.py`, adapters under `src/adapters/`, and boundary tests that reject external SDK imports from core files.

## Decision

Keep transport and use-case code thin. Core behavior depends on port protocols and runtime contracts; concrete OpenAI, Qdrant, MySQL, PDF, and filesystem details remain in adapters or composition/operator scripts.

## Alternatives considered

Direct SDK calls in routes, a service locator, or a framework-specific dependency graph.

## Consequences

The API remains simple, testable, and framework-independent. Operator scripts may still instantiate adapters directly when the script itself is the composition boundary.

## Invariants

Routes do not call OpenAI, Qdrant, or product MySQL directly. Core files do not import concrete adapters or external SDKs.

## Evidence

`src/ports.py`, `src/api_server.py`, `src/chat_service.py`, `src/bootstrap/composition.py`, `tests/test_core_boundaries.py`.

## Related tests/files

`tests/test_core_boundaries.py`, `tests/test_hexagonal_contract_restoration.py`.

## Supersedes / Superseded by

Supersedes V1 docs that referred to `src/chat.py` as the service boundary. Superseded by: none.
