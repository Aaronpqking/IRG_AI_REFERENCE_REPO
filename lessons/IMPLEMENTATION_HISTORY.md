# IRG AI Implementation History

This document preserves historical slice evidence separately from the current technical manual. Status labels:

- `CURRENT`: still describes active implementation.
- `SUPERSEDED`: replaced by later code or architecture.
- `PARTIALLY_SUPERSEDED`: some pieces remain true, but the framing changed.
- `HISTORICAL_EVIDENCE`: useful evidence for prior decisions, not current-state proof by itself.
- `OPERATOR_REPORTED`: live result reported by an operator or preserved artifact, not rerun in the current audit.
- `BLOCKED`: stopped by approval, environment, or policy.
- `FAILED`: gate failed.
- `PASS_WITH_WATCH`: passed with explicit watch items.

## MS1/MS2 Governance and Corpus

### MS2 Readiness and Corpus Governance - `PARTIALLY_SUPERSEDED`

- Established approved-PDF governance, traceable chunks, manifest validation, and readiness gates.
- Current authoritative source: `src/ingest.py`, `src/technical_text.py`, `data/manifest.json`, `data/chunks.jsonl`, `tests/test_manifest_shape.py`, `tests/test_approved_pdfs_snapshot.py`.
- Superseded framing: early readiness reports described the system mainly as a PDF retrieval/indexing pipeline. Current architecture is multi-source context assembly and applicability.

## MS3 Adapters and Indexing

### MS3-S1 Adapter-Only Pass - `CURRENT`

- Added OpenAI embedding adapter and Qdrant vector adapter behind ports.
- Preserved no import-time client construction and source-traceable payloads.
- Historical test evidence: `83 passed, 2 skipped`.
- Current authoritative source: `src/adapters/embeddings_openai.py`, `src/adapters/vector_qdrant.py`, `tests/test_openai_embedding_adapter.py`, `tests/test_qdrant_vector_adapter.py`.

### MS3-S2 Rebuild Qdrant Script - `CURRENT`

- Added `python -m src.scripts.rebuild_qdrant`.
- Dry-run validates `data/chunks.jsonl` without OpenAI or Qdrant.
- Recreate requires explicit `--confirm-recreate`.
- Historical dry-run evidence: `chunk_count=6084` at that time.
- Current refresh dry-run evidence: `chunk_count=4173`, `collection_name=AOG-TE`, `status=dry_run_valid`.
- Current authoritative source: `src/scripts/rebuild_qdrant.py`, `src/ingest.py`.

## MS4 Retrieval and Evaluation

### MS4-S1 Conditional P3 Smoke Gate - `BLOCKED`

- Live smoke was blocked before execution because corpus text egress to OpenAI and Qdrant writes required approval.
- Current resolution: live commands remain approval-gated; dry-runs are safe.

### MS4-S1R Synthetic Smoke - `HISTORICAL_EVIDENCE`

- Synthetic non-corpus text proved infrastructure path against a smoke collection.
- Did not unlock corpus evidence or production readiness.
- Current authoritative source: adapter and integration test gates, not the synthetic result alone.

### MS4-S1R6 Golden Eval Calibration and Version Policy - `PARTIALLY_SUPERSEDED`

- Added accepted sources/pages, exact-year behavior, failure classes, and better identifier extraction.
- Historical operator baseline: 20 questions, 11 passed, 9 failed.
- Superseded by later expanded datasets and MS6 evaluation layers.
- Current authoritative source: `data/golden_questions.jsonl`, `src/golden_policy.py`, `src/eval_gates.py`, `src/scripts/eval_golden.py`.

### MS4-S1R7 Final Retrieval Failure Fixes - `PARTIALLY_SUPERSEDED`

- Fixed GR18A catalog-vs-manual ranking and adjacent chunk answer-term checks.
- Historical operator evidence: 20 questions, 18 passed, 2 failed.
- Current relevance: path/year/identifier scoring remains important, but hybrid and controlled retrieval add newer paths.

### MS4-S1R8 Controlled Smoke Chat Eval - `FAILED`

- Added `--chat-eval`; retrieval-only stayed default.
- Historical full live chat result: 20 run, 11 passed, 9 failed.
- Superseded framing: current evaluation separates retrieval, context, applicability, and answer fidelity.

### MS4-S1R9 Chat Answer Term Fidelity - `FAILED`

- Hardened prompt expectations around exact technical terms.
- Historical full live result: 20 run, 8 passed, 12 failed.
- Current authoritative source: `src/chat_prompt_contract.py`, `src/scripts/run_unified_answering_eval.py`, and focused MS6-S5 validation.

