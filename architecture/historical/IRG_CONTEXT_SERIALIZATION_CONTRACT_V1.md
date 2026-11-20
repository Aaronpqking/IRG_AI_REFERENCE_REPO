<!-- Text transfer from https://docs.google.com/document/d/1H7s5uRURS_Xajd4QeaNC0yEGI_ZJSc9h/edit; original byte hash not certified. Historical candidate, not active runtime. -->

# IRG Context Serialization Contract V1

## Identity

| Field | Value |
| --- | --- |
| Contract | `IRG_CONTEXT_SERIALIZATION_V1` |
| Schema | `irg.model_visible_context.v1` |
| Lifecycle | `PROMPT_DEVELOPMENT_CANDIDATE` |
| Runtime activation | None by this artifact |
| Canonical implementation | `src/context_serialization.py` |
| Machine-readable schema | `docs/evaluation/context_serialization_contract_v1.schema.json` |

This contract versions the exact structure and labels used to present current
runtime information to the answer model. It is not a second behavior prompt.
`SYSTEM_PROMPT_V1` remains the single primary instruction payload.

## Governing boundaries

The serializer:

- preserves the literal current question;
- includes no more than the bounded conversation supplied by the runtime;
- separates conversation continuity from factual authority;
- distinguishes control records from factual evidence;
- provides neutral authority and source identity labels;
- omits unavailable blocks rather than simulating data; and
- does not describe ranking, fusion, chunk selection, or other retrieval
  mechanics to the model.

The serializer does not select sources, decide applicability, authorize a data
system, establish freshness, resolve conflicts, or change response behavior.
Those responsibilities remain in their governing runtime and policy layers.

## Canonical block order

When present, blocks appear in this order:

1. `CONVERSATION CONTINUITY`
2. `QUESTION`
3. `CONTROL`
4. `AUTHORITY RESULTS`
5. `TECHNICAL EVIDENCE`
6. `DYNAMIC STATE`
7. `SOURCE IDENTITIES`

Only `QUESTION` is universally required. Other blocks are emitted only when
the runtime has real applicable data for them. Repeated evidence or state
blocks retain their source order.

## Block contracts

### CONVERSATION CONTINUITY

Purpose: bounded prior user and assistant messages needed to interpret a
follow-up.

Model-visible label:

```text
[CONVERSATION CONTINUITY]
Authority: NONE - continuity only
```

Messages retain explicit `USER` or `ASSISTANT` role labels. Conversation is not
factual evidence. Current canonical answer generation supplies its bounded
user-message view; prior assistant prose must never become fact authority.

### QUESTION

Purpose: preserve the current literal user question exactly once.

Model-visible label:

```text
[QUESTION]
```

Whitespace and characters in the question are not rewritten by the serializer.

### CONTROL

Purpose: carry a bounded runtime instruction or governed absence state that is
not factual evidence.

Required fields:

- authority: `NONE - instruction only`;
- control identity; and
- control text.

Control records must say when they are not citable. They must not masquerade as
technical or operational sources.

### AUTHORITY RESULTS

Purpose: carry an explicitly governed authority decision, applicability result,
supersession result, or unresolved conflict when the runtime produces such a
record.

Required fields when emitted:

- fact or decision scope;
- authority type;
- applicability identity;
- source identity or mapping identity; and
- revision/effective-time identity when supplied.

The current canonical V1.9.39 path does not emit a separate authority-results
block. Its applicable static authority metadata is carried on technical
evidence, and valid absence is carried as `CONTROL`. The serializer must not
invent a separate result.

### TECHNICAL EVIDENCE

Purpose: carry applicable static technical evidence.

Required model-visible fields for a raw technical chunk:

- authority type;
- source identity;
- document name and document ID where present;
- page range;
- section where present;
- evidence identity;
- revision year when present; and
- exact evidence text, including structured tables when supplied.

The authority type for the governed canonical technical corpus is
`MANUFACTURER_TECHNICAL`. A different authority type may be emitted only when
the upstream source contract establishes it. The block does not expose why an
item ranked or which retrieval mechanism selected it.

### DYNAMIC STATE

Purpose: carry current operational facts such as inventory, price, promotion,
shipping, order, return, or workflow state.

Required fields when emitted:

- applicable operational authority type;
- source identity;
- record identity;
- scoped state;
- observation/effective timestamp when the source contract requires it; and
- location, store, customer, order, or workflow scope where applicable.

No dynamic integration is created or approved by this contract. The current
canonical path has no dynamic block. An absent dynamic block means the model
does not have current dynamic authority and must not fabricate it.

### SOURCE IDENTITIES

Purpose: provide a separate source/citation index when a runtime supplies one.

Each identity must bind to an actual model-visible evidence or state record and
retain the source class, stable identity, applicable page/record scope, and
runtime citation form. A standalone source index is omitted when those
identities are already carried by the evidence blocks and no separate runtime
index exists.

## Exact omission rules

- No conversation history: omit `CONVERSATION CONTINUITY`.
- No separate authority decision record: omit `AUTHORITY RESULTS`.
- No applicable static evidence: omit `TECHNICAL EVIDENCE`; an actual governed
  absence record may appear as `CONTROL`.
- No approved current dynamic data: omit `DYNAMIC STATE`.
- No separate runtime citation index: omit `SOURCE IDENTITIES`.
- Never emit empty placeholder facts or synthetic timestamps.

## Instruction and data separation

The Responses API composition is:

```text
instructions = exact selected SYSTEM_PROMPT_V1 payload
input        = exact IRG_CONTEXT_SERIALIZATION_V1 output
```

There is no separate mutable `ANSWER_PROMPT_V1`. A control block may constrain
handling of the supplied data, but it may not replace or contradict the primary
system behavior prompt.

## Identity and hashing

The runtime exposes:

- `version = IRG_CONTEXT_SERIALIZATION_V1`; and
- `schema_sha256`, calculated from the canonical JSON representation of the
  serializer schema constant.

The development freeze separately records SHA-256 hashes for this document,
the machine-readable schema, and the implementation file. Changing labels,
ordering, authority semantics, omission rules, or rendering behavior requires
a new version and new hashes.

## Non-activation statement

This contract is part of a development candidate. It does not qualify or
activate a prompt, promote a corpus, connect a dynamic source, mutate Qdrant or
a database, or establish production readiness.
