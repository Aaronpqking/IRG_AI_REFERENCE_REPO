# V2.0 Gate Scorer Contracts v1

Status: `AUTHORITATIVE_FROZEN`

Authority owner: Aaron

Approved by: Aaron

Approved at: 2026-09-02

Scorer contract version: `v1`

Pre-approval candidate SHA-256:
`e01bd5ea5673200c03c1aa2a87ce902b92221dd592a850184823c7e29dd5bc70`

Qualification status: `NOT_EXECUTED`

This is the authoritative frozen policy artifact for the seven V2.0 gate
scorers. It authorizes a conforming evaluator implementation but does not
approve any evaluator implementation and does not alter the frozen
population, triage, labels, expectation units, applicability, or release
classifications.

## Relationship to existing authority

`docs/EVALUATION_SCORING_CONTRACT.md` remains the general scoring contract, and
`docs/evaluation/V2_EVALUATION_AUTHORITY.md` remains the audit/history of how
the gates were recovered. This document is their V2.0 gate-specific
authoritative specialization; it is not a second population authority.
`V2_GATE_MANIFEST.json` records the exact post-approval contract hash and keeps
evaluator versions null until a conforming implementation is frozen and
separately approved. Its older proposed scorer language and open questions are
superseded by the approved D1-D7 rules here.

## Frozen authority binding

| Artifact | Frozen SHA-256 |
|---|---|
| `docs/evaluation/V2_MASTER_REGRESSION_POPULATION_v1.jsonl` | `4b561ffea79edc97c270cda38fbd0e5351615c0acd8d8be4eab291a3d504bd8e` |
| `docs/evaluation/V2_HISTORICAL_QUESTION_TRIAGE_v1.jsonl` | `8dc936cb0d7c600fdad13592f45f2b564ff8c0b41e9050294373f19432a25e2d` |
| Pre-scorer-approval `docs/evaluation/V2_MASTER_REGRESSION_MANIFEST_v1.json` | `2f8972bf6e12834b58561d19b4e2269c9d5744f6daaf5e1282f25ab882f4d3c5` |

The contract is invalid if the population or triage hash differs. The listed
master-manifest hash proves the exact pre-scorer-approval authority input; that
manifest acquires a new recorded hash when it binds this approved scorer
contract. A population, label, applicability, exclusion, authority-reference,
expected-behavior, or release-classification change requires a new population
artifact version and new authority approval.

## Normative common rules

### Release and observation populations

For G02, G03, G05, G06, and G07, a release-applicable expectation is exactly an
expectation where `blocking == true`, `release_effect == CAN_BLOCK_V2_0`, and
the gate ID occurs in `expectation.applicable_gates`. The frozen counts are:

| Gate | Release-blocking expectations | Non-blocking observations |
|---|---:|---:|
| V2-G02 | 82 | 0 |
| V2-G03 | 86 | 3 |
| V2-G05 | 15 | 10 |
| V2-G06 | 175 | 46 |
| V2-G07 | 14 | 6 |

Every release-applicable expectation must be scheduled. Non-blocking
expectations may be executed and reported in separate observation numerators
and denominators, but their outcomes cannot change any V2.0 gate result or the
V2.0 release disposition. In particular, `V2BQ-CD-004::E01` is blocking under
G03 and G07; `V2BQ-CD-004::E02` is future/non-blocking and has no local gate.

G01 and G18 do not use scenario tags as population authority. Their populations
are derived from the frozen execution and attempt ledgers defined below.

### Scheduling and runs

A scheduled unit is `(qualification_plan_id, run_id, gate_id,
expectation_id)` for expectation gates and `(qualification_plan_id, run_id,
logical_attempt_id)` for global gates. A unit whose execution consumes any
provider/model output, including turn analysis, product-reference analysis, or
answer generation, is generation-dependent and must occur in each of three
complete runs. A unit proven by the frozen plan to consume no provider/model
output is scheduled once. All three runs use identical population,
provider/model, prompt versions and hashes, configuration, and deterministic or
lowest-supported stochasticity. Each complete run must independently satisfy
every applicable gate threshold. Pooled three-run metrics are supplemental
reporting only and cannot rescue a failed run. There is no best-of-three or
selective retry.

The qualification plan freezes `generation_dependent`, scheduled run IDs, and
every expected unit before execution. A missing scheduled unit is not an
exclusion; it is a run-integrity defect and produces `RUN_INVALIDATION`.

### Unit outcomes and denominator integrity

The scorer output enum is:

- `PASS`: every per-unit predicate for the gate is true.
- `FAIL_EXPECTATION`: runtime completed but one or more required comparisons
  failed.
- `CORPUS_COVERAGE_FAILURE`: required approved corpus evidence was absent;
  runtime remained operational and notified or abstained without fabrication.
- `SYSTEM_FAILURE`: the logical attempt did not yield the structurally valid
  runtime result required to score it after the frozen automatic retry policy.
- `RUN_INVALIDATION`: corpus/configuration/evaluator/harness integrity makes the
  complete run non-authoritative.

There is no `EXCLUDED_AFTER_RUN`, `SKIP_FAILED_CASE`, partial-pass, or
unscored-completed outcome. Every pre-frozen applicable scheduled unit remains
in its gate denominator. `FAIL_EXPECTATION`, `CORPUS_COVERAGE_FAILURE`, and
`SYSTEM_FAILURE` are non-passing units for G02/G03/G05/G07. G06 uses its claim
rules plus the parent-attempt completeness rule. `RUN_INVALIDATION` prevents
all gate calculations for the affected run and requires a complete rerun with
a new run ID; it never becomes an exclusion.

Threshold comparisons use exact integers, not rounded display values, and are
performed independently for each required run. A percentage gate passes a run
when `100 * numerator >= threshold_percent * denominator`; G18 passes a run
when `100 * failures <= denominator`. A zero denominator is invalid, never an
automatic pass. The overall gate passes only when every required run passes.

