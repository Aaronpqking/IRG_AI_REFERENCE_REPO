# IRG AI — Lessons Learned

## Purpose

This is the master ledger for implementation learning that changes future work.
It exists to prevent repeated mistakes, AI-coder drift, weak evidence, data
contamination, and unsupported scope expansion.

The ledger has two levels:

1. **Implementation-wide lessons** apply across the IRG AI V1 build.
2. **Phase lessons** retain the context, evidence, and carry-forward rule for a
   phase, sprint, or slice.

The phase headings below are retrospective capability buckets requested for this
ledger. They do not rename, reopen, or alter any historical milestone, frozen
unit, test cycle, gate result, or closeout. The actual source slice is named in
the evidence.

## Effective-Date and Historical-Integrity Rule

- Past closeouts, frozen phases, test counts, and gate results remain unchanged.
- This ledger records lessons from prior evidence without applying a new gate
  retroactively.
- Current Gate 10 records use the required structured shape and may mark an
  earlier control `SUPERSEDED` without altering the report that originally
  adopted it.
- Current runtime/readiness claims must be tied to the code, configuration, and
  immutable evaluation artifact that produced them.

## Promotion Rule

A phase, sprint, or slice lesson promotes to implementation-wide if any of the
following is true:

- it repeats twice;
- it affects architecture;
- it changes a gate;
- it prevents data contamination;
- it prevents false answer confidence;
- it affects security;
- it affects rebuildability; or
- it affects source traceability.

## Anti-Bloat Rule

Every lesson must produce at least one of:

- a changed rule;
- a changed test;
- a changed gate;
- a changed prompt;
- a documented limitation.

No action means it is commentary, not a lesson.

## Current Gate 10 Lessons

### G10-001

Lesson ID: G10-001
Area: Retrieval and exact identity
Observation: Vector similarity is not sufficient as the sole rule for exact
model, part, or version questions; identifiers require explicit parsing,
normalization, candidate generation, and scoring.
Evidence: The vector-only baseline failed while hybrid exact/lexical candidate
retrieval reached full document candidate recall; identifier regressions are
covered by focused tests.
Engineering consequence: Semantic proximity cannot establish product identity
or exact technical evidence by itself.
Control or follow-up: Keep `parse_query_identity`, exact-identifier channels,
bounded fusion, and identifier regression cases in the shared retrieval
contract.
Status: PROVEN
Related files or reports: `src/query_identity.py`, `src/hybrid_retrieval.py`,
`tests/test_identifier_retrieval.py`, `tests/test_hybrid_pdf_retrieval.py`,
`reports/MS6-S5R1_HYBRID-PDF-CANDIDATE-RETRIEVAL-001_report.md`

### G10-002

Lesson ID: G10-002
Area: Product resolution and evidence retrieval
Observation: Resolving the exact product subject and retrieving technical
evidence are separate decisions and must remain separately observable.
Evidence: The controlled path resolves database candidates before PDF retrieval
and later applies document eligibility/evidence permission. The current
maintained-suite failures also prove that older terminal/no-context expectations
can drift from this separation after architecture changes.
Engineering consequence: A database match can identify the subject but cannot
by itself prove a technical claim, while a relevant PDF hit must not silently
change the resolved subject.
Control or follow-up: Preserve separate resolution, retrieval, applicability,
and **HISTORICAL** answer-permission diagnostics; reconcile the six failing legacy expectations
under G10-016 before calling the maintained suite green.
Status: PROVEN
Related files or reports: `src/product_discovery.py`,
`src/multi_source_retrieval.py`, `src/document_applicability.py`,
`tests/test_identity_resolution_evidence_gate.py`,
`reports/MS6-S4R2_IDENTITY-RESOLUTION-EVIDENCE-GATE-001_report.md`

### G10-003

Lesson ID: G10-003
Area: Product-centered context
Observation: Product-database identity and catalog context materially support
query construction, subject retention, source selection, and answer context,
but do not become technical authority.
Evidence: The S5R2 focused run retained the exact subject in 11/11 cases after
topic words stopped displacing the identifier; the context assembler preserves
product identity, categories, attributes, and PDF evidence as distinct inputs.
Engineering consequence: Product context should guide retrieval and explain
identity/relationships while technical procedures, warnings, clearances, and
dimensions remain PDF-grounded.
Control or follow-up: Keep allowlisted product fields, exact-subject retention,
and prompt rules that prohibit unsupported technical inheritance.
Status: PROVEN
Related files or reports: `src/product_applicability.py`,
`src/unified_answer_context.py`, `src/chat_prompt_contract.py`,
`tests/test_unified_answering.py`,
`reports/MS6-S5R2_EVIDENCE_FIRST_PRODUCT_CONTEXT_AND_EXACT_SUBJECT_RETENTION_report.md`

### G10-004

Lesson ID: G10-004
Area: Provenance
Observation: Database facts and PDF technical evidence require explicit,
claim-level provenance separation through context, diagnostics, persistence, and
customer-visible source serialization.
Evidence: The shared assembler emits `claim_source_provenance`; source
serialization uses distinct database-candidate and PDF shapes; regression tests
assert both.
Engineering consequence: A unified answer must not erase which authority
supports each claim.
Control or follow-up: Preserve source-type labels, admitted-source filtering,
and claim-provenance tests whenever context or API schemas change.
Status: PROVEN
Related files or reports: `src/unified_answer_context.py`,
`src/source_serialization.py`, `tests/test_production_debug_contract.py`,
`tests/test_source_serialization.py`, `docs/TECHNICAL_MANUAL.md`

### G10-005

Lesson ID: G10-005
Area: Context assembly
Observation: Retrieval anchors benefit from neighboring chunks, but expansion
must be bounded by document, anchor count, page distance, chunk count, and
character budget.
Evidence: The active controlled path uses `CorpusNeighborIndex.expand`; tests
prove previous/next/warning expansion and configured limits.
Engineering consequence: An anchor-only context can omit a warning or
continuation, while unbounded expansion can dilute evidence and exceed context
budgets.
Control or follow-up: Keep neighbor expansion read-only, post-selection,
diagnostic, and capped by the `CONTEXT_*` settings.
Status: PROVEN
Related files or reports: `src/corpus_neighbors.py`,
`src/multi_source_retrieval.py`, `tests/test_unified_answering.py`,
`tests/test_production_debug_contract.py`, `docs/TECHNICAL_MANUAL.md`

### G10-006

Lesson ID: G10-006
Area: Multi-need query construction
Observation: Mandatory topic/product-type terms can over-constrain an otherwise
exact product query; the identifier must remain the subject while requested
topics describe information needs.
Evidence: The AOG24-GA burner-pressure case previously let `+burner*` displace
the exact identifier; S5R2 removed mandatory product-type terms when an exact
identifier is present and the focused exact-subject set passed 11/11.
Engineering consequence: Multi-need questions should be decomposed into
identity and requested claims rather than forcing every claim term into one
candidate gate.
Control or follow-up: Retain information-needs diagnostics and the
exact-identifier query tests; add broader multi-claim cases before generalizing
to claim-level fusion.
Status: STRONG INDICATION
Related files or reports: `src/information_needs.py`,
`src/product_discovery.py`, `tests/test_identity_resolution_evidence_gate.py`,
`reports/MS6-S5R2_EVIDENCE_FIRST_PRODUCT_CONTEXT_AND_EXACT_SUBJECT_RETENTION_report.md`

### G10-007

