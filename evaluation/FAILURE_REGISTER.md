# Failure register
Taxonomy: IDENTITY_FAILURE, DOCUMENT_AUTHORITY_FAILURE, OWNER_FAILURE, CONFIGURATION_FAILURE, RETRIEVAL_FAILURE, RANKING_FAILURE, REPRESENTATION_FAILURE, STRUCTURAL_RECONSTRUCTION_FAILURE, CONTEXT_SELECTION_FAILURE, CONTEXT_SERIALIZATION_FAILURE, ANSWERABILITY_FAILURE, GENERATION_FAILURE, CITATION_FAILURE, EVALUATOR_DEFECT, RUN_INTEGRITY_FAILURE, PROVIDER_FAILURE, SCALE_REGRESSION, ARCHITECTURAL_COMPLEXITY.

| Observed issue | Category | Evidence status | Disposition |
|---|---|---|---|
| Gold retrieved but context still insufficient | CONTEXT_SELECTION_FAILURE / ANSWERABILITY_FAILURE | history-backed | stage-wise disambiguation |
| Full-view reranked without rescuing final context | REPRESENTATION_FAILURE | paired history-backed | do not automatically rebuild |
| Incorrect product family risk | IDENTITY_FAILURE / OWNER_FAILURE | project history | exact identity and applicability required |
| Enlarged corpus degraded generalization | SCALE_REGRESSION | project history | new holdout and exposure metrics |
| Conflicting frozen grounding of P2-IND-01 | RUN_INTEGRITY_FAILURE | reported paired run | exclude according to predeclared validity, do not repair gold post-run |
| P2-IND-05 lacked approved cleaning-method source | DOCUMENT_AUTHORITY_FAILURE / BLOCKED | reported paired run | block unsafe case |
| Unaligned serving and evaluator or stale tests | EVALUATOR_DEFECT / ARCHITECTURAL_COMPLEXITY | architecture audit | independent parity check |
Provider outages and unsupported evidence must have distinct counters. No failure is erased by a retry.