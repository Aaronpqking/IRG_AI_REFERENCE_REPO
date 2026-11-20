# Historical source snapshot — disposition and binding limitations

**Date:** 2026-11-20  
**Snapshot status:** `BLOCKED_COHERENT_CHECKOUT_UNAVAILABLE`  
**Permitted P0 alternative:** explicit documented reason no sanitized full historical source snapshot is published.  
**Reference authority:** Selected exact original source files are individually preserved, SHA-256 bound, and readable locally under `source_reference/`. They are **not** a complete or coherent historical checkout.

## Why an exact source snapshot cannot be certified

The historical `irg_ai-main` private archive includes selected original `src/`, `tests/`, `reports/`, and `docs/` files, but does not establish an immutable source Git commit, tree hash, synchronized checkout, dependency lock, or freeze manifest binding every file to the same runtime state. Archive timestamps and names cannot substitute for a Git tree. Selected structural files span separate milestones, not a single deployed runtime.

Publishing a synthetic tree assembled from the archive would misrepresent historical architecture, execution and test closure. A full copy would also risk disclosing unreviewed internal implementation, private conversations, sensitive fixtures, raw operational corpus, generated vectors and evaluation gold. The reference repository is public.

## Locally available exact source families

- `source_reference/identity/`: selected original source implementations. Historical identity test originals under `tests_reference/historical/identity/`. Exact source-to-local SHA-256 in `governance/publication_reviews/IDENTITY_SOURCE_TRIAGE_20261120.json`.
- `source_reference/retrieval/`: exact original retrieval mechanisms and `TRANSFER_MANIFEST.json`.
- `source_reference/context/`: exact original context and grounding mechanisms and `TRANSFER_MANIFEST.json`.
- `source_reference/contracts/`: original runtime/adapter/composition contracts and `TRANSFER_MANIFEST.json`.
- `source_reference/structural/`: selected original structural milestones and `TRANSFER_MANIFEST.json`.
- `tests_reference/historical/behavior/`: selected original behavior tests and `TRANSFER_MANIFEST.json` when landed.

Do **not** interpret these paths as one importable or executable application tree. Each transfer declares `original_git_revision: UNKNOWN` where the exact historical binding remains unavailable.

## Required conditions to replace this exception

1. Recover a historical Git commit SHA **and** its original tree or immutable fully hashed artifact bundle, with source and test provenance.
2. Reconcile file-byte digests against that bound tree and note any candidate mismatch.
3. Review public publication rights and remove sensitive files using explicit, reproducible classification; preserve source semantics when redaction is possible.
4. Provide reproducible environment closure and execute the original suite in the permitted isolated mode, without touching production.
5. Record the new snapshot hash/tree manifest and replace this intentional-unavailability notice only with directly verified evidence.

## What this exception does and does not satisfy

This file satisfies the **documentation alternative** for the source snapshot directory. It does **not** satisfy the absent coherent source Git commit, historical test execution, full corpus reproducibility, frozen evaluator reconciliation or strict release completion. `IRG-X001` remains `REVISION_CHAIN_INCOMPLETE`; no frozen document is modified.

**Disposition:** `SNAPSHOT_UNAVAILABLE_DOCUMENTED / NOT_A_RUNTIME_SOURCE_OF_TRUTH`.