Lesson ID: G10-007
Area: Failure taxonomy and operational behavior
Observation: Identity, retrieval, context, applicability, generation,
validation, evaluation, and external-service failures require separate
classification; operational failures must not collapse into
evidence-insufficient customer fallbacks.
Evidence: Embedding quota failures stopped before response execution and were
reported as `EMBEDDING_FAILED`; the later retry executed 11/11 and isolated a
relationship-context miss instead of a service failure.
Engineering consequence: Generic fallback labels hide the owner and can make a
provider outage look like a corpus or policy decision.
Control or follow-up: Preserve stage errors, response-origin fields, per-case
failure classes, and zero-execution reporting.
Status: PROVEN
Related files or reports: `src/execution_trace.py`, `src/eval_diagnostics.py`,
`src/scripts/run_technical_answer_validation.py`,
`reports/MS6-S5R3R1_FINAL_LIVE_VERIFICATION_AND_CLOSEOUT_REPORT.md`,
`reports/evaluation_runs/MS6-S5R3R1-FINAL-LIVE-RETRY/summary.json`

### G10-008

Lesson ID: G10-008
Area: Debuggability
Observation: Aggregate metrics are insufficient to diagnose controlled
retrieval; debug/eval evidence must expose the complete sanitized execution
trace and exact serialized model-facing context.
Evidence: The production debug contract records identity, database operations,
retrieval, neighbors, applicability, evidence decisions, context payload,
**HISTORICAL:** the then-current answer-permission signal, model execution, and response origin while hiding secrets
from normal responses.
Engineering consequence: Without the exact model payload, retrieval success
cannot distinguish context omission from generation omission.
Control or follow-up: Keep diagnostics opt-in, sanitized, schema-tested, and
captured in immutable evaluation artifacts.
Status: PROVEN
Related files or reports: `src/execution_trace.py`, `src/debug_contract.py`,
`src/api_server.py`, `tests/test_production_debug_contract.py`,
`docs/TECHNICAL_MANUAL.md`

### G10-009

Lesson ID: G10-009
Area: Runtime and evaluation parity
Observation: API and online CLI share `ChatService` composition, and unified and
focused evaluators build the production API app; legacy retrieval-only and
chat-eval entry points use a different retrieval path.
Evidence: `build_app` and the online CLI both inject
`build_controlled_retrieval`; unified/focused runners call `build_app`, while
`eval_golden` constructs embedding/vector adapters and legacy evaluators
directly.
Engineering consequence: A legacy retrieval-only score must not be presented as
production behavior, and parity claims require entry point, feature flags,
collection, model, and dataset hashes.
Control or follow-up: Use the production-composed evaluators for release claims;
retain legacy modes as explicitly labeled retrieval baselines.
Status: PROVEN
Related files or reports: `src/api_server.py`,
`src/scripts/conversation_cli.py`, `src/scripts/eval_golden.py`,
`src/scripts/run_unified_answering_eval.py`,
`src/scripts/run_technical_answer_validation.py`,
`tests/test_retrieval_eval_parity_s5r2.py`

### G10-010

Lesson ID: G10-010
Area: Guardrails and evaluation calibration
Observation: Guardrails must measure both unsafe answers and valid-answer
blocking or misclassification.
Evidence: R10 hard vetoes cover unsupported fitment/universal claims, while the
production-readiness smoke found correct sourced answers whose evidence decision
or evaluator expectation disagreed; the final S5R3 retry had zero unsupported
relationship claims but failed one relationship-term expectation.
Engineering consequence: Optimizing only unsafe-answer counts can preserve
overbroad refusals and false-negative gates.
Control or follow-up: Report unsafe-claim, refusal, context-sufficient/answer-
poor, and evaluator-disagreement counts separately; retain manual review for
close calls without hiding automated failures.
Status: PROVEN
Related files or reports: `src/chat_eval.py`, `src/eval_gates.py`,
`tests/test_r10_eval_types.py`,
`reports/CONTROLLED_PRODUCTION_READINESS_VERIFICATION_2026-07-23.md`,
`reports/evaluation_runs/MS6-S5R3R1-FINAL-LIVE-RETRY/summary.json`

### G10-011

Lesson ID: G10-011
Area: Architecture scope
Observation: The active architecture has evolved beyond the original
PDF-to-vector-to-answer loop into a feature-flagged multi-source application
with product discovery, identity resolution, hybrid retrieval, applicability,
unified context, HTTP/CLI surfaces, persistence, feedback, and layered
evaluation.
Evidence: The current source tree and technical manual map these active
components; API/frontend/conversation gates were closed in the V1 report.
Engineering consequence: Governance and project overviews that describe only a
PDF loop or an unwired frontend cause incorrect implementation and parity
assumptions.
Control or follow-up: Treat `docs/TECHNICAL_MANUAL.md` as the detailed runtime
map and update governance/README whenever a production entry point changes.
Status: PROVEN
Related files or reports: `docs/TECHNICAL_MANUAL.md`, `src/api_server.py`,
`src/multi_source_retrieval.py`, `frontend/components/chat/chatShell.js`,
`reports/V1_FINAL_CLOSEOUT.md`

### G10-012

Lesson ID: G10-012
Area: Product database safety evidence
Observation: Database authority must be bounded in code, while verification of
actual runtime behavior should inspect the operations performed rather than
rejecting a session solely because its credential is write-capable.
Evidence: The readiness trace classified the account
`WRITE_CAPABLE_AUTHORIZED` and observed procedure/select activity with zero
insert, update, delete, replace, DDL, commit, or rollback operations. The
adapter and tests enforce an allowlisted procedure and bound parameters.
Engineering consequence: Credential posture remains a hardening concern, but
operation-level evidence can prove that a bounded audit run performed no
writes.
Control or follow-up: Continue least-privilege remediation and capture
credential-safe operation deltas for authorized live verification; never use a
write probe.
Status: PROVEN
Related files or reports: `src/adapters/product_mysql.py`,
`src/product_db_contract.py`, `tests/test_product_db_contract.py`,
`reports/CONTROLLED_PRODUCTION_READINESS_VERIFICATION_2026-07-23.md`

### G10-013

Lesson ID: G10-013
Area: Product role and manual applicability
Observation: Product-role labels, role-derived
**SUPERSEDED:** `technical_answer_permitted`, role-based document exclusion, and deterministic
product/topic fallbacks are no longer active decision authorities.
Evidence: S5R3 removed the fields and routing helpers; the final live retry
recorded model synthesis for 11/11 cases with no deterministic or validation
fallback, and the removal audit found no forbidden terms in active source/tests
or the focused dataset.
Engineering consequence: Earlier lessons or policies that treat inferred role
as technical permission or manual applicability must not guide new work.
Control or follow-up: Base decisions on exact identity, eligible evidence,
explicit conflicts, source/model/MPN applicability, and observed context; retain
the old reports only as architecture history.
Status: SUPERSEDED
Related files or reports:
`reports/MS6-S4R3_PRODUCT_ROLE_MANUAL_APPLICABILITY_RECONCILIATION.md`,
`reports/MS6-S5R3_REMOVE_PRODUCT_ROLE_INFRASTRUCTURE_AND_DETERMINISTIC_FALLBACK_REPORT.md`,
`reports/MS6-S5R3R1_FINAL_LIVE_VERIFICATION_AND_CLOSEOUT_REPORT.md`

### G10-014

Lesson ID: G10-014
Area: Golden-question ownership
Observation: Business and engineering ownership are both required: business
owners define realistic intent and acceptable outcomes, while engineering
validates source, page, identifiers, alternates, and executable scoring. The
repository assigns those responsibilities but does not record row-level
approval provenance for every expectation.
Evidence: `docs/ARCHITECTURE_GUIDE.md` assigns business truth, golden questions,
ambiguity, and acceptance to Jason; `docs/decisions.md` records his input on
human-realistic question types. `data/golden_questions.jsonl` records expected
sources, pages, terms, identifiers, and status but no per-row approver; the S5R3
relationship-term miss shows that expectation wording can affect closure.
Engineering consequence: Corpus grounding alone does not establish business
acceptance, especially for relationship, fitment, and staff-natural wording.
Control or follow-up: Preserve the documented joint ownership, add row-level or
release-level approval provenance, and record acceptance without rewriting
historical results.
Status: PROVEN
Related files or reports: `data/golden_questions.jsonl`,
`docs/ARCHITECTURE_GUIDE.md`, `docs/decisions.md`,
`tests/test_golden_questions_shape.py`,
`reports/MS6-S5R3R1_FINAL_LIVE_VERIFICATION_AND_CLOSEOUT_REPORT.md`