### Identity and set comparison

Product identity uses `product_id` when the frozen expected identity contains
one. Model/MPN/identifier comparison uses the repository's separator-, Unicode-,
and case-normalization only; a product name or similar sibling is not a
substitute for a mismatched product ID. Document-only identities use exact
frozen `document_id`, source path, and page authority. Final canonical
resolved/admitted identity collections are compared as sets after normalization;
order and rank do not affect scoring because the frozen labels contain no rank
requirement. Missing expected admitted identities and extra admitted identities
both fail. Internal recall-oriented raw search or discovery candidate pools are
diagnostic only: extra raw candidates do not fail G02/G03 and raw rank is never
scored. Duplicate final admitted identities collapse only when all authoritative
identity fields agree; conflicting final duplicates fail structural validation.

### Clarification

Clarification passes only when the frozen expectation requires it and all of
these are true: actual response class is `CLARIFICATION_REQUIRED`; all frozen
resolved identities remain resolved; only the frozen unresolved targets are
queried; every `required_target` discriminator is represented in human-readable
language; prohibited raw product IDs are not exposed; and no candidate is
silently selected. If clarification is not expected, any actual clarification
fails. A vague acknowledgement such as “yes” never resolves an outstanding
choice unless the frozen label says that it does.

### Corpus, runtime, duplicates, and retries

Missing required approved evidence is always
`CORPUS_COVERAGE_FAILURE`, never `SYSTEM_FAILURE`. The item fails every gate
whose predicate requires that evidence. G01 may still pass its accounting-only
predicate when the failure is explicitly recorded. G18 treats the operational
attempt as `SUCCESS`, not a runtime failure.

One logical attempt has one immutable `logical_attempt_id`. Frozen automatic
transport retries are nested physical attempts and do not add denominator
units. Application-level retries are zero. Existing automatic SDK/provider/
transport retries may occur only when already present in the frozen client
configuration and fully recorded beneath the logical attempt. Each attempt
records `physical_call_count`, `retry_count`, `retry_reason`, available
`provider_error_class`, and `final_disposition`. Retry rate is a required
non-blocking reporting metric and does not change G18. A manual or selective
rerun cannot replace a result. Duplicate logical IDs invalidate the affected
run. Only a complete invalidated run may be repeated after repair; its ledger
is retained and the replacement uses new run and logical-attempt IDs.

## Scorer authority matrix

| Gate | Population | Scoring Unit | Deterministic? | Semantic Judge Needed? | Numerator | Denominator | Threshold | Multi-run? | Contract Status |
|---|---|---|---|---|---|---|---|---|---|
| G01 | Execution-ledger attempts with `qualification_eligible` and `retrieval_invoked` true | Logical attempt | Yes | No | Units with complete valid lane accounting | All eligible retrieval-bearing logical attempts | 100% independently per run | All scheduled runs | `AUTHORITATIVE_FROZEN` |
| G02 | 82 blocking expectations tagged G02 | Expectation-run | Yes | No | Exact frozen resolution/identity/response passes | All scheduled G02 expectation-runs | >=98% independently per run | Three runs when provider/model output is consumed; otherwise one | `AUTHORITATIVE_FROZEN` |
| G03 | 86 blocking expectations tagged G03 | Expectation-run | Yes | No | Exact frozen identity/candidate/clarification passes | All scheduled G03 expectation-runs | >=90% independently per run | Three runs when provider/model output is consumed; otherwise one | `AUTHORITATIVE_FROZEN` |
| G05 | 15 blocking expectations tagged G05 | Expectation-run | Yes, using structured ownership and claim ledgers | No LLM judge | Units passing every subject/scope/ownership predicate | All scheduled G05 expectation-runs | >=90% independently per run, plus critical-contamination veto | Three runs when any generated claim is consumed | `AUTHORITATIVE_FROZEN` |
| G06 | Atomic substantive claim across 175 blocking parent expectations | Claim, with mandatory parent-attempt and human inventory-completeness coverage | Structured first; bounded human review for residual meaning | Human review; no LLM judge in v1 | Unsupported plus contradicted substantive claims | All substantive claims in all valid completed scheduled parent attempts | 0 critical and <=1% unsupported independently per run | Three complete runs | `AUTHORITATIVE_FROZEN` |
| G07 | 14 blocking expectations tagged G07 | Follow-up expectation-run | Yes, using persisted transcript/lineage fields | No LLM judge | Units passing reference, identity, evidence ownership, and response behavior | All scheduled G07 expectation-runs | >=90% independently per run | Three runs when provider/model output is consumed; otherwise one | `AUTHORITATIVE_FROZEN` |
| G18 | Attempt-ledger rows with `qualification_eligible == true` | Logical attempt | Yes | No | `SYSTEM_FAILURE` count is the failure numerator | All eligible logical attempts in valid complete runs | <=1% independently per run | All scheduled runs | `AUTHORITATIVE_FROZEN` |

## Historical evaluator classification

