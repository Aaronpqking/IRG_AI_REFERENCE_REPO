# P0 reference seed verification ledger — 2026-11-20

## Completed (measured)
- Reference architecture, provenance policy, navigation and intellectual-state synthesis remain on `main` from earlier merged PRs.
- **Eight** frozen contract/manifest source files copied unchanged from Google Drive; exact source-byte equality checked by independently matching the local Git blob SHA-1 to GitHub's blob SHA-1.
- **Two** further evaluation historical reports transferred unchanged with the same blob comparison.
- Master population: **244 JSONL scenarios**, original SHA-256 matched the regression manifest; historical triage: **615 JSONL decisions**, original SHA-256 matched.
- Both raw JSONL corpora are deliberately **withheld** from the public repository because the question-level contents derive from historical live conversation material.
- [FROZEN_TRANSFER_LEDGER](evaluation/FROZEN_TRANSFER_LEDGER.json) records sources, byte counts, original SHA-256 hashes and visibility status. [INTEGRITY_FINDINGS](evaluation/INTEGRITY_FINDINGS_20261120.md) records binding checks and exception IRG-X001.
- Added read-only [offline validator](scripts/validate_reference_seed.py) for artifact hashes, JSON structure, population counts and cross-manifest links.

## Outstanding P0 blocks
1. **IRG-X001:** evaluator manifest binds master regression manifest SHA-256 `9ddf9eaf...`; available original is `fa6b6291...`. Locate/verify the bound revision before evaluating or promoting.
2. **Private frozen population reproduction:** records are hash-verified in authorized Drive but withheld from this public repository. Qualification must access them privately using hashes and permissions.
3. **Source/test binding:** a historical `irg_ai-main` source and test tree **was located in Google Drive**; 11 selected files totaling 421,897 bytes were independently SHA-256 hashed and parsed. It is not a Git-commit-bound, internally consistent checkout, and it is not verified as the October 2026 runtime. See [source bindings](source_reference/SOURCE_BINDINGS_20261120.json) and [source review](reports/reference/audits/GOOGLE_DRIVE_SOURCE_BINDING_20261120.md).
4. **Late P1/P2 and scale experiments:** original full run ledgers, hashes and experiment joins still absent from reference corpus; history-derived results remain provisional.
5. **Programmatic validator execution:** offline GitHub Actions previously passed; strict-mode must still intentionally reject qualification blockers and the newly added source metadata checks must pass CI.
6. **P0 source manifest completeness:** 30 destination groups are inventoried in [P0_COVERAGE_MATRIX](P0_COVERAGE_MATRIX.md), with 15 implemented and 15 partial; selected source availability has improved, but empirical proof remains partial.

## Guardrails
Repository is **public**. Do not upload unredacted conversation rows, private read-model traces, credentials, or entire source trees. Original frozen evidence, historical runtime, policy-only and synthesized conclusions retain separate states. The evaluator may not claim `QUALIFICATION_PASS` from the population freeze.

## Status
**P0_REFERENCE_SEED_EXPANDED / NOT FULLY QUALIFIED.** No production/runtime database, model, corpus, Qdrant, deployment or release state changed.

## Verified CI execution
GitHub Actions `Reference evidence validation` run **44689311401** passed on this review branch. It executed the offline validator, unit-test discovery, and a check that P0 retains explicit blockers. This is a passing *seed integrity* check, not a passing qualification gate. Drive revision history was also checked for IRG-X001; only the present revision is exposed for each manifest, so the discrepancy remains open.

## 2026-11-20 source discovery and integrity lineage
- Google Drive `irg_ai-main` contains the original `src/`, `tests/` and `src/v2_evaluator/` directories. Selected source evidence is available; GitHub source repo availability and Drive source availability must not be conflated.
- 11 source/test files: source bytes read, hashes recorded and AST-parsed; 130 historical `test_*` function definitions observed but **none executed**.
- [IRG-X001 lineage analysis](evaluation/IRG_X001_MANIFEST_LINEAGE_20261120.md) identifies three distinct master-manifest digests (pre-scorer, evaluator-bound, accessible Drive) with the evaluator-bound bytes still missing.
- Source code remains outside the public reference repository. Source metadata alone never qualifies a release or a model response.

## Evaluator implementation approval recovered
- Original owner approval `V2_EVALUATOR_APPROVAL_v1.json` dated 2026-09-02 binds the exact existing evaluator manifest (SHA-256 `2085173f...`) and the derived-population SHA-256 `3ea5a464...`; **both matched**.
- All **10/10** evaluator source/test files named in the manifest matched their original SHA-256 hashes directly from Drive. Four additional fixture/dependency/test-evidence/derived-population artifacts matched their bound hashes.
- Historical evaluator status is now `AUTHORITATIVE_FROZEN` following owner approval; **qualification remains `NOT_EXECUTED`** and IRG-X001 remains open. Original historical `PENDING_OWNER_APPROVAL` snapshots are preserved unchanged.
- [Evaluator provenance ledger](evaluation/EVALUATOR_PROVENANCE_LEDGER.json) and [approval reconciliation](evaluation/EVALUATOR_APPROVAL_RECONCILIATION_20261120.md) supersede earlier source-unavailable statements for this evaluator scope.
