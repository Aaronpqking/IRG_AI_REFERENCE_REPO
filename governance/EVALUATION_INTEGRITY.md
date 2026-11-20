# Evaluation integrity

- Predeclare population, applicability, denominator, exclusion rules and exact gold before qualification.
- Freeze and identify question text, corpus, evidence, prompts, evaluator, runtime/config and scoring rules.
- Do not tune on a fresh holdout after exposure; create a new independent holdout.
- Post-execution gold rewriting is prohibited.
- Invalid runs remain invalid; partial execution is diagnostic, not qualification.
- Do not silently shrink denominators after seeing outcomes.
- Case-level exceptions, skipped cases, blocked cases and infrastructure failures remain visible.
- Distinguish candidate retrieval, evidence sufficiency, model-visible context sufficiency, realization and citation support.
- Provider/system failure and evidence insufficiency require distinct failure classes.
- Public provenance may retain hashes for withheld sensitive material, but withheld material cannot be treated as locally reproducible evidence.

Repository-local frozen authority:
- [../evaluation/frozen/V2_GATE_MANIFEST.json](../evaluation/frozen/V2_GATE_MANIFEST.json)
- [../evaluation/frozen/V2_GATE_SCORER_CONTRACTS_v1.md](../evaluation/frozen/V2_GATE_SCORER_CONTRACTS_v1.md)
- [../evaluation/frozen/V2_MASTER_REGRESSION_MANIFEST_v1.json](../evaluation/frozen/V2_MASTER_REGRESSION_MANIFEST_v1.json)
- [../evaluation/historical/V2_EVALUATION_AUTHORITY.md](../evaluation/historical/V2_EVALUATION_AUTHORITY.md)

The captured V2 state did not establish completed release qualification. See [../evaluation/INTEGRITY_FINDINGS_20261120.md](../evaluation/INTEGRITY_FINDINGS_20261120.md).
