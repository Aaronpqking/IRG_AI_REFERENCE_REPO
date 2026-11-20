<!-- Historical direct text from Google Drive at https://docs.google.com/document/d/1clikto0CgPvarBSqY6XWgCEkf74qNsS8/edit; original source version and byte hash not independently established. Content copy not frozen empirical qualification. -->

# V1.5 Frozen Configuration and Artifact Identities

Date: 2026-07-31

State: PRE-COMMIT REVIEW

Secrets are omitted. `.env`, local database credentials, API keys, and endpoint
secrets are not release artifacts and were not staged.

## Code and contract identity

| Item | Value |
|---|---|
| Branch | `refactor/hexagonal-contract-restoration` |
| Pre-release committed HEAD | `0575638aea2d3c9d40e3f35ccb6c80cca380785f` |
| Pipeline contract | `hexagonal.v1` |
| Context packet | `context.v1` |
| Source schema | `sources.v2` |
| Prompt contract | `chat_prompt.v1` |
| Release commit | pending reviewed commit |
| Release staged-tree identity | reported after final staging |

## Resolved non-secret local configuration

| Setting | Frozen value |
|---|---|
| Chat model | `gpt-5.5` |
| Embedding model/dimensions | `text-embedding-3-small` / `1536` |
| Qdrant collection/vector | `AOG-TE` / `dense` |
| Product discovery | `observe` / enabled |
| Product procedure | `auto` |
| Product candidates | `10` |
| Product description bound | `0` / unbounded |
| Grounding validation | `observe` |
| PDF configuration applicability | `observe` |
| API debug diagnostics | `false` |
| CORS origin | `*` (production blocker) |
| Hybrid candidates/final/RRF | `50` / `5` / `60` |
| Lexical query candidates | `120` |
| Selected documents/anchors/neighbors | `3` / `5` / `4` |
| Max chunks per document/page distance | `8` / `1` |
| PDF/shared context ceiling | `45,000` characters |
| Separate product-context allocation | `0` |
| Product DB configuration present | yes; values omitted |
| Conversation DB configuration present | yes; values omitted |

The 45,000-character ceiling is shared. No deterministic per-source allocation
or product-description bound was introduced.

## Local corpus and evaluation identities

These files are ignored/local artifacts and are not staged.

| Artifact | Rows/size | SHA-256 |
|---|---:|---|
| `data/approved_pdfs.jsonl` | 132 rows / 40,400 bytes | `77D3167DB924F0D6BFADFB0D773F4D6C699063865551478BED4672AA179CEB2F` |
| `data/manifest.json` | 132 documents / 127,468 bytes | `C63CC88D12751154111B3015945DD0F40BA0C9E83947D94673940CAF46E4C44E` |
| `data/chunks.jsonl` | 4,173 rows / 15,413,225 bytes | `DB586DEAEFEA93EC281D8027A2F85D718F721305B7A32FB5D6FD610D1977E1FD` |
| `data/golden_questions.jsonl` | 30 rows / 17,638 bytes | `8AF11212536E253E04575F32D3E4ADCCA01BAD2299973F94733AB55350442A61` |
| `data/evals/v1_5_controlled_discovery.jsonl` | 14,076 bytes | `C137BB4F7FF54DA9603CFAD9E41B6BD0F00CA42B8A9F8091DBCF1E8AC3AF4619` |
| `reports/golden_eval_latest.json` | 84,982 bytes | `3D759F453F473863B1521492C65F285088BE9D908135733E9B3260B3852517B3` |

The current mutable golden latest pointer is an older chat-eval failure
artifact: 29 run, 17 passed, 12 failed, retrieval pass rate 65.52%, five
unsupported-answer diagnostics, zero missing required source refs, zero unsafe
fitment/universal claims, and no collection mutation. It is not a post-V1.5
accuracy comparison and is not used to claim V1.5 answer accuracy.

Configured live Qdrant count/payload identity was not refreshed in this offline
freeze. The ingestion dry run found 155 physical PDFs, 82 approved in source,
73 unapproved, and 50 approved paths missing. Corpus mutation: none. Qdrant
mutation: none.

## Dependency and migration identities

| Artifact | SHA-256 |
|---|---|
| `requirements.txt` | `7350BFB1E773FEAD36EF7B1976B6EE68B744081EB26D0FE23E6AAB80B7400395` |
| `frontend/package-lock.json` | `260FB7E376081477E91A37DF7FF7E91892E296DA964DB6C2AF17C57D4AEBB3D4` |
| `.env.example` | `B90AB591F5BFED85B9310DC5078449109C75CBF2B2F51A064F85F1251B7EDFFE` |
| `docs/migrations/20260724_add_turn_runtime_metadata.sql` | `6ACFBCF82622FEC1CC8AFC917FF8CB63084FFAF95B14ABE0178DBF5B554B1704` |

The migration artifact exists but the optional runtime-metadata table was
absent in the last authorized live capability check. No schema, stored
procedure, corpus, vector collection, or external service was changed by this
release freeze.
