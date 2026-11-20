# IRG AI — current intellectual reference state (2026-11-20)
**This is research/architecture synthesis; not a live checkout or release claim.**

## Directly bounded historical evidence
- V1.5 freeze, 2026-07-31: 132 approved PDFs; 4,173 chunks; OpenAI text-embedding-3-small 1536 dimensions, Qdrant AOG-TE/dense; hybrid candidates/final/RRF 50/5/60, lexical pool 120; shared 45,000-character context bound; the mutable golden latest artifact was an older failed run and explicitly **not** proof of V1.5 answer quality. Source: https://docs.google.com/document/d/1clikto0CgPvarBSqY6XWgCEkf74qNsS8/edit.
- Historical V1.5 release baseline was tagged with product DB discovery plus approved PDF hybrid retrieval and a shared bounded context; internal pilot candidate, not production-ready. Source: https://docs.google.com/document/d/17Ei0avusADOG5nlexfLAY4rnAypxLuqu/edit.
- V2 frozen master population report dated 2026-09-02: 615 unique questions screened, 208 retained historical + 36 expansion = 244 scenarios, 245 expectation units; 407 excluded before freeze. Population frozen; evaluator implementation was still awaiting approval **at that report date**. A separately retrieved owner approval dated 2026-09-02 verifies `v2-evaluator.1` as `AUTHORITATIVE_FROZEN`, binding all 10 evaluator source/test hashes; release qualification remained **NOT_EXECUTED**. See [reconciliation](evaluation/EVALUATOR_APPROVAL_RECONCILIATION_20261120.md). Source: https://docs.google.com/document/d/1ZnHzc0VX8PDXmv9PV59yLG7PPQvjHYEM/edit.
- IRG_AUTHORITY_POLICY_V1 is explicitly POLICY_ONLY_NOT_ACTIVATED. Source: https://docs.google.com/document/d/17L-A-sQILRF7mp3xHAYhFsF88AWsyz6J/edit.

## Later project-history observations requiring frozen artifact import to strengthen authority
- Structural corpus snapshot: ~39,997 pages; 19,705 tables; 24,344 procedures; 6,502 model and 23,077 part identities; 1,321,166 canonical evidence units; 5,520,135 retrieval views. **Reported history; verify hashes/date/denominators before treating as qualification.**
- Paired P2 standard/full-view: 17 valid unseen cases; both 3/17 sufficient context, 5/17 sufficient evidence@10, zero critical wrong-product errors. Full-view wins 0, losses 0, shared successes 3, shared failures 14. Ranking changes did not improve answerability. **History-derived observation; original ledgers pending.**
- Scale trial: current 16/40 exact gold vs earlier 13/40; narrative 3/10 vs 0/10. These are selected scale tests, not a production reliability estimate.
- P1/P2 reconstructed exact-gold Recall@10 100% on bounded reconstructions, while separate unseen answerability remained poor. Do not combine their denominators.
- Architecture audit identified excess overlapping execution paths, documentation/evaluation drift and large serving module closure; this motivates clean lab, not proof that any new design is superior.

## Decision posture
**Carry forward:** exact identity and document applicability; separate DB facts vs manufacturer facts; canonical evidence/provenance; hybrid channels only where measured; bounded structural reconstruction; context sufficiency; explicit abstention/citations; immutable evaluations.
**Do not automatically carry forward:** full-view proliferation, giant source graph, unactivated authority policy, feature-flag maze or old code paths.
**Open:** exact fresh holdout qualification; latency/storage/cost curves; specific missing master-manifest revision; private frozen cases; late October run ledgers; negative-case coverage; authenticated operational release gates. See P0_SEED_LEDGER.md.