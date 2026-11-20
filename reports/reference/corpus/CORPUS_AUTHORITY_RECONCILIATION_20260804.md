# V2-S2A governed-corpus authority reconciliation

**Classification:** `LOCAL_CURATED_REPORT_SUMMARY / ORIGINAL_REPORT_NOT_TRANSFERRED / REVIEW_PENDING`  
**Original:** `V2_S2A_CORPUS_RECONCILIATION.md`, dated **2026-08-04**, baseline commit `6945b281b57c27891b8778dc990eb782f69b2941`.

## Directly reported offline audit
| Authority or count | Historical result |
|---|---:|
| Physical PDFs (P) | 696 |
| Approval rows (A) | 696 |
| Manifest documents (M) | 132 |
| Chunk rows | 4,173 |
| Accounted path identities | 828 |
| P − A and A − P | 0 each |
| Approved physical PDFs not in manifest | 696 |
| Manifest documents lacking valid physical/approval authority | 132 |
| Manifest docs without chunks | 48 |
| Chunk paths outside manifest | 0 |
| Orphan chunk IDs | 0 |
| Exact duplicate SHA-256 groups | 28 |

**Original gate status:** `S2A_RECONCILIATION_ACCOUNTED` — an accounting/reconciliation result, **not** complete alignment or active-corpus approval. The same historical report marked `APPROVED_PHYSICAL_NOT_MANIFESTED: 696` and `MANIFEST_AUTHORITY_INVALID: 132`. Avoid confusing complete accounting with correct membership or retrieval coverage.

## Historical identity hashes
- Physical path set SHA-256: `e60aaeef1181e251bcb201a461e3e35ab872339f6e2c4aaee4772b5a580fea7e`.
- Approval registry SHA-256: `3d003a17a77c466ce6a8d0dde489c09a123855fe60f17c0ee0f968c3d176a397`.
- Manifest SHA-256: `c63cc88d12751154111b3015945dd0f40ba0c9e83947d94673940caf46e4c44e`.
- Chunks SHA-256: `db586deaefea93ec281d8027a2f85d718f721305b7a32fb5d6fd610d1977e1fd`.

Those are report-stated digest identities and were **not independently recomputed** in this seed pass.

## Safety
The report expressly states no mutation to PDFs, approvals, manifest, chunks, Qdrant collections or databases.

## Comparison rule
This is the August 4 authority audit at its bound baseline; its **696 physical PDFs** and **132 manifest entries** cannot be merged into July 15's 153/132 source-tree comparison or later corpus totals without an explicit snapshot mapping. This local document is not the full original report.
