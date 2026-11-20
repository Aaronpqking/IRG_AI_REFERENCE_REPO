# V1.5 final closeout — curated historical evidence

**Classification:** `LOCAL_CURATED_REPORT_SUMMARY / ORIGINAL_REPORT_NOT_TRANSFERRED / REVIEW_PENDING`  
**Original:** `V1_5_FINAL_CLOSEOUT_20260731.md`, dated **2026-07-31**. Historical engineering release baseline; not current production state.

## Historical release disposition
- Release decision: **`CLOSED - PASS_WITH_WATCH`**, effective when reviewed release commit and annotated tag were created (the report itself is conditional on those actions).
- Product readiness: **`INTERNAL PILOT CANDIDATE`**.
- Production readiness: **`NOT CLAIMED`**.

## Implemented shape reported
The V1.5 baseline combined structured product-DB evidence with unconditional hybrid PDF retrieval; independent evidence authority, document/configuration applicability, canonical DB/PDF evidence identity, bounded context, source projection, conversation persistence and shared API/CLI/evaluation composition. Some policies operated in `observe` mode; do not convert them into enforcement claims.

## Historical verification
| Validation scope | Reported result |
|---|---|
| Maintained Python suite | **792 passed**, 6 live-gated skips |
| Python compilation | PASS |
| Frontend lint/build | PASS |
| Frontend Markdown renderer safety | PASS |
| Offline conversation CLI with PDF source and persistence | PASS |
| Ingestion dry run | PASS (`dry_run_valid`) |
| External services in freeze | None |
| DB/schema or corpus/vector mutation | None |

A pre/post controlled retrieval accuracy or performance comparison **was not run** for this freeze.

## Distinguishing runtime configuration
Product discovery, grounding validation and PDF configuration applicability were reported as `observe`; hybrid PDF retrieval was unconditional; shared context ceiling **45,000 characters**; local vector collection **`AOG-TE`** with named vector `dense`. Product descriptions were not bounded by that field-specific statement. No corpus rebuild or metadata backfill was part of this closeout.

## Limits
Multi-subject continuity, recent-turn rehydration, larger governed corpus, expanded evaluation, explicit relationship authority and production security/reliability gates were deferred.

## Clean-build implication
Treat V1.5 as a historical integrated architecture, not proof of broad generalization or release qualification. Original implementation and test bytes must still be locally curated and independently bound.

The complete historical report was reviewed from the archive but not transferred here; this is **curated synthesis**, not `TRANSFERRED_EXACT`.
