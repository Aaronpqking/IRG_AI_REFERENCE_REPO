# IRG AI source retrieval — 2026-11-20

## Newly located original source snapshot
The historical private-source archive, identified in the local [source-binding ledger](../../source_reference/SOURCE_BINDINGS_20261120.json) as `irg_ai-main`, contains an actual Python `src/` tree, `tests/`, evaluation artifacts, technical documents, and archived reports. It was created in Drive on 2026-07-29, but its child timestamps are mixed. **Do not equate the Drive folder's creation date with the source version or a Git commit.** The source files are *not* necessarily all a consistent frozen Git checkout.

Eleven selected source/test files were read directly from Drive (**421,897 bytes total**), SHA-256 hashed, and parsed with Python's AST parser. No source code or private test cases were added to this public reference repository. The machine-readable [binding register](../../source_reference/SOURCE_BINDINGS_20261120.json) has the origin-record IDs, file paths, exact byte lengths and hashes. These IDs are provenance metadata only, not dependencies that Codex must resolve. **Original code is withheld and cannot be independently inspected or run from this public repository.**

## Static source observations
| Path | Directly observed symbol/line | Scope and limitation |
|---|---|---|
| `src/bootstrap/composition.py` | `build_runtime_components` lines 331–405; `build_evaluation_runtime` 422–423 | Shared composition entrypoints exist; no runtime composition invoked |
| `src/conversation_loop.py` | `run_conversation_turn` 262–759 | Turn orchestration exists, not claimed equivalent to current deployed service |
| `src/multi_source_retrieval.py` | `ControlledDiscoveryRetrievalService.retrieve` 271–573 and `_retrieve_multiple_products` 1160–1341 | Per-product retrieval code exists; no query run |
| `src/hybrid_retrieval.py` | `fuse_candidates` 555–634 and two channel `retrieve` methods | Hybrid candidate fusion code exists; no recall/precision conclusion |
| `src/unified_answer_context.py` | `assemble_answer_context` 274–409; `serialize_model_context` 507–517 | Serialized context stage exists; no evidence sufficiency conclusion |
| `src/context_serialization.py` | `serialize_context_v1` 48–70 | Explicit context serialization implementation exists |
| `src/v2_evaluator/scorers.py` | G01/G02/G03/G05/G06/G07/G18 scorers and `aggregate_gate_runs` | Implementation definitions exist; separately preserved owner approval verifies frozen evaluator implementation; release qualification remains unexecuted |
| Four selected `tests/` files | 10+27+28+65 = **130** test functions | Tests are readable/AST-valid, **not executed** as a historical suite |

File line ranges refer exclusively to this exact selected historical archive source snapshot; they are not guaranteed to correspond to October Git revisions. The 130 count is syntactic functions named `test_*`, **not a test pass count**.

## Source status upgraded
Previous state `SOURCE_UNAVAILABLE` was overly broad. Correct status is:

`SELECTED_SOURCE_AND_TESTS_AVAILABLE_IN_GOOGLE_DRIVE / SOURCE_COMMIT_AND_RUNTIME_BINDING_PENDING`.

All of these must remain separate:
1. Existence of source and test code in Drive: **VERIFIED**.
2. Byte identity of selected files: **VERIFIED** with SHA-256.
3. Cohesive checkout and commit binding: **NOT VERIFIED**.
4. Matching the V2 evaluator's dependency hashes: **NOT VERIFIED** except where checked explicitly.
5. Live runtime and test results: **NOT EXECUTED**.

## Next source validation
Obtain the original Git object tree or commit manifest (at minimum the historical audit SHA `b4f2fadab6b6645c1c5ad2093433a0041ff3e38a`, evaluator-bound source hash list, and the exact latest October serving revision). Compare every selected file to the bound versions, then inspect actual source tests at that revision. Do not force hash parity by changing frozen manifests.

No production, corpus, model, provider, database or source checkout was mutated.

## P0 portability classification
The local binding register and this report establish **externally checked provenance only** for the withheld historical code. This does not populate `source_reference/identity/`, `source_reference/retrieval/`, `source_reference/context/`, `source_reference/contracts/`, `source_reference/structural/`, `source_snapshot/`, or the curated historical tests. Thus strict P0 completeness remains blocked. Codex must not require the archive, a Google account, or the origin identifiers to follow the repository's current architecture. See [reference portability policy](../../governance/REFERENCE_PORTABILITY_POLICY.md).
