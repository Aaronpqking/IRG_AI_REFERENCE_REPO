# Metric definitions (clean-lab reference; reconcile against original scorer contracts)
Every metric requires run_id, query population, denominator, gold unit, retrieval stage, K, exclusion policy, source/corpus/model/config hashes and evaluator version.

- Candidate@K: fraction of eligible cases containing at least one applicable candidate within first K **before context construction**.
- Exact Gold@K / Recall@K: proportion of explicitly frozen gold evidence IDs reached in top K at the declared stage; record micro vs macro average separately.
- Semantic answer-set reachability: question-answer supporting facts reachable within selected evidence, independently of exact gold ID.
- MRR: mean reciprocal rank of the first qualifying evidence item per query; unanswered queries contribute 0.
- correct-owner@1 / wrong-owner@1: top candidate belongs to correct/incorrect applicable product authority, respectively; record ambiguous/unknown independently.
- selection-given-gold: context selects gold evidence conditional on it being retrieved in candidate pool; conditional denominator cannot be mistaken for overall.
- evidence sufficiency@K: selected evidence set jointly contains all required claims; independent of answer text.
- context sufficiency: serialized model-visible context suffices to construct supported answer, independently of retrieval pool success.
- answerability/clarification/abstention correctness: correct response disposition under source availability, uncertainty, ambiguity, conflict.
- final response correctness: all required answer claims correct on authorized evidence; distinguish complete vs partial and unsupported.
- citation precision: proportion of citations that actually support attached claims; citation completeness: required supported claims carrying valid source locators.
- unsupported claims: claim-level assertion unsupported by provided applicable evidence.
- contamination: holdout examples, gold or tuned answer content leaked into candidate design.
- authority correctness: source is approved for fact type, model/revision/configuration/time scope.
These are **normalized draft definitions**, not replacements for immutable historical scorer contracts.