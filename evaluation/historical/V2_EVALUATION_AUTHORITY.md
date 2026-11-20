# IRG AI V2.0 Evaluation Authority

Date: 2026-09-01

Status: `V2_0_EVALUATION_AUTHORITY_BLOCKED`

Branch inspected: `release/v2.0-baseline`

HEAD inspected: `40e02daadbbfc3fcd61d2f07cb3acd799b2cfc90`

Companion manifest: `docs/evaluation/V2_GATE_MANIFEST.json`

## Decision

Repository evidence does not establish an authoritative, immutable, executable
V2.0 dataset for any of V2-G01, V2-G02, V2-G03, V2-G05, V2-G06, V2-G07, or
V2-G18. The retained objectives and thresholds are authoritative, and several
historical artifacts are useful candidate inputs, but population membership,
labels, denominators, exclusions, exact scorers, and approval ownership remain
unresolved.

This document converts that ambiguity into an explicit approval surface. It
does not approve a dataset, create labels, change a threshold, qualify a
release, or authorize an evaluation run. All proposed measurement contracts
below remain `CANDIDATE` until the named owner and reviewer approve frozen
bytes and an evaluator version.

The production corpus remains `CORPUS_v3_RFFM_2026-08-05` at the last recorded
read-only count of 28,139 points. The 49,490-point Docling collection remains a
quarantined, unaliased experiment and is not V2.0 production or gate authority.

## Authority classification rule

Every item in this package uses exactly one of these classifications:

- `AUTHORITATIVE`: approved for the stated current V2.0 measurement.
- `CANDIDATE`: plausible source material requiring review and approval.
- `HISTORICAL`: authoritative or informative only for an older contract/run.
- `SUPERSEDED`: retained evidence whose active semantics were replaced.
- `PARTIAL`: supplies only part of a required population, label, or scorer.
- `UNVERIFIED`: provenance, integrity, or approval cannot be established.
- `INCOMPATIBLE`: uses a different population, unit, runtime, or milestone.

Approval for an older purpose does not make a dataset `AUTHORITATIVE` for
V2.0.

## Authority matrix

| Gate | Purpose | Existing Dataset | Dataset Status | Labels | Denominator Known? | Scoring Known? | Threshold Known? | Approval Known? | Executable Today? | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V2-G01 | Prove every configured/available retrieval lane is attempted or explicitly unavailable | No evaluated-turn lane ledger bound to an approved suite | `UNVERIFIED` | No approved lane expectation per turn | No | Partial runtime diagnostics; no exact gate scorer | Yes: 100% | No | No | Population, required-lane manifest, availability semantics, ledger, scorer, approval |
| V2-G02 | Prevent incorrect product resolution for exact identifiers | Proposed 20 V1.5 exact questions plus 10 local golden exact-model/part questions | `CANDIDATE` | Questions exist; authoritative expected product identity/resolution labels do not | No | Existing runners score other identity/retrieval contracts, not this gate | Yes: >=98% | No | No | Product truth, eligible population, exclusions, V2 scorer, frozen bytes, approval |
| V2-G03 | Measure product resolution for natural staff wording | Proposed 15 V1.5 natural questions plus 8 local staff-natural questions | `CANDIDATE` | Route behavior or source labels exist; approved product/resolution truth does not | No | No exact V2 natural-resolution scorer | Yes: >=90% | No | No | Resolution-state semantics, product truth, population, scorer, frozen bytes, approval |
| V2-G05 | Ensure each resolvable subject in a multi-subject turn receives applicable evidence | Proposed 8 prompt fixtures plus 4 S2D multi-product rows before deduplication | `CANDIDATE` | No approved per-subject resolvability and applicable-evidence truth | No | Runtime coverage fields are reusable; no gate scorer | Yes: >=90% of eligible turns | No | No | Canonical turns, per-subject labels, zero-resolvable policy, scorer, approval |
| V2-G06 | Prevent facts from being attributed to the wrong subject | V2-S3 8-case multi-subject prompt subset and 24 answers; 90-answer review is broader | `CANDIDATE` | Answer-level review exists; no approved atomic-claim ledger, owner truth, or severity rubric | No | Validators are diagnostic proxies, not approved truth | Yes: 0 critical and <=1% of reviewed claims | No | No | Claim segmentation, attribution labels, criticality, stochastic policy, denominator, approval |
| V2-G07 | Resolve follow-up references to the correct prior product/context | Proposed 4 prompt fixtures, 1 S2D row, and 4 Stage 3-6 stages use incompatible representations | `PARTIAL` | Focused assertions exist; no approved transcript-level reference truth | No | Transition tests are reusable; no percentage scorer | Yes: >=90% | No | No | Canonical multi-turn transcripts, expected references, eligibility, scorer, approval |
| V2-G18 | Bound application-origin failures during release qualification | Existing runners record errors/timeouts, but no approved release-suite ledger | `PARTIAL` | Runtime classifications exist but retry/exclusion authority does not | No | `src/full_suite_evaluation.py` provides a partial counter | Yes: <=1%, excluding intentionally unavailable external services | No | No | Exact suite denominator, logical-attempt unit, retry rules, external-unavailable rules, scorer approval |

No required gate is executable today.

## Dataset inventory

### Potentially relevant datasets and runs

