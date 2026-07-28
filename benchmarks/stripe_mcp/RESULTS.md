# Stripe OpenAPI Benchmark Results

Typed composition search (TCS) evaluated against the [Stripe OpenAPI spec](https://github.com/stripe/openapi) tool surface: **536 tools** derived from 414 API paths across payments, billing, connect, issuing, treasury, and more. The 536 operations collapse into **163 entity types**. 42 benchmark queries across 5 categories, evaluated with Qwen3-14B.

Rather than making the model better at selecting from hundreds of tools, we change the representation so it reasons over entity types instead.

## The scale problem

With 536 tools, encoding the complete tool surface as function schemas produces ~28,095 prompt tokens. While still executable for Qwen3-14B (40,960 token context), this consumes 69% of the context window before any query is processed. TCS reduces the prompt to ~1,839 tokens — a 15.3x reduction.

| Representation       | Elements          | Prompt Tokens | Executable |
|----------------------|:-----------------:|:------------:|:----------:|
| Function schemas     | 536 tools         | 28,095       | Yes        |
| Tool descriptions    | 536 tools         | 8,618        | Yes        |
| Entity types (TCS)   | 163 types         | 1,839        | Yes        |

## How the benchmark was built

### Where do the tools come from?

The tools are derived from the official Stripe OpenAPI specification (`spec3.json`). The parser reads the JSON spec and extracts every operation with its path, HTTP method, operationId, and response schema reference.

| Domain          | Operations | Examples                                       |
|-----------------|:----------:|-------------------------------------------------|
| Payments        | ~80        | Charges, PaymentIntents, Refunds, Disputes      |
| Billing         | ~50        | Subscriptions, Invoices, Prices, Coupons        |
| Connect         | ~60        | Accounts, Transfers, Payouts, Capabilities      |
| Issuing         | ~50        | Cards, Authorizations, Cardholders, Transactions|
| Treasury        | ~40        | Financial accounts, Inbound/outbound transfers  |
| Other           | ~256       | Terminal, Tax, Identity, Climate, Radar, etc.   |
| **Total**       | **536**    |                                                 |

Each operation becomes a typed tool edge: `tool(input_types) -> output_types`. For example, `GetCustomersCustomerPaymentMethods` takes a `Customer` and produces `PaymentMethod`. The 1,431 OpenAPI schema components collapse to 163 canonical entity types through deterministic heuristics (e.g., `deleted_account` maps to `DeletionResult`, path singularization maps `customers/{id}` to `Customer`).

### How was the composition graph constructed?

The graph was built using **deterministic heuristics only** — no LLM was involved in graph construction. The parser infers entity types from:

- **Path structure:** `/v1/customers/{customer}/payment_methods` implies `Customer -> PaymentMethod`
- **HTTP method:** `GET` on collection path = list, `GET` with `{id}` = retrieve, `POST` = create/action, `DELETE` = destroy
- **Response schema references:** `$ref` in the response schema identifies the output entity type
- **Singularization:** Plural path segments (e.g., `customers`) are singularized when followed by an `{id}` parameter

### Were the queries designed to match the graph?

No. The graph and queries were constructed in separate phases. The graph was built from the OpenAPI spec without knowledge of what queries would be asked. Queries were written from representative payment platform workflows — managing customers, processing payments, handling subscriptions, issuing refunds. After both were finalized, queries were annotated with expected tools by running the graph as oracle.

## Results: TCS (type prediction + graph search) vs Direct Tool Selection

Three approaches were evaluated:

1. **TCS (type prediction + graph search):** The LLM receives a list of 163 entity types with short descriptions and predicts a source and target type for the query (~1,839 prompt tokens). Graph search then finds the tool chain connecting those types. The LLM does type classification, not tool selection.
2. **Text baseline (direct tool selection):** The LLM receives all 536 tools listed as text lines in the format `- tool_name: (input_types) → (output_types)` (~8,618 prompt tokens) and selects tools by name.
3. **Function-calling baseline:** All 536 tools provided as function schemas with parameter definitions (~28,095 prompt tokens). The LLM uses native tool-calling.

### Overall metrics

| Metric              | Text Baseline | Function Calling | TCS        |
|---------------------|:------------:|:----------------:|:----------:|
| F1                  | **0.79**     | 0.76             | 0.74       |
| Precision           | 0.79         | 0.76             | 0.74       |
| Recall              | 0.79         | 0.76             | 0.74       |
| Exact match         | 79% (33/42)  | 76% (32/42)      | —          |
| Hallucinated tools  | 0            | 0                | **0**      |
| Avg prompt tokens   | 8,618        | 28,095           | **1,839**  |

### Per-category F1

| Category  | Queries | Text Baseline | Function Calling | TCS        |
|-----------|:-------:|:------------:|:----------------:|:----------:|
| clean     | 20      | **0.95**     | 0.90             | 0.85       |
| multihop  | 7       | **0.86**     | **0.86**         | **0.86**   |
| synonym   | 7       | 0.43         | 0.29             | **0.71**   |
| noisy     | 5       | 0.80         | **1.00**         | 0.40       |
| ambiguous | 3       | 0.33         | 0.33             | 0.33       |

### TCS type prediction accuracy

| Metric           | Qwen3-14B       |
|------------------|:---------------:|
| Source accuracy   | 83% (35/42)     |
| Target accuracy   | 83% (35/42)     |
| Exact match       | 74% (31/42)     |
| Path found        | 88% (37/42)     |

Unlike other TCS benchmarks where target accuracy exceeds source accuracy, Stripe shows equal accuracy (83%) for both. The financial domain's entity names (PaymentIntent, BalanceTransaction, CustomerBalanceTransaction) require precise disambiguation that challenges both predictions equally.

### Recall decomposition

End-to-end recall can be decomposed into two independent factors — model quality and graph robustness:

```
Recall_e2e = P(types correct) x Recall_correct + P(types wrong) x Recall_wrong
```

| Component          | Qwen3-14B |
|--------------------|:---------:|
| P(types correct)   | 0.74      |
| P(types wrong)     | 0.26      |
| Recall_correct     | 1.000     |
| Recall_wrong       | 0.000     |
| **Predicted recall** | **0.738** |
| **Actual recall**    | **0.738** |
| Gap                | 0.000     |

**When types are correct, recall is perfect (1.000).** The graph covers all 42 queries.

**The decomposition fits exactly (gap = 0.000).** End-to-end recall is fully explained by type prediction accuracy and graph reachability.

**Recall_wrong = 0.000.** Unlike the K8s MCP benchmark (Recall_wrong = 0.222) or the smaller benchmark domains (avg Recall_wrong = 0.415), the Stripe graph is sparse enough that wrong type predictions never accidentally recover the correct tools. This means type prediction accuracy directly determines end-to-end performance — improving the type classifier is the primary vector for improving TCS on this domain.

## Observations

**Text baseline outperforms TCS on clean queries.** At 536 tools, Qwen can still scan the full text tool list effectively. The text baseline achieves 0.95 F1 on clean queries vs 0.85 for TCS. The TCS failures on clean queries are source type errors (e.g., predicting `Payout→BankAccount` instead of `Platform→Payout`).

**TCS outperforms both baselines on synonym queries.** TCS achieves 0.71 F1 on synonyms vs 0.43 (text) and 0.29 (function calling). Entity type classification handles informal terminology better than direct tool name matching — "chargebacks" maps to `Dispute` more reliably than scanning 536 operationIds for `GetDisputes`.

**Token efficiency.** TCS uses 1,839 avg prompt tokens vs 8,618 for the text baseline (4.7x reduction) and 28,095 for function calling (15.3x reduction). At 536 tools, function-calling schemas consume 69% of Qwen3-14B's context window.

**Zero hallucinations under TCS.** All three strategies produced zero hallucinated tool names on this domain. At larger scale (AAP, 1,060 tools), the text baseline produces 2–3 hallucinated tools per run while TCS remains at zero by construction.

**Multi-hop performance is identical.** All three strategies achieve 0.86 F1 on multihop queries. The Stripe API has shallow composition depth — most sub-resource queries are single-edge traversals.

## TCS failure modes

### Qwen3-14B: 11 of 42 queries (26%) with wrong tools

- **Source/target confusion (4 queries):** "show all payouts to the bank account" → `Payout→BankAccount` instead of `Platform→Payout`. The model interprets the destination as target type. "List all bank transfers" → `Transfer→Transfer` instead of `Platform→Payout`. "Show all open disputes" → `Dispute→Dispute` (self-loop) instead of `Platform→Dispute`.
- **Wrong entity granularity (3 queries):** "balance transactions for a customer" → `Customer→BalanceTransaction` instead of `Customer→CustomerBalanceTransaction`. Stripe distinguishes platform-level `BalanceTransaction` from `CustomerBalanceTransaction` — the model misses this distinction.
- **Noisy query misinterpretation (2 queries):** Conversational context misleads source type. "A customer is complaining they didn't get their refund" → `Customer→Refund` instead of `Platform→Refund`. "Check which customers have active subscriptions" → `Subscription→Customer` (reversed) instead of `Platform→Subscription`.
- **Ambiguous queries (2 queries):** Expected failures on intentionally ambiguous queries.

All failures are type prediction errors. The graph structure covers all 42 queries — confirmed by R_correct = 1.000.

## Threats to validity

- **Automatic graph construction.** Entity types inferred from path structure and response schemas. The parser may miss semantic relationships not encoded in the URL hierarchy (e.g., invoices are linked to customers via query parameters, not URL nesting).
- **Single model evaluated.** Results are from Qwen3-14B only. Additional models would strengthen generalization claims.
- **Query set size.** 42 queries across 5 categories.
- **test_helpers excluded.** 51 test helper operations were filtered out as non-production tools, reducing the tool surface from 587 to 536.
- **Routing only.** The benchmark evaluates routing quality (selecting the correct tools), not end-to-end task execution against a live Stripe API.

## Reproducibility

```bash
# Download spec
curl -sL https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json \
  -o /tmp/stripe_spec3.json

# TCS (type prediction + graph search)
SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.run_benchmark --domain stripe_mcp qwen

# Text baseline (direct tool selection)
SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.run_baseline --domain stripe_mcp qwen

# Function-calling baseline (native tool use)
SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.run_baseline_tools --domain stripe_mcp qwen
```

## Configuration

| Parameter         | Value                                    |
|-------------------|------------------------------------------|
| Model             | Qwen3-14B                                |
| Tools in registry | 536                                      |
| Entity types      | 163                                      |
| Benchmark queries | 42                                       |
| Source             | stripe/openapi spec3.json                |
