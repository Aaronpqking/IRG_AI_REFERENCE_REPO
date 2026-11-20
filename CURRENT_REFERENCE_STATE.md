# IRG AI — current intellectual reference state (2026-11-20)

**Status:** synthesis over repository-local evidence plus explicitly labeled late project-history observations. This is not a live checkout, production-state claim, or release qualification.

## Repository-local bounded historical evidence

- V1.5 freeze: 132 approved PDFs; 4,173 chunks; OpenAI `text-embedding-3-small` at 1,536 dimensions; Qdrant dense collection; hybrid retrieval configuration; bounded shared context. Local source: [timeline/evidence/V1_5_FROZEN_CONFIGURATION_AND_ARTIFACTS_20260731.md](timeline/evidence/V1_5_FROZEN_CONFIGURATION_AND_ARTIFACTS_20260731.md).
- Historical V1.5 architecture: product DB discovery plus approved-PDF hybrid retrieval and bounded context; internal pilot/release baseline, not a claim about the later structural research system. Local source: [architecture/historical/V1_5_IMPLEMENTED_ARCHITECTURE_BASELINE.md](architecture/historical/V1_5_IMPLEMENTED_ARCHITECTURE_BASELINE.md).
- V2 master regression report: 244 scenarios / 245 expectation units; evaluator qualification was not executed at the captured report state. Local source: [evaluation/historical/V2_MASTER_REGRESSION_REPORT_v1.md](evaluation/historical/V2_MASTER_REGRESSION_REPORT_v1.md).
- IRG authority policy is explicitly policy-only/not activated. Local source: [governance/historical/IRG_AUTHORITY_POLICY_V1.md](governance/historical/IRG_AUTHORITY_POLICY_V1.md).
- Historical architecture and implementation evolution are preserved locally in [lessons/IMPLEMENTATION_HISTORY.md](lessons/IMPLEMENTATION_HISTORY.md), [lessons/LESSONS_LEARNED.md](lessons/LESSONS_LEARNED.md), the ADR set, and transferred historical contracts.

## Late project-history observations awaiting complete local run packages

These observations are retained because they materially change the current intellectual state. They remain **HISTORY_REPORTED_UNVERIFIED** until their original bound ledgers, source snapshots, evaluator bindings, and/or case manifests are present locally.

### October reconstruction and scale

- Verified October anchor reported 26/26 downstream parity. On the answerable subset, exact-gold Recall@10 was 21/21; sufficient context was 19/21 (P1 5/6, P2 14/15); critical wrong-product/revision errors were 0.
- P1 scale at that point: 80 logical documents, 48,447 views, 46,462 vectors.
- P2 scale: 437 logical documents, 107 physical sources, 216,921 views, 163,268 vectors. P2 eligibility was product-scoped rather than unrestricted 437-way competition.
- Expanded 40-case comparison later reported current representation 16/40 exact-gold versus recovered October representation 13/40. Narrative subset: 3/10 versus 0/10. These denominators are not interchangeable with the 21-case reconstruction population.

### Standard-view vs full-view paired generalization

- Planned 20, executed 19, valid unseen denominator 17.
- Both standard and full arms: sufficient context 3/17; sufficient evidence@10 5/17; critical wrong-product errors 0.
- Paired result: 0 full-view wins, 0 losses, 3 shared successes, 14 shared failures.
- The additional 10,868 contextualized views changed raw lexical/dense ordering in 17/18 valid comparisons, fusion in 9, reranking in 7, and delivered evidence/context in only one case; no failed case was rescued.
- Interpretation: the tested view expansion changed ranking behavior without demonstrating downstream generalization gain.

### November corpus/alias and authority audit

- A November audit reproduced 19/19 alias failures (13/13 cart cases).
- Historical inventory reported 1,502 canonical documents versus 935 physical revisions, with 567 excess canonical records; 1,110 duplicate references across 298 products.
- A reviewed inactive safety candidate removed 52 unsupported post/cart grants from 4,943 relationships while preserving 40/40 reviewed positives and 9/9 revocations; this was bounded candidate evidence, not global applicability certification.

