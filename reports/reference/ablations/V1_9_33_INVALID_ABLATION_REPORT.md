# V1.9.33 paired observe-only ablation — invalid run

- Status: `INVALID`
- Classification: `V1_9_33_ABLATION_INVALID`
- Run: `V1.9.33-ABLATION-20260924T142453Z`
- Execution HEAD: `3c82a29c2a3b5765145e974e6ae5021982828619`

The one-shot run loaded the frozen 110-case V1.9.31 population exactly once and completed 20 authoritative generator calls. Before case 21 could invoke the generator, the recomputed retrieval record failed exact parity with the immutable V1.9.32 record:

`V1_9_33_RETRIEVAL_PARITY_FAILURE:V1931-RQ-021`

The harness hard-stopped and marked the run invalid. No resume, tuning, scorer change, prompt change, retrieval change, or rerun is authorized. No 110-case aggregate or architectural conclusion may be drawn from this run.

## Diagnostic-only partial evidence

The 20 completed cases produced 20/20 ablation-authoritative correct scores while their unchanged passive V1.9.32-style control envelopes produced 0/20 correct scores. This is incomplete, invalid-run evidence only and is not an experiment result. The 20 calls consumed 45,260 input tokens and 1,751 output tokens at a recorded cost of $0.27883.

## Integrity

- Frozen authority loader calls: 1
- Exposed case IDs: 110
- Completed cases/provider calls: 20/20
- Provider retries: 0
- Qdrant points before/after: 28,139/28,139
- Qdrant mutation operations: 0
- Corpus SHA-256 before/after: `c79f08e3e26277d2e97bdcdd136a4112a3d9f790f87eaaf1af89c6260b002890`
- Code/config/prompt/retrieval/scorer changes after access: none
- Post-access tuning: none
- Reruns: 0
- Deployment/promotion: no/no

## Next action

Treat the exact-parity failure on `V1931-RQ-021` as the blocker. Any diagnostic replay or redesigned experiment requires new authority; this invalid population/run must not be resumed or rerun.
