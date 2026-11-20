# Late-run provenance and immutable-binding reconciliation — 2026-11-20

**Audit classification:** `LOCAL_REPORT_VERIFIED` (this audit itself)  
**Historical experiments:** `HISTORY_REPORTED_UNVERIFIED`  
**Scope:** public reference repository and authorized historical archive, *not* live R2 provider/DB/vector execution.

## Archive search and negative finding

Targeted searches of the accessible historical archive did **not** return original immutable late-run packages for the following query names/identifiers:

- `R2-CAMPAIGN-20261111-HANDOFF-001`;
- `20261119`, `20261118`;
- `P2-IND-05`, `G2-R1-R0`.

Certain broader archival queries returned access errors; this negative result does **not** prove the underlying original run artifacts never existed. It means these artifacts are **not available as repository-local immutable evidence in this completion pass**.

Historical July–September selected source and reports are present in the reference repository, but they are not interchangeable with October–November experiment execution ledgers.

## Existing historical findings retained but not promoted

| Historical observation | Reported denominator/result | Current authority |
|---|---|---|
| October bounded reconstruction | 26/26 downstream parity; 21/21 answerable exact-gold Recall@10; context 19/21 | `HISTORY_REPORTED_UNVERIFIED` |
| October P2 standard/full-view paired unseen study | 17 valid unseen; context 3/17 both; 0 full-view wins | `HISTORY_REPORTED_UNVERIFIED` |
| Expanded-scale comparison | 16/40 current vs 13/40 October; narrative 3/10 current vs 0/10 October | `HISTORY_REPORTED_UNVERIFIED` |
| November 18 R2 campaign | P1 6/150, 0 accepted gates; P5/P6 0/5; P7 parity 35/35, latency SLO not established | `HISTORY_REPORTED_UNVERIFIED` |
| November 19 G2/R1/R0 read-only comparison | 993/993 frozen G2 artifact entries; G2 bounded owner-conditioned occurrence 35/35 | `HISTORY_REPORTED_UNVERIFIED` |

These denominators and populations **must not be combined**. Direct original source snippets, current repository navigation, or hashes of other historical revisions are insufficient to upgrade them.

## Required closure
Recover the original immutable run folders with source/config/model/evaluator/prompt bindings, frozen case IDs, selected evidence/context payloads, population hashes, ledger scoring, validity exclusions, run timestamps, and complete metric denominators. Keep private gold and provider payloads in a separately authorized location, with an independently usable public metadata/claim record.

## Evaluator manifest exception — IRG-X001
The evaluator's frozen master-manifest authority requests SHA-256
`9ddf9eaf993a62182ce1c52f550002deb2d3584f12e9a56167fba1fe78df0f3c`.

The separately available original historical master manifest is SHA-256
`fa6b6291079fa0d2c2823a71824e492a80fbc21a0aad5345c91f60d3e5e6fa3e`.

No exact evaluator-bound `9ddf...` bytes were recovered. The existing frozen files remain unedited. **Status: `BLOCKED / IRG-X001_REVISION_CHAIN_INCOMPLETE`.**

## Publication and qualification boundary
Two original frozen population/triage JSONL files contain private historical conversation wording and are intentionally withheld from this public repository. Their cryptographic identities remain in `evaluation/FROZEN_TRANSFER_LEDGER.json`. This is a safety exception, not independent public reproducibility.

The historical test files published under `tests_reference/historical/` have byte-verified identity and AST validity, but have **not** been run against a coherent historical revision; passing reference integrity CI cannot qualify experiments or substitute for their original execution.

**Conclusion:** available local original source coverage advanced substantially. Late empirical reproducibility and evaluator closure remain blocked. Retain `HISTORY_REPORTED_UNVERIFIED` and `BLOCKED` flags; do not promote clean-build result claims.