| Artifact or logic | Classification | Permitted use |
|---|---|---|
| `src/product_discovery.py` normalization, production resolution enums, and `resolution_state_disposition` | `REUSABLE` | Actual-state normalization and structured identity comparison; frozen expected states remain authoritative. |
| `src/query_identity.py` identifier normalization | `REUSABLE` | Deterministic identifier comparison only. |
| `src/citation_validation.py` citation parsing, source/page matching, ownership checks, and atomic-element diagnostics | `PARTIAL` | Scorer primitives and candidate claim segmentation; not final semantic support or severity authority. |
| `src/scripts/v2_s3_lifecycle_gate.py` persisted-reference lifecycle checks | `REUSABLE` | G07 structural predicates after binding to frozen transcripts. |
| `src/scripts/v2_s3_stage_gate.py` | `PARTIAL` | Structural signals only; observe-only and stage-specific aggregation is not the release contract. |
| `src/execution_trace.py` | `PARTIAL` | Runtime field source; it lacks the required per-lane terminal ledger. |
| `src/full_suite_evaluation.py` | `PARTIAL` | Production composition and basic exception capture; its whole-question summary and runtime counter are not gate scorers. |
| `src/scripts/run_unified_answering_eval.py` and its dataset scoring | `SUPERSEDED` | Execution patterns may be studied; old labels, score views, exclusions, and aggregation cannot score V2.0. |
| `src/scripts/run_technical_answer_validation.py` | `HISTORICAL` | Diagnostic comparison patterns only. |
| `src/scripts/eval_golden.py`, `src/scripts/eval_hybrid_retrieval.py`, `src/chat_eval.py`, and `src/chat_assessment.py` | `SUPERSEDED` | Normalization helpers may be extracted only after tests; heuristic expected-term and whole-answer pass logic is not authoritative. |
| V2-S2D/V2-S2E results and percentage reports | `HISTORICAL` | Provenance and failure examples only; never a V2.0 numerator or denominator. |
| V2-S3 live/focused tests | `PARTIAL` | Known-pass/fail fixture patterns for G05/G07; never population or percentage authority. |
| A generic free-form LLM judge | `INCOMPATIBLE` | Prohibited as the default or fallback release scorer. |

## V2-G01 — retrieval lane accounting

1. **Gate ID:** `V2-G01`.
2. **Gate name:** Retrieval lane accounting.
3. **Risk/objective:** Detect an invoked or required retrieval lane that has no
   auditable terminal record. This measures accounting completeness, not
   relevance quality.
4. **Population source:** Frozen execution ledger.
5. **Applicability predicate:** `qualification_eligible == true AND
   retrieval_invoked == true` on a unique logical attempt.
6. **Scoring unit:** One logical attempt, regardless of nested physical calls.
7. **Expected-label fields used:** Frozen qualification plan's
   `required_lane_ids`, expectation IDs, requested identity set, corpus identity,
   and route predicates.
8. **Actual-result fields used:** Attempt identity, invoked lane IDs, one terminal
   record per required lane, lane query digest, owner IDs, evidence IDs/count,
   corpus identity, terminal status, error code, and timings.
9. **Numerator:** Applicable logical attempts satisfying the complete accounting
   pass condition.
10. **Denominator:** Every applicable logical attempt; scenario gate tags do not
    add or remove units.
11. **Exact pass condition per unit:** Actual corpus/config identity equals the
    frozen plan; actual required-lane set equals the planned set; every required
    lane has exactly one terminal record; every invoked lane is in that set; and
    each terminal record is structurally complete. Allowed terminal states are
    `EVIDENCE_FOUND`, `ZERO_RESULTS`, `CORPUS_COVERAGE_FAILURE`,
    `CLARIFICATION_REQUIRED`, and `SYSTEM_FAILURE`. Evidence-bearing records
    include unique evidence IDs and product ownership; zero/failure records
    include zero count or error code and no fabricated evidence.
12. **Exact fail condition per unit:** Missing/duplicate lane record, required
    lane not terminal, invoked lane absent from the plan, mismatched corpus,
    missing evidence ownership for evidence found, invalid zero count, or an
    undefined terminal state. Bad but fully accounted evidence does not by
    itself fail G01.
13. **Partial-credit policy:** None.
14. **Clarification treatment:** A recorded ambiguity-driven
    `CLARIFICATION_REQUIRED` terminal is accounted and can pass G01; its
    correctness is scored by G02/G03/G07.
15. **Corpus-failure treatment:** Explicit `CORPUS_COVERAGE_FAILURE` can pass
    G01 accounting while failing the evidence-dependent gate.
16. **Runtime-error treatment:** Explicit lane `SYSTEM_FAILURE` can pass G01
    accounting and counts against G18; an unrecorded error fails G01.
17. **Duplicate/retry treatment:** One logical unit; all physical calls and
    retries are nested and ordered. Duplicate logical IDs invalidate the run.
18. **Aggregation rule:** Exact sum within each valid run; all applicable units
    in every run must pass. Pooled counts are supplemental only.
19. **Threshold:** 100%.
20. **Multi-run rule:** Each complete run is evaluated independently; pooled
    accounting is supplemental only.
21. **Required ledger fields:** `qualification_plan_id`, `run_id`,
    `logical_attempt_id`, `scenario_id`, `turn_index`, `expectation_ids`,
    `qualification_eligible`, `retrieval_invoked`, `required_lane_ids`,
    `invoked_lane_ids`, `requested_product_refs`, `resolved_product_ids`,
    `collection_name`, `collection_fingerprint`, `runtime_version`,
    `lane_records[{lane_id,physical_attempt_ids,query_digest,terminal_state,
    evidence_ids,evidence_owner_refs,result_count,error_code,started_at,
    completed_at}]`.
22. **Required output artifacts:** Execution ledger JSONL, lane-detail JSONL,
    G01 unit-results JSONL, summary JSON, configuration/corpus manifest, and
    SHA-256 inventory.
23. **Deterministic vs semantic components:** Entirely deterministic.
24. **Evaluator dependency:** New schema validator and accounting scorer;
    existing traces are only a partial input adapter.
25. **Owner approval questions still unresolved:** None; D1 is approved.

## V2-G02 — exact identity and identifier performance

1. **Gate ID:** `V2-G02`.
2. **Gate name:** Exact identity/identifier performance.
3. **Risk/objective:** Prevent an exact identifier from resolving to the wrong
   product, wrong cardinality, or wrong ambiguity/no-match behavior.
4. **Population source:** Frozen expectation units.
5. **Applicability predicate:** Blocking expectation containing `V2-G02`.
6. **Scoring unit:** One expectation in each required scheduled run.
7. **Expected-label fields used:** Referenced expected identities and resolution
   states, expected response state, expected clarification, authority sources,
   and normalized user identifier.
