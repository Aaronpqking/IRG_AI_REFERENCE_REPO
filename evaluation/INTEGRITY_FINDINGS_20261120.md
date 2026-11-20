# Frozen evidence integrity review — 2026-11-20

## Independently verified source data

The V2 master population contains 244 parseable JSONL cases (659,697 bytes; SHA-256 `4b561ffea79edc97c270cda38fbd0e5351615c0acd8d8be4eab291a3d504bd8e`) and matches `V2_MASTER_REGRESSION_MANIFEST_v1.json`.

The historical triage contains 615 parseable JSONL records (284,953 bytes; SHA-256 `8dc936cb0d7c600fdad13592f45f2b564ff8c0b41e9050294373f19432a25e2d`) and matches the manifest.

These source JSONL files contain historical user-conversation wording and are intentionally withheld from this public repository. Their names, hashes, byte counts, and visibility status are preserved in [FROZEN_TRANSFER_LEDGER.json](FROZEN_TRANSFER_LEDGER.json). Codex does not require access to the external archive to interpret the public reference; qualification requiring the withheld populations must use separately authorized evidence matching these hashes.

Eight exact original policy/JSON frozen artifacts and two related historical reports were transferred into the repository. Each transferred Git blob SHA-1 was independently matched against the Git blob computed from the original source bytes.

## Binding checks

- Gate manifest SHA-256 `9e14682951ddea0b6720e74eecc87c680b5ddce580d8915a3d8918e07acfece0` matches the evaluator's gate binding.
- Evaluator schema SHA-256 `fdc579b24ef1fd9037cd73a84ec393e4b449941299af411693eca12779687ca0` matches its declared schema binding.
- Scorer contract SHA-256 `7a376ba1ab2775431625468b6e45bc9c859aff2a01c180c80118f9845f556be0` matches evaluator's contract binding.
- Regression population SHA-256 matches between the gate manifest, regression manifest, and separately controlled source bytes.

## Open exception IRG-X001 — cross-artifact master manifest mismatch

The repository-local `V2_MASTER_REGRESSION_MANIFEST_v1.json` hashes to:

`fa6b6291079fa0d2c2823a71824e492a80fbc21a0aad5345c91f60d3e5e6fa3e`

The evaluator manifest binds a different master-manifest SHA-256:

`9ddf9eaf993a62182ce1c52f550002deb2d3584f12e9a56167fba1fe78df0f3c`

They differ. This may reflect a distinct revision or post-freeze modification; it is not sufficient evidence to diagnose corruption. Do not repoint or rewrite frozen artifacts to make the check pass. Recover the evaluator-bound version from a bound historical checkout or archived hash-index, compare its content and population binding, and add an explicit reconciliation record.

Qualification across the two manifest revisions is **BLOCKED** until then.

## Current qualification

V2 historical artifacts remain `NOT_EXECUTED` for release qualification at the captured manifest state. `V2_EVALUATOR_MANIFEST_v1.json` records evaluator approval pending and no qualification authorization. The existence of scorers/manifests does not establish release readiness.

## Programmatic check

Run:

`python scripts/validate_reference_seed.py`

Use `--strict` only when the repository is intended to satisfy full seed-completion gates. The validator performs no live provider, product database, vector database, or corpus mutation.

## Revision-history limitation

The accessible historical artifact record did not yield the evaluator-bound master-manifest revision `9ddf9eaf...`. IRG-X001 therefore remains unresolved. Future resolution must come from a directly bound historical checkout or archived artifact-index evidence, not an inferred or reconstructed manifest.

## Addendum — owner-approval state and exact evaluator source binding
The evaluator implementation report and manifest record a preapproval state, while the independently retrieved **subsequent owner approval file** `frozen/V2_EVALUATOR_APPROVAL_v1.json` explicitly freezes `v2-evaluator.1` as `AUTHORITATIVE_FROZEN`. Its manifest and derived-population SHA-256 bindings match available original bytes. Ten of ten original evaluator source/test files also match the manifest; frozen dependency, fixture and focused-test evidence hashes match. Qualification stays `NOT_EXECUTED`; the approval file prohibits qualification execution by itself. This does **not** reconcile the evaluator-bound master manifest `9ddf9eaf...` against the available `fa6b6291...`. See [approval reconciliation](EVALUATOR_APPROVAL_RECONCILIATION_20261120.md) and [source lineage](IRG_X001_MANIFEST_LINEAGE_20261120.md).
