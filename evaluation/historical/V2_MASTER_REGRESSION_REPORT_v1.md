<!-- Historical direct text from Google Drive at https://docs.google.com/document/d/1ZnHzc0VX8PDXmv9PV59yLG7PPQvjHYEM/edit; original source version and byte hash not independently established. Content copy not frozen empirical qualification. -->

# V2 Master Regression Population v1

Date: 2026-09-02

Status: `AUTHORITATIVE_FROZEN`

Authority approval: Aaron, 2026-09-02

Release qualification: `NOT_EXECUTED`

## Outcome

The historical intake reviewed 615 normalized unique question texts from live conversation history and retained evaluation artifacts. It retained 208 historical scenarios whose expected behavior could be established from confirmed golden labels, approved corpus evidence, bounded read-model identity, current safety/applicability contracts, or deterministic synthetic contract fixtures. It excluded 407 rows with an explicit reason in the triage ledger.

All 36 behavior-expansion scenarios are included and now carry the required identity, response-state, clarification, factual-claim, source/page, unsupported-behavior, ownership, gate, severity, and immutable expectation-unit fields. The master population contains 244 scenarios and 245 independently scorable expectation units.

## Configuration boundary

- `V2BQ-CD-006` (#36) is retained as `REGRESSION_NON_BLOCKING_FUTURE_CONFIGURATION_ACTIVATION` because `product_valid_combinations` is still observe-only, model-invisible, and has no answer effect.
- The same contract also affects `V2BQ-CL-003` (#19), which asks the system to recommend/clarify a configuration from observe-only rows; it is retained as future/non-blocking rather than silently made release-blocking.
- `V2BQ-CD-004` (#34) is split by assertion: portable product-row resolution is current and blocking, while propane configuration observation is non-blocking until activation.

## Execution-scenario requirements

- `V2BQ-CT-007` (#15) requires a real persisted conversation, process restart, reload, and follow-up. Prompt-history simulation does not satisfy it.
- `V2BQ-CT-008` (#16) requires two real conversation IDs and fails if conversation B resolves its pronoun from conversation A.

## Artifacts

- `V2_MASTER_REGRESSION_POPULATION_v1.jsonl`: fully labeled retained scenarios and expectation units.
- `V2_HISTORICAL_QUESTION_TRIAGE_v1.jsonl`: one locked decision for every normalized historical question. Sensitive and excluded DB-only text is represented by hashes and provenance rather than copied into the repository.
- `V2_MASTER_REGRESSION_MANIFEST_v1.json`: byte-stable hashes, counts, database snapshot digests, authority decisions, freeze enforcement, and global gate population contracts.

## Freeze and denominator contract

- Candidate generation cannot overwrite a locked artifact version. Any population, label, or inclusion/exclusion correction requires a new artifact version and approval.
- Frozen verification is read-only for canonical artifacts; transient timestamps belong only in an optional verification ledger.
- G01 is derived from all qualification-eligible retrieval-bearing logical attempts in the execution ledger, not scenario gate tags.
- G18 is derived from all qualification-eligible logical attempts in the attempt ledger. `SYSTEM_FAILURE` counts against the gate; `RUN_INVALIDATION` invalidates the full affected run and never becomes an exclusion.
- One hundred percent of each pre-frozen applicable population remains in its denominator. Post-run exclusions are prohibited.

## Important boundary

This work establishes and freezes the authoritative expected-behavior population and gate-scorer contract v1. It does not approve a production-path evaluator or claim that a transcript restart harness, claim-level scorer, or release qualification run has executed. Evaluator implementation remains `BLOCKED_PENDING_IMPLEMENTATION`, and qualification remains `NOT_EXECUTED`.
