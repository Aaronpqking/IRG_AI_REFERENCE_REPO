# Evaluation integrity
- Predeclare population, applicability, denominator, exclusion rules and exact gold before qualifying.
- Hash and freeze original question text, corpus, evidence, prompts, evaluator, runtime/config and scoring rules. Source text may be kept private; public ledger retains non-sensitive hashes.
- Do not tune on fresh holdout; create a new separate holdout after exposure.
- Post-execution gold rewriting prohibited; invalid run remains invalid; no post hoc denominator shrinkage.
- Case-level exceptions are documented; system failure counts against a valid run's gate; invalidation is not silently excluded.
- Always distinguish retrieval, sufficient evidence@K, context sufficiency, realization and citations.
- Partial execution is diagnostic, not qualification; skipped and blocked cases remain visible.
- 2026-09-02 V2 master population freeze was not a completed qualification: https://docs.google.com/document/d/1ZnHzc0VX8PDXmv9PV59yLG7PPQvjHYEM/edit.