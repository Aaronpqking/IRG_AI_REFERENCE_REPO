# ADR-009 - Model Consistency

Status: Accepted

## Context

Previous snapshots described deterministic clarification/block paths as normal answer behavior. Current code calls the model on successful answer paths and reserves deterministic output for runtime failure or validation disposition.

## Decision

Successful answer paths call `ChatModelPort.answer`. `response_origin` records whether the delivered response came from the model, validation safe response, or deterministic runtime failure.

## Alternatives considered

Pre-model deterministic answers for ambiguous or low-confidence states.

## Consequences

Model-called diagnostics are auditable and stale model metadata cannot be reused.

## Invariants

Runtime failure paths set `model_called=false`; successful paths record model metadata.

## Evidence

`src/conversation_loop.py`, `src/adapters/chat_openai.py`, `src/debug_contract.py`.

## Related tests/files

`tests/test_chat_openai_adapter.py`, `tests/test_production_debug_contract.py`, `tests/test_chat_answer_fidelity.py`.

## Supersedes / Superseded by

Supersedes active deterministic answer-permission routing. Superseded by: none.
