# Architectural debt — cross-workstream synthesis
- Multiple overlapping runtime, research, and evaluator execution paths obscured exact behavior.
- Feature flags and version labels diverged from active composition; branch names and FINAL labels were misleading.
- Large derived view proliferation increased indexing and ranking complexity without demonstrated unseen answerability benefit.
- Selected exact-gold retrieval measures masked insufficient final context/answerability.
- Corpus scaling exposed weaker generalization than closed development sets implied.
- Broad source trees, stale tests, mutable latest reports, and docs drift raised reproducibility risk.
- Promoting proposed authority to an active runtime before implementation would be a category error.
Remediation: one serving composition, test-bound stage contracts, bounded indexes, immutable evidence and a claim/experiment promotion gate. Historical audit pointer: SOURCE_MANIFEST.md. Status: synthesis; exact code audit not re-run here.