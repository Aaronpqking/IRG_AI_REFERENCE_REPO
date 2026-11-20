<!-- Text transfer from https://docs.google.com/document/d/1TO4S81IuOz-XuCjrqobbA8KeLRXyxhpW/edit; original byte hash not certified. Historical candidate, not active runtime. -->

# Product DB Field Authority

Field authority is discovery-only unless lineage, upstream source, scope, and freshness are proven. `product_id` is authoritative only as a reproducible row key within `product_details`.

`product_description`, `attributes`, `categories`, and `filters` may be used as catalog context because they come from the OpenCart selling surface and can materially improve product identification, clarification, customer-friendly wording, and PDF retrieval enrichment. They are not manufacturer technical authority unless a field-level source record proves the originating manual, page, and source excerpt.

`price`, `stock_status`, and `quantity_on_stock` are available from the live stored procedure and may be exposed as freshness-sensitive operational context. They must not be used as customer-facing price or availability promises unless freshness, store scope, and operational source semantics are proven.

| Column | Meaning | Source/Lineage | Scope | Authority | Approved Use | Prohibited Use | Citation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `product_id` | Read-model row key | Upstream mapping unknown | Store/language/variant unknown | AUTHORITATIVE_WITH_SCOPE | Row identity for citations and deterministic fetches | Claim OCM/storefront authority | Required row key |
| `model` | Product model text | Unknown | Unknown | SEARCH_DISCOVERY_ONLY | Candidate discovery, display with citation | Assume unique or authoritative | Field citation required |
| `mpn` | Manufacturer part number text | Unknown | Unknown | SEARCH_DISCOVERY_ONLY | Candidate discovery, exact-match candidate lookup | Assume unique or authoritative | Field citation required |
| `upc` | UPC text | Unknown | Unknown; 3,626 blanks | SEARCH_DISCOVERY_ONLY | Candidate discovery when nonblank | Assume coverage or uniqueness | Field citation required |
| `product_name` | Product display name | Unknown | Unknown | DISPLAY_ONLY | Candidate display | Technical authority | Field citation required |
| `product_description` | Product description/free text | OpenCart catalog/read model; manual lineage unverified | Store/language/variant unknown | CATALOG_CONTEXT | Candidate search, display excerpt, customer-service context, PDF retrieval enrichment | Standalone technical authority, warnings, clearances, procedures | Excerpt/digest; source/page required for manual-derived authority |
| `stock_status` | Stock status label | OpenCart catalog/read model; freshness unverified | Store/language/variant unknown | OPERATIONAL_CONTEXT_UNVERIFIED | Staff-visible operational context, candidate display, filtering | Availability promise or fulfillment commitment | Field citation plus freshness caveat |
| `quantity_on_stock` | Quantity value | OpenCart catalog/read model; freshness unverified | Store/language/variant unknown | OPERATIONAL_CONTEXT_UNVERIFIED | Staff-visible operational context when labeled freshness-sensitive | Availability promise, stock guarantee, checkout commitment | Field citation plus freshness caveat |
| `path_to_product_image` | Image path | Unknown | Unknown | DISPLAY_ONLY | Candidate display after URL policy review | Product authority | Field citation required |
| `brand` | Brand/manufacturer display text | Unknown | Unknown | DISPLAY_ONLY | Candidate display/search | Override manufacturer PDFs | Field citation required |
| `price` | Price value | OpenCart catalog/read model; freshness unverified | Store/language/variant unknown | OPERATIONAL_CONTEXT_UNVERIFIED | Staff-visible operational context when labeled freshness-sensitive | Price quote, final sale price, promotion/tax/shipping promise | Field citation plus freshness caveat |
| `product_status` | Product status label | Unknown | Unknown | AUTHORITATIVE_WITH_SCOPE | Filter/display Active/Disabled with citation | Discontinued/delete semantics | Field citation required |
| `attributes` | Concatenated attribute text | OpenCart catalog/read model; per-attribute manual lineage unverified | Store/language/variant unknown | CATALOG_CONTEXT | Candidate discovery, display excerpt, retrieval enrichment, customer-service context | Standalone compatibility/fitting proof or safety claim | Excerpt/digest; source/page required for manual-derived authority |
| `categories` | Concatenated category text | OpenCart taxonomy/read model | Store/language/variant unknown | CATALOG_CONTEXT | Candidate discovery, merchandising context, retrieval enrichment | Compatibility proof or technical product classification without corroboration | Excerpt/digest; taxonomy provenance recommended |
| `filters` | Concatenated filter text | OpenCart filter/read model | Store/language/variant unknown | CATALOG_CONTEXT | Candidate discovery, faceted context, retrieval enrichment | Compatibility proof, fitment proof, safety or installation authority | Excerpt/digest; taxonomy provenance recommended |
| `product_valid_combinations.main_product_id` | Website configuration owner | Daily website/catalog configuration read model | Active website products; relationship may be orphaned | CURRENT_WEBSITE_CONFIGURATION_AVAILABILITY | Join only after unique `product_details.product_id` resolution | Model-only join or product identity discovery | Product ID plus retrieval timestamp |
| `product_valid_combinations.configuration_id` | Complete configuration group identity; adapter alias over an allowlisted physical spelling | Daily website/catalog configuration read model | One product; snapshot-scoped | CURRENT_WEBSITE_CONFIGURATION_AVAILABILITY | Group complete option rows and cite the observed group | Treat a partial/truncated group as complete or stable across refreshes | Product ID, configuration ID, snapshot digest |
| `product_valid_combinations.option_name` / `option_value_description` / `valid_combination` | Original website option labels, values, and codes | Daily website/catalog configuration read model | Complete configuration group | CURRENT_WEBSITE_CONFIGURATION_AVAILABILITY | Observe whether requested selections coexist in one offered group | Engineering compatibility, safety, installation, inventory, or manufacturer approval | Original values, group ID, retrieval timestamp |

Rules:

- Manufacturer PDFs remain authoritative for installation, warnings, clearances, wiring, servicing, safety procedures, and manufacturer-defined compatibility.
- Product database text must not override explicit manufacturer technical evidence.
- Catalog context fields may be included in retrieval enrichment and staff-visible candidate context when labeled as catalog context.
- Catalog context fields become manual-derived authority only when field-level provenance records the manual/source, page, excerpt or chunk, match method, and verification status.
- Model and MPN duplicates exist; exact lookup must surface ambiguity.
- Categories, filters, and attributes cannot prove compatibility unless corroborated by manufacturer PDF evidence or verified field-level provenance.
- Price, stock status, and quantity may be displayed only as freshness-sensitive operational context. Customer-facing price quotes and availability commitments require proven freshness, store scope, and operational source semantics.
- Website configuration presence/absence remains observe-only until the controlled activation gate is separately approved. It must not change or qualify delivered answers in the current integration.