| Dataset or evidence | Format / count | Date and corpus/runtime | Potential gates | Labels and scoring actually present | Historical result | Classification | V2.0 validity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Historical V1 golden snapshot, recorded as `data/golden_questions.jsonl` | JSONL; 30 defined, 29 enabled; recorded SHA-256 `8af11212536e253e04575f32d3e4adcca01bad2299973f94733ab55350442a61` | V1/V1.5 PDF retrieval; exact bytes absent from current Git/tag | G02, G03 source material | Expected source/page/answer terms/identifiers; no authoritative DB product-resolution label | Retrieval 23/29; atomic 19/19; staff-natural 3/8; fitment 1/2 | `HISTORICAL` | Wrong measurement contract; natural subset was WATCH; frozen bytes cannot be recovered |
| Current local `data/golden_questions.jsonl` | JSONL; 30 rows, 29 confirmed and 1 candidate; SHA-256 `763c3ec1e5dcfc0fe55d092d58debac9df9a139ea8f0821873303ac8a94cb7be` | Ignored local successor, modified 2026-08-04; production corpus-era source labels | G02: 10 exact-model/part; G03: 8 staff-natural | Source/page/answer/identifier labels; no approved DB product identity/resolution truth | Used in later retrieval runs | `CANDIDATE` | Bytes differ from V1 authority and have no V2 population/label approval |
| `data/evals/v1_5_controlled_discovery.jsonl` | JSONL; 60 rows; SHA-256 `562fd04f49d811bca773ab6714ba6c5c34f093b79f4d6a7426b71cf2ac19c221` | Added at `1e59dfb`, preserved in V1.5 tag | G02: 20 exact; G03: 15 natural | Expected route, candidate behavior, DB authority, and safety; no expected product IDs | Live proof was exact 1/1, natural 2/2 candidate-return, handoff 1/1, not the 60-row semantic set | `HISTORICAL` | Immutable for its original controlled-pilot purpose but missing current gate truth |
| `data/evals/v1_5_unified_answering.jsonl` | JSONL; 80 current rows; current SHA-256 `0fd2499dd0c63a65ae3dd3caecc0bb6bca328d20901c13f76c264fa5795e7dbd`; historical recorded hash `bf360d86f5ffbe3ec1c6652ac5676328cd8bd3e155d463c294b0155a1d6fe967` | Historical MS6 unified answering | G02, G03, G18 conceptual overlap | Product/source/document/fact labels plus removed role-resolution semantics | Original 0/80; corrected 15/80; supported subset 15/15; audit found 51 invalid product identities and 9 invalid document expectations | `SUPERSEDED` | Active scoring contract excludes affected semantics; current bytes differ from historical authority |
| `data/evals/ms6_s4r2_identity_resolution_evidence_gate.jsonl` | JSONL; 50 rows; SHA-256 `636f4d34fcb51db19839f6c2df0520aeb16baeb394e848e7f5b41981f462f622` | Historical MS6-S4R2 | G02, G03 conceptual overlap | Identifier parsing and removed role/evidence states; incomplete expected-product truth | Focused implementation checks passed | `SUPERSEDED` | Explicitly non-gating in `docs/EVALUATION_SCORING_CONTRACT.md` |
| `data/evals/ms6_s5_technical_answer_validation.jsonl` | JSONL; 11 rows; SHA-256 `74dc7ac5e76462778dbc43269e89c991d7c209848e188c195fbc82f51c16cfcd` | Historical technical-answer path | G02, G18 partial overlap | Some product IDs/models, resolution, source, answer terms, response status | 11/11 executed with zero runtime errors; one relationship case left final status FAIL | `PARTIAL` | Too narrow, no natural-staff population, and no V2 approval |
| `reports/V2_S2D_RETRIEVAL_RESULTS.jsonl` and `reports/V2_S2E_RETRIEVAL_RESULTS.jsonl` | JSONL result rows; 51 each; SHA-256 `d740db2c8c41b6a0a0f50531d22c6b304832a39ee6226cb07692674b1b5087c4` / `4dd7cf057d9d911056b22572632121013305be65b9133c97e5943c8fa359720e` | Committed at `0f91884`; governed-corpus retrieval | G02/G03 diagnostic; G05 has 4 multi-product rows; G07 has 1 follow-up-context row | Expected document/manufacturer/model/evidence; 22 corpus-derived rows lack independent approval | 39/46 supported rows passed aggregate identity = 84.78% | `CANDIDATE` | Mixed categories/units; results are not a frozen question/label authority; derived rows unapproved |
| V2-S3 stratified selection and adjudication under `.tmp/v2-s3-validation-experiment-20260807/` | JSON; 30 cases, 90 answers; selection SHA-256 `640e5a9860a0d6c9cbaa4614c509782e33304350c059f422b616ee253ceac056`; adjudication SHA-256 `9e61a0c9c49a5914cdc66c59f2115e97a7972ea2089f1deaf0947b48b297f088` | 2026-08-07 prompt replay on frozen evidence, three prompt arms | G05: 8 multi-subject cases; G06: 24 corresponding answers; G07: 4 follow-up/reuse fixtures | Direct answer review; no retrieval, persistence, evidence-state, or claim-level gate ledger | 90/90 calls; unsupported factual claims 0/30, 0/30, 1/30 by arm; structural invariants explicitly indeterminate | `CANDIDATE` | Frozen for an observe-only prompt experiment, uncommitted, and not approved as V2 gate population |
| V2-S3 Stage 3-6 scenario and focused tests | Python fixtures/assertions; one live sequence plus deterministic unit/fault cases | Committed at current HEAD for V2-S3 implementation | G05, G07 | Explicit ownership, continuity, ordinal, persistence, and lifecycle assertions | Focused invariant suites pass | `PARTIAL` | Strong regression evidence but not an approved population or percentage denominator |
| Provider batch-2 and Gate-3 rescue cohorts on separate refs | JSONL; 30 provider fixtures and 16 combined adjudicated cases; hashes recorded in August 26 report | V2.4/local-provider evaluation, not current V2.0 runtime | G02/G03 conceptual overlap | Rich provider-generation and identity labels | Rescue resolution 7/16; activation HOLD | `INCOMPATIBLE` | Different provider, runtime, metric, branch, and milestone |
| Docling frozen 78-case comparison set and 8-document targeted holdout | JSON/report artifacts; 78 retrieval cases; frozen comparison hash `3428b7526dc628af62bb9e6b307adead5fa4d76b509b90b01c1f0d46c51bdf76` | 49,490-point quarantined shadow versus production; not promoted | Future V2.1 structural evaluation; no exact current V2.0 gate | Expected source/page/identifier/structural evidence, not DB resolution or multi-turn truth | `SHADOW_RETRIEVAL_MIXED`; later `NO_TUNING_GAIN`; targeted holdout 3/8 | `INCOMPATIBLE` | Useful future structural candidate material only; not current production or V2.0 gate authority |

