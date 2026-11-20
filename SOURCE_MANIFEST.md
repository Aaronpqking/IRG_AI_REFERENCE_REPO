# Provenance ledger

This ledger distinguishes **repository-local transferred artifacts** from **synthesized reference documents**. Repository-local files, hashes, and claim status are sufficient for Codex use. External archive systems are not required to interpret or validate a local transfer.

| Destination | Origin class | Date | Class | Authority | Why retained | Superseded/combined with |
|---|---|---|---|---|---|---|
| README.md | seed specification + project-history synthesis | 2026-11-20 | HYBRID | interpretation | navigation and boundary | none |
| REFERENCE_POLICY.md | historical governance + evaluation + synthesis | 2026-11-20 | HYBRID | repository policy | evidence precedence | older snapshot guidance |
| CURRENT_REFERENCE_STATE.md | local historical artifacts + dated project-history observations | 2026-11-20 | HYBRID | current synthesis | state of evidence | later verified runs may supersede |
| architecture/TARGET_REFERENCE_PIPELINE.md | late project-history synthesis | 2026-11-20 | HYBRID | proposed clean reference | separates decision stages | not a single historical runtime |
| evaluation/EXPERIMENT_REGISTER.md | local experiment reports + project-history records | 2026-11-20 | HYBRID | experiment index | prevents false equivalence | exact late-run ledgers still pending |
| CLAIM_REGISTER.jsonl | local evidence + explicitly labeled history observations | 2026-11-20 | GENERATED | claim-level registry | claim support and status | verify provisional claims against local run artifacts |
| transferred historical copies | original historical artifact bytes | historical | TRANSFER | historical evidence | source fidelity | no automatic current authority |

## Local transfer authority

For every exact transfer, the repository should retain:

- destination path;
- original artifact name;
- byte count;
- SHA-256 of the source bytes;
- transfer status;
- sensitivity/visibility disposition;
- any binding/version exception.

A local artifact plus its cryptographic identity is the operational reference. External storage URLs are intentionally omitted because they may not be accessible to Codex or future maintainers.

Current exact frozen transfers are recorded in [evaluation/FROZEN_TRANSFER_LEDGER.json](evaluation/FROZEN_TRANSFER_LEDGER.json).

## Withheld evidence

Some historical evaluation populations are intentionally absent from this public repository because their contents may include historical user-conversation wording. For withheld items, only the artifact name, cryptographic hash, byte count, reason withheld, and binding status belong here. A withheld hash proves identity of the separately controlled artifact; it does **not** make the public repository independently reproducible.

## Current integrity exception

**IRG-X001**: the available historical master-regression manifest and the evaluator-bound master-manifest hash differ. Do not rewrite either artifact to force consistency. Qualification remains blocked until the evaluator-bound revision is recovered or the mismatch is otherwise reconciled by direct evidence.

## Transfer rule

A transfer is complete only when:

1. the complete source bytes were read;
2. the repository file exists;
3. byte length and SHA-256 match the source;
4. format validation succeeds where applicable;
5. the transfer ledger records the result;
6. the artifact is classified correctly as frozen, historical, research, or current synthesis.

A pointer, filename, summary, or project-history statement is never sufficient to label an artifact `TRANSFERRED_EXACT`.

## Externally verified, not locally transferred (2026-11-20)

The [source binding inventory](source_reference/SOURCE_BINDINGS_20261120.json) and [evaluator provenance ledger](evaluation/EVALUATOR_PROVENANCE_LEDGER.json) record hashes of private historical source/test bytes. Both explicitly set `p0_local_evidence_status: EXTERNALLY_VERIFIED_NOT_LOCAL`; these inventories **do not** satisfy the curated local implementation/test folders. The owner-approved evaluator contract/fixture/approval metadata is separately available as exact local transfers under `evaluation/frozen/`, subject to publication review. For transfer vs archive-source rules, see [reference portability policy](governance/REFERENCE_PORTABILITY_POLICY.md).

## Identity implementation publication triage — 2026-11-20
Eight original identity/authority source and historical test files were located and byte-hashed (138,849 bytes; 8 SHA-256 fingerprints computed; 0 independent frozen-digest comparisons performed). See [identity publication triage](governance/publication_reviews/IDENTITY_SOURCE_TRIAGE_20261120.json) and [review](governance/publication_reviews/IDENTITY_SOURCE_REVIEW_20261120.md). The original code is **not** in this public repository; `transfer_status=EXTERNALLY_VERIFIED_NOT_LOCAL`, `publication_review=BLOCKED_PENDING_HUMAN_AUTHORIZATION`, `local_sha256=null`. These records establish provenance but do not meet local source/test completeness or executable qualification.

