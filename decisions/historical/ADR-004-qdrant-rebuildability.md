# ADR-004 - Qdrant Rebuildability

Status: Accepted

## Context

Qdrant stores searchable vectors, but corpus authority lives in approved local artifacts.

## Decision

Treat Qdrant as rebuildable index state over `data/chunks.jsonl`, not as source-of-truth content.

## Alternatives considered

Treating Qdrant payloads as corpus authority.

## Consequences

Rebuild and ingestion scripts validate chunks and require explicit flags before destructive indexing. Corpus and Qdrant reconciliation remains auditable.

## Invariants

Dry runs must not mutate Qdrant. Recreate requires explicit confirmation.

## Evidence

`src/scripts/rebuild_qdrant.py`, `src/scripts/ingest_pdfs.py`, `src/ingest.py`, `src/adapters/vector_qdrant.py`.

## Related tests/files

`tests/test_rebuild_qdrant_script.py`, `tests/test_ingest_pdfs_script.py`, `tests/test_rebuild_qdrant_flow.py`.

## Supersedes / Superseded by

Supersedes any description of Qdrant as the corpus source of truth. Superseded by: none.