The inventory does not merge similar questions. Any approved population must
copy or reference exact reviewed rows into a new versioned artifact only after
the owner resolves semantic duplicates and label authority.

## Proposed gate contracts

The following are minimum recommended contracts, not approvals.

## V2-G01 - Retrieval lane accounting

### Purpose

Catch silent loss or bypass of a configured DB or PDF retrieval lane.

### Evaluation Population

Recommended: every executed turn in the approved union of V2-G02, G03, G05,
G06, and G07 qualification cases. The run manifest must freeze the set of
configured lanes before execution.

### Ground Truth

For each turn, each configured lane is required unless the frozen manifest
marks it intentionally unavailable with an approved reason. Runtime evidence
must record one terminal state per required lane: `ATTEMPTED` or
`EXPLICITLY_UNAVAILABLE`.

### Dataset Authority

No current dataset or evaluated-turn ledger is approved. Candidate population:
the future approved union above. Classification: `UNVERIFIED`.

### Numerator

Count of eligible turns for which every required lane has exactly one valid
terminal accounting record.

### Denominator

Recommended: all scheduled eligible turns, including runtime failures and
abstentions. Current authoritative denominator: unresolved.

### Exclusions

Recommended: exclude only lanes absent from the frozen configuration. Do not
exclude a turn because a configured service failed, returned no evidence, or
the answer abstained. Intentional external unavailability must be declared
before the run and independently evidenced.

### Scoring Procedure

Freeze required lanes; execute each turn once; validate unique terminal lane
records; count a turn only when the entire required set is accounted for.
Current runtime diagnostics expose DB/PDF detail but no canonical gate ledger
or exact scorer.

### Pass Threshold

100% of eligible turns.

### Failure Semantics

Any missing, duplicate, unknown, or post-hoc unavailable lane record fails the
turn and therefore the gate.

### Reproducibility

Freeze corpus/collection identity, branch/commit, runtime composition manifest,
configured lane set, dataset hashes, evaluator version, provider/model/prompt
identities, and first-attempt record. Randomness policy is unresolved where
turn analysis uses a model.

### Evidence Artifacts

Run manifest, scheduled-turn ledger, per-turn lane ledger, exclusions ledger,
per-turn results, numerator/denominator summary, and hashes.

### Approval

Owner: V2 product/release owner plus designated evaluation/data reviewer.

Status: `BLOCKED`.

Date: null.

Evidence: none.

### Open Questions

- Approve the union population and whether runtime-failed turns remain in this
  denominator.
- Approve pre-run intentional-unavailability evidence.
- Engineering must add/freeze the canonical lane ledger and scorer.

## V2-G02 - Exact-identifier product resolution

### Purpose

Catch wrong or ambiguous product identity when staff supplies an exact model,
MPN, SKU, UPC, or part identifier.

### Evaluation Population

Recommended candidate: semantic-deduplicated review of CD-001 through CD-020
plus GQ-001 through GQ-006 and GQ-021 through GQ-024. Include only cases whose
identifier and expected product identity are valid in the frozen read model.

### Ground Truth

Each row must carry identifier type/literal/normalized value, expected
resolution state, authoritative product ID, canonical model/MPN, allowed
equivalent identities, and label-source evidence from the approved read model.

### Dataset Authority

No approved V2 dataset exists. The 30-row source inventory is `CANDIDATE`; it
must not be frozen until product identities and duplicates are reviewed.

### Numerator

Eligible cases whose runtime resolution state and resolved product identity
exactly match the approved label.

### Denominator

Recommended: every approved eligible exact-identifier case. Runtime errors,
wrong-product results, clarification, abstention, and no-match responses count
as failures unless that response state is explicitly the approved truth.
Current authoritative denominator: unresolved.

### Exclusions

Recommended pre-freeze exclusions only: invalid identifier, no authoritative
read-model truth, duplicate semantic case, or product outside the declared V2
scope. Missing corpus PDF evidence is not a product-resolution exclusion.

### Scoring Procedure

Execute through current production composition; compare normalized actual
resolution state and stable product identity with the frozen label; record
candidate list and route diagnostically. PDF retrieval rank is not this gate.

### Pass Threshold

At least 98%. A 30-case denominator requires 30/30; 29/30 is 96.67%.

### Failure Semantics

Wrong product, unresolved/clarification contrary to truth, missing result,
runtime failure, or label/evaluator integrity failure blocks the gate.

