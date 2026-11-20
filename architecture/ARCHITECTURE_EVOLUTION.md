# Architecture evolution and status

| Mechanism | Historical state | Evidence/why introduced | Clean-build status |
|---|---|---|---|
| PDF → chunks → Qdrant | implemented foundation | approved corpus, traceability, rebuildable index | carry concept |
| Exact identifier + product DB identity | implemented V1/V1.5 | vector ambiguity on technical identifiers | carry |
| Hybrid lexical/dense fusion | implemented V1.5 | exact-token and semantic candidate coverage | carry conditionally |
| Product/document applicability | implemented/evolved | prevent wrong-source technical grounding | carry |
| Bounded context + provenance | implemented/evolved | retrieval candidate != model-visible evidence | carry |
| Structural Docling evidence | research lineage | tables, procedures, warnings, model/part identities | revalidate selectively |
| Owner/configuration authority | research with reported gains | wrong-owner/configuration errors | carry concept, retest |
| Canonical evidence + multiview | later research | separate evidence from retrieval representations | canonical evidence: carry; view proliferation: reject by default |
| Local technical reranking | research | improve selected ranking sets | controlled A/B required |
| Sufficiency/answerability | later research/target | gold retrieval did not imply answerable context | build/test explicitly |
| Full clean-lab pipeline | proposed | remove historical path and authority drift | not historical deployed end-to-end |

## Local evidence
- Historical implemented V1.5 baseline: [historical/V1_5_IMPLEMENTED_ARCHITECTURE_BASELINE.md](historical/V1_5_IMPLEMENTED_ARCHITECTURE_BASELINE.md)
- Historical context serialization contract: [historical/IRG_CONTEXT_SERIALIZATION_CONTRACT_V1.md](historical/IRG_CONTEXT_SERIALIZATION_CONTRACT_V1.md)
- Implementation evolution: [../lessons/IMPLEMENTATION_HISTORY.md](../lessons/IMPLEMENTATION_HISTORY.md)
- Lessons and supersessions: [../lessons/LESSONS_LEARNED.md](../lessons/LESSONS_LEARNED.md)
- Accepted historical architecture decisions: [../decisions/historical/](../decisions/historical/)

## Boundary
The target pipeline is a synthesis of mechanisms and later findings. It must never be represented as a single historical production runtime unless a bound source snapshot proves that composition.