### R2 authoritative ledger reported 2026-11-18

This is the latest project-history state currently known and supersedes earlier R2 progress summaries where they conflict.

- **P0 corpus recovery:** deferred; 183 logical / 177 physical in the reported recovery scope.
- **P1 evaluation:** 6/150 latest baseline cases completed; 0 accepted gates.
- **P2 identity controls:** 49/49 literals and 19/19 controls completed; the target of at least 98% identity correctness remained unproven.
- **P3 document competition:** scopes 83 / 38 / 561 / 67 with mean document reduction 90.85%. This is evidence that metadata authority can reduce document competition.
- **P4 evidence competition:** canonical reduction ranged 18.92%–51.62%, but fine exclusions were 0; lexical competition reduction was 0% and dense reduction only 0%–6.22%. This is the central negative finding: document-level narrowing did not reliably translate into retrieval-level competition reduction.
- **P5/P6 sufficiency:** 0/5 sufficient-context outcomes in the reported slice.
- **P7 execution/parity:** 35 valid cases; cold execution 141.935 s, repeat 28.175 s; parity 35/35. No SLO or p95 was established.

Earlier 2026-11-16 observations are retained as progression evidence but are superseded by the 2026-11-18 ledger where inconsistent: P1 accessibility 2,047/2,047 docs and 1,331 revisions; an identity-normalization defect where Bromic possessive `s` could collapse to model `S`; metadata-only Arm B substantially reduced candidate documents for several brands but still had packaging failures and one blocked manufacturer case.

## Current technical interpretation

1. **Identity is necessary but not sufficient.** Exact identifiers, literals, and document authority must be explicit and independently measurable.
2. **Document narrowing is not evidence narrowing.** P3 showed large document reduction while P4 showed little or no lexical/dense competition reduction.
3. **Candidate retrieval is not context sufficiency.** Strong exact-gold retrieval on bounded populations coexisted with poor sufficient-context delivery on independent/unseen and later R2 slices.
4. **Canonical evidence remains useful; uncontrolled view multiplication does not.** Derived representations must earn promotion through downstream evidence/context gains.
5. **Authority, retrieval, context, answerability, generation, and citation are separate failure surfaces.**
6. **Scale claims require bound populations.** The 21-case reconstruction, 17-case P2 unseen study, 40-case scale comparison, 110-case development replay, 150-case R2 holdout, and 244-scenario frozen V2 population must never be merged into one accuracy number.
7. **Latency remains unresolved.** P7 parity does not establish acceptable SLO/p95 behavior.

## Current decision posture

**Carry forward only with repository-local evidence and fresh clean-build tests:** exact identity; document applicability; fact-specific authority; canonical evidence/provenance; lexical + dense retrieval where measured; bounded structural reconstruction; explicit context sufficiency; clarification/abstention; citation validation; immutable evaluation.

**Do not automatically carry forward:** full-view proliferation; giant graph/view materialization; product-role permission infrastructure; feature-flag mazes; unactivated policies; historical runtime code paths; metadata narrowing assumed to reduce retrieval competition.

## Open blockers

- Curated legacy source and tests are not yet fully present under `source_reference/`, `source_snapshot/`, and `tests_reference/`.
- Several intended milestone report directories remain unseeded.
- Late October/November run ledgers and case manifests are not yet local.
- IRG-X001 frozen-manifest mismatch remains unresolved.
- Private frozen populations are hash-verified but intentionally absent from the public repository.
- R2 150-case evaluation is incomplete; no accepted gates, no established SLO/p95, and insufficient-context failures remain open.

See [P0_SEED_LEDGER.md](P0_SEED_LEDGER.md), [P0_COVERAGE_MATRIX.md](P0_COVERAGE_MATRIX.md), and [SEED_COMPLETENESS_AUDIT_20261120.md](SEED_COMPLETENESS_AUDIT_20261120.md).

## Self-contained evidence rule

Current/reference documents must be interpretable using repository-local artifacts and explicit claim status. External archive locations may be retained only in non-required provenance metadata; Codex must never need external storage access to understand, verify the local transfer hash, or follow the current reference logic.
