# ADR-018 - V2 Conversation and Multi-Subject Context

Status: Accepted

Date: 2026-08-05

## Context

V1.5 proved bounded follow-up behavior around one resolved product, but V2 must
support recent conversation context and zero, one, or many requested products
without silently selecting one global context owner. Prior assistant messages
can help interpret the conversation, but they are not current technical
evidence.

## Decision

1. Load at most the 10 most recent persisted user/assistant messages for the
   same conversation, in chronological order.
2. Preserve the literal current user question unchanged in persistence, API
   output, diagnostics, retrieval ownership, and the answer-model packet.
3. Treat prior messages as conversation context only. Retrieve and admit fresh
   DB/PDF evidence for every current turn.
4. Retain each requested product or reference separately with its resolution,
   candidates, DB evidence, PDF evidence, applicability, omissions, and
   model-context ownership.
5. Permit shared evidence to remain one canonical evidence record while naming
   every requested product that owns it.
6. Do not introduce a rolling summary, canonical rewritten question, hidden
   primary-subject state, or unrestricted memory.

## Alternatives considered

- Continue the V1.5 single-subject/effective-question model.
- Let the language model infer one primary subject from merged context.
- Persist a rolling conversation summary or unrestricted subject registry.

## Consequences

The model can see bounded conversational language while factual claims remain
tied to newly admitted evidence. Multi-product answers can be evaluated for
coverage and cross-subject attribution. Per-product balancing, bounded
enrichment rounds, and complete restart-safe subject metadata remain governed
V2 work rather than implicit behavior.

## Invariants

- The current literal question appears once and remains unchanged.
- Conversation history never crosses conversation IDs.
- Prior assistant text is not promoted to evidence.
- Every requested subject has an explicit coverage/omission record.
- Canonical source identity survives context, response, persistence, and reload.

## Evidence

`docs/V2_PRODUCT_CONTRACT.md`, `docs/ROADMAP_TO_INTERNAL_PRODUCTION.md`,
`src/conversation_history.py`, `src/requested_products.py`,
`src/multi_source_retrieval.py`, `src/unified_answer_context.py`.

## Related tests/files

`tests/test_conversation_history.py`,
`tests/test_requested_product_ownership.py`,
`tests/test_production_debug_contract.py`.

## Supersedes / Superseded by

Supersedes V1.5 follow-up guidance that depended on one active subject and an
internally rewritten effective question. Superseded by: none.
