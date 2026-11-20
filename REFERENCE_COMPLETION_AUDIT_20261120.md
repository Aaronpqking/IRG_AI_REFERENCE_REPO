# IRG AI reference completion audit — 2026-11-20

**Repository:** `Aaronpqking/IRG_AI_REFERENCE_REPO`  
**Audited branch:** `audit/p0-completion-reconciliation-20261120`  
**Audited source HEAD before this report:** `dcfe8ade1622022f7ab931656ab48db26cf60bf8`  
**Authoritative final merge HEAD:** GitHub `main` after merging this report; read and cite the merge SHA in final completion response. A tracked report cannot encode its own future Git commit SHA without changing that SHA.  
**Audit run:** GitHub Actions #`44756722813` (success).  
**Verdict:** **`NOT_COMPLETE`** — strict validation is blocked by three material frozen/private authority exceptions and October–November run packages remain unavailable.

## 1. Measured repository census

The GitHub Actions read-only command `python scripts/audit_reference_completion.py` reported the following **before adding this report**:

| Metric | Measured |
|---|---:|
| Substantive nonempty repository files | **191** |
| Zero-byte substantive files | **0** |
| Remaining `.gitkeep` placeholders | **0** |
| Original historical implementation modules transferred | **34** |
| Original behavior-test modules transferred | **13** |
| Total exact original source/test transfers | **47** |
| Total exact original source/test bytes | **894,329** |
| Required evidence areas with substantive files | **11 / 11** |
| Source/local SHA-256 mismatch failures | **0** |
| Reference integrity unittest results | **27 passed, 0 failed** |

Adding this report increments the expected substantive file count by one; final CI must reread the actual HEAD to confirm.

Required-area census (source files include manifest JSON where present):

- `source_reference/identity/`: 5
- `source_reference/retrieval/`: 7
- `source_reference/context/`: 8
- `source_reference/contracts/`: 8
- `source_reference/structural/`: 10
- `source_snapshot/`: 1
- `research/structural/`: 2
- `reports/reference/v1/`: 2
- `reports/reference/v1_5/`: 2
- `reports/reference/corpus/`: 2
- `reports/reference/structural/`: 2

All five required original implementation families now contain substantive source evidence. Exact source bytes, historical original paths, local file paths, source/local SHA-256 values, byte lengths, redaction status and explicit unknown original Git revision are recorded in family-local manifests. The historical source files are **not a unified verified checkout**.

## 2. Original source and tests available to Codex

| Family | Exact historical modules | Local evidence |
|---|---:|---|
| Identity | 5 | `source_reference/identity/` |
| Retrieval | 6 | `source_reference/retrieval/TRANSFER_MANIFEST.json` |
| Context and grounding | 7 | `source_reference/context/TRANSFER_MANIFEST.json` |
| Ports/contracts/composition | 7 | `source_reference/contracts/TRANSFER_MANIFEST.json` |
| Structural milestones | 9 | `source_reference/structural/TRANSFER_MANIFEST.json` |
| Historical identity tests | 3 | `tests_reference/historical/identity/` |
| Historical behavior tests | 10 | `tests_reference/historical/behavior/TRANSFER_MANIFEST.json` |

No originals were rewritten as cleaner synthetic implementations. Selected structural milestones belong to different historical research/development arms and cannot be treated as one concurrent production pipeline. The original historical tests were **archived, parsed and hash-checked**, not executed against a coherent original runtime environment.

## 3. Snapshot and milestone-report authority

The source-snapshot gate uses the explicit documented-unavailability alternative in `source_snapshot/SNAPSHOT_MANIFEST.md`, because the available historical archive does not establish one frozen Git tree and no complete public safe checkout can be certified. No synthetic snapshot was created.

Five historical milestone/report families have substantive self-contained curated local summaries; their `PROVENANCE.json` records classify them **`CURATED_NOT_EXACT_TRANSFER`**, not identical original historical reports. Original immutable October/November run packages remain unavailable, recorded in `reports/reference/audits/LATE_RUN_PROVENANCE_RECONCILIATION_20261120.md`. Historical findings retain `HISTORY_REPORTED_UNVERIFIED` where required.

## 4. Strict validator — actually executed

| Gate | Result |
|---|---|
| `python scripts/validate_reference_seed.py` | `PASS_WITH_BLOCKERS` |
| `python -m unittest discover -s tests_reference -p 'test_*.py' -v` | `PASS: 27 tests` |
| `python scripts/validate_reference_seed.py --strict` | **FAIL, exit code 1** |
| Integrity errors | **0** |
| Completion blockers | **3** |
| `.gitkeep` placeholder blockers | **0** |
| Required-area-empty blockers | **0** |
| GitHub CI, audited branch | **PASS** |

The three exact validator blockers are:
1. `PRIVATE_SOURCE_NOT_IN_REPO`: `V2_MASTER_REGRESSION_POPULATION_v1.jsonl`. Frozen user-conversation-containing population deliberately withheld from public Git.
2. `PRIVATE_SOURCE_NOT_IN_REPO`: `V2_HISTORICAL_QUESTION_TRIAGE_v1.jsonl`. Private historical-conversation triage deliberately withheld.
3. `MASTER_MANIFEST_REVISION_CONFLICT` (`IRG-X001`): evaluator-bound master-manifest SHA-256 `9ddf9eaf993a62182ce1c52f550002deb2d3584f12e9a56167fba1fe78df0f3c` versus available frozen master-manifest SHA-256 `fa6b6291079fa0d2c2823a71824e492a80fbc21a0aad5345c91f60d3e5e6fa3e`.

No frozen SHA, qualification status, question labels, or evaluator was changed. The validator was not weakened to produce a pass.

## 5. Additional remaining authority limitations

- Original source Git commit/tree parity is **UNKNOWN**; the historical archive contains authentic source files from potentially mixed revisions.
- Historical behavior tests were **not executed** with their original imports/dependencies and bound runtime; CI validates their preserved source identity and current reference integrity.
- October P1/P2, the 17-case unseen ablation, 40-case scale comparison, and November 18–19 R2/G2 results still lack local immutable experiment run packages. They cannot be promoted from `HISTORY_REPORTED_UNVERIFIED`.
- Privacy prevents public publication of the two frozen population inputs. A separately authorized hash-matched replay environment is required for private qualification.
- `IRG-X001` remains `REVISION_CHAIN_INCOMPLETE` until direct evaluator-bound bytes or immutable historical Git objects establish the expected SHA-256.

## 6. Independent operational usability

A new implementation agent can inspect the selected original source/test mechanisms, the original paths/digests, architecture/ADR history, curated reports, negative findings and precise pending authority boundaries **without needing access to Google Drive, a previous conversation, or a private host path**. It cannot independently reproduce the missing frozen populations or late run experiments from this public reference alone, and must not claim that it can.

## 7. Final verdict and next actions

**`NOT_COMPLETE`**, because the repository's own **strict validator fails** and immutable empirical/source revision closure remains unproven. This is a measurable improvement from the earlier placeholder-only source families: all required directory areas contain local evidence, all 47 original transfers are byte-hash verified, and all 27 reference integrity tests pass.

Next closure actions: (1) authorize and independently reproduce protected frozen populations outside public Git; (2) recover the evaluator-bound `9ddf...` master-manifest revision or preserve its explicit blocker; (3) recover a coherent original Git tree and missing immutable late-run artifacts, rerun original historical tests with dependency closure, then rerun `--strict`. Do not override blockers merely for a green completion label.

**Production/corpus/DB/Qdrant/provider/deployment changes:** none.