### G10-015

Lesson ID: G10-015
Area: Conversation, feedback, and frontend integration
Observation: Conversation persistence, feedback linkage, the HTTP API, and
frontend integration are implemented; the previous ledger described them as
future work.
Evidence: The conversation loop saves the user turn before retrieval and the
assistant turn with sources after response generation; service/store/API tests
cover feedback-to-assistant linkage, and the frontend calls the API client.
Engineering consequence: Current governance must test and maintain these
surfaces instead of planning their first implementation.
Control or follow-up: Keep event-time persistence and API/frontend regression
coverage; treat broad multi-turn memory and authentication as separate future
scope.
Status: PROVEN
Related files or reports: `src/conversation_loop.py`, `src/chat_service.py`,
`src/api_server.py`, `frontend/components/chat/chatShell.js`,
`tests/test_conversation_loop.py`, `tests/test_chat_service.py`,
`tests/test_api_server.py`, `reports/V1_FINAL_CLOSEOUT.md`

### G10-016

Lesson ID: G10-016
Area: Regression-contract drift
Observation: The current maintained suite contains six failures whose
expectations still require terminal decisions to return no context and avoid
the chat model, while the later S5R3 architecture removed role-derived
permission and deterministic topic/product fallback behavior.
Evidence: The Gate 10 audit command
`.\.venv\Scripts\python.exe -m pytest tests -q` produced 497 passed, 6 failed,
6 skipped; all failures are in `test_hybrid_pdf_retrieval.py` and
`test_identity_resolution_evidence_gate.py` around terminal/no-context/no-model
assertions. A direct two-module rerun reproduced three failures and passed 42
tests, indicating that the other three also depend on broader suite order or
environment state.
Engineering consequence: A report that cites an older green maintained-suite
count is not current regression evidence, and neither runtime nor tests should
be changed until the intended post-S5R3 contract is explicitly resolved.
Control or follow-up: Owner TBD must classify each failing assertion against the
S5R3 removal decision, then either restore the safety invariant in runtime or
update the superseded expectation and add replacement evidence-admission tests.
Acceptance requires both isolated and maintained-suite execution to pass with no
hidden behavioral weakening or order-dependent environment leakage.
Status: PROVEN
Related files or reports: `tests/test_hybrid_pdf_retrieval.py`,
`tests/test_identity_resolution_evidence_gate.py`,
`reports/MS6-S5R3_REMOVE_PRODUCT_ROLE_INFRASTRUCTURE_AND_DETERMINISTIC_FALLBACK_REPORT.md`,
`reports/MS6-S5R3R1_FINAL_LIVE_VERIFICATION_AND_CLOSEOUT_REPORT.md`

### G10-017

Lesson ID: G10-017
Area: Clarification policy
Observation: Clarification should request the smallest human-readable fact that
materially changes identity or applicability; raw product IDs and undifferentiated
candidate lists transfer internal ambiguity to the user.
Evidence: `_identity_clarification` asks for an exact model/configuration and the
relationship path asks for installed model/series and fuel, while
`product_discovery.clarification_answer` still formats candidate choices with
raw `product_id` values.
Engineering consequence: A technically safe clarification can still be
operationally poor or disclose internal identifiers that do not help the user.
Control or follow-up: Prefer model, size, fuel, generation, configuration, or
year discriminators; keep raw product IDs in debug diagnostics only and add
customer-answer tests for multiple-candidate distinctions.
Status: PROVEN
Related files or reports: `src/product_discovery.py`,
`src/multi_source_retrieval.py`, `tests/test_controlled_discovery_pilot.py`,
`tests/test_unified_answering.py`

### G10-018

Lesson ID: G10-018
Area: Configuration and feature flags
Status: **SUPERSEDED IN PART.** Feature flags remain part of the effective
architecture, but hybrid PDF retrieval is no longer flag-controlled.
Historical observation:
`PRODUCT_DISCOVERY_ENABLED` controls whether the multi-source service exists and
`HYBRID_PDF_RETRIEVAL_ENABLED` changes the PDF evidence adapter inside that
service.
Evidence: The controlled-retrieval factory returns `None` when product discovery
is disabled and selects vector-only or hybrid PDF evidence by the hybrid flag;
API health and evaluation manifests record only part of this effective state.
Engineering consequence: Two runs from the same commit can execute materially
different retrieval, gating, and context paths.
Current control or follow-up: Record all route-changing flags in startup/debug/evaluation
artifacts, test enabled and disabled composition, and compare configuration
before parity or readiness claims. Treat hybrid retrieval as unconditional and
`PDF_CONFIGURATION_APPLICABILITY_MODE` as an admission-only policy.
Status: PROVEN
Related files or reports: `src/controlled_retrieval_factory.py`,
`src/api_server.py`, `src/scripts/run_unified_answering_eval.py`,
`tests/test_hybrid_pdf_retrieval.py`,
`reports/evaluation_runs/MS6-S5R3R1-FINAL-LIVE-RETRY/run_manifest.json`

### G10-019

Lesson ID: G10-019
Area: Orchestration integrity
Observation: The final answer decision, delivered model context, and model-call
permission must be enforced as one invariant; a clarification/block decision
must not silently coexist with unrestricted answer generation.
Evidence: The S4R2 report records an unsafe pre-fix path where normal generation
could still run. The current maintained suite now fails assertions concerning
terminal decisions, nonempty context, and chat-model calls, so the intended
post-S5R3 invariant is not currently settled.
Engineering consequence: Logging a safe policy label is ineffective if the
context/model path can act on a different decision.
Control or follow-up: Resolve G10-016, explicitly define scoped-answer versus
context-suppression behavior, and require tests that assert decision, context,
model-called, response-origin, and customer answer together.
Status: PROVEN
Related files or reports: `src/multi_source_retrieval.py`,
`src/conversation_loop.py`, `tests/test_hybrid_pdf_retrieval.py`,
`tests/test_identity_resolution_evidence_gate.py`,
`reports/MS6-S4R2_IDENTITY-RESOLUTION-EVIDENCE-GATE-001_report.md`

### G10-020

Lesson ID: G10-020
Area: Evaluation coverage
Observation: Atomic exact-model lookups are necessary but do not represent the
support workload; evaluation must also preserve natural ambiguity,
staff-language, fitment, relationship, related-product, and partial-answer
behavior.
Evidence: The current golden set contains 20 atomic, 8 staff-natural, and 2
applied-fitment cases, while the focused technical dataset adds direct,
relationship, and related-product classes. R10 records that business feedback
triggered the human-realistic types.
Engineering consequence: An atomic-only pass can hide clarification quality,
scope omissions, relationship errors, and valid-answer blocking.
Control or follow-up: Keep category-balanced natural phrasing and explicit
answer/clarify/refuse expectations; add comparison and multi-product cases only
after their evidence is verified.
Status: PROVEN
Related files or reports: `data/golden_questions.jsonl`,
`data/evals/ms6_s5_technical_answer_validation.jsonl`,
`tests/test_golden_questions_shape.py`, `docs/decisions.md`,
`reports/MS4-S1R10-B_closure.md`

### G10-021