### Reproducibility

Freeze dataset bytes/hash, read-model schema/procedure identity and snapshot
evidence, branch/commit, corpus identity, runtime composition, turn-analysis
prompt/model, evaluator version, and top-k/configured bounds. Temperature and
seed are currently omitted by the provider path and must be recorded as such;
repeat policy requires approval.

### Evidence Artifacts

Manifest, dataset validation, per-case expected/actual identity, response and
diagnostic capture, error ledger, score summary, and hashes.

### Approval

Owner: V2 product/release owner plus designated product-data reviewer.

Status: `BLOCKED`.

Date: null.

Evidence: none.

### Open Questions

- Approve population membership and semantic deduplication.
- Supply/approve product truth and equivalent-identity policy.
- Approve treatment of exact identifiers with multiple valid products.
- Engineering must implement/freeze the exact V2 scorer and schema validator.

## V2-G03 - Natural staff product resolution

### Purpose

Catch wrong product selection or unsafe certainty when staff uses natural,
incomplete, or descriptive product language.

### Evaluation Population

Recommended candidate: semantic-deduplicated review of CD-021 through CD-035
plus GQ-021 through GQ-028, after resolving the historical WATCH disposition.

### Ground Truth

Each row needs an approved resolution class (`UNIQUE_PRODUCT`,
`MULTIPLE_PLAUSIBLE`, `NO_SUPPORTED_MATCH`), expected product identity or
candidate set, required clarification facts, and read-model evidence.

### Dataset Authority

No approved V2 natural-staff dataset exists. The 23-row inventory is
`CANDIDATE`; historical route labels and PDF source labels are insufficient.

### Numerator

Recommended: eligible cases whose resolution class, product/candidate identity,
and required clarification behavior match all approved labels.

### Denominator

Recommended: all approved eligible natural-staff cases. Runtime failures and
incorrect abstentions/clarifications count as failures. Whether correctly
clarifying ambiguous cases counts as successful resolution requires owner
approval. Current authoritative denominator: unresolved.

### Exclusions

Recommended pre-freeze exclusions only: duplicate case, invalid/out-of-scope
request, or absent authoritative label. Do not exclude a case because the
runtime currently fails it.

### Scoring Procedure

Run current production composition; compare resolution class, stable product or
candidate identities, and clarification requirements. Do not substitute PDF
retrieval recall, route selection, or candidate presence for correct product
resolution.

### Pass Threshold

At least 90%. A 23-case denominator requires at least 21/23.

### Failure Semantics

Wrong identity/candidate set, unsafe unique resolution, unnecessary or missing
clarification, runtime failure, or integrity failure blocks the case.

### Reproducibility

Same frozen runtime/read-model requirements as V2-G02, plus exact natural
question text, turn-analysis model/prompt identity, provider response model,
and approved repeat policy. Temperature/seed are omitted today and must be
recorded, not invented.

### Evidence Artifacts

Manifest, dataset/label validation, per-case resolution comparison, candidate
and clarification evidence, error ledger, summary, and hashes.

### Approval

Owner: V2 product/release owner plus designated product-data reviewer.

Status: `BLOCKED`.

Date: null.

Evidence: none.

### Open Questions

- Approve whether correct clarification is a successful resolution.
- Approve population, product/candidate truth, and ambiguity labels.
- Approve repeat policy for model-backed turn analysis.
- Engineering must implement/freeze the exact scorer and schema validator.

## V2-G05 - Multi-subject applicable evidence coverage

### Purpose

Catch turns where one resolvable requested subject is omitted or receives
evidence belonging to another subject.

### Evaluation Population

Recommended candidate: review and semantic deduplication of the eight V2-S3
two-/three-product fixtures and four S2D multi-product rows. Canonical rows must
execute retrieval rather than replay frozen context.

### Ground Truth

Each turn must enumerate requested subjects, approved resolvability per subject,
stable expected product identity, required evidence class, and at least one
approved applicable DB/PDF evidence identity for every resolvable subject.

### Dataset Authority

No approved population exists. The 12 source entries are `CANDIDATE`; the
Stage 3-6 scenario is `PARTIAL` supporting regression evidence.

### Numerator

Eligible multi-subject turns for which every resolvable requested subject has
at least one admitted applicable evidence record owned by that subject.

### Denominator

Recommended: eligible multi-subject turns with at least one resolvable subject,
counted once per turn. A turn fails if any resolvable subject lacks applicable
evidence. Zero-resolvable turns should be excluded from this gate but retained
for lane/runtime gates. Current authoritative denominator: unresolved.

### Exclusions

Recommended pre-freeze exclusions only: semantic duplicate, fewer than two
requested subjects, or no authoritative per-subject truth. Unresolved subjects
are not evidence omissions but must carry an explicit resolution record.

### Scoring Procedure

Execute the normal multi-product path at frozen production bounds (recommended
top-k 5); compare runtime requested-product groups, resolution states,
applicability decisions, evidence IDs, and owners to the labels; score one
boolean per turn.

### Pass Threshold

At least 90% of eligible turns. A 12-turn denominator requires at least 11/12.

### Failure Semantics

Missing subject, missing applicable evidence, wrong evidence owner,
non-applicable evidence admitted as qualifying, runtime failure, or integrity
failure fails the turn.

### Reproducibility

Freeze dataset/corpus/read-model identities, runtime composition, top-k and
context bounds, turn-analysis and answer prompt/model identities, evaluator
version, and exact per-subject labels. Record omitted provider controls and the
approved repeat policy.

