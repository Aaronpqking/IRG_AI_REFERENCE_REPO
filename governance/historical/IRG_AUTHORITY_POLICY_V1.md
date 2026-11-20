<!-- Historical direct text from Google Drive at https://docs.google.com/document/d/17L-A-sQILRF7mp3xHAYhFsF88AWsyz6J/edit; original source version and byte hash not independently established. Content copy not frozen empirical qualification. -->

# IRG Authority Policy V1

## Policy identity

| Field | Value |
| --- | --- |
| Policy | `IRG_AUTHORITY_POLICY_V1` |
| Version | `1.0` |
| Status | `POLICY_ONLY_NOT_ACTIVATED` |
| Scope | Fact-type authority, conflict handling, temporal precedence, missing authority, and handoff principles |
| Runtime effect | None |

This policy defines which source class is entitled to support each kind of
fact in an IRG AI answer. Authority is fact-type specific. No source is
universally authoritative merely because it is available, structured, recent,
or already connected to a runtime.

This document is a target governance contract. It does not approve a specific
database, API, tool, corpus, or integration for a new use. Existing source
approval and scope limits remain binding, including
`PRODUCT_DB_FIELD_AUTHORITY.md`, `PRODUCT_DATA_SOURCE_CONTRACT.md`, and the
manufacturer-document policies. A source becomes authoritative for a fact type
only after its identity, scope, freshness where relevant, lineage, permissions,
and approved use have been established.

## Purpose

The policy establishes:

- the primary authority for static technical, dynamic commercial, dynamic
  operational, and approved internal-mapping facts;
- the limited role of secondary sources;
- how applicability, supersession, recency, and fact type resolve conflicts;
- how static and dynamic information may be combined without conflating their
  authority;
- how inferred or synthesized information must be distinguished from facts;
- what to do when authority is unavailable or conflicts cannot be resolved;
  and
- when human handoff is useful and proportionate.

It does not change retrieval, source routing, generation, citations,
evaluation, observability, corpora, Qdrant, operational integrations, or
serving behavior.

## Terms

- **Fact type**: the category of the claim being answered, such as technical
  clearance, current price, stock availability, or order status.
- **Primary authority**: the approved source class entitled to establish the
  fact.
- **Secondary authority**: an approved source that may corroborate, identify,
  scope, or contextualize a fact but may not silently replace its primary
  authority.
- **Applicable source**: a source proven to match the relevant product,
  model, revision, configuration, location, store, customer, order, and time
  scope required by the question.
- **Dynamic fact**: state whose truth can change through normal commercial or
  operational activity.
- **Static or semi-static fact**: technical or governed mapping information
  that changes through controlled document or mapping revision.
- **Inference**: a reasoned implication that is not itself asserted by an
  authoritative source.

## Core rules

1. Determine the fact type before selecting authority.
2. Use only sources approved for that fact type and required scope.
3. Applicability outranks recency. A newer source for the wrong model,
   configuration, location, or workflow does not outrank an applicable source.
4. Explicit supersession outranks simple recency.
5. When applicability is equivalent and no explicit supersession applies, the
   newer authoritative information generally outranks older information.
6. Dynamic state must come from its current operational system of record.
   Historical copy and technical documents cannot establish current price,
   inventory, shipping, or order state.
7. Static technical authority remains authoritative for technical facts.
   Catalog or operational state cannot establish installation requirements,
   safety requirements, or manufacturer compatibility.
8. Availability does not imply compatibility, and compatibility does not
   imply availability.
9. Approved IRG mappings must remain distinguishable from manufacturer claims.
10. Inference and synthesis must never silently become authority.
11. If required authority is unavailable or an applicable conflict remains
    unresolved, do not fabricate a resolution.

## Source eligibility gate

Before a concrete source can occupy an authority class, its governing contract
must establish, as applicable:

- source identity and system ownership;
- fact-type approval;
- product, model, revision, configuration, store, location, customer, and
  workflow scope;
- freshness or effective-date semantics;
- lineage and update ownership;
- permission to access and disclose the fact;
- traceable source or record identity; and
- failure behavior when the source is unavailable or ambiguous.

If these conditions are not satisfied, the source may retain a separately
approved discovery or context role, but it is not promoted by this policy. For
example, an operational-looking field with unproven freshness remains
operational context rather than final price or availability authority.

