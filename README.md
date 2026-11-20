# IRG AI Reference Repository — Evidence and Architecture

**Snapshot:** 2026-11-20. **Status:** P0 initial seed, review branch, NOT fully qualified.

This is a historical/reference repository for the clean-lab implementation, not the implementation runtime. The clean implementation has no dependency on this repository.

**Codex reading order:** [REFERENCE_INDEX](REFERENCE_INDEX.md) → [CURRENT_REFERENCE_STATE](CURRENT_REFERENCE_STATE.md) → [CLAIM_REGISTER.jsonl](CLAIM_REGISTER.jsonl) / [EXPERIMENT_REGISTER](evaluation/EXPERIMENT_REGISTER.md) → original historical evidence.

## Authority

Immutable empirical run artifacts (only when transferred and hash-verified) > source/tests bound to revision > accepted decisions > current synthesis > historical status summaries > plans/experimental designs > archive. No filename, including FINAL or CURRENT, grants authority. See [REFERENCE_POLICY](REFERENCE_POLICY.md). In this first seed, **original frozen run payloads are not yet verified**; pointers and historical summaries are not substituted for those artifacts.

## Evidence classes

- `evaluation/frozen/`: must contain byte-verified, immutable run data only; currently pending original transfers.
- `architecture/historical/`, `evaluation/historical/`, `governance/historical/`, `timeline/evidence/`: source text copied from Drive, clearly labeled historical and not a current runtime claim.
- `source_reference/`: examples and future selected implementation evidence; never copy wholesale into the clean build.
- `archive/`: deprecated plans and documentation, never current design authority.
- Root and thematic Markdown: present intellectual synthesis and conditional guidance.

## Status and safe handling

Consult [P0_SEED_LEDGER](P0_SEED_LEDGER.md) for incomplete original frozen evidence, source/tests, hashes, and late-case verification. This is a **public GitHub repository**: no private customer/employee/conversation records, credentials, internal connection traces, or raw operational files. No model, corpus, index, deployment, or source implementation mutation occurred during this seed.
