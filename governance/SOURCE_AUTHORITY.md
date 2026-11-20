# Fact-specific source authority

The historical authority policy preserved at [historical/IRG_AUTHORITY_POLICY_V1.md](historical/IRG_AUTHORITY_POLICY_V1.md) is explicitly **POLICY_ONLY_NOT_ACTIVATED**. This document synthesizes durable authority principles; it does not retroactively activate that policy.

| Fact class | Candidate primary authority | Mandatory scope |
|---|---|---|
| Product/catalog identity | governed read-only product data | SKU/model/store/lifecycle |
| Technical specification | approved applicable manufacturer document | model/fuel/year/config/revision |
| Installation procedure/warnings | approved applicable manufacturer document | exact model/config/revision |
| Manufacturer compatibility | explicit applicable technical evidence | products/config/revision |
| Approved internal alias/crosswalk | explicitly governed mapping | owner/version/effective dates |
| Current price/promotion | live commerce pricing authority | store/customer/time |
| Inventory | live authorized inventory authority | location/time |
| Shipping charge | live checkout/shipping authority | cart/address/time/config |
| Order/returns/warranty state | permitted operational system | authorized record/user/time |

## Rules
- Applicability outranks generic recency.
- Explicit supersession outranks publication date alone.
- Product identity authority does not automatically confer technical-claim authority.
- Manufacturer technical evidence does not establish dynamic commerce, inventory, shipping, or order state.
- Catalog descriptions must not be treated as installation instructions.
- Missing or conflicting authority triggers clarification, abstention, or escalation.

## Historical local support
See [historical/PRODUCT_DB_FIELD_AUTHORITY.md](historical/PRODUCT_DB_FIELD_AUTHORITY.md), [historical/IRG_AUTHORITY_POLICY_V1.md](historical/IRG_AUTHORITY_POLICY_V1.md), and the authority/provenance ADRs under [../decisions/historical/](../decisions/historical/).
