# Frozen evidence integrity review — 2026-11-20

## Independently verified source data
Direct Google Drive source bytes were read and SHA-256 calculated locally. The **V2 master population** contains 244 parseable JSONL cases (659,697 bytes; SHA-256 `4b561ffea79edc97c270cda38fbd0e5351615c0acd8d8be4eab291a3d504bd8e`) and matches `V2_MASTER_REGRESSION_MANIFEST_v1.json`. The **historical triage** has 615 parseable JSONL records (284,953 bytes; SHA-256 `8dc936cb0d7c600fdad13592f45f2b564ff8c0b41e9050294373f19432a25e2d`) and matches the manifest.

These source JSONL files have historical user-conversation wording and are **withheld** from this public repository; their hashes remain provenance references, not proof that a future user can reproduce evaluation from this repository alone. Original Drive URLs and source hashes are preserved in [FROZEN_TRANSFER_LEDGER.json](FROZEN_TRANSFER_LEDGER.json).

Eight exact original policy/JSON frozen artifacts and two related historical reports were transferred to this branch. Each transferred Git blob SHA-1 was independently matched against the Git blob computed from the original Drive bytes (10/10 match).

## Binding checks
- Gate manifest SHA-256 `9e14682951ddea0b6720e74eecc87c680b5ddce580d8915a3d8918e07acfece0` matches the evaluator's gate binding.
- Evaluator schema SHA-256 `fdc579b24ef1fd9037cd73a84ec393e4b449941299af411693eca12779687ca0` matches its declared schema binding.
- Scorer contract SHA-256 `7a376ba1ab2775431625468b6e45bc9c859aff2a01c180c80118f9845f556be0` matches evaluator's contract binding.
- Regression population SHA-256 matches between the gate manifest, regression manifest and local source bytes.

## Open exception IRG-X001 — cross-artifact master manifest mismatch
The available source `V2_MASTER_REGRESSION_MANIFEST_v1.json` hashes to
`fa6b6291079fa0d2c2823a71824e492a80fbc21a0aad5345c91f60d3e5e6fa3e`.

The evaluator manifest binds a master manifest hash:
`9ddf9eaf993a62182ce1c52f550002deb2d3584f12e9a56167fba1fe78df0f3c`.

They differ. This can reflect a separate revision or a post-freeze modification; it is **not enough evidence to diagnose corruption**. Do not repoint/rewrite any frozen artifact to make the check pass. Find the evaluator-bound version, compare its byte content and frozen population binding, and add a new explicit reconciliation record. Qualification across the two manifests is **BLOCKED** pending that resolution.

## Current qualification
V2 historical artifacts remain **NOT_EXECUTED** for release qualification at the captured manifest state. `V2_EVALUATOR_MANIFEST_v1.json` says evaluator approval pending and no qualification authorized. The existence of a scorer and manifest does not prove release readiness.

## Programmatic check
Run `python scripts/validate_reference_seed.py`; `--strict` requires no blockers. No live provider, product database, Qdrant or corpus mutation is part of this check.