8. **Actual-result fields used:** Per-mention normalized identifiers, resolution
   state/disposition, selected product ID, final canonical resolved/admitted
   product-ID set, diagnostic raw candidate-set digest, current alias/mapping
   record when expected, response class, and clarification target fields.
9. **Numerator:** Units passing the exact state-specific comparison.
10. **Denominator:** All scheduled G02 release-applicable expectation-runs;
    current one-run count is 82 if none is generation-dependent.
11. **Exact pass condition per unit:** For singleton resolved labels, the actual
    state is resolved and the authoritative identity exactly matches. For
    `MULTIPLE_PLAUSIBLE_CANDIDATES`, actual state is ambiguous, the final
    canonical admitted set exactly equals all frozen identities, none is
    selected, and expected clarification passes. For
    `DISTINCT_MATCH_RETURNED_WITHOUT_SILENT_SELECTION`, the returned set exactly
    equals the frozen set and no silent top-one selection occurs. For
    `NO_SUPPORTED_MATCH`, actual state is no match, the final admitted set is
    empty, and frozen response behavior passes. Raw recall candidates are never
    scored. An approved stale/alias mapping passes only when the frozen current
    product ID and mapping evidence both match.
12. **Exact fail condition per unit:** Wrong/missing/extra identity, wrong
    cardinality or state, related sibling substituted, silent selection from a
    multi-match set, incorrect/no unnecessary clarification, or wrong response
    state.
13. **Partial-credit policy:** None; membership without the correct frozen state
    is failure.
14. **Clarification treatment:** Common clarification rule; correct
    clarification passes only for a clarification-labeled unit.
15. **Corpus-failure treatment:** If an authority reference required by the
    identity expectation is approved corpus evidence and is unavailable, record
    `CORPUS_COVERAGE_FAILURE`; otherwise DB identity scoring proceeds
    independently.
16. **Runtime-error treatment:** Non-passing G02 unit and `SYSTEM_FAILURE` for
    G18.
17. **Duplicate/retry treatment:** Common rule; repeated physical calls do not
    add or replace units.
18. **Aggregation rule:** Calculate each required run independently with no
    category averaging or rank-weighted credit. Pooled results are supplemental
    and cannot rescue a failed run.
19. **Threshold:** At least 98%; compare exact integer counts.
20. **Multi-run rule:** Three runs only when the plan proves provider/model
    output is consumed; otherwise one.
21. **Required ledger fields:** Common IDs/versions plus input identifier and
    normalized form, expected/actual state, expected/actual identity set,
    selected identity, candidate-set digest, alias/mapping evidence ID,
    response state, clarification result, unit outcome, and reason codes.
22. **Required output artifacts:** G02 population snapshot, per-unit results,
    mismatch ledger, summary, run/config manifest, and hashes.
23. **Deterministic vs semantic components:** Entirely deterministic.
24. **Evaluator dependency:** Repository identifier normalization and product
    resolution state adapter; new frozen-label comparator.
25. **Owner approval questions still unresolved:** None; D2 is approved with
    final canonical resolved/admitted-set scoring and diagnostic raw pools.

## V2-G03 — natural staff query performance

1. **Gate ID:** `V2-G03`.
2. **Gate name:** Natural staff product resolution.
3. **Risk/objective:** Prevent natural employee wording from resolving to a
   related but wrong product, losing partially resolved scope, or guessing
   through genuine ambiguity.
4. **Population source:** Frozen expectation units.
5. **Applicability predicate:** Blocking expectation containing `V2-G03`.
6. **Scoring unit:** One expectation in each required scheduled run.
7. **Expected-label fields used:** Referenced identity set and per-identity
   resolution state, response state, clarification targets, conversation turns,
   and unsupported/abstention behavior.
8. **Actual-result fields used:** Per-mention product refs, normalized request,
   selected and final canonical admitted product IDs, diagnostic raw candidate
   digest, resolution states, response class, clarification targets, and
   retained resolved-scope IDs.
9. **Numerator:** Units matching every frozen identity, state, and response
   behavior predicate.
10. **Denominator:** All scheduled G03 release-applicable expectation-runs;
    current one-run count is 86.
11. **Exact pass condition per unit:** Actual final canonical resolved/admitted
    identity sets equal the frozen referenced sets; each mention has the frozen resolution
    disposition; all already resolved subjects remain present; only unresolved
    subjects are clarified; and the exact expected response behavior passes.
    Admitted-set order is ignored, but extra/missing admitted identities fail.
    Raw search candidates and their rank are diagnostic only. No PDF relevance
    score or semantic product similarity can substitute for identity.
12. **Exact fail condition per unit:** Any wrong sibling, missing resolved
    subject, unexpected final admitted identity, wrong resolution state, guessed ambiguity,
    unnecessary clarification, clarification of already resolved scope, or
    response-state mismatch.
13. **Partial-credit policy:** None at the expectation level. Partial-resolution
    scenarios pass only when every frozen resolved and unresolved component is
    handled as labeled.
14. **Clarification treatment:** Common rule; correctly labeled clarification
    is a pass, not an abstention failure.
15. **Corpus-failure treatment:** Identity/behavior scoring remains separate
    from evidence relevance. If required identity authority itself is missing,
    the unit is `CORPUS_COVERAGE_FAILURE`; missing answer evidence is scored by
    G05/G06 where applicable.
16. **Runtime-error treatment:** Non-passing G03 unit and G18 system failure.
17. **Duplicate/retry treatment:** Common rule.
18. **Aggregation rule:** Exact expectation results are aggregated independently
    per required run, with no phrase-family average or candidate-rank weighting.
    Pooled results are supplemental and cannot rescue a failed run.
19. **Threshold:** At least 90%.
20. **Multi-run rule:** Three runs when provider/model output is consumed;
    otherwise one.
