# Evaluation evolution

Historical progression:

```text
retrieval recall
→ exact identifier correctness
→ source/page grounding
→ answer fidelity
→ identity/document applicability
→ owner/configuration correctness
→ structural evidence completeness
→ model-visible context sufficiency
→ response-plan correctness
→ final answer correctness
→ citation support/completeness
→ fresh holdout
→ scale robustness
→ paired ablation
```

Do not compare populations, gold units, K definitions, exclusion rules, or pipeline arms without a crosswalk.

Repository-local historical evidence:
- [historical/V2_MASTER_REGRESSION_REPORT_v1.md](historical/V2_MASTER_REGRESSION_REPORT_v1.md)
- [historical/V2_EVALUATION_AUTHORITY.md](historical/V2_EVALUATION_AUTHORITY.md)
- [frozen/e2e_metric_registry_v1.json](frozen/e2e_metric_registry_v1.json)
- [frozen/V2_GATE_SCORER_CONTRACTS_v1.md](frozen/V2_GATE_SCORER_CONTRACTS_v1.md)
- [../lessons/LESSONS_LEARNED.md](../lessons/LESSONS_LEARNED.md)

The V2 frozen master population is evidence of a frozen evaluation design/population, not evidence of a successful qualification run.
