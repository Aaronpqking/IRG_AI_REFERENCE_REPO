# Codex reference index
Start at [CURRENT_REFERENCE_STATE.md](CURRENT_REFERENCE_STATE.md); inspect [REFERENCE_POLICY.md](REFERENCE_POLICY.md) before design decisions.

| Question | Starting point | Evidence escalation |
|---|---|---|
| What is established vs not? | CURRENT_REFERENCE_STATE.md | CLAIM_REGISTER.jsonl, SOURCE_MANIFEST.md |
| Where did capabilities originate? | timeline/BUILD_TIMELINE.md | Drive IMPLEMENTATION_HISTORY |
| Product/model identity? | architecture/DURABLE_ARCHITECTURE_PRINCIPLES.md | governance/SOURCE_AUTHORITY.md |
| Applicable technical documents? | governance/SOURCE_AUTHORITY.md | historical authority contracts |
| Retrieval and fusion? | architecture/TARGET_REFERENCE_PIPELINE.md | evaluation/EMPIRICAL_FINDINGS.md |
| Structural context and procedures? | architecture/ARCHITECTURE_EVOLUTION.md | source/reference material pending |
| Which experiments can be trusted? | evaluation/EXPERIMENT_REGISTER.md | evaluation/frozen/ (pending payload verification) |
| Definitions and denominators? | evaluation/METRIC_DEFINITIONS.md | evaluation/EVALUATION_INTEGRITY |
| Negative results? | evaluation/FAILURE_REGISTER.md | evaluation/REJECTED_MECHANISMS.md |
| Which architectural choices? | decisions/ADR_INDEX.md | original accepted ADRs |
| What should clean build inherit? | lessons/CLEAN_LAB_CARRY_FORWARD.md | proven downstream evidence |
| What to avoid? | architecture/ARCHITECTURAL_DEBT_AND_FAILURES.md | negative ablations |
| What was not transferred? | P0_SEED_LEDGER.md | SOURCE_MANIFEST.md |

**Codex boundary:** This is not a full source checkout. Never assume a referenced file was copied merely because it appears in an index. Require a verified repository path and checksum for frozen empirical authority.