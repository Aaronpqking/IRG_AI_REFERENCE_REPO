# Experiment register — repository-local evidence map

This register is not a substitute for original run ledgers. Every row states whether supporting evidence is repository-local and whether the result is qualified.

| Experiment | Date | Population / scope | Changed variable | Result | Status | Promoted? | Repository-local evidence |
|---|---|---|---|---|---|---|---|
| V1.5 frozen configuration | 2026-07-31 | 132 PDFs / 4,173 chunks | release freeze | configuration documented; no new final quality estimate | PROVEN_WITH_GAP | historical only | [V1.5 freeze](../timeline/evidence/V1_5_FROZEN_CONFIGURATION_AND_ARTIFACTS_20260731.md) |
| V2 master population freeze | 2026-09-02 | 244 scenarios / 245 expectation units | population + gates | frozen design; qualification not executed | BLOCKED | no | [historical report](historical/V2_MASTER_REGRESSION_REPORT_v1.md), [manifest](frozen/V2_MASTER_REGRESSION_MANIFEST_v1.json) |
| V1.9.33 observe-only paired ablation | 2026-09-24 | 110 planned; 20 completed before parity stop | control-layer comparison | retrieval parity failed at case 21; no qualifying aggregate | INVALID | no | [local report](../reports/reference/ablations/V1_9_33_INVALID_ABLATION_REPORT.md) |
| V1.9.35 single-retrieval forked paths | 2026-09-24 | 110 development cases | response-decision path after identical retrieval | A 82/110 correct; B 10/110; B prevented 20 unsupported cases but suppressed 82 correct | PROVEN_WITH_GAP | no | [local report](../reports/reference/ablations/V1_9_35_SINGLE_RETRIEVAL_FORKED_PATH_ABLATION_REPORT.md) |
| October reconstruction anchor | 2026-10-27 | 26 retained; 21 answerable | reconstructed October runtime | 26/26 downstream parity; exact-gold Recall@10 21/21; sufficient context 19/21; wrong-product/revision 0 | HISTORY_REPORTED_UNVERIFIED | no | original run package pending |
| P1/P2 corpus reconstruction | 2026-10-27 | P1 80 logical docs; P2 437 logical docs / 107 physical sources | larger product-scoped corpus | P1 48,447 views / 46,462 vectors; P2 216,921 views / 163,268 vectors; later history also reports exact-gold Recall@10 100% on bounded reconstruction populations | HISTORY_REPORTED_UNVERIFIED | no | original run package pending |
| Standard vs contextualized full-view P2 | 2026-10-27 onward | 17 valid unseen; 20 planned, 19 executed | +10,868 contextualized views | 3/17 context both; 5/17 evidence@10 both; 0 wins / 0 losses; 0 critical wrong-product | HISTORY_REPORTED_UNVERIFIED / NO_GAIN_REPORTED | no | [ablation synthesis](../reports/reference/ablations/STANDARD_VS_FULL_VIEW_P2_ABLATION.md); original ledger pending |
| Expansion scale trial | 2026-10-30 | 40 selected gold + 10 narrative | expanded corpus/current representation | 16/40 vs 13/40; narrative 3/10 vs 0/10 | HISTORY_REPORTED_UNVERIFIED | no | [scale synthesis](../reports/reference/scale/EXPANDED_CORPUS_SCALE_TEST.md); original ledger pending |
| Alias/canonical-source audit | 2026-11-05 | 19 alias failures; canonical/physical inventory | dedup/alias diagnosis | 19/19 failures reproduced; 1,502 canonical docs vs 935 physical revisions; 1,110 duplicate refs across 298 products | HISTORY_REPORTED_UNVERIFIED | no | original audit package pending |
| C1 inactive safety candidate | 2026-11-05 | 4,943 relationships; reviewed positives/revocations | remove unsupported post/cart grants | 52 grants removed; 40/40 reviewed positives and 9/9 revocations preserved; 4,903 unrelated unchanged; no production change | HISTORY_REPORTED_UNVERIFIED / BOUNDED_PASS | no | original candidate package pending |
| Metadata-only document narrowing — intermediate | 2026-11-16 | selected manufacturers/brands | metadata authority before retrieval | strong document-count reduction for several brands; packaging failures remained; one manufacturer blocked; P4 retrieval-level reduction small | HISTORY_REPORTED_UNVERIFIED | no | superseded by 2026-11-18 R2 ledger where inconsistent |
| R2 P0–P7 authoritative ledger | 2026-11-18 | P0–P7; 150-case evaluation target | staged authority/retrieval/sufficiency evaluation | P0 183/177 deferred; P1 6/150 and 0 accepted gates; P2 49/49 literals + 19/19 controls with ≥98% identity unproven; P3 mean document reduction 90.85%; P4 lexical reduction 0%, dense 0–6.22%; P5/P6 sufficiency 0/5; P7 parity 35/35, cold 141.935s, repeat 28.175s, no SLO/p95 | HISTORY_REPORTED_UNVERIFIED / ACTIVE_FINDING | no | latest project-history authority; original ledger pending |
| Nov 19 G2/R1/R0 historical comparison | 2026-11-19 | active R2 campaign candidate 60; frozen-G2 993/993 artifact entries | compare historical ordering/authority behavior without mutation | G2 35/35 bounded owner-conditioned occurrence retrieval; Fire Magic favored neural top-three evidence; Bromic/Twin Eagles showed upstream identifier/metadata loss unrecoverable by reranking | HISTORY_REPORTED_UNVERIFIED / READ_ONLY_COMPARISON | no | original comparison artifact and campaign manifest pending local transfer |
| Codebase/architecture audit | 2026-10 onward | bound source per historical audit | serving closure / boundaries | reported serving closure 130→105 modules, prohibited serving-reachable 23→0, architecture boundary conforming, 36 scoped tests passing; observability gaps remained | HISTORY_REPORTED_UNVERIFIED | no | bound source/audit package pending |

Statuses: `PROVEN`, `PROVEN_WITH_GAP`, `PARTIAL_GAIN`, `NO_GAIN`, `REGRESSION`, `INVALID`, `BLOCKED`, `SUPERSEDED`, `HISTORY_REPORTED_UNVERIFIED`.

## Current interpretation

The latest R2 result materially sharpens the earlier October conclusion:

- document competition can be reduced substantially without equivalent lexical/dense evidence-competition reduction;
- identity controls can pass bounded literal/control checks while the target identity gate remains unproven;
- retrieval/parity success does not establish sufficient context;
- parity does not establish latency SLOs;
- added representations or metadata stages require downstream evidence/context improvement, not merely candidate-count or rank movement.

## Promotion rule

A history-only row cannot become clean-build promotion evidence until its original source/run package is repository-local or otherwise bound by a reproducible immutable identifier available to the implementing agent. No history-only result may silently become a clean-build acceptance gate.
