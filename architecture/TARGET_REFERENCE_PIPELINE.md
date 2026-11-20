# Target reference pipeline — proposed clean lab, NOT a historical deployed runtime
```text
USER QUESTION
 → identity extraction → exact product/model resolution → fact-type authority
 → document applicability and revision authority
 → exact + lexical + dense candidate retrieval
 → canonical evidence ID collapse → fused ranking
 → product/technical/owner/configuration rerank
 → bounded table/procedure/warning/parent-child context reconstruction
 → context selection / budget / model-visible evidence serialization
 → sufficiency, ambiguity, conflict and answerability decision
 → grounded generation OR targeted clarification OR abstention
 → per-claim evidence attribution + citation completeness validation
```
Separate five independently testable subsystems: AUTHORITY, RETRIEVAL, EVIDENCE CONSTRUCTION, DECISION, REALIZATION. Instrument the input/output and failure class of each. Candidate@K and context sufficiency must never share a metric name.

Hard constraints: no model/brand hardcoding; no runtime import from this repository; no retrieval views serving as citation owners; no unbounded structural graph traversal; no synthetic gold promotion; no unapproved corpus/index mutation. Reference decisions require qualified experiment promotion.