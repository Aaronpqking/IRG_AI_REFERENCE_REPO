# Evidence-linked capability timeline

This is a capability chronology rather than a roadmap. Dates and version claims must be interpreted through repository-local source/revision evidence and explicit claim status.

1. Initial approved technical-PDF retrieval, source-traceable chunks, embeddings, and Qdrant-derived indexing.
2. Identifier handling and golden evaluation; increasing emphasis on exact model/year and source-page fidelity.
3. Product-database controlled discovery; product identity/catalog context separated from manufacturer technical claims.
4. Multi-source DB+PDF retrieval, document applicability, source/context/citation contracts.
5. V1.5 bounded multi-source baseline (2026-07/08). Local evidence: [historical architecture baseline](../architecture/historical/V1_5_IMPLEMENTED_ARCHITECTURE_BASELINE.md) and [frozen configuration](evidence/V1_5_FROZEN_CONFIGURATION_AND_ARTIFACTS_20260731.md).
6. Corpus governance/expansion; Docling-based structural shadow extraction; page/table/procedure representation.
7. Product-owner and configuration authority; canonical evidence separated from derived retrieval views.
8. Lexical/dense multiview retrieval; canonical collapse, RRF/fusion, and local reranker research. These mechanisms were not all one historical serving composition.
9. October P1/P2 reconstruction; scale generalization testing; standard/full-view paired ablation.
10. November alias/canonical-source audits and staged R2 P0–P7 work. R2 later showed strong document-level narrowing without equivalent lexical/dense competition reduction and with insufficient-context failures still open.
11. Architecture/codebase audits and clean-lab rebuild decision.

## Local historical chronology

- [IMPLEMENTATION_HISTORY.md](evidence/IMPLEMENTATION_HISTORY.md)
- [LESSONS_LEARNED.md](../lessons/LESSONS_LEARNED.md)
- [CURRENT_REFERENCE_STATE.md](../CURRENT_REFERENCE_STATE.md)
- [EXPERIMENT_REGISTER.md](../evaluation/EXPERIMENT_REGISTER.md)

## Boundary

Steps 6–11 combine repository-local historical documents with explicitly labeled project-history observations. Any late result whose original bound run package is absent remains `HISTORY_REPORTED_UNVERIFIED`; chronology does not promote it to verified runtime evidence.
