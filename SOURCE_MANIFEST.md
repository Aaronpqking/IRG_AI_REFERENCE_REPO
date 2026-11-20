# Provenance ledger
The ledger records *existing copied artifacts and synthesized files separately*. References to Drive are source pointers, not proof of byte-identical transfer.

| Destination | Origin | Date | Class | Authority | Why retained | Superseded/combined with |
|---|---|---|---|---|---|---|
| README.md | seed specification and project-history synthesis | 2026-11-20 | HYBRID | interpretation | navigation and boundary | none |
| REFERENCE_POLICY.md | historical governance, evaluation, and synthesis | 2026-11-20 | HYBRID | policy for this repository | evidence precedence | old snapshot guidance |
| CURRENT_REFERENCE_STATE.md | dated Drive documents and project-history observations | 2026-11-20 | HYBRID | synthesis | state of evidence | later verified runs may supersede |
| architecture/TARGET_REFERENCE_PIPELINE.md | late project history | 2026-11-20 | HYBRID | proposed clean reference | separates decision stages | not single historic runtime |
| evaluation/EXPERIMENT_REGISTER.md | project-history experiment reports | 2026-11-20 | HYBRID | historical summary only | prevents false equivalence | exact run ledgers pending |
| CLAIM_REGISTER.jsonl | dated Drive records and project history | 2026-11-20 | GENERATE | claim hypotheses scoped by source | claim-level support | verify against run artifacts |
| evidence historical copies | Drive document URLs recorded in each file header | 2026-11-20 | TRANSFER when fetched complete | historical only | source fidelity | no automatic current authority |

## Primary direct Drive pointers
- V1.5 configuration freeze: https://docs.google.com/document/d/1clikto0CgPvarBSqY6XWgCEkf74qNsS8/edit
- V2 frozen regression population **report**: https://docs.google.com/document/d/1ZnHzc0VX8PDXmv9PV59yLG7PPQvjHYEM/edit; the source manifest was transferred exactly; raw JSONL data was verified by hash but withheld from the public repository.
- V1.5 architecture baseline: https://docs.google.com/document/d/17Ei0avusADOG5nlexfLAY4rnAypxLuqu/edit
- Historical implementation evolution: https://docs.google.com/document/d/1ufsZWtjRgpA2fi7ajURE1G91U3j0IKRZ/edit
- Policy-only authority contract: https://docs.google.com/document/d/17L-A-sQILRF7mp3xHAYhFsF88AWsyz6J/edit
- Accepted thin hexagonal ADR: https://docs.google.com/document/d/1vGuDSv6VF-qm5A9RdNc59_Ovv4bqyIxT/edit

For each future transfer add SHA-256 from actual bytes, origin version, sensitivity classification, proof of completeness, transfer timestamp and validation status. Never mark a pointer TRANSFER.
## 2026-11-20 exact frozen evidence update

- [evaluation/FROZEN_TRANSFER_LEDGER.json](evaluation/FROZEN_TRANSFER_LEDGER.json) now holds **10 exact-byte transfers**: eight frozen contracts/metadata artifacts and two historical evaluator reports. Original SHA-256 and Google Drive source URLs are recorded per file.
- [evaluation/INTEGRITY_FINDINGS_20261120.md](evaluation/INTEGRITY_FINDINGS_20261120.md) confirms 244 population rows and 615 triage decisions match their frozen SHA-256 identities; their source text remains restricted to authorized Drive access.
- Both master regression manifests and scorer schemas are historical evidence for their own versions. **IRG-X001** prohibits blindly joining discrepant evaluator/master manifest revisions.
- The new private technical-data-platform GitHub repository was found but empty when checked; it does not provide legacy source or tests.

Do not infer that the reference repository includes the complete original qualification runner or a transferable user-question corpus.
