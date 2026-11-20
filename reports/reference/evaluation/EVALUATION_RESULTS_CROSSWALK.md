# Results crosswalk — non-comparable stages

| Evidence | Population | Metric/stage | Value | Caveat |
|---|---|---|---|---|
| 2026-07-31 frozen configuration document | 29 older mutable golden results | historic chat pass | 17/29 | expressly NOT V1.5 accuracy |
| 2026-09-02 V2 master population | 244 scenarios / 245 expectation units | qualification | NOT_EXECUTED | population freeze ≠ scored run |
| Oct P1/P2 reconstructed | bounded population | exact-gold Recall@10 | reported 100% | historical; different stage |
| Oct scale trial | 40 exact gold; 10 narrative | selected test | 16/40; 3/10 | comparison arm 13/40; 0/10 |
| P2 full vs standard | 17 valid unseen | sufficient evidence @10 | 5/17 both | zero paired wins |
| P2 full vs standard | 17 valid unseen | sufficient context | 3/17 both | original run ledger pending |
| R2 P3 | scopes 83 / 38 / 561 / 67 | mean document reduction | 90.85% | latest history-reported state; local original ledger pending |
| R2 P4 | same staged program | lexical competition reduction | 0% | document narrowing did not imply lexical evidence narrowing |
| R2 P4 | same staged program | dense competition reduction | 0–6.22% | local original ledger pending |
| R2 P5/P6 | 5 reported cases | sufficient context | 0/5 | latest history-reported state |
| R2 P7 | 35 valid | execution parity | 35/35 | cold 141.935 s; repeat 28.175 s; no SLO/p95 |

## Repository-local sources

- V1.5 configuration: [../../../timeline/evidence/V1_5_FROZEN_CONFIGURATION_AND_ARTIFACTS_20260731.md](../../../timeline/evidence/V1_5_FROZEN_CONFIGURATION_AND_ARTIFACTS_20260731.md)
- V2 master population/report: [../../../evaluation/historical/V2_MASTER_REGRESSION_REPORT_v1.md](../../../evaluation/historical/V2_MASTER_REGRESSION_REPORT_v1.md) and [../../../evaluation/frozen/V2_MASTER_REGRESSION_MANIFEST_v1.json](../../../evaluation/frozen/V2_MASTER_REGRESSION_MANIFEST_v1.json)
- Late October/November results: [../../../CURRENT_REFERENCE_STATE.md](../../../CURRENT_REFERENCE_STATE.md), [../../../evaluation/EXPERIMENT_REGISTER.md](../../../evaluation/EXPERIMENT_REGISTER.md), [../ablations/STANDARD_VS_FULL_VIEW_P2_ABLATION.md](../ablations/STANDARD_VS_FULL_VIEW_P2_ABLATION.md), and [../scale/EXPANDED_CORPUS_SCALE_TEST.md](../scale/EXPANDED_CORPUS_SCALE_TEST.md)

Metrics from these rows cannot be pooled into one accuracy estimate. Populations, pipeline stages, and validation status differ.
