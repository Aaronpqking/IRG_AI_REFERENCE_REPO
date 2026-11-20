# Codex reference index
Start at [CURRENT_REFERENCE_STATE.md](CURRENT_REFERENCE_STATE.md), then read [REFERENCE_POLICY.md](REFERENCE_POLICY.md).

| Question | Starting point | Repository-local escalation |
|---|---|---|
| What is established vs provisional? | CURRENT_REFERENCE_STATE.md | CLAIM_REGISTER.jsonl, SOURCE_MANIFEST.md |
| Where did capabilities originate? | timeline/BUILD_TIMELINE.md | lessons/IMPLEMENTATION_HISTORY.md, timeline/evidence/ |
| Product/model identity? | architecture/DURABLE_ARCHITECTURE_PRINCIPLES.md | governance/SOURCE_AUTHORITY.md, decisions/historical/ |
| Applicable technical documents? | governance/SOURCE_AUTHORITY.md | architecture/historical/, governance/historical/ |
| Retrieval and fusion? | architecture/TARGET_REFERENCE_PIPELINE.md | evaluation/EMPIRICAL_FINDINGS.md, source_reference/retrieval/ when populated |
| Structural context and procedures? | architecture/ARCHITECTURE_EVOLUTION.md | source_reference/structural/ and research/structural/ when populated |
| Which experiments can be trusted? | evaluation/EXPERIMENT_REGISTER.md | evaluation/frozen/, evaluation/INTEGRITY_FINDINGS_20261120.md |
| Definitions and denominators? | evaluation/METRIC_DEFINITIONS.md | evaluation/frozen/e2e_metric_registry_v1.json, evaluation/frozen/V2_GATE_SCORER_CONTRACTS_v1.md |
| Negative results? | evaluation/FAILURE_REGISTER.md | reports/reference/ablations/, evaluation/REJECTED_MECHANISMS.md |
| Which architectural choices? | decisions/ADR_INDEX.md | decisions/historical/ |
| What should clean build inherit? | lessons/CLEAN_LAB_CARRY_FORWARD.md | local historical evidence and qualified experiments |
| What to avoid? | architecture/ARCHITECTURAL_DEBT_AND_FAILURES.md | reports/reference/ablations/, reports/reference/audits/ |
| What is still missing? | P0_COVERAGE_MATRIX.md | P0_SEED_LEDGER.md |

## Codex boundary
This repository is not yet a complete historical source checkout. Never infer that a referenced capability exists locally unless its repository path resolves. A current claim must either point to repository-local evidence or be explicitly labeled unverified synthesis/history.

External source URLs may appear only in provenance ledgers. They are not evidence dependencies for clean-build reasoning.

Validate with:

```bash
python scripts/validate_reference_seed.py
```

Strict completion is intentionally blocked until required source/test/report groups are locally populated and frozen-evidence blockers are resolved.