## Authority classes

### A. Manufacturer Technical Authority

Applicable manufacturer installation manuals, owner manuals, specification
sheets, parts schedules, service manuals, safety and warning documents,
technical bulletins, and revision notices are primary authority for:

- dimensions, clearances, capacities, and ratings;
- electrical, gas, ventilation, and installation requirements;
- technical part numbers and procedures;
- safety warnings and manufacturer restrictions;
- manufacturer-declared compatibility and fitment; and
- manufacturer technical specifications.

Document identity, model/configuration applicability, revision, and any
explicit supersession must be preserved. Manufacturer authority does not
establish IRG's current price, stock, fulfillment, or catalog state.

### B. IRG Product and Catalog Authority

The approved current structured product/catalog system is primary authority
for IRG-specific product state, including:

- whether IRG currently carries or lists a product;
- current internal product identity and governed SKU/model mappings;
- enabled, disabled, or other approved catalog lifecycle state;
- store and category assignment; and
- current merchandising metadata.

This class does not establish manufacturer technical facts. Store, language,
variant, and refresh scope must be proven before making scoped claims.

### C. Commerce and Pricing Authority

The approved current commerce/pricing system is primary authority for:

- current selling and sale price;
- active promotion;
- store-specific price;
- configured discounts; and
- the current pricing-engine result.

Static manuals, PDFs, product copy, cached exports, and historical prices may
not override the current commerce authority. Taxes, customer-specific terms,
and checkout totals require their own applicable scope.

### D. Inventory Authority

The approved live inventory/availability system is primary authority for:

- current stock state;
- stock quantity; and
- location-specific availability.

Quantity is disclosure-sensitive even when authoritative. It must not be
volunteered merely because it is available. Surface quantity only when the
user explicitly asks for it or when it is directly necessary to answer the
broader operational task. Otherwise answer at the minimum useful availability
level.

### E. Shipping and Fulfillment Authority

The approved current shipping, pricing, and fulfillment engine is primary
authority for:

- shipping charge and free-shipping qualification;
- remote-region handling;
- local delivery or pickup eligibility;
- shipping-category logic; and
- fulfillment restrictions.

Do not infer these facts from catalog categories, product copy, manuals, or
historical orders when the authoritative engine exists.

### F. Order Authority

The approved order-management or commerce order system is primary authority
for order status, payment state, fulfillment state, order-level events, and
transaction state. Access and disclosure must be scoped to the authorized
order and user.

### G. Returns, Warranty, and CRM Authority

The relevant approved operational system of record is primary authority for
return status, warranty-claim status, approvals, customer case state, and
workflow ownership. Manufacturer warranty terms may define general coverage,
but the operational system governs the current state of a specific IRG case or
claim.

### H. Approved IRG Mapping Authority

An explicitly governed IRG mapping may establish an IRG-specific relationship
when manufacturer evidence alone is insufficient, including:

- approved compatibility mappings;
- internal model aliases;
- operational crosswalks; and
- normalized SKU/model relationships.

The mapping must be explicit, traceable, distinguishable from source evidence,
and versioned where practical. Its effective scope and owner must be known. An
IRG mapping must be presented as an IRG-approved mapping, never as a
manufacturer statement.

## Fact-type authority matrix

`None` in the secondary column is intentional. A convenient source is not a
legitimate fallback merely because the primary source is unavailable.

