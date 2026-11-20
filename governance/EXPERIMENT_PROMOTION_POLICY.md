# Experiment → clean-build promotion policy

Required: frozen hypothesis, one changed variable, baseline/candidate bindings, population/gold, truly unseen holdout, validity ledger, downstream final-context and response metrics, safety regressions, latency/storage/cost deltas, operator approval and rollback. Source and evaluator must be bound by hash. Rank-order change alone cannot justify promotion. Do not repair gold or denominator after execution.

Separate stages: MECHANISM_PROVEN; DOWNSTREAM_GAIN_PROVEN; SCALE_ROBUST; GENERALIZATION_PROVEN; ARCHITECTURE_PROMOTED. None implies the next.

Promotion records conform to [../promotion_record.schema.json](../promotion_record.schema.json). Rejected/no-gain results remain in [../evaluation/REJECTED_MECHANISMS.md](../evaluation/REJECTED_MECHANISMS.md). No threshold invented retroactively.