### Evidence Artifacts

Per-turn subject/label ledger, requested-product diagnostics, applicability and
evidence-owner ledger, context manifest, exclusions, summary, and hashes.

### Approval

Owner: V2 product/release owner plus product-data and technical-evidence
reviewers.

Status: `BLOCKED`.

Date: null.

Evidence: none.

### Open Questions

- Approve canonical population and semantic deduplication.
- Approve resolvability and applicable-evidence truth per subject.
- Approve turn-level denominator and zero-resolvable exclusion.
- Engineering must implement/freeze the scorer over existing diagnostics.

## V2-G06 - Cross-subject attribution defects

### Purpose

Catch claims that transfer facts, values, compatibility, procedures, or
warnings from one requested subject to another.

### Evaluation Population

Recommended: model answers produced for the approved V2-G05 multi-subject
turns. The prompt-replay answers may inform reviewer training but cannot replace
a production-path qualification run.

### Ground Truth

Every atomic factual claim needs a human-approved subject owner or explicit
shared/comparison classification, supporting evidence IDs, defect status, and
severity. The criticality rubric must identify safety, fitment, compatibility,
installation, and other owner-approved critical categories.

### Dataset Authority

No claim-level dataset is approved. The V2-S3 reviewed answers are `CANDIDATE`;
validator outputs are not ground truth.

### Numerator

Two reported values are required: critical cross-subject defects, and all
cross-subject attribution defects.

### Denominator

Recommended percentage denominator: all human-reviewed atomic factual claims
in valid completed answers for the approved population. Non-factual prose and
citations without claims are excluded. Runtime-failed turns remain failures in
V2-G18 but yield no claim denominator. Current authoritative denominator and
claim segmentation method: unresolved.

### Exclusions

Only predeclared non-factual text, verbatim user question, and formatting may be
excluded. Shared/comparative claims remain included and require every premise
owner. Do not exclude claims because a validator missed or false-alarmed them.

### Scoring Procedure

Freeze outputs; segment claims under an approved deterministic-plus-human
protocol; blind reviewers to prompt arm where applicable; compare each claim's
subject and evidence owners; adjudicate disagreements; emit claim-level labels.
Existing citation/grounding validators are review aids only.

### Pass Threshold

Zero critical defects and no more than 1% attribution defects among reviewed
claims. Both conditions are conjunctive.

### Failure Semantics

Any critical defect fails immediately. Total defects above 1%, missing required
claim review, unadjudicated disagreement, output-integrity failure, or an
unapproved generation configuration fails the gate.

### Reproducibility

Freeze question/context bytes, corpus/read-model/runtime identities, answer and
analysis prompt hashes, requested/response model, provider, omitted
temperature/seed, retry policy, raw outputs, claim-segmentation version,
reviewer protocol, and adjudication. Statistical confidence intervals are not
required by the inherited gate but may be reported; repeat count requires
approval.

### Evidence Artifacts

Raw answer ledger, immutable context packets, atomic-claim ledger, blinded
reviews, adjudication ledger, severity rubric/version, numerator/denominator
summary, and hashes.

### Approval

Owner: V2 product/release owner plus designated technical/safety reviewers.

Status: `BLOCKED`.

Date: null.

Evidence: none.

### Open Questions

- Approve claim segmentation and shared/comparative-claim rules.
- Approve criticality rubric, reviewer qualifications, and adjudication.
- Approve generation repeat/retry policy and completed-answer denominator.
- Engineering must implement/freeze claim-ledger and score aggregation.

## V2-G07 - Follow-up reference resolution

### Purpose

Catch pronoun, ordinal, alias, or implicit follow-up turns that attach to the
wrong prior product or lose restart-safe reference continuity.

### Evaluation Population

Recommended: create reviewed canonical multi-turn transcripts from the four
V2-S3 follow-up/reuse fixtures, the S2D follow-up concept, and Stage 3-6
scenarios. Do not count prompt replays or single questions with antecedent text
as equivalent to persisted conversations.

### Ground Truth

Each scored follow-up turn must specify prior turns and product state, literal
current question, expected referenced `product_ref_id` values and product
identities, expected resolution/clarification state, and allowed evidence
lineage behavior.

### Dataset Authority

No approved transcript dataset exists. Existing representations are `PARTIAL`
and incompatible as one denominator until migrated and reviewed.

### Numerator

Eligible follow-up turns whose resolved prior references, product identities,
and required clarification state exactly match the approved labels.

### Denominator

Recommended: every approved labeled follow-up turn, counted per current user
turn. Runtime failures, wrong references, and unjustified clarification count
as failures. Current authoritative denominator: unresolved.

### Exclusions

Recommended pre-freeze exclusions only: no actual anaphoric/ordinal/alias
reference, invalid prior state, duplicate transition, or missing authoritative
label. Restart cases should remain included as a declared cohort.

### Scoring Procedure

Initialize the frozen transcript/state; execute the literal follow-up through
the production service and persistence path; compare selected prior references,
product identity, response state, and lineage to labels; score one boolean per
follow-up turn.

### Pass Threshold

At least 90%. If the approved denominator is nine turns, all nine must pass
because 8/9 is 88.89%.

### Failure Semantics

Wrong/missing prior reference, prior-subject contamination, non-persistent
identity, incorrect clarification, runtime failure, or integrity failure fails
the turn.

### Reproducibility

Freeze transcripts, initial persistence state, branch/commit, runtime and store
composition, model/prompt identities, corpus/read-model identity, evaluator
version, provider controls, and repeat policy. Run restart cohorts with the
same persisted bytes across process restart.