Lesson ID: G10-021
Area: Model-context serialization
Observation: The model-facing serialized payload is an architectural contract;
the presence of an upstream structured field does not prove that the model
received it.
Evidence: `assemble_answer_context` builds bounded chunks and
`serialize_model_context` converts them into the final string recorded as
`model_payload.serialized_context`; diagnostics separately record truncation,
estimated tokens, and claim provenance.
Engineering consequence: Serialization order, labels, omission, and truncation
can cause answer failures even when retrieval and internal context objects are
correct.
Control or follow-up: Test the exact serialized payload and truncation
decisions, compare it with upstream context objects, and retain provenance
labels through the chat adapter boundary.
Status: PROVEN
Related files or reports: `src/unified_answer_context.py`,
`src/execution_trace.py`, `src/conversation_loop.py`,
`tests/test_production_debug_contract.py`, `tests/test_unified_answering.py`

### G10-022

Lesson ID: G10-022
Area: Multi-source degradation
Observation: Product discovery adds useful context but also introduces
operational and ambiguity failure modes; those failures should not automatically
be interpreted as absence of PDF evidence.
Evidence: The active controlled service performs discovery without an internal
operational fallback and returns before PDF retrieval for several ambiguity
states. Earlier multi-source reports show candidate-resolution/applicability
failures while standalone retrieval could still find candidate evidence.
Engineering consequence: Safe degradation rules are needed so database
availability and identity certainty do not become one undifferentiated PDF
retrieval gate.
Control or follow-up: Define separately what happens for discovery service
failure, partial identity, material applicability ambiguity, and safe
document-level questions; continue PDF retrieval only where scope can remain
truthful and safe.
Status: STRONG INDICATION
Related files or reports: `src/multi_source_retrieval.py`,
`reports/MS6-S4E1_UNIFIED-ANSWERING-EVALUATION-001_report.md`,
`reports/MS6-S4R1_EVALUATION-CONTRACT-IDENTITY-RETRIEVAL-001_report.md`,
`reports/MS6-S5R2_RETRIEVAL-EVALUATION-PARITY-AND-MISS-REMEDIATION-001_report.md`

### G10-023

Lesson ID: G10-023
Area: Product-to-document applicability
Observation: Product resolution and semantically relevant PDF retrieval do not
prove that a document applies to the product; source-document mapping is a
separate capability.
Evidence: S4R1 reported source-mapping failures independently from candidate
resolution and manual applicability. The active code parses explicit product
document references and assesses source/model/MPN, series, fuel, year,
generation, and document-type signals.
Engineering consequence: Folder proximity or vector similarity cannot stand in
for a product-to-document relationship.
Control or follow-up: Prefer direct identifiers and approved mappings, retain
alternate applicable sources, keep mapping diagnostics distinct, and regression
test null/sentinel/malformed references.
Status: PROVEN
Related files or reports: `src/source_document_mapping.py`,
`src/document_applicability.py`, `tests/test_unified_answering.py`,
`reports/MS6-S4R1_EVALUATION-CONTRACT-IDENTITY-RETRIEVAL-001_report.md`

### G10-024

Lesson ID: G10-024
Area: Version and generation policy
Observation: Exact-year, historical, and latest/current questions require
different applicability and ranking behavior; newer is not universally more
relevant.
Evidence: Retrieval policy tests prove exact-year preference over newer
documents, latest preference only within matching scope, and protection against
a generic newer catalog outranking an exact manual. Golden rows distinguish
`requires_latest` and `requires_exact_year`.
Engineering consequence: Version intent must be extracted and evaluated
separately from generic similarity and document recency.
Control or follow-up: Preserve exact-year and scoped-latest tests, retain year
and generation conflict diagnostics, and add evidence-backed cross-year cases.
Status: PROVEN
Related files or reports: `src/retrieval_policy.py`, `src/query_intent.py`,
`src/document_applicability.py`, `tests/test_retrieval_policy.py`,
`tests/test_identifier_retrieval.py`, `data/golden_questions.jsonl`

### G10-025

Lesson ID: G10-025
Area: Multi-product comparison
Observation: Multi-product questions require separate requested-subject owners;
one global primary subject or one merged context can silently mix products,
years, catalog facts, and manual facts.
Evidence: V2 now retains every literal requested reference, its resolution,
candidate and evidence ownership, omissions, and model-context group. Shared
documents retain one canonical evidence identity with all applicable owners.
Engineering consequence: Multi-product support is an ownership and attribution
contract, not permission to concatenate independently retrieved passages.
Control or follow-up: Preserve requested-product coverage and cross-subject
attribution tests. Complete the remaining V2 gates for evidence balancing,
bounded retrieval rounds, and persistence/reload identity before claiming the
full V2 release threshold.
Status: PROVEN
Related files or reports: `docs/V2_PRODUCT_CONTRACT.md`,
`docs/decisions/ADR-018-v2-conversation-and-multi-subject-context.md`,
`src/requested_products.py`, `src/multi_source_retrieval.py`,
`tests/test_requested_product_ownership.py`

### G10-026

Lesson ID: G10-026
Area: Product and category context bounds
Observation: Richer product/category context is useful only when it remains
bounded, provenance-labeled, and honest about hierarchy completeness.
Evidence: The serializer exposes ordered category paths and metrics for parent
IDs/full ancestry, but the approved AOG24-GA read path did not prove parent IDs
or a complete root-to-leaf hierarchy. Context assembly also enforces product and
PDF character/token budgets.
Engineering consequence: Flat labels must not be presented as a proven
hierarchy, and indiscriminate context expansion can introduce cross-product
contamination and truncation.
Control or follow-up: Preserve ordered paths when supplied, never fabricate
ancestry, report hierarchy metrics and context size, deduplicate context, and
keep category membership non-authoritative for compatibility.
Status: STRONG INDICATION
Related files or reports: `src/product_applicability.py`,
`src/unified_answer_context.py`, `tests/test_unified_answering.py`,
`reports/MS6-S5R2_EVIDENCE_FIRST_PRODUCT_CONTEXT_AND_EXACT_SUBJECT_RETENTION_report.md`

### G10-027

Lesson ID: G10-027
Area: Requested subject and related entities
Observation: The entity asked about must remain distinct from records,
accessories, components, bases, configurations, or products merely mentioned or
retrieved alongside it.
Evidence: S5R2 found topic wording could displace the exact AOG24-GA subject,
and the active relationship diagnostics separately expose the active subject,
resolved product, requested topic, and explicit/derived relationship context.
The approved data does not yet provide a complete directional relationship
graph.
Engineering consequence: One resolved record or inferred role cannot authorize
claims about every related entity.
Control or follow-up: Preserve exact-subject retention and explicit relationship
direction when available; add verified accessory-for, component-of,
configuration-of, and replacement-for cases before generalizing.
Status: STRONG INDICATION
Related files or reports: `src/product_discovery.py`,
`src/product_applicability.py`, `src/multi_source_retrieval.py`,
`reports/MS6-S5R2_EVIDENCE_FIRST_PRODUCT_CONTEXT_AND_EXACT_SUBJECT_RETENTION_report.md`

### G10-028

