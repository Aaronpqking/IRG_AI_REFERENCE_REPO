# ADR-014 - Failure Taxonomy

Status: Accepted

## Context

Runtime and evaluation failures need stable categories for triage.

## Decision

Use pipeline failure stages for runtime errors and explicit failure categories in evaluation reports.

## Alternatives considered

Single low-confidence or generic failure labels.

## Consequences

Failures can be separated into product discovery, PDF retrieval, model, citation, persistence, evaluator, corpus, and service classes.

## Invariants

Customer-visible runtime failures use a safe generic response; diagnostics retain the sanitized stage/category.

## Evidence

`src/runtime_contracts.py`, `src/conversation_loop.py`, `src/scripts/run_unified_answering_eval.py`.

## Related tests/files

`tests/test_production_debug_contract.py`, `tests/test_unified_answering_eval_runner.py`.

## Supersedes / Superseded by

Supersedes aggregate-only pass/fail reporting. Superseded by: none.
