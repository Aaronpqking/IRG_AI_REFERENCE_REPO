# Expanded corpus scale test — November 2026 historical synthesis

**Evidence class:** HYBRID — reconstructed from IRG AI project conversation history and the seed manifest. The original October 2026 scale-test ledger, frozen sample identities and serving/composition hashes have **not** been transferred to this repository. This document is **not** a new experiment or a qualification result.

## Recorded October comparison
| Evaluation slice | Current | October comparator | Denominator |
|---|---:|---:|---:|
| Exact gold identified in scale test | 16 (40.0%) | 13 (32.5%) | 40 cases each |
| Narrative questions succeeded | 3 (30.0%) | 0 (0.0%) | 10 cases each |

Arithmetic differences: +3/40 (+7.5 percentage points) for the gold slice; +3/10 (+30 percentage points) for narrative. No causal effect size or confidence interval is asserted: population equivalence, source/index binding and evaluator versions have not been proven here.

## Interpretation
- Prior reconstruction on bounded P1/P2 exact-gold populations reportedly achieved 100% Recall@10. It was **not** the same 40-case scale denominator, nor a final answer-quality measure.
- Structural expansion created multiple representation levels. More views can change ordering while the correct applicable evidence or complete model-visible context remains unavailable.
- Accuracy on development/controlled questions does not estimate expanded-corpus unseen-case generalization unless holdout sampling and exposure can be audited.

## Necessary artifacts before qualification
1. The frozen 40 gold and 10 narrative test case manifests for both comparator arms.
2. Per-case source, approved document applicability, owner/configuration, gold IDs, and scorer versions.
3. Source commit, corpus canonical count/hash, embedding/reranker config, view population, context serialization and prompt/provider binding.
4. Per-case candidate@K, sufficient evidence@K, serialized context sufficiency, final-answer/citation validity, and failure class.
5. Paired outcome table and independent untouched holdout; explicitly report invalid/blocked cases.

## Negative control
Do not use the reported +3 cases as evidence that corpus growth is beneficial or that a chosen mechanism generalizes. Do not merge these selected denominators with historical 110-case development replay or V2 frozen 244-scenario release population.

## Provenance
- User-supplied IRG AI project history (2026-10-30 20%-scale test) and 2026-11-20 reference seed manifest.
- [Evaluation results crosswalk](../evaluation/EVALUATION_RESULTS_CROSSWALK.md)
- [Corpus scale evolution](CORPUS_SCALE_EVOLUTION.md)

**Status:** `HISTORY_REPORTED_UNVERIFIED` / `NOT_PROMOTED`.