### Evidence Artifacts

Transcript manifest, before/after persisted state, per-turn reference labels
and actuals, evidence-lineage ledger, restart evidence, summary, and hashes.

### Approval

Owner: V2 product/release owner plus designated conversation-behavior reviewer.

Status: `BLOCKED`.

Date: null.

Evidence: none.

### Open Questions

- Approve canonical transcript population and migration of old fixtures.
- Approve reference/clarification truth and restart cohort requirements.
- Approve turn-level denominator and repeat policy.
- Engineering must implement/freeze the transcript runner and scorer.

## V2-G18 - Release-evaluation runtime failure rate

### Purpose

Prevent a favorable quality score from hiding application, evaluator,
provider, timeout, or orchestration failures during qualification.

### Evaluation Population

Recommended: every scheduled logical evaluation turn in the approved V2.0
qualification plan, identified before execution. Multi-turn cases contribute
their scheduled scored turns; repeated reviewer work does not add runtime
units.

### Ground Truth

Each scheduled unit needs a terminal state: valid result,
application-origin failure, evaluator/integrity failure, externally unavailable
before execution, or canceled by an approved global hard stop. Failure origin
must be evidence-backed, not inferred from a missing output.

### Dataset Authority

No approved release-suite ledger exists. Existing runner summaries are
`PARTIAL` reusable engineering.

### Numerator

Recommended: scheduled units without a valid result because of an
application-origin runtime failure, including exhausted timeout/retry behavior.
Whether evaluator/integrity failures join this numerator or hard-stop the run
separately requires approval.

### Denominator

Recommended: all scheduled units except services explicitly declared
intentionally unavailable before the run under an approved exclusion. A retry
does not create a new denominator unit. Current authoritative denominator:
unresolved.

### Exclusions

Only pre-run intentional external-service unavailability with service, reason,
owner, and evidence. Do not exclude unexpected provider errors, application
timeouts, invalid outputs, skips, aborts, or cases omitted after the run starts.

### Scoring Procedure

Freeze scheduled units; reserve one logical attempt ID per unit; record every
physical attempt/retry; classify terminal origin under the approved taxonomy;
verify ledger completeness; calculate failure units divided by denominator.

### Pass Threshold

At most 1%, excluding approved intentional external unavailability.

### Failure Semantics

Rate above 1%, incomplete ledger, duplicate/missing logical IDs, unapproved
exclusion, or inability to establish failure origin blocks qualification.

### Reproducibility

Freeze suite manifest, case/turn IDs, runtime composition, timeout/retry rules,
provider/model/prompt identities, corpus/read-model identity, evaluator
version, environment availability manifest, and raw attempt ledger.

### Evidence Artifacts

Scheduled-unit manifest, attempt/retry ledger, terminal-state ledger,
availability/exclusion approvals, failure-origin evidence, score summary, and
hashes.

### Approval

Owner: V2 product/release owner plus evaluation owner and service owner for any
intentional-unavailability exclusion.

Status: `BLOCKED`.

Date: null.

Evidence: none.

### Open Questions

- Approve logical turn/case unit and the exact suite union.
- Approve retry, timeout, skip, abort, and evaluator-failure semantics.
- Approve the narrow intentional-unavailability rule.
- Engineering must extend/freeze the runtime ledger and exact scorer.

## Gap analysis

| Gate | Engineering missing | Data/label missing | Scoring-contract missing | Business/owner approval missing |
| --- | --- | --- | --- | --- |
| V2-G01 | Canonical required-lane/terminal-state ledger and scorer | Approved evaluated-turn union and required lanes | Availability/exclusion and failed-turn denominator semantics | Population, lanes, exclusions, denominator |
| V2-G02 | V2 identity schema validator, production runner, exact scorer | Stable product IDs, resolution truth, duplicate decisions | Equivalent identity, ambiguity, runtime-failure treatment | Population, labels, exclusions, scorer |
| V2-G03 | Natural-resolution runner/scorer | Product/candidate truth, ambiguity and clarification labels | Whether correct clarification counts, repeat policy | Population, labels, semantics, scorer |
| V2-G05 | Per-turn all-subject scorer over existing diagnostics | Per-subject resolvability and applicable evidence IDs | Turn denominator, zero-resolvable and unresolved-subject policy | Population, labels, exclusions, scorer |
| V2-G06 | Claim ledger, review import, adjudication and aggregation | Atomic claims, subject/evidence ownership, severity | Segmentation, criticality, completed-answer and repeat rules | Reviewer authority, rubric, denominator, scorer |
| V2-G07 | Canonical transcript runner and reference scorer | Prior state, expected references, identity and clarification truth | Transition unit, restart cohort, repeat policy | Population, labels, exclusions, scorer |
| V2-G18 | Scheduled-unit and attempt/retry ledger; terminal-origin scorer | Approved qualification suite manifest | Logical unit, retries, timeouts, skips, aborts, external-unavailable semantics | Suite, exclusions, denominator, scorer |

These are governance/data gaps plus bounded evaluator engineering. They are not
serving defects and do not authorize retrieval, corpus, prompt, or runtime
tuning.

## Minimum approval package

