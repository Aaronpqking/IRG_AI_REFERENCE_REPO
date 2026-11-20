# ADR-003 - Versioned Runtime Contracts

Status: Accepted

## Context

Responses, sources, runtime metadata, and model context need additive compatibility across API, CLI, frontend, and evaluation.

## Decision

Use `hexagonal.v1`, `sources.v2`, `context.v1`, and `phase0.v1` as current contract versions.

## Alternatives considered

Unversioned dictionaries or one monolithic response schema.

## Consequences

Changes must preserve compatibility or bump the relevant version. Debug payloads may be richer than the serialized model input.

## Invariants

`answer_sources` and `candidate_basis` remain separate. Model-facing serialization remains `context.v1`.

## Evidence

`src/runtime_contracts.py`, `src/chat_contracts.py`, `src/unified_answer_context.py`, `src/source_serialization.py`.

## Related tests/files

`tests/test_answer_contract.py`, `tests/test_source_serialization.py`, `tests/test_runtime_metadata_migration_compatibility.py`.

## Supersedes / Superseded by

Supersedes unversioned V1 response descriptions. Superseded by: none.