Lesson ID: G10-028
Area: Corpus expansion, retrieval quality, and controlled promotion
Observation: A larger indexed corpus is not promotable from successful
embedding, point-count parity, or aggregate recall alone. Short identifier
preservation, manufacturer isolation, evidence sufficiency, claim-to-citation
alignment, bypass absence, and rollback identity must all be verified.
Evidence: The initial 51-case V2 evaluation found 76.09% Recall@5, 52.17%
product/model identity, and 6.52% cross-brand contamination. Generic repairs
raised Recall@5 and evidence sufficiency to 86.96%, identity to 84.78%, and
manufacturer accuracy to 100% with zero contamination. A later six-case online
run still failed 4/6 until generic short-reference and citation-segmentation
repairs produced 6/6. The governed 28,139-point collection was then copied,
verified, activated, and paired with the unchanged AOG-TE rollback collection.
Engineering consequence: Retrieval metrics and answer/citation correctness are
separate promotion gates. Intermediate failure reports remain valid history but
must not remain the current recommendation after a later immutable repair run.
Control or follow-up: Freeze manifest/chunk hashes; require retrieval, identity,
contamination, answer, citation, hardcoding, and bypass evidence; promote by
verified named copy without re-embedding; preserve a tested rollback target.
Status: PROVEN
Related files or reports: `reports/V2_S2D_RETRIEVAL_EVALUATION.md`,
`reports/V2_S2E_RETRIEVAL_REPAIR.md`,
`reports/V2_S2G_PROMOTION_READINESS.md`,
`reports/V2_S2H_CONTROLLED_PROMOTION_REVIEW.md`,
`reports/V2_S2H_PROMOTION_RESULT.md`,
`docs/decisions/ADR-019-governed-corpus-promotion-and-rollback.md`

## Attached Additional-Lesson Mapping

The supplied `LL-01` through `LL-30` were de-duplicated against the current
ledger. Proposed statuses were changed where repository evidence contradicted
them.

| Attached lesson | Current record | Audit disposition |
|---|---|---|
| LL-01 | G10-001 | Incorporated; vector score remains one bounded retrieval signal. |
| LL-02 | G10-001 | Consolidated with explicit identifier extraction/scoring. |
| LL-03 | G10-002 | Incorporated; resolution and evidence stages remain distinct. |
| LL-04 | G10-010, G10-019 | Incorporated with bidirectional gating and decision/context invariant. |
| LL-05 | G10-013 | Proposed active-role status rejected; role authorization is `SUPERSEDED`. |
| LL-06 | G10-027 | Retained as subject/related-entity separation, not active role classification. |
| LL-07 | G10-003 | Incorporated. |
| LL-08 | G10-026 | Retained as `STRONG INDICATION`; full category ancestry is not proven. |
| LL-09 | G10-004 | Incorporated. |
| LL-10 | G10-005 | Incorporated. |
| LL-11 | G10-005, G10-026 | Incorporated as bounded context and honest hierarchy. |
| LL-12 | G10-006 | Retained as `STRONG INDICATION`; broad multi-claim proof is incomplete. |
| LL-13 | G10-017 | Added; current raw-product-ID clarification gap recorded. |
| LL-14 | G10-007 | Incorporated. |
| LL-15 | G10-007 | Incorporated. |
| LL-16 | G10-007, G10-009, G10-010 | Incorporated across failure taxonomy, parity, and guardrails. |
| LL-17 | G10-009 | Incorporated. |
| LL-18 | G10-018 | Added. |
| LL-19 | G10-010 | Incorporated. |
| LL-20 | G10-019, G10-016 | Added with the current failing invariant tests disclosed. |
| LL-21 | G10-014 | Revised to joint ownership; per-row approval provenance remains missing. |
| LL-22 | G10-020 | Added from current natural/focused dataset evidence. |
| LL-23 | G10-008 | Incorporated; obsolete `product_role` debug authority not restored. |
| LL-24 | G10-021 | Added. |
| LL-25 | G10-022 | Added as `STRONG INDICATION`; graceful degradation is not implemented generally. |
| LL-26 | G10-023 | Added. |
| LL-27 | G10-024 | Added. |
| LL-28 | G10-025 | Added as `STRONG INDICATION`; verified comparison coverage is absent. |
| LL-29 | G10-012 | Incorporated. |
| LL-30 | G10-011 | Incorporated. |

## V2.1 Structural Retrieval Lessons

These records summarize the bounded Docling structural-retrieval work through
2026-09-09. They describe unpromoted experiments only. The production corpus,
retriever, Qdrant selection, and serving composition were not changed.

### V2.1-001

Lesson ID: V2.1-001
Area: Candidate depth and evaluation semantics
Observation: A deep candidate pool is an availability ceiling, not ranked
retrieval quality. Increasing depth cannot repair evidence that is absent from
the representation, and an unranked union must not be compared as though it
were a ranked arm.
Evidence: Across the frozen 78-case P0/D1/D2 diagnostic, the all-arm document
ceiling reached 76.92% at depth 50 while atomic evidence reached only 36.86%; 18
cases still had no expected document within 50. The category-policy follow-up
classified `CATEGORY_POLICY_NO_GAIN` despite 76.92% classifier accuracy.
Engineering consequence: Diagnose document availability, page localization,
atomic evidence, and ranking separately before selecting the next experiment.
Control or follow-up: Preserve first-hit ranks, report oracle unions only as
ceilings, and route representation failures to extraction/structure work rather
than hiding them with larger `k`.
Status: PROVEN
Related files or reports:
`reports/docling_candidate_depth/20260908T201745Z/candidate_depth.md`,
`reports/category_retrieval_policy/20260908T213935Z/evaluation.md`

### V2.1-002

Lesson ID: V2.1-002
Area: Structural expansion and reranking
Observation: Structural parent expansion produced the largest first material
gain; generic neighboring chunks were not an adequate substitute.
Evidence: Structural V1 raised correct-owner@1 from 26.19% P0 and 30.95% D1 to
71.43%, complete evidence to 47.50%, and document recall to 92.86%. Removing
structural expansion reduced complete evidence to 17.50%; generic neighbor
expansion reached 27.50%.
Engineering consequence: Parent/child relationships are retrieval semantics,
not presentation decoration.
Control or follow-up: Keep structural expansion bounded, typed, provenance
preserving, and independently ablated.
Status: PROVEN
Related files or reports:
`reports/docling_structural_retrieval_v1/20260909T151200Z/evaluation.md`

### V2.1-003

Lesson ID: V2.1-003
Area: Page-centric retrieval
Observation: Better page availability does not imply a better final evidence
packet. Combining page and node reranking can compound scoring errors.
Evidence: The page-only arm improved regression complete evidence to 55.00%,
but page-plus-rerank fell to 42.50%. On the fresh holdout, page-plus-rerank fell
to 34.62% complete evidence and 64.29% correct-owner@1. The candidate was
classified `PAGE_STRUCTURAL_RERANK_NO_GAIN`.
Engineering consequence: Page retrieval, local node selection, bundle
construction, and final reranking require separate scorecards and ablations.
Control or follow-up: Do not promote a composite arm from one improved
intermediate metric; compare the complete ranked output on fresh holdout and
regression sets.
Status: PROVEN
Related files or reports:
`reports/docling_structural_page_v1_1/20260909T193000Z/evaluation.md`

### V2.1-004

Lesson ID: V2.1-004
Area: Owner and configuration authority
Observation: Exact document-owner and configuration evidence must participate
in ranking before structurally similar content is allowed to win.
Evidence: V1.2 owner reranking raised correct-owner@1 to 96.55%, eliminated all
eight prior owner failures, and reduced wrong-owner@1 to 3.45%. V1.3
configuration authority reached 100% exact-model and model-plus-configuration
owner accuracy and fixed the E1060 analog/digital confuser.
Engineering consequence: Structural similarity alone is unsafe for dense
families of near-identical manuals and configurations.
Control or follow-up: Derive owner/configuration identity generically from
corpus metadata, reject conflicts explicitly, and retain wrong-owner metrics as
hard diagnostic evidence.
Status: PROVEN
Related files or reports:
`reports/docling_structural_owner_v1_2/20260909T173330Z/evaluation.md`,
`reports/docling_structural_v1_3/20260909T204000Z/evaluation.md`

### V2.1-005

