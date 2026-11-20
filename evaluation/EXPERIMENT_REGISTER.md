# Experiment register — repository-local evidence map

This register is not a substitute for original run ledgers. Every row states whether supporting evidence is local and whether the result is qualified.

| Experiment | Date | Population | Changed variable | Result | Status | Promoted? | Repository-local evidence |
|---|---|---|---|---|---|---|---|
| V1.5 frozen configuration | 2026-07-31 | 132 PDFs / 4,173 chunks | release freeze | configuration documented; no new final quality estimate | PROVEN_WITH_GAP | historical only | [V1.5 freeze](../timeline/evidence/V1_5_FROZEN_CONFIGURATION_AND_ARTIFACTS_20260731.md) |
| V2 master population freeze | 2026-09-02 | 244 scenarios / 245 expectation units | population + gates | frozen design; qualification not executed | BLOCKED | no | [historical report](historical/V2_MASTER_REGRESSION_REPORT_v1.md), [manifest](frozen/V2_MASTER_REGRESSION_MANIFEST_v1.json) |
| V1.9.33 observe-only paired ablation | 2026-09-24 | 110 planned; 20 completed before parity stop | control-layer comparison | retrieval parity failed at case 21; no qualifying aggregate | INVALID | no | [local report](../reports/reference/ablations/V1_9_33_INVALID_ABLATION_REPORT.md) |
| V1.9.35 single-retrieval forked paths | 2026-09-24 | 110 development cases | response-decision path after identical retrieval | A 82/110 correct; B 10/110; B prevented 20 unsupported cases but suppressed 82 correct | PROVEN_WITH_GAP | no | [local report](../reports/reference/ablations/V1_9_35_SINGLE_RETRIEVAL_FORKED_PATH_ABLATION_REPORT.md) |
| P1/P2 reconstruction | 2026-10 | bounded P1/P2 | structural recovery | history reports exact-gold Recall@10 100%; no answerability inference | HISTORY_REPORTED_UNVERIFIED | no | original run package not yet local |
| Expansion scale trial | 2026-10-30 | 40 selected gold + 10 narrative | expanded corpus | 16/40 vs 13/40; narrative 3/10 vs 0/10 | HISTORY_REPORTED_UNVERIFIED | no | [scale synthesis](../reports/reference/scale/EXPANDED_CORPUS_SCALE_TEST.md); original ledger pending |
| Standard vs contextualized full-view P2 | 2026-10-27 onward | 17 valid unseen; 20 planned, 19 executed | +10,868 contextualized views | 3/17 context both; 5/17 evidence@10 both; 0 wins / 0 losses | HISTORY_REPORTED_UNVERIFIED / NO_GAIN_REPORTED | no | [ablation synthesis](../reports/reference/ablations/STANDARD_VS_FULL_VIEW_P2_ABLATION.md); original ledger pending |
| Codebase/architecture audit | 2026-10 | bound source per historical audit | serving closure / boundaries | reported prohibited modules 23→0 and 36 scoped tests passing | HISTORY_REPORTED_UNVERIFIED | no | bound source/audit package not yet local |

Statuses: PROVEN, PROVEN_WITH_GAP, PARTIAL_GAIN, NO_GAIN, REGRESSION, INVALID, BLOCKED, SUPERSEDED, HISTORY_REPORTED_UNVERIFIED.

## Rule
A history-only row cannot become clean-build promotion evidence until its original source/run package is repository-local or otherwise bound by a reproducible immutable identifier and accessible to the implementing agent.