## MS5 API, UI, and Persistence

### MS5-S1 P5-T3 Chat API Contract and CLI UX Harness - `CURRENT`

- Added `src/chat_contracts.py` and `src/chat_service.py`.
- Conversation CLI uses the same service boundary as API/eval paths.
- JSON and MySQL stores implement conversation persistence surfaces.
- Historical live smoke found multi-turn recall weakness.
- Current authoritative source: `src/chat_service.py`, `src/scripts/conversation_cli.py`, `src/adapters/conversation_store_json.py`, `src/adapters/conversation_store_mysql.py`.

### MS5-S1 P5-T4A Thin HTTP API and Frontend Wiring - `CURRENT`

- Added `src/api_server.py`, `/health`, conversation start, chat turn, load conversation, feedback, and end routes.
- Frontend client `frontend/utils/api/irgAiClient.js` calls the Python API.
- Current refresh verified `npm run lint` and `npm run build` pass.

### MS5-S1 Documentation Handoff Alignment - `SUPERSEDED`

- Older statement: "no Python HTTP API exists yet" and "frontend chat shell is local-state only."
- Current source: `src/api_server.py`, `frontend/utils/api/irgAiClient.js`, `frontend/components/chat/chatShell.js`.
- Resolution: HTTP API and frontend wiring now exist; older handoff wording is historical.

## MS6 Product Discovery, Multi-Source Context, and Evidence-Grounded Synthesis

### MS6-S2 Product DB Authority - `PASS_WITH_WATCH`

- Established controlled product DB discovery and authority boundaries.
- Product DB access is through allowlisted stored procedure calls and approved field handling.
- Watch item: credential grants and upstream read-model authority remain operator/live concerns unless reverified.
- Current authoritative source: `src/adapters/product_mysql.py`, `src/product_db_contract.py`, `tests/test_product_db_contract.py`.

### MS6-S3 Multi-Source Retrieval - `CURRENT`

- Added controlled retrieval orchestration, source selection, product DB plus PDF evidence, and route labels.
- Current authoritative source: `src/multi_source_retrieval.py`, `src/source_selection.py`, `tests/test_unified_answering.py`.

### MS6-S4 Product Context and Unified Answering - `PARTIALLY_SUPERSEDED`

- Added product-context construction, information-needs analysis, DB/PDF context assembly, document applicability, customer-safe DB answering, and debug-gated diagnostics.
- Product-context assembly and document applicability remain active.
- Product-role-based applicability framing was superseded by MS6-S5R3.
- Current authoritative source: `src/product_applicability.py`, `src/document_applicability.py`, `src/information_needs.py`, `src/unified_answer_context.py`, and `src/answer_synthesis_policy.py`.

### MS6-S5R1 Hybrid PDF Candidate Retrieval - `CURRENT`

- Added hybrid candidate retrieval with exact identifier, lexical, metadata filter, and semantic vector channels.
- Uses reciprocal rank fusion and diagnostic reporting.
- **SUPERSEDED configuration detail:** the original implementation was
  feature-flagged by `HYBRID_PDF_RETRIEVAL_ENABLED`; hybrid retrieval is now
  unconditional in the controlled multi-source path.
- Current authoritative source: `src/hybrid_retrieval.py`, `tests/test_hybrid_pdf_retrieval.py`.

### MS6-S5R2 Retrieval/Evaluation Parity - `PARTIALLY_SUPERSEDED`

- **HISTORICAL:** Corrected production-path retrieval diagnostics and separated candidate recall, evidence recall, selected evidence correctness, the then-current answer-permission metric, and answer correctness.
- Current relevance remains in evaluator design and diagnostics.
- Current authoritative source: `src/scripts/eval_hybrid_retrieval.py`, `src/scripts/run_unified_answering_eval.py`, `src/multi_source_retrieval.py`.

### MS6-S5R2 Evidence-First Post-Assembly Applicability - `PARTIALLY_SUPERSEDED`

- Replaced the earlier coarse product-role gate with a post-assembly applicability and answer-mode contract.
- Preserved exact-subject resolution, rich product context, corpus-neighbor expansion, and shared context assembly.
- Introduced deterministic relationship, related-product, and targeted clarification behavior.
- These deterministic routing and product-role decision concepts were subsequently removed by MS6-S5R3.
- Retained value:
  - exact subject retention;
  - assemble-before-permission ordering;
  - rich product context;
  - evidence provenance;
  - production/evaluation observability.
