# P0 seed delivery / remaining evidence gates — 2026-11-20
## Implemented
- Reference navigation, authority hierarchy, source pointers and claimed-vs-verified labeling.
- Architecture, timeline, governance, evaluation metrics, experiment/failure registers and clean carry-forward synthesis.
- Claim-level JSONL and machine-readable promotion schema with regression/holdout/cost constraints.
- Bounded historical transfers from Google Drive where completed and provenance-labeled.

## Not yet complete — blocks unqualified clean-build decisions
- Copy **exact frozen JSONL, schema, manifest, evaluator and hash-bound run artifacts** into evaluation/frozen/ after checking confidentiality; a report about their existence is insufficient.
- Import and test referenced source snapshots and tests_reference; GitHub current reference repo does not contain implementation authority.
- Verify structural corpus counts, P1/P2 audit, scale and ablation against the actual frozen run logs and hashes; historical conversation is lower-authority.
- Reconcile late research with executable source and latest commit, and confirm whether source repositories are accessible through GitHub connector.
- Conduct independent public-repo sensitivity/secret screening of every later transfer. Historical Drive docs may include operational or private data; never mass mirror.
- Run machine validation on frozen hashes and full experiment joins; this first seed only validates text/schema representation.
## Completion criterion
P0_SEED_COMPLETE requires every P0 manifest destination present or explicitly marked BLOCKED with rationale, frozen evidence verified by hash, and no unverified content treated as empirical promotion. Current status: **P0_INITIAL_SEED_PARTIAL / NOT QUALIFIED**.