21. **Required ledger fields:** Common IDs/versions; raw and normalized phrase;
    expected/actual mention IDs, product refs, product IDs, resolution states,
    candidate-set digests, retained-scope IDs, response state, clarification
    result, unit outcome, and reason codes.
22. **Required output artifacts:** G03 population snapshot, per-unit results,
    identity/clarification mismatch ledger, summary, manifest, and hashes.
23. **Deterministic vs semantic components:** Deterministic structured scoring;
    no semantic judge.
24. **Evaluator dependency:** Structured requested-product and runtime product
    state adapters plus frozen comparator.
25. **Owner approval questions still unresolved:** None; D2 is approved with
    final canonical resolved/admitted-set scoring and diagnostic raw pools.

## V2-G05 — multi-product ownership and scope

1. **Gate ID:** `V2-G05`.
2. **Gate name:** Multi-product ownership/scope integrity.
3. **Risk/objective:** Detect identity loss, evidence crossover, claim transfer,
   or incorrect scope transitions in multi-subject answers.
4. **Population source:** Frozen expectation units.
5. **Applicability predicate:** Blocking expectation containing `V2-G05`.
6. **Scoring unit:** One expectation in each required scheduled run, not one
   point per product.
7. **Expected-label fields used:** Referenced identities/states, claims and
   owners, source authority, clarification targets, turn scope, and expected
    response state. Any `CRITICAL` safety/fitment cross-subject contamination
    also invokes the complete-run veto.
8. **Actual-result fields used:** Requested/current product refs and IDs,
   resolution states, canonical evidence IDs and owners, admitted applicability,
   claim-ledger owner/evidence bindings, retained/added/removed refs, and
   response state.
9. **Numerator:** Expectation-runs satisfying every identity, scope, evidence,
   and claim ownership predicate.
10. **Denominator:** Every scheduled G05 release-applicable expectation-run;
    current one-run count is 15.
11. **Exact pass condition per unit:** Distinct frozen subjects have distinct
    product refs; every resolvable subject maps to the exact frozen identity and
    has at least one admitted authoritative evidence record owned by that ref;
    every actual factual claim has evidence owned by the claim's subject; no
    source is assigned to an unowned subject; frozen partial ambiguity preserves
    all resolved subjects and clarifies only unresolved ones; and additive,
    subtractive, switch-back, ordinal, correction, and order changes produce the
    exact frozen active-subject set.
12. **Exact fail condition per unit:** Missing/merged/swapped subject, evidence
    without an owner, evidence owned by a different subject, claim/evidence
    crossover, lost resolved scope, fabricated comparison, wrong active set, or
    clarification behavior mismatch. One critical safety/fitment cross-subject
    claim also fails G05 for the complete affected run.
13. **Partial-credit policy:** None per expectation; a two-of-three product
    result fails the unit.
14. **Clarification treatment:** A mixed resolved/ambiguous unit passes only if
    resolved subjects remain answerable and only ambiguous subjects are
    clarified.
15. **Corpus-failure treatment:** Missing required evidence for any resolvable
    subject is `CORPUS_COVERAGE_FAILURE` and fails the unit; it does not suppress
    valid evidence for other subjects.
16. **Runtime-error treatment:** Non-passing G05 unit and G18 system failure.
17. **Duplicate/retry treatment:** Common rule; duplicate product refs inside a
    turn are structural failure unless the frozen scope explicitly represents
    the same product once.
18. **Aggregation rule:** Calculate each run independently over all-or-nothing
    expectation results. Any critical safety/fitment cross-subject contamination
    makes that complete run fail regardless of its percentage. Pooled metrics
    are supplemental and cannot rescue the run.
19. **Threshold:** At least 90%.
20. **Multi-run rule:** Three complete runs whenever generated claims are part
    of the pass predicate; otherwise the frozen plan may schedule one run.
21. **Required ledger fields:** Common IDs/versions; expected/actual active
    product refs and IDs; per-ref resolution; added/retained/removed refs;
    evidence IDs, source IDs, owners and applicability; claim IDs and owners;
    response/clarification result; severity; unit outcome and reasons.
22. **Required output artifacts:** G05 population snapshot, expectation results,
    subject/evidence/claim ownership ledger, transition mismatches, critical
    defects, summary, manifest, and hashes.
23. **Deterministic vs semantic components:** Structured identity, state, source,
    and claim-owner comparison. Semantic claim support belongs to G06.
24. **Evaluator dependency:** Requested-product/runtime state, lifecycle and
    citation ownership primitives; new all-subject comparator.
25. **Owner approval questions still unresolved:** None; D3 is approved.

## V2-G06 — unsupported claim control

1. **Gate ID:** `V2-G06`.
2. **Gate name:** Unsupported substantive claim control.
3. **Risk/objective:** Prevent unsupported, contradicted, or cross-owned factual
   claims, with zero tolerance for critical safety or damage risk.
4. **Population source:** Claims extracted from every valid completed scheduled
   attempt for the 175 blocking G06 parent expectations in each required run.
5. **Applicability predicate:** Parent expectation is blocking and contains
   `V2-G06`; every substantive factual claim emitted for it is applicable.
6. **Scoring unit:** One atomic substantive factual claim. Before support
   adjudication is complete, a human reviewer must confirm that the claim ledger
   represents every substantive factual claim in the response. Parent-attempt
   and human claim-inventory completeness are mandatory gate preconditions.
7. **Expected-label fields used:** Factual claims, claim owners, expected source
   and page authority, unsupported/abstention behavior, expected response state,
   and severity policy.
8. **Actual-result fields used:** Exact answer text and span, atomic claim text,
   subject owner, claim type, evidence IDs/source/page/owner, support class,
   severity, scorer method, human inventory-completeness decision, reviewer
   decisions, and response state.