## Exact local identity originals — approved publication (2026-11-20)
After the user's explicit approval, five historical implementation files were transferred **unchanged** to `source_reference/identity/` and three historical tests to `tests_reference/historical/identity/`. [Original-to-local transfer ledger](governance/publication_reviews/IDENTITY_SOURCE_TRIAGE_20261120.json) contains original path, destination, **138,849 bytes**, original/local SHA-256, publication state and no-redaction status for all eight. All eight are `LOCAL_EXACT_TRANSFER_VERIFIED`; source-commit binding is still unknown and the original tests have not been run. This closes the selected *file-transfer* slice, not full identity architecture coverage or P0 strict completion.

## Approved bounded report-family reconciliation (2026-11-20)
The original conflicting multi-report draft PR #10 was closed without merge. Its five curated summaries were preserved on separate, current-main review branches and merged individually as PRs #15–#19. The local destinations and source-provenance records are:
- [V1](reports/reference/v1/PROVENANCE.json): `reports/reference/v1/V1_CLOSEOUT_EVIDENCE_SUMMARY_20260715.md`
- [V1.5](reports/reference/v1_5/PROVENANCE.json): `reports/reference/v1_5/V1_5_CLOSEOUT_EVIDENCE_SUMMARY_20260731.md`
- [Corpus](reports/reference/corpus/PROVENANCE.json): `reports/reference/corpus/CORPUS_AUTHORITY_RECONCILIATION_20260804.md`
- [Structural](reports/reference/structural/PROVENANCE.json): `reports/reference/structural/STRUCTURAL_GATE3_LOSS_BOUNDARIES_20260813.md`
- [Structural research](research/structural/PROVENANCE.json): `research/structural/SHADOW_CORPUS_PROCEDURE_HOLDOUT_20260909.md`
These five are **`CURATED_NOT_EXACT_TRANSFER`**; source archive SHA-256 and original run-package proof remain unavailable. Their locally synthesized contents are reference evidence but cannot substitute for full original milestone reports or empirical replay.

## P0 original-source expansion and exact transfer totals — 2026-11-20
The five original-source reference families now contain transferred, nonempty, unmodified source under `source_reference/{identity,retrieval,context,contracts,structural}/`. Ten additional original historical behavior tests are locally archived, making **34 original implementation modules plus 13 original test modules, 47 exact source/test transfers totaling 894,329 bytes**, including the prior identity slice. Source originals, original relative paths, destination paths, exact byte counts, original/local SHA-256, no-redaction status, and `original_git_revision: UNKNOWN` are documented in the four family `TRANSFER_MANIFEST.json` files plus [identity transfer record](governance/publication_reviews/IDENTITY_SOURCE_TRIAGE_20261120.json) and [historical tests](tests_reference/historical/behavior/TRANSFER_MANIFEST.json). These are file-level exact transfers, **not** a coherent original Git checkout.

[SNAPSHOT_MANIFEST](source_snapshot/SNAPSHOT_MANIFEST.md) documents the explicit reason a full coherent snapshot is unavailable. [Late-run audit](reports/reference/audits/LATE_RUN_PROVENANCE_RECONCILIATION_20261120.md) retains the original November/October run evidence gaps, the private frozen-population restrictions, and `IRG-X001`. Five existing historical report summaries remain `CURATED_NOT_EXACT_TRANSFER` and are not counted as 47 original source/test transfers.

## Structural research synthesis provenance (2026-11-20)
[research/structural/STRUCTURAL_RESEARCH_SUMMARY.md](research/structural/STRUCTURAL_RESEARCH_SUMMARY.md) is **`HYBRID / SYNTHESIS`**: a newly authored integration of locally available byte-verified structural implementations, curated August/September reports, historical V1.5 architecture and explicitly unverified October–November experiment observations. It is not `TRANSFERRED_EXACT`, a frozen run ledger or source-code activation proof. Historical source Git revision remains `UNKNOWN`; the existing private-population and IRG-X001 exceptions are preserved. No additional historical artifact was transferred by this synthesis.
