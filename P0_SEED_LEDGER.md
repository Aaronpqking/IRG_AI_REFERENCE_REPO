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
3. **Source/test binding:** old implementation source and test snapshots are not available through the two installed GitHub repositories (reference repo and currently empty technical-data-platform repo). Obtain authorized historical source checkout or the bound tests without pushing sensitive internals into public reference.
4. **Late P1/P2 and scale experiments:** original full run ledgers, hashes and experiment joins still absent from reference corpus; history-derived results remain provisional.
5. **Programmatic validator execution:** script is added; independent execution of the GitHub checkout and strict-mode gate still needed. Readback and pure-data binding checks are separate from executing that Python script.
6. **P0 source manifest completeness:** a smaller subset of priority artifact transfers is complete; the full original seed manifest requires an item-by-item reconciliation.

## Guardrails
Repository is **public**. Do not upload unredacted conversation rows, private read-model traces, credentials, or entire source trees. Original frozen evidence, historical runtime, policy-only and synthesized conclusions retain separate states. The evaluator may not claim `QUALIFICATION_PASS` from the population freeze.

## Status
**P0_REFERENCE_SEED_EXPANDED / NOT FULLY QUALIFIED.** No production/runtime database, model, corpus, Qdrant, deployment or release state changed.
