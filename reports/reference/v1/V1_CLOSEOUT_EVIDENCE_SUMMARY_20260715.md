# V1 closeout — curated historical evidence

**Classification:** `LOCAL_CURATED_REPORT_SUMMARY / ORIGINAL_REPORT_NOT_TRANSFERRED / REVIEW_PENDING`  
**Original:** `V1_closeout_audit_report.md`, dated **2026-07-15**. This is a scoped summary of the original report read in the historical archive, not a reproduction of its entire 31 KB text, source code, or executable tests.

## Original determination
The historical audit recommended **option B: close V1 after a short closeout/test/report task**. It considered the approved-PDF/manual RAG system materially implemented, with index rebuild paths, retrieval-only evaluation, grounded source references, conversation logging, feedback persistence and a thin HTTP frontend connection.

**Do not convert that recommendation into an already approved release.** The audit identified unresolved corpus provenance and evaluation limitations.

## Corpus discrepancy at that point
- Physical source tree: **153 PDFs**.
- Manifest: **132 documents**.
- Physical PDFs not represented in manifest: **71**.
- Manifest paths missing in the observed source tree: **50**.
- `data/` and generated report JSON/log outputs were ignored from version control; the physical corpus/manifest state could not be assumed from tracked files.

These numbers refer to the **July 15 observed local state**, not the later August corpus state. They demonstrate why byte/manifest authority requires explicit run binding.

## Architectural boundary
Historical V1 was PDF-first. Product database/table retrieval was expressly deferred to **V1.5 / MS6**; database functions present in V1 were for conversations and feedback. The report argued that product-data facts should use structured direct queries and row/cell provenance rather than vectorized product-description replicas.

## Tests and limits
The original report includes named offline source/API/service tests, with one subset of 40 passing and another of 44 passing; those are historical assertions from the report, **not independent runs executed for this summary**. The report did not run live evaluation, ingestion, Qdrant rebuild, corpus mutation or DB product retrieval in that closeout review.

## Clean-build implication
Preserve the distinction among a working PDF baseline, corpus authority, retrieval-only evaluation, and production approval. Do not infer qualified answer accuracy from module existence.

## Source/protection statement
The complete original internal closeout file remains in the historical archive. This local file contains the substantive findings needed for reference navigation but **does not satisfy an exact-original-transfer requirement**. No provider or repository-runtime access is required to read this summary. Publication remains subject to review.
