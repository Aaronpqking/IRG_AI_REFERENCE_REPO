# Docling structural shadow retrieval — September holdout

**Classification:** `LOCAL_CURATED_REPORT_SUMMARY / ORIGINAL_REPORT_NOT_TRANSFERRED / REVIEW_PENDING`  
**Original:** `DOCLING_STRUCTURAL_SHADOW_CORPUS.md`, updated through **2026-09-09**. It describes a quarantined, non-production retrieval program.

## Architecture
The project used Docling's structural extractor with provenance-bearing pages and units, table header paths, row keys, captions, figure labels, layout-region OCR and cautious procedure/warning scope. The source explicitly left diagram edges unresolved without parser-supported relationship evidence.

Historical runtime: pinned `docling[rapidocr]==2.119.0`, Heron layout model, RapidOCR/ONNX, accurate table structure with cell matching. Local/offline model settings were required for strict air-gapped evaluation.

## Latest complete historical arm
**Structural V1.4** on a fresh 30-case holdout, classified `SCOPED_PROCEDURE_RETRIEVAL_PARTIAL_GAIN`:

| Metric | Before | V1.4 reported |
|---|---:|---:|
| Complete evidence | 46.67% | 66.67% |
| Complete procedure evidence | 16.67% | 75.00% |
| Procedure MRR | 19.44% | 81.39% |

**Remaining adverse results:** cross-procedure contamination **25.00%**, with **three new procedure failures**.

The report explicitly **did not authorize promotion** or a full corpus build. Incomplete V1.3/V1.4 attempts had invalidation records and were prohibited from being combined with successful fresh runs.

## Interpretation
The claimed procedural gain was bounded and did not satisfy contamination safety. Do not reuse the quoted percentages as universal evidence for Docling adoption, a current parser, or expanded-corpus generalization.

Source retrieval and run-artifact files were not transferred to this public reference repository; this is scoped source-grounded synthesis and remains nonqualifying for strict P0 run reproducibility.
