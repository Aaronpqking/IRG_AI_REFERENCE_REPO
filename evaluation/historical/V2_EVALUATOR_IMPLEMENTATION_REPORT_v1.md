# V2.0 Evaluator Implementation Candidate v1

Status: `READY_FOR_EVALUATOR_APPROVAL`

Evaluator version: `v2-evaluator.1`

Evaluator approval: `PENDING_OWNER_APPROVAL`

Qualification: `NOT_EXECUTED`

## Frozen authority

- Population SHA-256: `4b561ffea79edc97c270cda38fbd0e5351615c0acd8d8be4eab291a3d504bd8e`
- Triage SHA-256: `8dc936cb0d7c600fdad13592f45f2b564ff8c0b41e9050294373f19432a25e2d`
- Master-manifest SHA-256: `9ddf9eaf993a62182ce1c52f550002deb2d3584f12e9a56167fba1fe78df0f3c`
- Scorer-contract SHA-256: `7a376ba1ab2775431625468b6e45bc9c859aff2a01c180c80118f9845f556be0`

No frozen population, triage, label, gate applicability, scorer policy, or
threshold was changed.

## Architecture

The evaluator is an offline-only subsystem with six separated layers:

1. An immutable, self-hash-validating qualification-plan schema binds every
   qualification-sensitive input rather than inheriting mutable environment
   settings.
2. Typed execution records and an append-only JSONL ledger preserve logical
   attempts, nested provider calls, retrieval lanes, final identity results,
   scope/ownership transitions, atomic claims, completeness reviews, and human
   adjudications.
3. Shared deterministic primitives perform exact set/state/ownership/source,
   numeric/unit, polarity, condition, relationship, uniqueness, schedule, and
   integer threshold checks.
4. Seven separate scorers implement V2-G01, G02, G03, G05, G06, G07, and G18.
5. Human G06 control requires complete claim inventory confirmation before
   support aggregation and permits only blinded human residual adjudication.
6. Aggregation preserves individual runs as authority. Pooled metrics and retry
   rate are supplemental only.

## Gate implementations

| Gate | Callable | Frozen/static population authority |
|---|---|---|
| V2-G01 | `src.v2_evaluator.scorers.score_g01` | Execution-ledger-derived |
| V2-G02 | `src.v2_evaluator.scorers.score_g02` | 82 blocking expectations per run |
| V2-G03 | `src.v2_evaluator.scorers.score_g03` | 86 blocking expectations per run |
| V2-G05 | `src.v2_evaluator.scorers.score_g05` | 15 blocking expectations per run |
| V2-G06 | `src.v2_evaluator.scorers.score_g06` | Claims from 175 blocking parent expectations per run |
| V2-G07 | `src.v2_evaluator.scorers.score_g07` | 14 blocking expectations per run |
| V2-G18 | `src.v2_evaluator.scorers.score_g18` | Attempt-ledger-derived |

For three provider-dependent runs, the static scheduled blocking parent/unit
counts are G02 246, G03 258, G05 45, G06 525 parent attempts, and G07 42. G06's
claim denominator is deliberately not guessed: it is the complete human-
confirmed atomic substantive claim inventory emitted in each run. G01 and G18
denominators remain execution-derived exactly as required by the scorer
contract.

## Validation fixtures

The manifest-bound candidate fixture matrix contains known-pass, known-fail, and edge cases for
every gate, plus multi-run and non-blocking-isolation cases. It includes the
required zero-result accounting, final-versus-raw identity, clarification,
ownership, critical veto, claim omission, compound claim, wrong-owner,
critical unsupported, exact 1% boundary, restart/reload, conversation leakage,
transport retry, system failure, run invalidation, duplicate attempt,
three-run, pooled non-rescue, and mixed-release-effect cases.

The test evidence records 17/17 core evaluator tests, 23/23 focused evaluator
and artifact tests, and 43/43 broader offline authority-regression tests
passing without provider calls. The evaluator runtime itself uses only the
Python standard library; pytest is test-only.

## Approval boundary and remaining execution inputs

This is a candidate evaluator freeze, not owner approval. A concrete
qualification plan has intentionally not been created because its exact corpus,
retriever, runtime, provider/model, prompt, stochastic, retry, lane, and run IDs
must be resolved and frozen without mutable environment inheritance. Aaron must
approve this evaluator artifact and the subsequently resolved qualification
plan before qualification may execute.

No production runtime, prompt, retrieval behavior, corpus, Qdrant, or MySQL
state was changed, and no qualification or live model evaluation was run.
