<!-- Historical direct text from Google Drive at https://docs.google.com/document/d/17Ei0avusADOG5nlexfLAY4rnAypxLuqu/edit; original source version and byte hash not independently established. Content copy not frozen empirical qualification. -->

# V1.5 Implemented Architecture Baseline

Date: 2026-08-05

Release status: `CLOSED - PASS_WITH_WATCH` at release commit `c464c1a3` and tag
`irg-ai-v1.5-multisource-baseline`.

Product readiness: `INTERNAL PILOT CANDIDATE`.

Production readiness: `NOT CLAIMED`.

## Runtime flow

```text
original question + conversation ID
  -> canonical request and bounded recent-turn load
  -> information needs and literal identifier extraction
  -> product DB discovery
       exact parameterized identifier lane
       broad stored-procedure fallback after exact miss
  -> candidate resolution and product-context enrichment
  -> unconditional hybrid PDF candidate retrieval
       exact identifier + lexical + metadata + vector channels
  -> document and configuration applicability assessment
  -> corpus-neighbor expansion
  -> one shared bounded model context
  -> configured chat model
  -> observe/enforce validation according to explicit policy modes
  -> canonical DB/PDF source projection
  -> conversation, sources, feedback, and optional runtime metadata
```

## Implemented contracts

- API, CLI, and production-path evaluation compose through `src/bootstrap/`.
- `PRODUCT_DISCOVERY_ENABLED=observe` is the canonical enabled state. This is
  core retrieval composition, not a three-mode response policy.
- Controlled retrieval always composes the hybrid PDF adapter. Configuration
  applicability cannot enable or disable retrieval channels.
- Exact identifier normalization is limited to the exact DB lane. Natural
  semantic query text is not globally normalized through a product taxonomy.
- DB records and PDFs remain different evidence types with different authority.
- Every admitted model-visible record receives one canonical evidence identity.
- Public and persisted answer sources project from that admitted evidence set.
- Discovery-only candidate basis remains distinct from answer evidence.
- PDF admission requires positive applicability or lacks an authoritative
  conflict according to the active contract; explicit conflicts can reject.
- Year mismatch is ranking/diagnostic evidence, not an independent rejection
  or authorization basis.
- Configuration policy defaults to `observe`. Observe never changes admission;
  future enforcement requires explicit exclusion or complete authoritative
  coverage conflict, not a path or taxonomy mismatch alone.
- One canonical document may retain multiple catalog aliases. Byte-identical
  approved physical files can collapse into one document/chunk set.
- Context uses one 45,000-character ceiling with no predetermined DB/PDF
  allocation. Product descriptions remain unbounded pending measurement.
- External calls are operation-owned; startup does not perform implicit DDL or
  Qdrant mutation.

## Current limitations that define V2

- The product-context contract remains singular even when several candidates
  or identifiers are represented.
- Follow-up resolution uses a four-turn window plus in-memory active context
  and can rewrite the internal effective question.
- Conversation persistence does not yet store compact per-turn subject state
  sufficient for restart-safe evidence rehydration.
- DB discovery is exact-first with broad fallback, not exact-plus-broad merging
  after exact success.
- DB/PDF retrieval is not yet a bounded multi-round planner with per-subject
  completeness targets.
- Current corpus records do not automatically gain prospective metadata fields.

These are V2 scope. They do not negate the V1.5 multi-source evidence proof.