- Superseded value:
  - product-role infrastructure;
  - role-aware applicability state machine;
  - bounded product answer modes;
  - deterministic relationship fallback;
  - deterministic related-product fallback.

### MS6-S5R3 Remove Product-Role Infrastructure and Deterministic Fallback - `HISTORICAL - BLOCK CLEARED BY LATER LIVE EVIDENCE`

- Removed `product_role` from production and evaluator decision surfaces.
- **SUPERSEDED:** Removed the former product-role technical-answer permission.
- Removed role-visible focused scoring.
- Removed deterministic relationship and related-product fallback routing.
- Removed production use of `focused_clarification()`.
- Exact subject identity, document applicability, source integrity, fuel, year, generation, and fitment protections remain.
- Normal resolved cases with eligible evidence now proceed to model synthesis.
- Generic fallback remains only for:
  - no eligible context;
  - model failure;
  - empty model response;
  - validation fallback.
- Added response-execution reporting:
  - `response_origin`;
  - `model_called`;
  - `model_name`;
  - `fallback_reason`;
  - `fallback_function`;
  - `model_error`.
- Product context now distinguishes:
  - `category_context`;
  - `ordered_category_paths`;
  - `category_metrics`;
  - `catalog_attributes`;
  - `derived_relationship_context`;
  - `explicit_product_relationships`.
- Explicit relationships require structured mapping fields. Ordinary attributes are not promoted to explicit mappings.
- Removal audit returned no matches for role and deterministic-router terms.
- Focused tests: `87 passed, 1 warning`.
- Maintained tests: `479 passed, 6 skipped, 1 warning`.
- Best complete live post-removal run:
  - 11/11 executed;
  - 11/11 response origin `MODEL`;
  - deterministic fallback count 0;
  - validation fallback count 0;
  - direct technical 5/5;
  - related-product technical 3/3;
  - relationship 2/3 under the then-current strict expectation.
- Final clean verification after the last code and expectation change could not execute because the embedding stage returned `RetrievalStageError: EMBEDDING_FAILED`.
- Decision at that time: `BLOCKED_ON_LIVE_EMBEDDING_VERIFICATION`.
- Later evidence: the authorized July 23 five-case Mode B rerun passed 5/5,
  and later V2 bounded online validation passed 6/6 before controlled corpus
  promotion. These later artifacts clear the historical live-execution block
  without rewriting the original failed/blocked runs.
- Coverage gap: no new case proves that a product previously excluded by role now receives a direct technical model answer.

## Historical Conflict Map

| Statement | Older Source | Current Source | Resolution |
| --- | --- | --- | --- |
| The system is a PDF retrieval pipeline. | early technical manual and MS3/MS4 logs | controlled retrieval/context modules | Superseded by multi-source context assembly and applicability. |
| No Python HTTP API exists yet. | July 3 documentation handoff entry | `src/api_server.py` | Superseded; thin HTTP API exists. |
| Frontend chat is local-state only. | July 3 documentation handoff entry | `frontend/utils/api/irgAiClient.js`, `frontend/components/chat/chatShell.js` | Superseded; frontend calls backend API. |
| Product role remains as deprecated diagnostic metadata. | MS6-S5R2 documentation | MS6-S5R3 removal audit and active code | Superseded; remaining role infrastructure was removed. |
| Post-assembly applicability uses role-aware states and answer modes. | MS6-S5R2 architecture | MS6-S5R3 | Superseded; active path uses evidence eligibility, model synthesis, and generic fallback. |
| Relationship cases may pass via deterministic clarification. | MS6-S5R2 evaluator/runtime | MS6-S5R3 focused dataset and execution reporting | Superseded; B/C cases require model origin and model invocation. |
| Category attributes can be explicit product relationships. | older applicability construction | MS6-S5R3 product context semantics | Superseded; ordinary attributes produce derived relationship context only. |
| AOG24-GA has a proven ordered category hierarchy or explicit mapping. | desired architecture/task assumptions | observed approved read path | Not proven; only flat category context and catalog attributes are currently observed. |
| S5R2 focused 11-case PASS is the current acceptance result. | MS6-S5R2-EVIDENCE-FIRST-AFTER-R4 | S5R3, the July 23 five-case rerun, and V2 S2G/S2H | Historical only; later live evidence and the promoted V2 corpus now define the current direction. |
| Source refs are sufficient context. | older citation-centric framing | `src/unified_answer_context.py` | Superseded; substantive model-facing context is required. |