| Fact type | Primary authority | Secondary authority | Conflict behavior |
| --- | --- | --- | --- |
| Technical specification | Applicable Manufacturer Technical Authority | None by default; an approved mapping may normalize identity but not invent or override the value | Select the applicable model/revision; then explicit supersession; then recency. Otherwise report an unresolved conflict. |
| Dimensions | Applicable Manufacturer Technical Authority | None | Do not use catalog dimensions to override applicable technical documentation. Resolve by applicability, supersession, then recency. |
| Installation requirement | Applicable Manufacturer Technical Authority | None | Never synthesize a requirement across models or configurations. Ask for the discriminator or state the conflict. |
| Safety warning | Applicable Manufacturer Technical Authority | None | Preserve applicable warnings. If two applicable warnings differ and supersession cannot be proven, use the safer non-actionable posture and escalate; do not choose silently. |
| Part number | Applicable manufacturer parts schedule/service documentation | Approved IRG alias or crosswalk, clearly labeled | Preserve manufacturer part identity and distinguish an IRG alias. Resolve model/revision scope before recency. |
| Manufacturer compatibility | Explicit applicable manufacturer evidence | None | Only an explicit manufacturer statement can establish a manufacturer compatibility claim. Similarity and catalog association do not count. |
| IRG-approved compatibility | Approved IRG Mapping Authority | Applicable manufacturer evidence as context, not as attribution for the IRG mapping | Identify the claim as IRG-approved. If the mapping conflicts with manufacturer evidence, do not claim manufacturer approval; follow the fail-closed rule in `OPEN_POLICY_DECISIONS`. |
| Current price | Commerce/Pricing Authority | None | Current scoped commerce state wins. Static or historical prices are not fallback authority. |
| Current promotion | Commerce/Pricing Authority | None | Require current effective dates, store/customer scope, and promotion conditions. If unavailable, do not infer. |
| Inventory availability | Inventory Authority | None | Use current location scope. Catalog active state and prior inventory snapshots do not establish availability. |
| Stock quantity | Inventory Authority | None | Use current location scope and disclose only when requested or materially necessary. Conflicting live records require operational resolution. |
| Product active/discontinued state | IRG Product/Catalog Authority for IRG carrying/listing state; Manufacturer Technical Authority for a manufacturer discontinuation claim | None unless a separately approved lifecycle crosswalk exists | State which lifecycle is meant. Manufacturer discontinuation and IRG active status are different facts and may both be true. |
| Shipping charge | Shipping/Fulfillment Authority | None | Use the current engine result for the exact cart, destination, store, and fulfillment method. Do not infer from catalog text. |
| Free-shipping status | Shipping/Fulfillment Authority | None | Use the current engine result and conditions. Promotional copy cannot override the computed scoped result. |
| Store-specific product state | Store-scoped IRG Product/Catalog Authority | None | Do not generalize an unscoped or different-store record. Ask which store when needed. |
| Order status | Order Authority | None | Use the authorized current order record. Historical messages may provide context but do not override current state. |
| Return status | Returns/CRM Authority | None | Use the current authorized case or return record. Policy documents define rules, not the current case state. |
| Warranty status | Warranty/CRM Authority for a specific claim; applicable manufacturer/IRG warranty terms for general coverage | The other named class only for its distinct fact type | Distinguish general coverage terms from the state or approval of a specific claim. Do not infer approval from eligibility language. |

## Temporal authority

The temporal rule is:

> Applicability outranks recency. When applicability is equivalent, newer
> authoritative information generally outranks older information.

Apply the rule in this order:

1. **Fact-type authority**: compare only sources authorized for the fact being
   answered.
2. **Applicability**: select the source matching the actual product, model,
   revision, configuration, store, location, order, customer, and other needed
   scope.
3. **Explicit supersession**: if an applicable authoritative source explicitly
   supersedes another, the superseding source wins.
4. **Equivalent-scope recency**: if applicability is equivalent and no explicit
   supersession applies, the newer authoritative source generally wins.
5. **Unresolved applicability or chronology**: do not choose silently. State
   the conflict or request the practical discriminator.

Dynamic operational or commercial state outranks historical static data only
for dynamic facts. It does not outrank manufacturer authority for technical
facts. Examples:

- current price does not come from an old PDF;
- current inventory does not come from a static document;
- technical clearance does not come from the product database when an
  applicable manufacturer manual governs it; and
- a newer manual for a different configuration does not outrank the applicable
  older manual.

## Conflict classifications

Authority selection and observability may record one of these classifications:

- `NO_CONFLICT`
- `RESOLVED_BY_APPLICABILITY`
- `RESOLVED_BY_EXPLICIT_SUPERSESSION`
- `RESOLVED_BY_RECENCY`
- `RESOLVED_BY_FACT_TYPE_AUTHORITY`
- `UNRESOLVED_CONFLICT`

These are internal classifications, not required user-facing wording.

For `UNRESOLVED_CONFLICT`:

1. do not fabricate a resolution;
2. identify the differing values or instructions clearly when safe and useful;
3. identify or request the practical discriminator, such as model, serial
   range, fuel type, revision, store, location, or order;