Lesson ID: V2.1-005
Area: Procedure retrieval
Observation: Procedure intent and document ownership are insufficient when a
manual contains dozens of plausible procedures. The retriever must select a
scoped parent and then assemble its governed children.
Evidence: The pre-scoring audit found below-cutoff procedure nodes and
step-to-parent promotion failures. V1.3 did not improve procedure completeness
and increased cross-procedure contamination. V1.4 raised parent, step,
ordered-step, and complete-procedure recall from 16.67% to 75.00%, raised
procedure MRR from 19.44% to 81.39%, and reduced contamination from 41.67% to
25.00%.
Engineering consequence: Procedure retrieval is a relationship-recovery task,
not a generic top-chunk task.
Control or follow-up: Rank procedure parents within the resolved document,
expand only linked children, preserve order/ordinal semantics, and keep
cross-procedure contamination visible. V1.4 remains a partial gain, not a
promotion candidate.
Status: PROVEN_WITH_REMAINING_GAP
Related files or reports:
`reports/docling_structural_v1_3/pre_scoring_audit/20260909T180000Z/procedure_failure_audit.md`,
`reports/docling_structural_v1_3/20260909T204000Z/evaluation.md`,
`reports/docling_structural_v1_4/20260909T212033Z/evaluation.md`

### V2.1-006

Lesson ID: V2.1-006
Area: Run integrity and invalidation
Observation: A partial ledger from an interrupted or schema-incompatible run
is not reusable evidence, even when some result files exist.
Evidence: The first V1.3 attempt stopped on an incompatible
`required_relationships` shape. The first V1.4 attempt timed out after writing
new-holdout output but before completing bounded verification. Both were marked
`INVALIDATED`; the successful replacements recorded
`prior_run_resumed=false` and `prior_results_reused=false`.
Engineering consequence: Resuming partial scoring creates unverifiable mixed
run authority.
Control or follow-up: Start a fresh physical run set after any failed
qualification attempt, preserve the invalidation record, and score only a
complete sealed ledger.
Status: PROVEN
Related files or reports:
`reports/docling_structural_v1_3/20260909T203131Z/INVALIDATED.md`,
`reports/docling_structural_v1_4/20260909T211736Z/INVALIDATED.md`

## Historical Implementation-Wide Lessons

The following table is the pre-MS6 implementation-wide snapshot. It is retained
for historical traceability and is not a substitute for the structured current
records above.

| ID | Lesson | Source phase / evidence | Impact | Action taken | Test added | Status |
|---|---|---|---|---|---|---|
| IW-001 | Freeze scope and protected boundaries before implementation expands. | MS1C staged migration; decisions and freeze log | Prevents architecture and AI-coder drift. | Slice contracts, allowed/prohibited paths, and freeze records govern changes. | `test_core_boundaries.py`, `test_imports.py` | Active |
| IW-002 | Qdrant is a rebuildable index, never corpus source of truth. | MS2 readiness; MS3-S2 rebuild command | Protects rebuildability and recovery. | `source_pdfs`, `chunks.jsonl`, and `manifest.json` remain authoritative; rebuild reads chunks. | `test_rebuild_qdrant_flow.py`, `test_rebuild_qdrant_script.py` | Active |
| IW-003 | Core use cases depend on ports; SDK clients stay in adapters and runtime composition. | MS1C-A3, MS3-S1 | Prevents external calls from leaking into core logic or import time. | Adapter-only SDK imports, no global clients, thin command entrypoints. | `test_core_boundaries.py`, adapter import tests | Active |
| IW-004 | Corpus approval is snapshot-specific, not folder-wide. | MS2-F1B/F1C | Prevents unreviewed PDFs from entering trusted output. | `approved_pdfs.jsonl` gates ingestion; later files require a new approval action. | `test_approved_pdfs_snapshot.py`, `test_corpus_approval.py` | Active |
| IW-005 | PDF failures and image-only documents must remain visible and produce no trusted chunks. | MS2 ingestion/readiness | Prevents silent contamination and false OCR claims. | `PDF_READ_FAILED` and `NO_TEXT_EXTRACTED` are persisted limitations. | `test_pdf_quality.py`, `test_ingest_chunks.py` | Active |
| IW-006 | Persist relative source identity; never persist machine-local absolute paths. | MS2 local store, manifest, and vector payload work | Protects traceability, portability, and local path privacy. | Models, stores, readiness, and payload adapters reject absolute paths. | `test_manifest_store.py`, `test_ms2_readiness.py`, `test_qdrant_vector_adapter.py` | Active |
| IW-007 | Technical PDFs require identifier-aware enrichment; blind text splitting is insufficient. | MS2-A4 technical chunk contract | Improves retrieval evidence for models, parts, warnings, tables, dimensions, installation, wiring, schematics, and figures. | Enriched chunk metadata and source context are included in embedding text. | `test_technical_text.py`, `test_technical_chunk_strategy.py` | Active |
| IW-008 | Validate actual embedding output before any Qdrant collection mutation. | MS4-S1R2 zero-vector failure | Prevents invalid collection creation and partial index mutation. | Vector size comes from returned vectors; empty, inconsistent, and zero-length output fails first. | `test_openai_embedding_adapter.py`, `test_rebuild_qdrant_flow.py` | Active |
| IW-009 | Offline, synthetic-live, corpus-live, and full-corpus evidence are distinct proof tiers. | MS2 tiered readiness; MS4-S1/S1R | Prevents mocked or partial proof from becoming a readiness claim. | Gate reports state the evidence tier and preserve blocked live states. | `test_ms2_readiness.py`; opt-in integration tests | Active |
| IW-010 | Generic vector similarity is insufficient for exact model and part questions. | MS4-S1 P4 retrieval implementation | Prevents semantically plausible but identifier-wrong results. | Normalize digit-led identifiers and rerank exact matches above generic hits. | `test_identifier_retrieval.py`, identifier cases in `test_technical_text.py` | Active |
| IW-011 | Golden questions must be grounded in corpus evidence and cover failure-prone categories. | MS4-S1 P4 golden evaluation | Prevents invented expectations and false confidence. | Confirmed rows carry expected source, page, text, category, and identifiers; low confidence is explicit. | `test_golden_questions_shape.py`, `test_eval_golden_script.py` | Active |
| IW-012 | Test success is not the same as external-service or product readiness. | MS2 readiness and MS4-S1 blocked live eval | Prevents overstated completion. | Closeouts separate test results, live evidence, limitations, and gate state. | Existing tier/readiness tests; full-loop E2E deferred | Active |
| IW-013 | Repository state must be audited and unrelated dirty-tree work preserved. | MS4-S1 pre/post audit and build report | Prevents accidental overwrite and misleading slice scope. | Scope reports distinguish pre-existing tracked, untracked, and ignored files. | Documented process limitation; no new test | Active |
| IW-014 | Conversation and feedback persistence must occur at event time, not only at chat close. | V1 target, implemented conversation loop, service/store/API tests | Prevents lost questions, answers, sources, and feedback. | User and assistant turns are saved at event time; feedback links to the assistant turn. | `test_conversation_loop.py`, `test_chat_service.py`, `test_api_server.py` | Active; implementation state updated by G10-015 |

## Phase Lessons

### MS1 — Repo Foundation / Governance

#### What worked

- Staged migration separated documentation alignment, archived POCs, core
  contracts, adapters, and runtime commands.
- Ports and adapters kept OpenAI and Qdrant imports out of core modules.
- Freeze and decision logs made protected boundaries reviewable.

#### What failed / almost failed

- Documentation described target paths before the checked-out tree contained
  them, creating a risk that intended architecture would be mistaken for
  implemented evidence.
- A dirty working tree made slice ownership ambiguous unless baseline and
  post-change state were compared.
- Historical casing and path movement could have been normalized casually,
  breaking traceability to earlier work.

#### Decision changes

- Treat current tree, target tree, and frozen tree as separate facts.
- Require explicit slice scope before code or path expansion.
- Keep SDK construction in adapters/runtime composition and forbid import-time
  side effects.