## Current Historical Use Rule

Use this history for provenance and decision context. Do not cite historical pass rates, operator reports, or blocked runs as current implementation truth unless they are tied to the current commit, current dataset, current collection, and immutable report artifact.

## 2026-07-31 - V1.5 release rebaseline

- Preserved the historical V1 runtime and closeout as separate immutable
  identities without changing `reports/V1_FINAL_CLOSEOUT.md`.
- Replaced the planned V1.5 description with the implemented multi-source
  architecture baseline and accomplishment matrix.
- Consolidated all remaining limitations into one WATCH register.
- Defined one release model from V1 through V3, numerical V2/V2.5/V3 gates,
  annotated-tag policy, and rollback authority.
- Classified the inherited dirty tree and restricted the release to an
  explicit staging allowlist; generated evaluation JSON remains excluded.
- Verified 792 maintained tests with 6 live-gated skips, compileall, frontend
  lint/build/Markdown safety, offline chat/persistence smoke, ingestion dry run,
  and diff checks without external or corpus/vector mutation.
- Release decision completed: commit `c464c1a3bfef62377e318fd2af7bfb516a7e8325`
  and annotated tag `irg-ai-v1.5-multisource-baseline` freeze V1.5 as
  `CLOSED - PASS_WITH_WATCH`; internal production is not claimed.
# 2026-07-24 — Hexagonal contract restoration

- Added a neutral public composition root shared by API, CLI, and
  production-path evaluation.
- Added explicit discovery/evidence/retrieval ports and versioned runtime,
  source, context, result, and failure contracts.
- **SUPERSEDED:** Removed active answer-permission/model-authorization fields and the test-only
  model-force flag.
- Separated answer sources from candidate basis and corrected citation
  grounding so source presence alone cannot pass.
- Added additive turn metadata persistence and structured backend logging.
- Historical role/permission datasets remain immutable historical evidence and
  do not gate the current contract.

## 2026-08-05 - V2 contextual and governed-corpus progression

- Replaced the V1.5 single-active-subject continuity path with a bounded window
  of 10 persisted messages; prior assistant messages remain context, not
  evidence, and every current turn retrieves fresh DB/PDF evidence.
- Added requested-product ownership so zero, one, or many current references
  retain separate resolution, evidence, omission, and model-context groups.
- Froze the V2 corpus authority at 642 manifest documents and 28,139 chunks,
  with immutable manifest/chunk fingerprints and a matching staging index.
- The first 51-case evaluation exposed identity, ranking, and cross-brand
  contamination defects; generic repairs raised Recall@5 and evidence
  sufficiency to 86.96%, product/model identity to 84.78%, manufacturer
  accuracy to 100%, and contamination to 0%.
- A six-case online gate moved from 4/6 to 6/6 after generic short-reference
  preservation and claim-to-citation segmentation repairs. No product- or
  manufacturer-specific serving exception was added.
- Controlled promotion copied the validated snapshot to
  `CORPUS_v3_RFFM_2026-08-05`, verified all 28,139 point IDs, vector schema,
  46 payload indexes, representative payload/vector parity, health, and an
  operational retrieval smoke, then switched the existing runtime setting.
- `AOG-TE` remains intact as the recorded rollback collection. No corpus
  re-embedding occurred during promotion.
- Current direction: normal V2 operation may continue against the promoted
  corpus, but V2.5 pilot and V3 internal-production claims remain gated by
  `docs/V2_PRODUCT_CONTRACT.md` and
  `docs/ROADMAP_TO_INTERNAL_PRODUCTION.md`.

## 2026-08-07 - V2-S3 controlled capability closeout

- Completed multi-product conversational identity for explicit comparisons,
  restart continuity, ordinal references, prior-plus-new composition, and
  three-product composition.
- Persisted independent product evidence as validated parent-plus-additions
  lineages with collection ancestry, duplicate-root prevention, no-addition
  reuse, and delta-only extension.
- Kept canonical citation, grounding, response relevance, and structural
  validators diagnostic and nonblocking in the approved runtime mode; no
  evaluator exception or safety-gate bypass was added.
- Froze prompt state without activation: production remains
  `v1_20260806_baseline`, `v2_employee_voice_multi_product` is a candidate for
  separate review, and `v3_employee_voice_grounding_responsibility` remains
  `EXPERIMENTAL_NOT_PROMOTED`.
- Final offline closeout passed 263 focused tests, 51 structural/lifecycle/
  lineage tests, and the maintained 1,126-test suite with 11 expected skips.
