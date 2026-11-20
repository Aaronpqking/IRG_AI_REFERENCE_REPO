# Codex reference index
Start at [CURRENT_REFERENCE_STATE.md](CURRENT_REFERENCE_STATE.md); inspect [REFERENCE_POLICY.md](REFERENCE_POLICY.md) before design decisions.

| Question | Starting point | Evidence escalation |
|---|---|---|
| What is established vs not? | CURRENT_REFERENCE_STATE.md | CLAIM_REGISTER.jsonl, SOURCE_MANIFEST.md |
| Where did capabilities originate? | timeline/BUILD_TIMELINE.md | lessons/IMPLEMENTATION_HISTORY.md |
| Product/model identity? | architecture/DURABLE_ARCHITECTURE_PRINCIPLES.md | governance/SOURCE_AUTHORITY.md |
| Applicable technical documents? | governance/SOURCE_AUTHORITY.md | historical authority contracts |
| Retrieval and fusion? | architecture/TARGET_REFERENCE_PIPELINE.md | evaluation/EMPIRICAL_FINDINGS.md |
| Structural context and procedures? | architecture/ARCHITECTURE_EVOLUTION.md | source/reference material pending |
| Which experiments can be trusted? | evaluation/EXPERIMENT_REGISTER.md | evaluation/FROZEN_TRANSFER_LEDGER.json, evaluation/INTEGRITY_FINDINGS_20261120.md |
| Definitions and denominators? | evaluation/METRIC_DEFINITIONS.md | evaluation/EVALUATION_INTEGRITY |
| Negative results? | evaluation/FAILURE_REGISTER.md | evaluation/REJECTED_MECHANISMS.md, evaluation/EXPERIMENT_ADDENDUM_20261120.md |
| Which architectural choices? | decisions/ADR_INDEX.md | original accepted ADRs |
| What should clean build inherit? | lessons/CLEAN_LAB_CARRY_FORWARD.md | proven downstream evidence |
| What to avoid? | architecture/ARCHITECTURAL_DEBT_AND_FAILURES.md | negative ablations |
| What was not transferred? | P0_SEED_LEDGER.md | SOURCE_MANIFEST.md |

**Codex boundary:** This is not a full source checkout. Never assume a referenced file was copied merely because it appears in an index. Require a verified repository path and checksum for frozen empirical authority.
**Frozen transfer update:** Ten original Drive source artifacts have exact SHA-256 and Git-blob verification in [FROZEN_TRANSFER_LEDGER](evaluation/FROZEN_TRANSFER_LEDGER.json); raw historical question-level population/triage remain withheld. [IRG-X001](evaluation/INTEGRITY_FINDINGS_20261120.md) prevents qualifying mismatched evaluator/master manifest revisions. Validate locally with `python scripts/validate_reference_seed.py` (strict mode rejects blockers).

**Source-binding update:** [Selected archived source/test hashes](source_reference/SOURCE_BINDINGS_20261120.json), [static source review](reports/reference/audits/GOOGLE_DRIVE_SOURCE_BINDING_20261120.md), and [IRG-X001 hash lineage](evaluation/IRG_X001_MANIFEST_LINEAGE_20261120.md). Source code remains private; the archived source snapshot is **not** an October commit-bound implementation.

**Approved evaluator reconstruction:** [Owner approval and version-state reconciliation](evaluation/EVALUATOR_APPROVAL_RECONCILIATION_20261120.md) → [all 10 source/test bindings](evaluation/EVALUATOR_PROVENANCE_LEDGER.json) → [original approval record](evaluation/frozen/V2_EVALUATOR_APPROVAL_v1.json). Evaluator implementation is historically approved, qualification remains NOT_EXECUTED, and IRG-X001 remains open.

## Updated P0 external-storage rule (2026-11-20)
See [reference portability and Drive boundary](governance/REFERENCE_PORTABILITY_POLICY.md). External archives may be used for discovery, but current claims must be comprehensible from repository-local evidence. Historical source hashes are provenance only; they **do not populate** the required curated implementation and historical test folders. Passing non-strict CI proves integrity only. Strict P0 completion remains blocked until local evidence and the remaining authority gates are satisfied.
