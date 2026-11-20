# V2 evaluator implementation — exact-source approval reconstruction

**Evidence date:** 2026-11-20 retrieval of historical 2026-09-02 artifacts.  
**Result:** `EVALUATOR_IMPLEMENTATION_APPROVED_AND_SOURCE_BOUND`  
**Qualification:** `NOT_EXECUTED` — separate release gate.

## Direct evidence
1. Historical `V2_EVALUATOR_MANIFEST_v1.json` file SHA-256: `2085173fb9871a6a4a2bb6da2960c4163a4a5f3288a2682e71f4f9075e5cd60e`.
2. Original `V2_EVALUATOR_APPROVAL_v1.json`, found in Google Drive: status `AUTHORITATIVE_FROZEN`, approved 2026-09-02. It binds that **exact** evaluator manifest hash and the `V2_DERIVED_GATE_POPULATIONS_v1.json` file SHA-256 `3ea5a4648e9a7043d3100fcf6aafb9494fb76c5146e842f6335dab50ed7ce0f0`. Both bindings were independently recomputed and matched.
3. All ten files named by evaluator manifest `source_hashes` (eight source files) and `test_source_hashes` (two test files) were located in Drive and their SHA-256 digests independently matched **10/10**. Original source code was **not copied to this public reference repository**.
4. Evaluator dependencies `fbc7ebe8...`, fixture matrix `de16b353...`, focused test evidence `70dcfee0...` and derived gate population `3ea5a464...` each matched exact evaluator-manifest bindings.
5. The frozen focused-test evidence reports passing historical offline tests; the tests were **not replayed in this investigation**.

## Correct temporal interpretation
- Historical evaluator implementation report `READY_FOR_EVALUATOR_APPROVAL` / `PENDING_OWNER_APPROVAL` was accurate at the time of its preapproval snapshot.
- **Separate, later owner approval artifact** makes `v2-evaluator.1` `AUTHORITATIVE_FROZEN` for the listed evaluator/scorer/fixture contracts. This does **not** retroactively edit the original manifest or report.
- The approval expressly states `qualification_execution_authorized: false`, `qualification_plan: PENDING`, `qualification: NOT_EXECUTED` and `v2_0: RELEASE_BLOCKED_PENDING_QUALIFICATION`.
- `IRG-X001`: evaluator bound master regression manifest digest `9ddf9eaf...` differs from currently available manifest `fa6b6291...`. Source and evaluator approval verification **do not** resolve that separate cross-artifact mismatch.

## Public-safe machine record
See [EVALUATOR_PROVENANCE_LEDGER.json](EVALUATOR_PROVENANCE_LEDGER.json) for all direct Drive IDs, SHA-256 identities and publication boundaries, and the exact limited approval record at [frozen/V2_EVALUATOR_APPROVAL_v1.json](frozen/V2_EVALUATOR_APPROVAL_v1.json).

## Design implication
The clean-build reference may cite the historical approved evaluator **implementation and frozen contracts**, but may not infer its use in an accepted V2 release, current deployed runtime, or the final October P1/P2 research composition. Prefer a fresh, independent production-path qualification with protected holdout.

## P0 portability qualifier
The 10/10 source-hash result was directly verified against private archival bytes; it is **not locally reproducible by Codex from this repository** because source files remain withheld. The approval and contract files copied here are repository-local and independently hash-checkable. Evaluator approval is separate from public artifact publication authorization: the original approval record explicitly sets `git_publication_authorized: false` by that record. The public PR must receive independent sensitivity/publication approval before merge. See [reference portability policy](../governance/REFERENCE_PORTABILITY_POLICY.md).