| Decision | Recommendation | Alternative | Effect |
| --- | --- | --- | --- |
| Gate population | Approve versioned semantic-deduplicated manifests derived from the candidate source inventories | Author a new independently reviewed set | Fixes exact case membership and enables hashes/counts |
| Label authority | Require product-data reviewer for identity labels and technical reviewer for evidence/claim labels | Single release-owner approval | Determines whether ground truth is independent and auditable |
| V2-G02 exact semantics | Score exact stable product identity and resolution state; wrong clarification/abstention fails | Permit candidate-set credit | Changes numerator and potentially weakens exact resolution |
| V2-G03 ambiguity semantics | Count approved correct clarification/candidate-set behavior as correct resolution | Score only unique product IDs | Determines labels and denominator for natural staff cases |
| V2-G05 unit | One multi-subject turn; every resolvable subject must have applicable owned evidence; exclude zero-resolvable turns | Per-subject denominator | Preserves the inherited turn-level wording and prevents large turns from dominating |
| V2-G06 claim protocol | Human-reviewed atomic claims with shared/comparison premises and a signed severity rubric | Validator output as truth | Determines denominator and critical defects; recommended choice avoids proxy authority |
| V2-G07 representation | Canonical persisted multi-turn transcripts, including restart cohort | Prompt replay or antecedent embedded in one question | Determines whether actual reference continuity is measured |
| V2-G18 runtime unit | Scheduled logical turns; retries do not add units; unexpected failures are not excluded | Physical attempts or completed results only | Prevents retries/omissions from diluting failure rate |
| External unavailability | Allow exclusion only when declared before execution with owner/evidence | Exclude any provider/service failure after the fact | Prevents post-hoc denominator changes |
| Model repeatability | Freeze one first logical completion per case and separately report retries; approve a repeat cohort only if desired before freeze | Multiple unplanned reruns and best-result selection | Prevents stochastic cherry-picking |
| Thresholds | Retain 100%, 98%, 90%, 90%, 0 critical/1%, 90%, and 1% exactly | Replace/retire through a separate signed decision | Preserves the active historical crosswalk |
| Release effect | Keep all seven gates conjunctive and release-blocking | Make one or more advisory | Determines whether a failure can block V2.0 |

The owner should approve only these decisions plus the final labeled row
manifests. Counts and hashes should then be derived automatically.

## Exact path to executable qualification

1. Name the V2 product/release owner and independent product-data,
   technical-evidence, safety/claim, and evaluation reviewers.
2. Approve the decision table above or record explicit alternatives.
3. Materialize one canonical, versioned dataset/transcript/claim schema per gate
   without altering the historical inputs.
4. Review every candidate row, resolve semantic duplicates and ambiguous or
   missing labels, and record source evidence for each label.
5. Freeze dataset bytes, counts, eligible populations, exclusions, corpus/read
   model identity, and SHA-256 hashes.
6. Implement only the missing generic schema validators, ledgers, and scorers;
   do not change retrieval, generation, prompts, corpus, or production data.
7. Freeze evaluator versions and run focused offline contract tests using
   synthetic fixtures, not the approval dataset as a tuning target.
8. Update `V2_GATE_MANIFEST.json` with exact paths, hashes, counts, denominators,
   evaluator versions, approvers, dates, and `APPROVED` statuses.
9. Construct the isolated V2.0 release candidate from the separately approved
   allowlist and freeze its commit/configuration identity.
10. Verify production corpus/read-model identities read-only and record service
    availability before execution.
11. Execute retrieval/transition gates G01, G02, G03, G05, and G07 once against
    the frozen plan; never change labels after viewing results.
12. Execute G06 generation/review under the frozen provider/prompt/retry and
    claim-review protocol.
13. Calculate G18 from the predeclared scheduled-unit and attempt ledgers.
14. Emit per-item results, exclusions, failures, numerators, denominators,
    metrics, environment/configuration manifests, and hashes.
15. Apply every threshold conjunctively and classify V2.0 `PASS` or
    `V2_0_RELEASE_BLOCKED`. Do not tune against failed cases inside the same
    frozen qualification run.

## Required immutable package after approval

Use one canonical location rather than parallel sources of truth:

```text
evaluation/v2/
  manifest.json
  datasets/
    V2-G01_<version>.jsonl
    V2-G02_<version>.jsonl
    V2-G03_<version>.jsonl
    V2-G05_<version>.jsonl
    V2-G06_<version>.jsonl
    V2-G07_<version>.jsonl
    V2-G18_<version>.jsonl
  contracts/
    V2-G01.md
    V2-G02.md
    V2-G03.md
    V2-G05.md
    V2-G06.md
    V2-G07.md
    V2-G18.md
  hashes/
    SHA256SUMS
  README.md
```

Do not create this executable tree until the population and labels are
approved. The current `docs/evaluation/` files are governance proposals, not
executable datasets.

## Historical-result invalidity under the recovered contracts

- V1 golden retrieval scores expected PDF source/page/terms, not authoritative
  DB product resolution for V2-G02/G03; its exact frozen bytes are also absent.
- V1.5 controlled discovery labels routes and candidate behavior but not stable
  expected product identities; its tiny live subset is not the 60-row set.
- Unified-answering results contain superseded role semantics, invalid product
  and document expectations, and historical/current hash mismatches.
- The V2-S2E 84.78% value mixes categories and scores retrieval product/model
  identity over 46 supported rows. It is neither the exact-only G02 rate nor
  the natural-staff G03 rate.
- V2-S3 prompt replay did not execute retrieval, persistence, or evidence-state
  transitions, so it cannot score G01, G05, or G07. Its answer review lacks the
  atomic reviewed-claim denominator required by G06.
- Focused Stage 3-6 tests prove implementation invariants but do not supply an
  approved percentage population.