- Recorded the nonblocking redundant-retrieval WATCH and exact release
  allowlist/exclusions in `reports/V2-S3_FINAL_CLOSEOUT_20260807.md`.

## 2026-08-20 - V2-V3 roadmap sequence decision

- Approved V2.0 release reconciliation and the V2.1 coupled Docling/OCR
  structural-corpus and Docling-native-retriever scope.
- Accepted V2.2 full approved-corpus expansion as a direction while leaving
  its exact inventory, thresholds, and promotion gate pending.
- Re-sequenced the remaining proposed work through V2.8, with identity and
  authorization at V2.5, security at V2.6, operability at V2.7, controlled
  internal pilot/UAT at V2.8, and internal production at V3.0.
- Preserved `docs/ROADMAP_TO_INTERNAL_PRODUCTION.md` as a historical numerical
  gate record and made `docs/IRG_AI_V2_V3_ROADMAP_DRAFT.md` the current
  planning sequence.
- Recorded that roadmap approval is not runtime, corpus, Qdrant, prompt,
  schema, provider, deployment, or production authorization.

## 2026-08-21 - V2.0 initialization

- Adopted the roadmap while retaining phased execution and release gates.
- Mapped every historical V2, pilot, and production threshold to its current
  V2.0-V3.0 owner without silently weakening or retiring a gate.
- Captured branch `feature/local-generation-round-1` at `40e02da`, with 31
  tracked modifications and 362 untracked files when expanded.
- Reproduced the six V2.0 blockers against the current maintained suite:
  `1181 passed, 11 skipped, 6 failed`.
- Passed 69 focused V2-S3 ownership/continuity tests, frontend lint, and the
  frontend production build.
- Verified the unchanged live governed Qdrant collection at 28,139 `dense`
  1,536-dimensional cosine points.
- Recorded the workstream split and initial gate state in
  `reports/V2_0_INITIALIZATION_20260821.md`; no staging, release, promotion, or
  external mutation occurred.

## 2026-09-03 to 2026-09-04 - V2.0 qualification execution attempts

- Progressed the V2.0 evaluation package from missing authority to a frozen
  master population, scorer contracts, evaluator implementation, qualification
  plan, and versioned execution bindings.
- Preserved the original phase-one run set after the approved binding exposed
  an assistant-fixture execution defect; no partial results were scored.
- Built and rehearsed binding v3 across all 244 scenarios and 269 turn/control
  events, including real MySQL persistence/restart behavior without live model
  calls in the zero-live-model rehearsal.
- Stopped the fresh live binding-v3 run set on sustained provider HTTP 429.
  The partial run is not resumable or scoreable; a new run set requires restored
  provider capacity and explicit authorization.
- V2.0 remains release-blocked. These attempts did not create a release commit
  or tag and did not authorize corpus, prompt, schema, or production changes.

## 2026-09-08 to 2026-09-09 - V2.1 structural retrieval experiments

- Proved that deeper P0/D1/D2 candidate pools were bounded availability
  diagnostics, not a sufficient retrieval architecture: the 78-case all-union
  ceiling reached 76.92% document availability at depth 50 but only 36.86%
  atomic evidence, with 18 expected documents still absent.
- Rejected the category-routing policy as `CATEGORY_POLICY_NO_GAIN`; its
  classifier reached 76.92% accuracy but did not improve the complete ranked
  system and did not repair representation gaps.
- Structural V1 demonstrated the first material system gain on 45 cases:
  71.43% correct-owner@1, 47.50% complete evidence, and 92.86% document recall.
  Structural parent expansion materially outperformed generic neighbors.
- Rejected the page-plus-rerank composition as
  `PAGE_STRUCTURAL_RERANK_NO_GAIN`, then repaired exact owner scoring in V1.2
  to 96.55% correct-owner@1 with all eight prior owner failures fixed.
- V1.3 configuration authority eliminated model/configuration confusers but did
  not repair procedure relationships. V1.4 scoped parent-plus-child retrieval
  raised complete procedure evidence from 16.67% to 75.00% and procedure MRR
  from 19.44% to 81.39%, while remaining a partial gain with 25.00%
  cross-procedure contamination.
- Invalidated incomplete V1.3 and V1.4 attempts and reran each from a fresh
  physical run set with no partial-ledger reuse.
- Every structural run remained evaluation-only: no PDF reparse or corpus
  rebuild in the later arms, no embedding/generator/Qdrant calls, no promotion,
  and no production mutation.