4. avoid action-guiding advice when the unresolved conflict is safety
   sensitive; and
5. offer a proportionate human or system-of-record check when it can resolve
   the issue.

A natural response is preferred: "I have two applicable values and can't tell
which one applies without the fuel type." Internal source-selection labels
should not be exposed unless the audience explicitly needs diagnostic detail.

## Static and dynamic data

### Static or semi-static

- manuals;
- specification sheets;
- parts schedules;
- installation and service documents;
- technical bulletins and revision notices; and
- approved technical or operational mappings.

These remain subject to model, configuration, revision, and effective-scope
checks.

### Dynamic

- pricing and promotions;
- inventory and availability;
- IRG product active/store state;
- shipping and fulfillment;
- orders and payments; and
- returns, warranty claims, and workflow state.

Dynamic facts must come from approved current operational systems. Price,
stock, shipping, and order state must not be inferred from document evidence.
Dynamic availability does not establish technical compatibility; technical
compatibility does not establish current availability.

## Inferred and synthesized information

Inference is not a new authority class. A synthesis may combine independently
authoritative facts across classes when the relationship is useful and safe,
but it must preserve each fact's scope and must not imply that one source owns
another source's fact.

An inference may be communicated only when:

- its supporting facts are authoritative and applicable;
- it is clearly distinguished from established fact when that distinction is
  material;
- it does not substitute for unavailable authority; and
- it is not used to decide safety, compatibility, ordering, installation, or
  another high-consequence action that requires confirmation.

Similarity is not compatibility. Catalog association is not manufacturer
approval. Availability is not fitment. A historical order is not current
inventory.

## Missing or unavailable authority

When the required authoritative source is unavailable, inaccessible, out of
scope, stale beyond its approved semantics, or absent:

- do not use an unauthorized source as a silent fallback;
- answer any independently confirmable portion;
- state the missing detail in natural language;
- avoid narrating retrieval, table, database, or pipeline mechanics; and
- offer a next step only when it is useful in context.

Preferred patterns include:

- "I don't have that exact information."
- "I have information on the part, but not that specific detail."
- "I can't confirm that from the information available to me."
- "I don't have enough information to determine which one applies."

Internal telemetry may classify the condition as `MISSING_AUTHORITY`,
`INSUFFICIENT_EVIDENCE`, or `UNRESOLVED_DISCRIMINATOR`. Those labels must not
be substituted for natural user-facing language.

## Human handoff

Offer human escalation when it can materially resolve the task, including
when:

- the required authority is unavailable;
- an applicable conflict cannot be resolved;
- a safety-sensitive decision remains ambiguous;
- current operational data is unavailable;
- the user asks for confirmation by a person; or
- access or permission limitations prevent completion.

Handoff must be contextual and proportionate. Do not offer sales or technical
follow-up for every unknown. Identify the most relevant team, system owner, or
manufacturer source only when known and useful. Do not promise a handoff
mechanism that is not integrated.

## Traceability and observability

Authority decisions should remain machine traceable even when the prose is
natural. Observability may record source class, source identity, scope,
freshness, conflict classification, selected authority, missing-authority
reason, and handoff outcome. Citation and trace records do not themselves
become authority.

Evaluation metadata, retrieval rank, benchmark labels, gold answers, response
modes, and diagnostic fields are not answer authority. They may measure or
explain behavior in their own lane but must not silently supply facts.

## OPEN_POLICY_DECISIONS

1. **IRG mapping conflict precedence**: define the business-owner workflow for
   an approved IRG compatibility mapping that directly conflicts with
   applicable manufacturer evidence. Until decided, fail closed for action,
   disclose the conflict naturally, and never represent the IRG mapping as
   manufacturer approval.
2. **Automatic dynamic timestamps**: decide which operational contexts, if any,
   should show source timestamps automatically rather than only when freshness
   is material or requested.

These open decisions do not authorize runtime behavior. Related response-level
decisions are listed in `IRG_RESPONSE_POLICY_V1.md`.

## Activation boundary

This policy does not alter the current serving path or promote any source. A
future implementation must separately version and validate source bindings,
failure behavior, prompts, evaluation, observability, and rollback before any
activation.