- Provider/Gate-3 rescue evidence used a different V2.4 provider/runtime and
  cannot qualify the current OpenAI-backed V2.0 path.
- Docling evidence measures a quarantined structural retrieval candidate, not
  the production collection or these V2.0 product/multi-turn gates.
- Historical zero-runtime-failure claims apply only to their own selected runs;
  none binds a predeclared complete V2.0 scheduled-unit denominator.

## Current-state update after approval

This task does not change `docs/chatgpt_project/CURRENT_STATE.md`. After all
seven manifest entries have approved datasets, hashes, denominators, scorers,
owners, and dates, the accurate update would be: evaluation authority approved
and qualification executable, but V2.0 remains release-blocked pending an
isolated candidate run. Only a complete passing qualification can change the
release result.

## Mutation statement

- Serving code, tests, prompts, runtime configuration, datasets, corpus,
  Qdrant, MySQL, providers, processes, and deployment changed: no.
- Historical datasets copied, relabeled, or promoted: no.
- Live evaluation executed: no.
- Git stage/commit/tag/push/merge: no.

## 2026-09-02 artifact-contract hardening addendum

The V2 master evaluation population v1 is `AUTHORITATIVE_FROZEN`, approved by
Aaron on 2026-09-02. This freezes its scenario membership, labels, historical
triage decisions, expectation-unit structure, authority references, gate
applicability, and release classifications. The separate gate-scorer and
evaluator-implementation approvals remain blocked and no qualification has run.

The master-population schema uses immutable expectation units beneath each
scenario's scored turn. Every scenario has at least one expectation. Each unit
has a globally unique ID, its own expected state, release classification,
blocking effect, local scoring paths, severity, and references to the
scenario-owned identity, claim, source, clarification, and unsupported-claim
authority. Mixed scenarios therefore have independently scored blocking and
non-blocking requirements without changing scenario membership or labels.

Artifact version `v1` is decision-locked once its canonical manifest records
`immutability.version_locked = true`. `BUILD_CANDIDATE` cannot overwrite that
version. `VERIFY_FROZEN` checks canonical hashes, counts, schema, references,
and invariants, regenerates a candidate only in temporary storage, compares
all frozen historical decisions, and leaves canonical bytes untouched. Any
population, label, or include/exclude correction requires a new artifact
version, new hashes, and new approval. Verification timestamps and duration may
be written only to a separate, non-canonical verification ledger.

G01 and G18 are global ledger-derived gates, not scenario-tag populations:

- G01 includes every logical attempt where `qualification_eligible == true`
  and `retrieval_invoked == true`. Its numerator is the subset with valid
  required-lane accounting, and its threshold remains 100%.
- G18 includes every logical attempt where `qualification_eligible == true`.
  `SYSTEM_FAILURE` counts in its numerator. `RUN_INVALIDATION` invalidates the
  full affected run, never becomes an exclusion, and requires a complete rerun;
  an individual retry cannot erase a logical-attempt failure. Its threshold
  remains at most 1%.

For every gate, 100% of the pre-frozen applicable population stays in the
denominator. No post-run exclusion exists. Generation-dependent gates retain
the approved three-complete-run policy using the same frozen population,
provider/model, prompt, and deterministic or lowest-supported stochasticity.
There is no best-of-three selection and no individual failed-case retry
selection. G06 retains zero critical unsupported claims across all required
runs and at most 1% unsupported substantive claims overall, with the existing
critical, major, and minor severity definitions.

## 2026-09-02 scorer-contract v1 approval addendum

Aaron approved and froze `docs/evaluation/V2_GATE_SCORER_CONTRACTS_v1.md` as
`AUTHORITATIVE_FROZEN` on 2026-09-02. The pre-approval candidate SHA-256 was
`e01bd5ea5673200c03c1aa2a87ce902b92221dd592a850184823c7e29dd5bc70`;
the approved post-amendment SHA-256 is
`7a376ba1ab2775431625468b6e45bc9c859aff2a01c180c80118f9845f556be0`.
The frozen population and historical-triage hashes remain
`4b561ffea79edc97c270cda38fbd0e5351615c0acd8d8be4eab291a3d504bd8e`
and `8dc936cb0d7c600fdad13592f45f2b564ff8c0b41e9050294373f19432a25e2d`.

The approval records D1 `APPROVED`, D2
`APPROVED_WITH_CLARIFICATION`, D3 `APPROVED`, D4
`APPROVED_WITH_COMPLETENESS_CONTROL`, D5 `APPROVED`, D6
`APPROVED_AS_AMENDED`, and D7 `APPROVED`. In particular, G02/G03 score the
final canonical resolved/admitted identity set while raw discovery candidates
remain diagnostic; G05 has a complete-run veto for any critical
safety/fitment cross-subject contamination; G06 requires human confirmation
that every substantive response claim appears in the claim inventory; and
every provider/model-dependent gate must pass its threshold independently in
each of three complete runs. Pooled metrics are supplemental and cannot rescue
a failed run.

Application-level qualification retries are zero. Any pre-existing frozen
SDK/provider/transport retry remains inside one logical attempt, requires the
approved telemetry, and contributes only to a non-blocking retry-rate metric.
Only a complete invalidated run may be rerun after repair.

This approval authorizes implementation only where it conforms exactly to
scorer-contract v1. Evaluator implementation remains
`BLOCKED_PENDING_IMPLEMENTATION`; qualification remains `NOT_EXECUTED`; V2.0
remains release-blocked pending implementation, validation, evaluator freeze
and owner approval, and passing qualification results.
