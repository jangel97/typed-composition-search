# Shopify Benchmark Domain

Benchmark domain derived from the **Shopify Admin REST API** documentation at
[shopify.dev/docs/api/admin-rest](https://shopify.dev/docs/api/admin-rest).

## Why Shopify

The other four benchmark domains (Kubernetes, Ansible, GitHub, CI/CD) are all
DevOps/infrastructure APIs. Shopify adds an **e-commerce** domain, making it
harder to argue that typed composition search only works for one API family.

## Construction methodology

### 1. Resource inventory

We started from the official REST Admin API reference and identified every
documented resource group. Each resource maps to one or more entity types in
the composition graph.

### 2. Endpoint-to-tool mapping

For each resource we read the endpoint list on shopify.dev and created one tool
per documented endpoint. Tool descriptions include the real HTTP method and
path (e.g. `GET /admin/api/products/{id}/variants.json`) so that every tool is
traceable back to the API documentation.

The following resources were cross-checked against the live docs on 2026-06-25:

| Resource | Docs URL | Endpoints mapped |
|----------|----------|-----------------|
| Product | [product](https://shopify.dev/docs/api/admin-rest/latest/resources/product) | list, get, create, update, delete, count |
| Product Variant | [product-variant](https://shopify.dev/docs/api/admin-rest/latest/resources/product-variant) | list, get, create, update, delete, count |
| Product Image | [product-image](https://shopify.dev/docs/api/admin-rest/latest/resources/product-image) | list, get, create, delete, count |
| Custom Collection | [customcollection](https://shopify.dev/docs/api/admin-rest/latest/resources/customcollection) | list, get, create, update, delete, count |
| Smart Collection | [smartcollection](https://shopify.dev/docs/api/admin-rest/latest/resources/smartcollection) | list, get, create, update, delete |
| Collect | [collect](https://shopify.dev/docs/api/admin-rest/latest/resources/collect) | list (by collection_id) |
| Customer | [customer](https://shopify.dev/docs/api/admin-rest/latest/resources/customer) | list, search, get, create, update, delete, count |
| Customer Address | [customer-address](https://shopify.dev/docs/api/admin-rest/latest/resources/customer-address) | list, get, create, delete |
| Order | [order](https://shopify.dev/docs/api/admin-rest/latest/resources/order) | list, get, create, update, close, cancel, count |
| Draft Order | [draftorder](https://shopify.dev/docs/api/admin-rest/latest/resources/draftorder) | list, get, create, update, delete, complete, count |
| Transaction | [transaction](https://shopify.dev/docs/api/admin-rest/latest/resources/transaction) | list, get, create, count |
| Refund | [refund](https://shopify.dev/docs/api/admin-rest/latest/resources/refund) | list, get, create |
| Fulfillment | [fulfillment](https://shopify.dev/docs/api/admin-rest/latest/resources/fulfillment) | list, get, create, cancel, update_tracking, count |
| Fulfillment Order | [fulfillmentorder](https://shopify.dev/docs/api/admin-rest/latest/resources/fulfillmentorder) | list, get |
| Fulfillment Event | [fulfillmentevent](https://shopify.dev/docs/api/admin-rest/latest/resources/fulfillmentevent) | list |
| Inventory Item | [inventoryitem](https://shopify.dev/docs/api/admin-rest/latest/resources/inventoryitem) | get, update |
| Inventory Level | [inventorylevel](https://shopify.dev/docs/api/admin-rest/latest/resources/inventorylevel) | list, set, adjust |
| Location | [location](https://shopify.dev/docs/api/admin-rest/latest/resources/location) | list, get, inventory_levels, count |
| Price Rule | [pricerule](https://shopify.dev/docs/api/admin-rest/latest/resources/pricerule) | list, get, create, update, delete, count |
| Discount Code | [discountcode](https://shopify.dev/docs/api/admin-rest/latest/resources/discountcode) | list, get, create, delete, count, lookup |
| Blog | [blog](https://shopify.dev/docs/api/admin-rest/latest/resources/blog) | list, get, create, update, delete |
| Article | [article](https://shopify.dev/docs/api/admin-rest/latest/resources/article) | list, get, create, update, delete, count |
| Page | [page](https://shopify.dev/docs/api/admin-rest/latest/resources/page) | list, get, create, update, delete, count |
| Theme | [theme](https://shopify.dev/docs/api/admin-rest/latest/resources/theme) | list, get |
| Asset | [asset](https://shopify.dev/docs/api/admin-rest/latest/resources/asset) | list, get, update, delete |
| Webhook | [webhook](https://shopify.dev/docs/api/admin-rest/latest/resources/webhook) | list, get, create, update, delete, count |
| Event | [event](https://shopify.dev/docs/api/admin-rest/latest/resources/event) | list, get, count |
| Metafield | [metafield](https://shopify.dev/docs/api/admin-rest/latest/resources/metafield) | list (per product/customer/order), get, create, delete, count |
| Report | — | list, get (deprecated since REST API 2024-04) |
| Carrier Service | [carrierservice](https://shopify.dev/docs/api/admin-rest/latest/resources/carrierservice) | list, get |
| Shop | [shop](https://shopify.dev/docs/api/admin-rest/latest/resources/shop) | get |

### 3. Graph construction

Each tool is registered with typed inputs and outputs. The types encode the
real nesting relationships from the API (e.g. `Product` → `VariantList` →
`ProductVariant` → `InventoryItem` → `InventoryLevelList`).

Intermediate "list" types (e.g. `ProductList`, `VariantList`) and "select"
tools bridge one-to-many relationships, matching how the API requires listing a
collection and then fetching a specific item by ID.

### 4. Query design

29 queries across 6 categories, modelled on realistic e-commerce operations:

| Category | Count | Description |
|----------|-------|-------------|
| clean | 10 | Straightforward single-resource operations |
| ambiguous | 3 | Underspecified queries with multiple valid interpretations |
| multihop | 6 | Chains through 3–5 tools across multiple resources |
| synonym | 4 | Alternative terminology (e.g. "coupons" → discount codes, "SKUs" → variants) |
| noisy | 4 | Casual/messy real-world phrasing |
| multipath | 2 | Multiple valid graph paths to the answer |

Expected tools are aligned to the BFS-shortest path in the composition graph
so that the oracle benchmark achieves F1 = 1.0 on all queries.

## Key statistics

| Metric | Value |
|--------|-------|
| Tools | 170 |
| Entity types | 61 |
| Graph nodes | 102 |
| Graph edges | 170 |
| Queries | 29 |
| Graph diameter | 7 |
| Max query path length | 5 |
| Oracle pruning | 99% |

## Notes

- The Shopify REST Admin API was designated legacy on 2024-10-01, with new apps
  required to use the GraphQL Admin API from 2025-04-01. The REST endpoints
  remain documented and the resource structure is unchanged, making it a valid
  reference for our benchmark.
- The Report resource was deprecated in REST API version 2024-04. We include it
  because it was a documented resource at the time of API design.
- The `discount_codes/lookup.json` endpoint is marked deprecated but still
  documented.
- Not every endpoint for every resource is included (e.g. `send_invoice` for
  draft orders, `calculate` for refunds). We focused on the core CRUD
  operations and the key composition chains that exercise multi-hop graph
  traversal.