9. **Numerator:** For the overall unsupported rate, all substantive claims with
   final support class `UNSUPPORTED` or `CONTRADICTED`; separately, the subset
   of those with severity `CRITICAL`.
10. **Denominator:** Every atomic substantive claim in every valid completed
    scheduled G06 parent attempt across all three runs. `NON_SUBSTANTIVE` and
    `NOT_APPLICABLE` records are audited but not denominator claims.
11. **Exact pass condition per unit:** Final class is `SUPPORTED`: every material
    factual component is entailed by admitted evidence of the correct authority
    type, source/page and product owner, with no contrary admitted evidence.
    Numeric value, unit, model/MPN, polarity, comparison direction, conditions,
    and safety qualifier must all match. Conversation history and prior assistant
    text are never evidence. Compatibility/fitment requires explicit
    authoritative relationship evidence; similarity is insufficient.
12. **Exact fail condition per unit:** Final class `UNSUPPORTED` when any material
    component lacks support, or `CONTRADICTED` when authoritative evidence
    conflicts. Wrong owner/source/page is unsupported even if another product's
    evidence contains the words.
13. **Partial-credit policy:** `PARTIALLY_SUPPORTED` is prohibited. Compound
    statements must be split until each atomic claim can receive one final
    class. Failure to split is scorer validation failure and invalidates the run.
14. **Clarification treatment:** Style and the question itself are
    `NON_SUBSTANTIVE`; any factual assertion inside a clarification is scored.
    Unnecessary clarification is scored by its expectation gate, not converted
    into a supported claim.
15. **Corpus-failure treatment:** Required evidence absent yields parent outcome
    `CORPUS_COVERAGE_FAILURE`. The system must notify/abstain; fabricated claims
    are still scored unsupported. A parent attempt with no
    valid and human-confirmed complete claim ledger fails G06 completeness
    rather than diluting the claim denominator.
16. **Runtime-error treatment:** No synthetic claim is invented. The parent
    attempt is incomplete, counts as G18 `SYSTEM_FAILURE`, and prevents G06 from
    passing.
17. **Duplicate/retry treatment:** Identical claim spans are one claim only when
    they share answer span, owner, and meaning. Repeated assertions at different
    spans are separate claims. Common logical-attempt retry rule applies.
18. **Aggregation rule:** G06 passes only if parent-attempt coverage and human
    claim-inventory completeness are 100% in each run, and each run independently
    has zero critical unsupported claims and satisfies `100 * (UNSUPPORTED +
    CONTRADICTED) <= substantive_claim_count`. The pooled three-run rate and
    counts are supplemental reporting only and cannot rescue a failed run.
19. **Threshold:** In every run, zero critical unsupported claims and at most 1%
    unsupported substantive claims overall.
20. **Multi-run rule:** Exactly three complete qualification runs for all G06
    parents, using the same frozen inputs/configuration.
21. **Required ledger fields:** `claim_id`, `qualification_plan_id`, `run_id`,
    `logical_attempt_id`, `scenario_id`, `turn_index`, `expectation_id`, answer
    hash, span start/end, original and normalized claim text, claim type,
    subject/product owner, severity, evidence IDs/source types/paths/pages/owners,
    deterministic checks, provisional/final support class, scorer method,
    extractor version, human completeness reviewer ID, completeness status,
    missing-claim count and correction references, support reviewer IDs,
    disagreement/adjudication status, reason codes, and timestamps.
22. **Required output artifacts:** Immutable answer ledger, atomic claim ledger,
    reviewer and adjudication ledger, critical-defect ledger, parent coverage
    report, per-run and pooled summaries, scorer/judge manifests, and hashes.
23. **Deterministic vs semantic components:** Deterministic source/page/owner,
    identifier, number, unit, polarity, and explicit relation checks first.
    Residual qualitative entailment receives blinded human review under the same
    rubric. No LLM judge is authorized in v1. If later proposed, its exact model,
    provider, prompt bytes/hash, temperature, input schema, machine verdict,
    evidence references, uncertainty handling, and no-fallback rule require a
    separately approved scorer version.
24. **Evaluator dependency:** Citation/claim-element diagnostics are partial
    primitives; new immutable claim extraction, human inventory-completeness
    review, support-review import, adjudication, and aggregation are required.
25. **Owner approval questions still unresolved:** None; D4 is approved with
    human claim-inventory completeness control.

The mandatory order is: generated response → atomic claim decomposition →
human claim-inventory completeness confirmation → deterministic support checks
→ blinded residual entailment review → per-run G06 aggregation. Completeness
review may add omitted claim-ledger entries and record extractor defects, but it
cannot change the generated response or any frozen label.

Support classes are exactly:

- `SUPPORTED`: all material components supported by correctly owned authority.
- `UNSUPPORTED`: at least one material component lacks such support.
- `CONTRADICTED`: authoritative evidence conflicts with the claim.
- `NON_SUBSTANTIVE`: style, navigation, greeting, or other text with no factual
  proposition.
- `NOT_APPLICABLE`: a valid ledger record that is not an answer assertion, such
  as quoted user text. It requires a reason code.

Severity is exactly the approved model: `CRITICAL` for safety, gas, electrical,
venting, clearances, installation, hazardous compatibility/fitment, or
equipment-damage-risk claims; `MAJOR` for materially incorrect technical,
specification, identity, or product attribution without direct safety impact;
and `MINOR` for low-impact factual or presentation defects. When categories
overlap, the highest severity wins.

## V2-G07 — follow-up and continuity

1. **Gate ID:** `V2-G07`.
2. **Gate name:** Follow-up/reference continuity.
3. **Risk/objective:** Prevent ordinal, pronoun, correction, scope, persistence,
   or conversation-boundary references from resolving to the wrong subject.
