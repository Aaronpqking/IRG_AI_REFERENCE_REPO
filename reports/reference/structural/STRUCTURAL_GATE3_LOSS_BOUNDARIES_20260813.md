# Structural Gate 3 — historical loss-boundary findings

**Classification:** `LOCAL_CURATED_REPORT_SUMMARY / ORIGINAL_REPORT_NOT_TRANSFERRED / REVIEW_PENDING`  
**Original:** `GATE_3_STRUCTURAL_INFORMATION_PRESERVATION_20260813T191541Z.md`, run `20260813T191541Z`. Historical source commit `40e02daadbbfc3fcd61d2f07cb3acd799b2cfc90`.

## Observation scope
The source described a frozen **48-case, 14-page** visual cohort drawn from 12 approved PDFs. Cohort families: controls 5, diagrams 18, multiproduct/identifier ownership 6, tables 13, warnings/instructions 6.

## Earliest material loss boundary
At the historical production transformation from **PyMuPDF parser-native page objects** to `page.get_text()`, a flat text representation discarded coordinates, images, vector paths, table topology, leader lines and diagram connectivity. The report judged this the earliest material structural loss boundary on its cohort.

- **Arm C:** layout-preserving linearization with frozen visual annotations recovered **32** visually verified relationships, with **0** lost controls and **0** newly false relationships.
- **Arm B:** page admission repair recovered native-text facts from three diagram pages previously discarded by a `low_text` rule; it did **not** recover unlabeled graphical relationships.
- OCR gap: one raster instruction page had zero native text. No OCR provider/executable was allowed in that audit; this remained unresolved.
- Typed structural scorer (16 valid/corrupt pairs): **100% precision and recall** reported; legacy term-presence evaluator falsely accepted **12 corrupted relationship fixtures**.

## Limits
The audit's Arm C relied on frozen, visually inspected relationship annotations. It established **recoverability** of structural information, **not** a qualified automated structural parser, production extractor, or generalizable retrieval improvement. The report's source and metric denominators are local to this cohort.

## Clean-build requirements supported
Protect parser-native objects and geometry until structured evidence extraction; test ownership, row/column/edge and warning scope using typed bindings, not bag-of-terms matching. Evaluate OCR, table and diagram recovery separately.

Original run files and visual ground truth were not transferred here; reproduction is blocked. This is a *curated summary*, not an exact original artifact.
