# Architecture evolution and status
| Mechanism | Historical state | Evidence/why introduced | Clean-build status |
|---|---|---|---|
| PDF → chunks → Qdrant | implemented foundation | traceability/rebuildable index | carry |
| Exact identifier/DB identity | implemented V1.5 multi-source | vector ambiguity on technical part IDs | carry |
| Hybrid lexical/dense RRF | implemented V1.5 | lexical exactness + semantic recall | carry conditionally |
| PDF applicability & shared context | implemented V1.5 | source owners and evidence fidelity | carry |
| Structural Docling shadow | research, holdout failures reported | tables, procedures, warnings | revalidate selectively |
| Canonical evidence + multiview | later research architecture | structural retrieval richness | do not assume full-view value |
| Local technical reranking | research, not equivalent to serving | improved ordering on selected sets | controlled A/B required |
| Sufficiency/answerability gate | target reference architecture | gold hit != answerable answer | build/test |
| Full clean-lab pipeline | proposed | remove architecture debt | not historical deployed end-to-end |

V1.5 baseline: https://docs.google.com/document/d/17Ei0avusADOG5nlexfLAY4rnAypxLuqu/edit. History: https://docs.google.com/document/d/1ufsZWtjRgpA2fi7ajURE1G91U3j0IKRZ/edit. See TARGET_REFERENCE_PIPELINE.md. Never say the target pipeline existed as one historical production implementation.