4. **Population source:** Frozen expectation units and their multi-turn scripts.
5. **Applicability predicate:** Blocking expectation containing `V2-G07`.
6. **Scoring unit:** The scored follow-up expectation in each scheduled run;
   setup turns are mandatory execution prerequisites but not numerator units.
7. **Expected-label fields used:** All turns/events, referenced identities and
   states, response/clarification behavior, claim/source ownership, and
   unsupported behavior.
8. **Actual-result fields used:** Conversation and turn IDs, process instance
   IDs, persisted/reloaded transcript and product refs, prior/current product
   states, active evidence-state lineage, selected references, canonical
   evidence owners, response state, and clarification result.
9. **Numerator:** Follow-up expectation-runs satisfying every continuity
   predicate.
10. **Denominator:** All scheduled G07 release-applicable expectation-runs;
    current one-run count is 14.
11. **Exact pass condition per unit:** Actual referenced identity set and active
    scope equal the frozen set; ordinal/original/second/other/pronoun references
    map to the exact prior product refs; corrections, switch-back, additions and
    removals produce the exact new scope; reused evidence retains the correct
    lineage and owner; fresh evidence is attached only to the intended subject;
    and response/clarification behavior matches. All predicates are required.
12. **Exact fail condition per unit:** Wrong/unresolved reference contrary to
    label, cross-product evidence, lost/additional scope, guessed ambiguity,
    wrong response state, prompt-history simulation of restart, or cross-
    conversation leakage.
13. **Partial-credit policy:** None.
14. **Clarification treatment:** Unsafe ambiguous reference must clarify exactly
    when labeled; a resolved reference that unnecessarily clarifies fails.
15. **Corpus-failure treatment:** If the frozen follow-up requires fresh or
    retained approved evidence and it is missing, the unit is
    `CORPUS_COVERAGE_FAILURE`; valid identity continuity alone does not rescue it.
16. **Runtime-error treatment:** Non-passing G07 unit and G18 system failure.
17. **Duplicate/retry treatment:** Common rule. Setup and scored turn IDs must be
    unique within their conversation.
18. **Aggregation rule:** All-predicate expectation results are aggregated
    independently per required run. Pooled results are supplemental only.
19. **Threshold:** At least 90%.
20. **Multi-run rule:** Three runs when provider/model output is consumed;
    otherwise one. Each run independently executes its complete transcript.
21. **Required ledger fields:** Common IDs/versions; conversation IDs; turn IDs
    and order; process instance IDs; restart/reload events; prior/current product
    refs and IDs; selected antecedents; active/parent evidence-state IDs;
    expected/actual scope; evidence owners; response/clarification result;
    outcome and reasons.
22. **Required output artifacts:** Frozen transcript plan, transition ledger,
    persistence/restart ledger, conversation-isolation ledger, per-unit results,
    summary, manifest, and hashes.
23. **Deterministic vs semantic components:** Structured deterministic scoring;
    required-target language uses deterministic normalized phrase matching.
24. **Evaluator dependency:** Real persistence harness, process lifecycle
    controller, runtime-state/lifecycle adapter, and exact transition scorer.
25. **Owner approval questions still unresolved:** None; D5 is approved.

For `V2BQ-CT-007`, the process instance after the recorded restart must differ
from the instance before it, the conversation must be reloaded from the
persistence port, and no setup prompt history may be injected into the new
process. For `V2BQ-CT-008`, conversation A and B must have distinct IDs and
product state from A must be absent from B; “it” in B remains unresolved and
receives the frozen clarification behavior.

## V2-G18 — runtime failure rate

1. **Gate ID:** `V2-G18`.
2. **Gate name:** Qualification runtime failure rate.
3. **Risk/objective:** Bound application-origin failure without denominator
   dilution or selective retry.
4. **Population source:** Frozen attempt ledger.
5. **Applicability predicate:** `qualification_eligible == true` on a unique
   logical attempt in a valid run.
6. **Scoring unit:** One logical attempt, not a physical provider call.
7. **Expected-label fields used:** Frozen qualification schedule, runtime/corpus/
   model/prompt configuration, and allowed automatic retry policy.
8. **Actual-result fields used:** Logical and physical attempt records,
   completion/result schema, exception stage/code, corpus/config identity,
   persistence outcome, retry records, and run-integrity findings.
9. **Numerator:** Logical attempts whose final taxonomy is `SYSTEM_FAILURE`.
10. **Denominator:** Every qualification-eligible logical attempt in all valid
    complete scheduled runs.
11. **Exact pass condition per unit:** `SUCCESS`: runtime completed and emitted a
    structurally valid attempt/result record after the frozen automatic retry
    policy. Product/evidence/answer incorrectness and
    `CORPUS_COVERAGE_FAILURE` are evaluation failures but remain G18 successes.
12. **Exact fail condition per unit:** `SYSTEM_FAILURE`: unhandled runtime
    exception; DB/vector/retrieval exception; malformed or missing internal
    response; provider/generation failure; persistence failure affecting
    completion; timeout; or contract serialization failure after the frozen
    automatic retry policy.
13. **Partial-credit policy:** None.
14. **Clarification treatment:** A structurally valid clarification is G18
    success regardless of whether another gate finds it correct.
15. **Corpus-failure treatment:** Operational `CORPUS_COVERAGE_FAILURE` is G18
    success; corpus connection/query exception is `SYSTEM_FAILURE`; wrong corpus
    identity is `RUN_INVALIDATION`.
16. **Runtime-error treatment:** Counts once as `SYSTEM_FAILURE` per logical
    attempt.
17. **Duplicate/retry treatment:** Frozen automatic physical retries remain
    nested. Exhaustion yields one failure. Manual selective retry cannot replace
    it. Duplicate logical IDs invalidate the run.
18. **Aggregation rule:** On each valid complete run, calculate exact
    `SYSTEM_FAILURE / eligible logical attempts` and require that run to pass.
    Pooled counts and retry rates are supplemental and cannot rescue a failed
    run. Any run invalidation stops qualification and produces no gate pass
    until the whole affected run is repeated under a new run ID.