- Require future AI-coder slices to review `README.md`, `Governance.md`, the
  active slice/freeze record, and this ledger before editing.

#### Tests added

- `tests/test_imports.py`
- `tests/test_core_boundaries.py`
- `tests/test_models_traceability.py`
- `tests/test_settings.py`
- `tests/test_no_secrets.py`

#### Carry-forward rules

- Do not infer implementation from a target tree or document.
- Do not touch protected or unrelated dirty-tree files without explicit scope.
- No global clients and no network, client construction, or file creation at
  import time.

### MS2 — Corpus / PDF Ingestion

#### What worked

- An explicit approved-path snapshot made corpus membership testable.
- Relative directory structure yielded useful manufacturer, brand, series,
  product, and year metadata.
- Generated/temp fixtures proved ingestion behavior without populating trusted
  corpus artifacts.
- Visible quality states kept 43 no-text PDFs out of the 6,084 trusted chunks.

#### What failed / almost failed

- Folder presence alone could have been mistaken for approval.
- Invalid or image-only PDFs could have appeared successful if only file counts
  were measured.
- Absolute workstation paths could have leaked into manifest, chunks, or vector
  payloads.
- Full-corpus embedding cost and policy constraints were not evident until the
  preflight measured 6,823,013 embedding-text characters.

#### Decision changes

- Approval is snapshot-specific and checked before trusted ingestion.
- Bad PDFs fail visibly; image-only PDFs create zero trusted chunks and remain
  documented OCR-deferred limitations.
- Persisted source paths are relative.
- Run local corpus size and readiness preflight before requesting live work.

#### Tests added

- `tests/test_approved_pdfs_snapshot.py`
- `tests/test_corpus_approval.py`
- `tests/test_corpus_pdf.py`
- `tests/test_pdf_quality.py`
- `tests/test_ingest_chunks.py`
- `tests/test_path_metadata.py`
- `tests/test_manifest_store.py`

#### Carry-forward rules

- A later PDF is unapproved until explicitly added to a reviewed snapshot.
- `PDF_READ_FAILED`, `NO_TEXT_EXTRACTED`, and zero-chunk outcomes cannot be
  hidden by aggregate success counts.
- Never persist an absolute local path.

### MS3 — Chunking / Technical Metadata

This capability was implemented historically within MS2-A4. This heading does
not move or rename that closed work.

#### What worked

- Chunk records preserved source pages and directory-derived metadata.
- Embedding text combined source context with technical content.
- Explicit technical flags and token extraction made downstream retrieval
  inspectable.

#### What failed / almost failed

- Generic chunk splitting did not by itself preserve the meaning of warnings,
  tables, dimensions, installation steps, compatibility, wiring, schematic
  references, or figure references.
- Identifier extraction initially risked missing digit-led part formats.
- Invalid or no-text chunks could have reached embedding without a validation
  boundary.

#### Decision changes

- Extract and normalize model and part identifiers, including digit-led forms.
- Preserve technical content flags in chunks and Qdrant payloads.
- Include source metadata and identifiers in embedding text.
- Reject invalid and unembeddable chunks before adapter calls.

#### Tests added

- `tests/test_technical_text.py`
- `tests/test_technical_chunk_strategy.py`
- traceability assertions in `tests/test_qdrant_vector_adapter.py`

#### Carry-forward rules

- Chunking policy must be evaluated against technical-document structures, not
  prose alone.
- Metadata enrichment may improve, but source identity and validation cannot
  weaken.

### MS4 — Embeddings / Qdrant Rebuild

Historical implementation spans MS2 readiness, MS3-S1/S2, and MS4-S1
remediation. Those slice names and results remain unchanged.

#### What worked

- Fake-client adapter tests proved batching, ordering, failure wrapping, named
  and unnamed vectors, deterministic IDs, and source payloads offline.
- A dry-run validated all 6,084 chunk rows without constructing live clients.
- The rebuild command made Qdrant recoverable from `chunks.jsonl`.
- Smoke and primary collection names were kept separate.

#### What failed / almost failed

- A live path allowed `vector_size=0` to approach Qdrant setup before actual
  embedding output was validated.
- Synthetic live infrastructure proof did not prove approved-corpus readiness.
- External approval policy blocked corpus calls even when code and user intent
  were otherwise ready.
- Qdrant client API shape and named-vector routing required adapter-level
  compatibility rather than assumptions in core logic.

#### Decision changes

- Derive vector size from successful embedding output.
- Empty lists, inconsistent dimensions, and zero-length vectors fail before
  ensure/recreate/upsert.
- Live Qdrant validation uses an explicit smoke collection only.
- Report synthetic, limited-corpus, full-corpus, and primary-collection evidence
  separately.

#### Tests added

- `tests/test_openai_embedding_adapter.py`
- `tests/test_qdrant_vector_adapter.py`
- `tests/test_rebuild_qdrant_flow.py`
- `tests/test_rebuild_qdrant_script.py`
- opt-in tests under `tests/integration/`

#### Carry-forward rules

- Never configure collection dimensions from settings assumptions alone.
- Never mutate a primary collection during smoke testing.
- Qdrant readiness must be reproducible from the local source artifacts.
- A blocked live gate remains blocked regardless of offline pass counts.

### MS5 — Retrieval / Golden Eval

This capability is recorded historically as MS4-S1 P4. Its contract was
`CANDIDATE` when this phase note was written; later closeouts and current
`G10-*` records supersede that temporal description without rewriting the
original evidence.

#### What worked

- Twenty confirmed questions were grounded in chunk evidence across seven
  technical categories.
- Port-driven retrieval preserved source metadata and exposed score details.
- Exact identifier and keyword evidence improved ranking transparency.
- The dry-run validated question shape without OpenAI or Qdrant calls.

#### What failed / almost failed

- Vector similarity alone ranked generic semantic hits above exact part/model
  evidence.
- Initial token handling needed explicit support for identifiers such as
  `24-B-06` and `3598-20`.
- Offline pass and a valid smoke index still did not prove live golden-question
  quality.
- Live evaluation was blocked because workspace question text could not be sent
  externally under the active policy.

#### Decision changes

- Detect and normalize exact model/part identifiers before final ranking.
- Expose low-confidence/no-result state.
- Ground golden expectations in source path, page, answer text, category, and
  identifier evidence.
- Keep live-eval readiness separate from offline implementation readiness.

#### Tests added

- `tests/test_identifier_retrieval.py`
- `tests/test_golden_questions_shape.py`
- `tests/test_eval_golden_script.py`

#### Carry-forward rules

- Do not tune retrieval from intuition alone; use grounded evaluation evidence.
- Do not label an offline or blocked run as live retrieval proof.
- Low-confidence results must remain distinguishable from grounded answers.

### MS6 — Chat / Logging / Feedback

This phase is implemented across the conversation loop, service, JSON/MySQL
stores, HTTP API, CLI, and Next.js frontend. Controlled product discovery,
hybrid PDF retrieval, unified context, debug traces, and focused evaluators were
also added during MS6.

#### What worked

- The user turn is saved before retrieval; the assistant turn and source
  references are saved after response generation.
- Feedback is linked to an assistant turn through the service/store/API path.
- API, online CLI, unified evaluation, and focused validation reuse production
  service composition where documented.
- Product DB identity/catalog context and PDF technical evidence are assembled
  with explicit provenance.

#### What failed / almost failed

- Role-derived technical permission and deterministic topic/product fallbacks
  overblocked supported cases and were later removed.
- Provider quota failures initially appeared as retrieval failures until stage
  traces isolated `EMBEDDING_FAILED`.
- Correct sourced answers could still disagree with evidence-decision or exact
  evaluator wording, exposing valid-answer-blocking risk.
