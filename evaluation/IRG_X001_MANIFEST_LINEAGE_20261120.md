# IRG-X001 — V2 master manifest lineage investigation

**Investigation date:** 2026-11-20  
**Status:** `REVISION_CHAIN_INCOMPLETE` — original manifest bytes are not falsified or modified.

## Three recorded master manifest identities

| Context | SHA-256 | Proof observed | Interpretation |
|---|---|---|---|
| V2 scorer contract pre-approval reference | `2f8972bf6e12834b58561d19b4e2269c9d5744f6daaf5e1282f25ab882f4d3c5` | Historical authoritative scorer contract, lines 35–47 | Scorer document explicitly labels this the *pre-scorer-approval* input; predicts a subsequent new manifest digest |
| V2 evaluator manifest and evaluator implementation report | `9ddf9eaf993a62182ce1c52f550002deb2d3584f12e9a56167fba1fe78df0f3c` | `V2_EVALUATOR_MANIFEST_v1.json` authority and evaluator implementation report | Bound manifest version at evaluator freeze (reported), original bytes not found |
| Current Drive `V2_MASTER_REGRESSION_MANIFEST_v1.json` | `fa6b6291079fa0d2c2823a71824e492a80fbc21a0aad5345c91f60d3e5e6fa3e` | Direct downloaded Drive bytes, SHA-256 recomputed | Available document, different digest from evaluator binding |

**Do not assume a chronological proof solely from the three identities.** The scorer contract explicitly documents a pre/post-approval revision expectation, but `9ddf...` and `fa6b...` are not yet paired with two retrieved original master-manifest bodies. A frozen file may be canonical with different keys, formatting, or fields; that cannot be decided without its bytes.

## Convergent immutable bindings
- V2 master population hash: `4b561ffea79edc97c270cda38fbd0e5351615c0acd8d8be4eab291a3d504bd8e`. It matches directly obtained 244-case raw source bytes, present master manifest, scorer contract, evaluator manifest, and gate manifest.
- Historical triage hash: `8dc936cb0d7c600fdad13592f45f2b564ff8c0b41e9050294373f19432a25e2d`. It matches directly obtained 615-row raw source bytes and the bound reports.
- Evaluator manifest correctly binds frozen gate manifest SHA-256 `9e14682951ddea0b6720e74eecc87c680b5ddce580d8915a3d8918e07acfece0`.
- The available manifest is syntactically well-formed and reports approved frozen population; it remains historically useful in its own right.

## Revision search performed
- Direct Drive name query returned no second original JSON manifest.
- Drive version-history listing exposed one accessible revision for each of the master and evaluator manifests, both `2026-09-30T15:48:29Z` (no previous revision ID).
- Exact string search for `9ddf9eaf...` returned the evaluator implementation report, not the missing master-manifest bytes.
- A Drive snapshot `irg_ai-main` was found, with original source and tests; its source tree does not automatically establish the missing manifest revision.

## Safe resolution paths (ordered)
1. **Original Git objects:** retrieve the exact frozen historical manifest at the revision bound by the evaluator artifact, verify `sha256(bytes) == 9ddf...` and compare to `fa6b...`. This is strongest proof.
2. **Immutable artifact archive:** find the materialized report/run bundle with the original 11,467-byte (or other independently observed) file; verify its digest and metadata.
3. **Versioned supersession record:** if the earlier bytes are irrecoverable, preserve both hashes as unresolved and create a new approved evaluator binding to an independently qualified manifest. Do not rewrite, silently relabel or retroactively approve the previous evaluator.

## Decision
`IRG-X001` remains an evidence-chain exception, **not evidence that population records were changed**. The master population and triage hashes remain consistent, while qualification under the specific evaluator's master-manifest binding is blocked. No original gate/manifest bytes changed.