19. **Threshold:** At most 1%.
20. **Multi-run rule:** Includes every attempt from every scheduled single or
    three-run gate execution.
21. **Required ledger fields:** `qualification_plan_id`, `run_id`,
    `logical_attempt_id`, scenario/turn/expectation IDs,
    `qualification_eligible`, `generation_dependent`, physical-attempt array,
    `physical_call_count`, `retry_count`, `retry_reason`, available
    `provider_error_class`, `final_disposition`, configured retry policy,
    start/end/duration, terminal taxonomy,
    failure stage/code/class, result-schema validity, persistence completion,
    corpus/model/prompt/runtime versions, and run-integrity status.
22. **Required output artifacts:** Complete attempt ledger, physical-call ledger,
    system-failure ledger, run-invalidation ledger, G18 summary, configuration
    manifest, non-blocking retry-rate report, and hashes.
23. **Deterministic vs semantic components:** Entirely deterministic taxonomy
    from stage/error/config fields.
24. **Evaluator dependency:** New attempt schema validator and taxonomy scorer;
    existing full-suite exception count is partial.
25. **Owner approval questions still unresolved:** None; D6 is approved as
    amended and D7 is approved.

`RUN_INVALIDATION` is limited to wrong corpus/collection identity, wrong
provider/model/prompt/configuration, corrupted frozen artifact, evaluator or
scorer defect, incomplete/duplicate schedule, or qualification-harness defect.
It is never an item exclusion and never a product-answer failure. The invalid
run and every attempt remain in the audit package.

## Owner approval record

Aaron approved D1-D7 on 2026-09-02. Thresholds and prior frozen authority are
not reopened.

| Decision | Status | Approved Rule |
|---|---|---|
| D1 — G01 accounting boundary | `APPROVED` | G01 is accounting-only. A bad or zero-result retrieval may pass when every required lane has an explicit valid terminal record and evidence ownership where evidence exists. Relevance is scored elsewhere. |
| D2 — G02/G03 identity semantics | `APPROVED_WITH_CLARIFICATION` | Compare frozen state and identity set to the final canonical resolved/admitted identity set. Raw recall-oriented search candidates and rank are diagnostic only. Clarification and zero-match must exactly match their frozen labels. |
| D3 — G05 critical contamination | `APPROVED` | Every subject/scope/evidence/claim-owner predicate is required. Any critical safety/fitment cross-subject contamination fails G05 for the complete affected run regardless of percentage. |
| D4 — G06 review and completeness | `APPROVED_WITH_COMPLETENESS_CONTROL` | Prohibit partial support; atomize claims; require human confirmation that every substantive response claim is inventoried before deterministic checks and blinded residual review. Each run independently requires zero critical and at most 1% unsupported claims. |
| D5 — G07 all-predicate continuity | `APPROVED` | Require identity, reference, scope, evidence lineage/ownership, and response behavior, with real restart/reload and two-conversation isolation where labeled. |
| D6 — generation-dependent scope | `APPROVED_AS_AMENDED` | Provider/model-dependent gates run three complete runs and each run independently passes its threshold. Pooled metrics are reporting-only and cannot rescue a failed run. Proven no-provider gates may run once. |
| D7 — transport retry and run invalidation | `APPROVED` | Application retries are zero. Frozen automatic SDK/provider/transport retries remain under one logical attempt with complete retry telemetry. Retry rate is non-blocking. Only a complete invalidated run may be rerun. |

No owner decision remains for scorer-contract v1. This approval authorizes only
a conforming evaluator implementation; it does not approve that implementation
or authorize qualification.

## Implementation sequence after approval

1. Define the immutable qualification-plan schema and frozen schedule.
2. Define the one-row-per-logical-attempt ledger.
3. Define the nested physical provider-call/retry sub-ledger with the approved
   retry telemetry.
4. Define the retrieval execution-lane ledger and terminal-state validator.
5. Define the identity-resolution result schema separating raw candidates from
   final canonical admitted identities.
6. Define the scope/ownership transition ledger.
7. Define the atomic claim ledger.
8. Define the human claim-inventory completeness-review schema.
9. Define the blinded residual G06 adjudication schema.
10. Implement deterministic normalization, identity-set, response,
    clarification, ownership, lane, severity, retry, and runtime primitives.
11. Implement all seven gate scorers exactly from this contract.
12. Add known-pass fixtures for every state and disposition.
13. Add known-fail fixtures for every fail rule and veto.
14. Add ambiguity, corpus, continuity, retry, claim-splitting, and invalidation
    edge fixtures.
15. Prove deterministic denominator derivation from the frozen plan.
16. Prove run isolation and independent per-run thresholds.
17. Prove selective retry cannot replace a logical result.
18. Prove mixed blocking/non-blocking outcomes cannot cross-affect release
    disposition.
19. Implement per-run threshold aggregation as the qualification authority.
20. Implement pooled three-run and retry-rate metrics as supplemental,
    non-rescuing/non-blocking reporting.
21. Hash evaluator source, dependency lock, schemas, prompts/configuration, and
    fixture results.
22. Freeze a versioned evaluator artifact.
23. Request Aaron's separate approval of the evaluator artifact and derived
    gate populations/denominators.
24. Execute qualification only after that approval; do not tune, exclude, or
    selectively retry within the frozen run set.

## Freeze record

Scorer-contract v1 is `AUTHORITATIVE_FROZEN`, approved by Aaron on 2026-09-02.
The exact post-approval SHA-256 is recorded in `V2_GATE_MANIFEST.json` and the
master regression manifest because a file cannot canonically contain its own
SHA-256. Qualification remains `NOT_EXECUTED`; evaluator implementation remains
`BLOCKED_PENDING_IMPLEMENTATION`.
