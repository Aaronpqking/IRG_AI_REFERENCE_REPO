# ADR-007 - Identity Locking and Follow-Ups

Status: Accepted

## Context

Support conversations include short follow-ups such as "why" or "what about that one" after a resolved product subject.

## Decision

Store bounded conversation product context in controlled retrieval and use recent turns plus active subject/topic to rewrite follow-up questions.

## Alternatives considered

Treat every turn as stateless or pass full conversation history to the model.

## Consequences

Follow-ups can retain exact subject scope without unbounded customer history in model input.

## Invariants

Only recent bounded turn context and active product context can affect follow-up rewriting.

## Evidence

`src/multi_source_retrieval.py`, `src/conversation_loop.py`, `src/unified_answer_context.py`.

## Related tests/files

`tests/test_production_debug_contract.py`, `tests/test_conversation_loop.py`.

## Supersedes / Superseded by

Supersedes stateless chat-turn-only assumptions. Superseded by: none.
