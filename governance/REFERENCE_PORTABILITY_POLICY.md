# P0 reference portability and Google Drive boundary

**Status:** `ACTIVE_REFERENCE_SEED_POLICY` (2026-11-20). This document interprets repository-local `REFERENCE_POLICY.md`, `SOURCE_MANIFEST.md`, `governance/AUTONOMY_BOUNDARIES.md`, and `SEED_COMPLETENESS_AUDIT_20261120.md`. It does not retroactively amend any historical freeze or grant release authority.

## Permitted external discovery
- Google Drive and other authorized archives may be searched to **locate, read, authenticate, hash, and classify** historical source, tests, frozen artifacts, and reports.
- Origin IDs may be retained **only as optional provenance metadata** in explicitly labeled ledgers; Codex must never require access to Google Drive, Docs, a private account, or an external URL to understand a current/reference claim.
- A hash verified against private bytes is an **externally verified identity**, not a repository-local executable source. Label private/withheld files distinctly and never claim a pointer or hash constitutes a completed source transfer.

## Required local transfer and documentation
- Only an actual nonempty, locally present artifact may be called `TRANSFERRED_EXACT`, after reading original bytes, byte-count and SHA-256 equality, format validation and correct provenance/classification.
- A redacted or selected excerpt must be explicitly identified as `CURATED`/`REDACTED`, accompanied by original identity where appropriate and an explanation of which behavior/evidence is no longer reproducible.
- Current synthesis cites repository-local artifacts. Retained exact historical copies may contain original external references as historical text, but the current/reference interpretation cannot depend on them.
- Never infer source implementation from an artifact filename, static design text or source-hash inventory. When source is withheld, label the source-level claim `EXTERNALLY_VERIFIED_NOT_LOCAL` and keep clean-build acceptance unproven.

## Publication and protection
- This repository is **public**. Screen every proposed transfer for credentials, customer/employee content, private conversations, trace payloads, restricted source, and approval limits. Sensitive original bytes remain in their approved controlled environment.
- Historical owner approval of evaluator implementation **does not by itself authorize Git publication**. The preserved `V2_EVALUATOR_APPROVAL_v1.json` explicitly says `git_publication_authorized: false` **by that approval record**. The P0 transfer requires independent review and authorization for publication of each public artifact.
- Do not alter approved gold, scorer contracts, population labels, evaluator manifests, run artifacts, source revisions, production systems or deployment state to reconcile a mismatch.

## Completion and promotion gates
- `python scripts/validate_reference_seed.py` verifies current integrity while tolerating explicit blockers.
- `python scripts/validate_reference_seed.py --strict` is the required complete-P0 gate. A passing non-strict workflow is **not** full P0 completion.
- Every required reference folder must contain substantive files, not `.gitkeep`; selected historical source and behavior-defining tests must be local (or explicitly blocked, in which case P0 is not complete).
- Late research results remain `HISTORY_REPORTED_UNVERIFIED` until original bound run artifacts and denominators are local, with private populations withheld.
- `IRG-X001` remains unresolved until an original evaluator-bound master manifest is recovered and verified; never silently substitute `fa6b...` for `9ddf...`.
- Historical `AUTHORITATIVE_FROZEN` evaluator implementation approval and `NOT_EXECUTED` release qualification must remain distinct.

## Accepted evidence status values for external recovery
| Label | Meaning | May satisfy P0 local source gate? |
|---|---|---|
| `LOCAL_EXACT_TRANSFER_VERIFIED` | Current repository bytes match independently verified original bytes | Yes, subject to scope and privacy |
| `LOCAL_CURATED_REDACTED` | Reproducible, scope-limited derivative with documented redactions | Only for expressly approved scope |
| `EXTERNALLY_VERIFIED_NOT_LOCAL` | Original bytes matched hashes elsewhere; source is absent here | No |
| `HISTORY_REPORTED_UNVERIFIED` | Historical report without requisite immutable backing | No |
| `BLOCKED` | Missing/contradictory authority or security conditions | No |

This is the governing distinction for the archived Drive-source inventory under `source_reference/SOURCE_BINDINGS_20261120.json` and the evaluator provenance ledger. Raw private source stays separate from the public reference seed.