- One-turn product/topic reuse improved follow-ups, but broad multi-turn memory
  remains outside the proven behavior.

#### Decision changes

- Separate product identity resolution from PDF evidence admission.
- Preserve exact product subject while treating topic terms as information
  needs.
- Keep DB and PDF provenance distinct in context and serialized sources.
- Record the exact model-facing context, response origin, and stage-specific
  failures in opt-in debug/evaluation evidence.
- Use bounded corpus-neighbor expansion and feature-flagged controlled
  retrieval.

#### Tests added

- `tests/test_chat_service.py`
- `tests/test_conversation_loop.py`
- `tests/test_api_server.py`
- `tests/test_controlled_discovery_pilot.py`
- `tests/test_unified_answering.py`
- `tests/test_production_debug_contract.py`
- `tests/test_technical_answer_validation_runner.py`
- `tests/test_unified_answering_eval_runner.py`

#### Carry-forward rules

- Do not infer production behavior from the legacy retrieval-only/chat-eval
  entry points.
- **SUPERSEDED terminology:** Do not use product-role labels or topic terms as a hidden answer-permission mechanism.
- Do not collapse provider/service errors into insufficient-evidence responses.
- Do not claim broad multi-turn memory, full category ancestry, or relationship
  authority beyond the explicit evidence captured for a run.

## Version Lessons

### V1 Engine Loop

The production backend implements the PDF/product-context-to-answer-to-feedback
loop through API and CLI surfaces. Version-level evidence must still separate:

- legacy retrieval-only and chat-eval baselines;
- production-composed unified/focused evaluation;
- offline regression evidence;
- authorized live external-service evidence;
- unsafe-answer controls and valid-answer-blocking controls; and
- immutable run configuration, hashes, sources, and exact model context.

The July 23 remediated five-case live smoke was subsequently authorized and
passed 5/5, clearing that historical Mode B stop condition. V1.5 was later
frozen at tag `irg-ai-v1.5-multisource-baseline` as
`CLOSED - PASS_WITH_WATCH`. V2 is now the active development line; its governed
28,139-point collection was promoted on 2026-08-05 after the final bounded
online set passed 6/6. These milestones do not claim V2.5 pilot completion or
V3 internal-production readiness; those remain governed by
`docs/ROADMAP_TO_INTERNAL_PRODUCTION.md` and `docs/V2_PRODUCT_CONTRACT.md`.

## Lessons Learned — MS4-S1R10

Historical note: these records explain the R10 decision at that time. Current
Gate 10 controls are the structured `G10-*` records above; later MS6 evidence
does not rewrite the R10 closeout.

1. Atomic technical questions are necessary but insufficient.
They prove extraction accuracy but do not prove staff usability.

2. Staff questions are often reverse lookups.
Staff may ask “What is the main burner replacement part for a 24 inch AOG grill?” rather than “What replacement component is part number 24-B-06?”

3. Concise answers can become incomplete answers.
The previous prompt produced technically correct but under-scoped answers such as “Main burner,” which omitted the part number and product scope.

4. Source citations do not replace answer-body fidelity.
A model number or part number in the source path does not count as a clear answer for the user.

5. Applicability scope is safety-critical.
An answer about “24 inch grills” can be misleading if it really applies only to AOG, a specific series, or a specific manual/year.

6. Fitment requires clarification behavior.
When the user gives only partial dimensions or ambiguous product references, the safer V1 behavior is to ask for the missing detail instead of forcing a fitment answer.

7. Fitment should be measured now and built later.
The eval should capture fitment failures and unsafe claims, but full fitment logic belongs in a later iteration.

8. Staff-natural quality is a soft V1 usability signal.
The 70% target helps measure readiness, but answer-style or wording variation does not block V1 unless it causes a safety or supported-answer source-reference failure.

9. Applied fitment is discovery evidence, not a V1 pass-rate gate.
Fitment questions should observe direct-answer and clarification behavior, detect unsafe claims, and create backlog evidence. Safe fitment misses do not fail the overall gate.

10. Safety vetoes remain hard even for report-only question types.
An unsupported fitment answer, unsafe universal compatibility claim, or unsafe fitment claim must fail the overall gate regardless of question-type pass rates.

11. Exact-match scoring can produce V1 false negatives.
Operationally correct, source-cited answers may fail when they omit an exact label, punctuation variant, expected source, or mechanically required scope phrase.

12. Automated diagnostics and release readiness can diverge.
For MS4-S1R10-B, the automated live result remains `FAIL`/`WATCH`, while manual review accepted the implementation for V1 because the safety, citation, prompt-leakage, hardcoding, and collection-mutation checks remained clean.

13. Eval calibration is a separate follow-up slice.
Closing R10-B does not authorize retrieval tuning, fitment logic, threshold reduction, or hiding failures. Staff-natural and applied-fitment results remain visible backlog evidence.
# G10-HEX-001

Lesson ID: G10-HEX-001
Area: Runtime boundaries and grounding
Observation: Entry-point-owned composition, implicit dependency signatures, and
source-presence grounding allowed runtime/evaluation drift.
Evidence: The API imported private CLI factories, controlled retrieval inspected
method signatures, and grounding lacked a separate claim-support state.
Engineering consequence: Composition and major request/evidence/result
boundaries require public typed contracts; citation resolution and claim support
must be separate decisions.
Control or follow-up: Public bootstrap factories, explicit ports, versioned
contracts, negative citation tests, and composition manifests.
Status: PROVEN
Related files or reports: `src/bootstrap/`, `src/runtime_contracts.py`,
`src/citation_validation.py`, `docs/HEXAGONAL_RUNTIME_CONTRACTS.md`

# G10-RELEASE-001

Lesson ID: G10-RELEASE-001
Area: Release control
Observation: A tested integrated dirty tree is evidence of behavior, but it is
not an immutable release and cannot prove which generated, local, or unrelated
paths are required.
Evidence: V1.5 began from committed HEAD `0575638...` with a large integrated
runtime/test/documentation tree plus generated validation outputs and ignored
mutable corpus artifacts.
Engineering consequence: Historical baseline, current committed state,
integrated release tree, local artifacts, and future target must be recorded as
different authorities.
Control or follow-up: Require explicit staging/exclusion manifests, frozen
non-secret configuration and artifact hashes, cached-diff review, annotated
immutable tags, numerical phase gates, and a rollback reference before release.
Status: PROVEN
Related files or reports: `reports/V1_BASELINE_VERIFICATION_20260731.md`,
`reports/V1_5_FINAL_CLOSEOUT_20260731.md`,
`docs/decisions/ADR-017-release-model-and-freeze-control.md`

# G10-V2S3-001

Lesson ID: G10-V2S3-001
Area: Conversational evidence continuity
Observation: Answer-context reuse and durable evidence ancestry are different
decisions. A turn may intentionally exclude prior evidence from the current
model context while still needing the prior state to prevent a second root.
Evidence: V2-S3 Stage 4 retained the same product ref and product ID but set
`use_prior_evidence=false`; coupling lineage hydration to that flag caused a
duplicate-root defect when fresh retrieval returned the same evidence.
Engineering consequence: Product-local lineage compatibility must depend on
owner, authoritative product identity, state coordinates, and collection
identity, not on whether prior evidence is selected for the current answer.
Control or follow-up: Keep context reuse and lineage reuse separate; retain the
parent state when retrieval adds nothing; create one additions-only child when
new evidence appears; observe redundant retrieval until bounded persisted
coverage metadata is separately approved.
Status: PROVEN
Related files or reports: `src/product_runtime_state.py`,
`src/multi_source_retrieval.py`,
`reports/V2-S3_STAGE4_LINEAGE_REPAIR_VALIDATION_20260807.md`,
`reports/V2-S3_FINAL_CLOSEOUT_20260807.md`
