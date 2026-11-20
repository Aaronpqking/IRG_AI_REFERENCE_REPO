# Historical ablation addendum — 2026-09-24

Two original Drive reports are retained at:
- [V1.9.33 invalid](../reports/reference/ablations/V1_9_33_INVALID_ABLATION_REPORT.md)
- [V1.9.35 paired](../reports/reference/ablations/V1_9_35_SINGLE_RETRIEVAL_FORKED_PATH_ABLATION_REPORT.md)

## V1.9.33 — INVALID (not evidence of gain)
Run `V1.9.33-ABLATION-20260924T142453Z` stopped after 20 calls because the frozen retrieval record for `V1931-RQ-021` failed exact parity. The report explicitly prohibits interpreting 20/20 as a 110-case effect, rerunning, or silently repairing the run. Status `INVALID`. Retained as run-integrity evidence only.

## V1.9.35 — 110-case paired development replay, not release qualification
Run `V1.9.35-ABLATION-20260924T163703Z`. One retrieval per case and branch-input hash parity were reported. Path A had 82/110 correct (74.55%), Path B 10/110 correct (9.09%). On the suppression control comparison, the report recorded:
- 82 correct answers suppressed (82/82 available correct answers; 100% false-positive suppression recall).
- 20 hallucinated/unsupported answer cases prevented (20/20 reported).
- Only 28/110 suppressions were correct, a **25.45% suppression precision**.
- 10/10 insufficient-evidence cases handled correctly by Path B; 0/10 by Path A.
- The two paths have materially different response policies and are not independent retrievers; this is a decision/realization control comparison.

The report also records exact gold@10 100/100 but semantic answer-set reachability@10 0/100 under the historical metric definitions. **Do not infer that 100% exact-gold guarantees answerability.** Reconcile those metric definitions with their original scorers before comparing downstream metrics across systems.

## Design implication
A blanket fail-closed controller can reduce unsafe factual assertions at the cost of suppressing most valid answers. Measure the dual objective: unsupported generation and correct-answer suppression, stratified by sufficient/insufficient/ambiguous evidence. This does **not** justify turning off safety or adopting Path A; both had critical response failures. The observed result is historical **NO_PROMOTION**, not a clean-build acceptance.

## Provenance
- Original V1.9.35 Drive report: https://docs.google.com/document/d/1sOhTqRaVFFjVAz_GSxRjyPVh62elts8W/edit
- Original V1.9.33 Drive report: https://docs.google.com/document/d/1tyXelq1JetJeRtAKxwZ4XxC_W6MLqG5y/edit

Case-level 88MB paired records, private generator inputs and other generated artifacts are not copied to the public repository. Full run hash chain has not been independently replayed.
