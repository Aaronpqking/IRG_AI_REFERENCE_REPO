# Identity and authority historical source — publication triage

**Date:** 2026-11-20  
**Evidence class:** `EXTERNALLY_VERIFIED_NOT_LOCAL`  
**Decision:** `PUBLICATION_BLOCKED_PENDING_HUMAN_REVIEW`  
**Machine-readable provenance:** [IDENTITY_SOURCE_TRIAGE_20261120.json](IDENTITY_SOURCE_TRIAGE_20261120.json)

## Exact original source read, without publication
Eight original historical Python files were read from the authorized private archive and examined without modifying their bytes: five implementation modules (`query_identity`, `query_normalization`, `source_identity`, `document_applicability`, `product_discovery`) and three behavior-test modules (identifier inventory, source identity registry, document applicability identity).

**All eight parsed with Python AST**. Total original bytes: **138,849**; all eight newly computed SHA-256 fingerprints are recorded from their *actual fetched source bytes*, without comparison to an independent prior frozen digest in the adjacent local ledger. **24 syntactic test functions** were identified in the three selected test files; these tests were **not executed**. A file's test count is not evidence of passing behavior.

| Mechanism | Source-bound observations | Reproducibility limit |
|---|---|---|
| Query identity | `QueryIdentifier`, `QueryIdentity`, `normalize_identifier`, `parse_query_identity` are defined | No frozen Git revision or attached behavior run |
| Query normalization | `NormalizedQuestion` and `normalize_question` are defined | No current-runtime parity inference |
| Approved source identity | `ApprovedSourceRegistry`, `SourceIdentity`, `SourceMatch`, `canonical_corpus_path`, `sources_match` are defined | Approved manifest and runtime data not bound |
| Document applicability | `DocumentApplicability`, `assess_document_applicability`, document identifier/conflict utilities are defined | No operational enforcement claim |
| Product discovery | `DiscoveryQuery`, `ProductCandidate`, `CandidateResolution`, `resolve_candidates` are defined | No retrieval or product DB execution |
| Three historical test modules | Tests explicitly cover identifier collisions, source path authority, cross-brand mismatch and incorrect product protection | Test existence != execution or pass |

## Security and publication boundary
A **heuristic static text scan** of the eight files found no syntactically obvious literal credential assignments, email addresses, or local `C:\\Users` paths. This scan is not a secrets, intellectual-property, dependency-license, privacy, data-flow, or indirect-data review; it cannot authorize publication. In particular, unit-test literals and product/brand fixtures need human screening, and internal implementation code requires an explicit disclosure decision.

No original source file was copied to the public reference repository. No rewritten representative source, synthetic test or stub was substituted. `source_reference/identity/`, `source_snapshot/`, and the historical behavior-test publication gates **remain incomplete**.

## Required before original source transfer
1. Verify file and fixture rights and explicit public Git publication approval, with reviewer/date/evidence; validate that test-data literals do not expose private product/customer/employee/internal data.
2. Bind the original files to a historical source revision or classify the checkout as `VERSION_UNBOUND`. Never infer a Git SHA from a folder name or timestamp.
3. Stage selected unmodified originals or narrowly redacted originals only after approval. A redaction must not change behavior, and needs original path, source SHA-256, source/local byte counts and SHA-256, redaction diff and coverage disposition.
4. Execute relevant original behavior tests in an authorized isolated environment and record exact passes, failures, skips and dependency closure. Absence of a coherent checkout remains a blocker.
5. Keep `IRG-X001` and late October/November empirical qualification separate; identity source publication does not resolve them.

## Outcome
This slice establishes *what can be located and authenticated in the identity family*, while explicitly deferring source publication and clean-build promotion. It does not claim P0 completion.
