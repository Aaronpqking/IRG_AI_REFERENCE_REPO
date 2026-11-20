# ADR-002 - Composition Roots

Status: Accepted

## Context

HTTP API, CLI, and evaluation need consistent adapter wiring while preserving offline smoke mode.

## Decision

Use `src/bootstrap/composition.py` for primary runtime composition. It loads environment, builds stores, selects offline or online adapters, and conditionally adds controlled retrieval.

## Alternatives considered

Per-route adapter construction or separate CLI/API/eval wiring.

## Consequences

Runtime parity is easier to verify. Configuration failures surface at startup or first service use.

## Invariants

API and CLI build `ChatService` through runtime components. Online mode requires OpenAI and Qdrant config.

## Evidence

`src/bootstrap/composition.py`, `src/api_server.py`, `src/scripts/conversation_cli.py`, `src/scripts/run_unified_answering_eval.py`.

## Related tests/files

`tests/test_api_server.py`, `tests/test_conversation_cli.py`, `tests/test_unified_answering_eval_runner.py`.

## Supersedes / Superseded by

Supersedes scattered V1 wiring guidance. Superseded by: none.
