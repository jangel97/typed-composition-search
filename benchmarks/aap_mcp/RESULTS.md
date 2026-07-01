# AAP MCP Server Benchmark Results

Typed composition search (TCS) evaluated against the real [ansible/aap-mcp-server](https://github.com/ansible/aap-mcp-server) tool surface: **1,060 tools** derived from 4 OpenAPI specs across Controller, EDA, Galaxy, and Gateway services. 47 benchmark queries across 6 categories, evaluated with three models: Granite 4.1 8B, Qwen3-14B, and Claude Haiku 4.5.

Rather than making the model better at selecting thousands of tools, we change the representation so it never has to.

## The scale problem

With 1,060 tools, a common approach of presenting all tools to the LLM hits a hard limit. For Qwen3-14B (40,960 token context), encoding the complete tool surface as function schemas produces a prompt of 40,961 tokens — exceeding the context window and preventing execution entirely.

TCS sidesteps this by replacing tool selection with type classification. The 1,060 tools collapse into 79 entity types. The LLM classifies source and target types from this compact list; graph search handles tool lookup deterministically.

| Representation       | Elements          | Prompt Tokens | Executable |
|----------------------|:-----------------:|:------------:|:----------:|
| Function schemas*    | 1,060 tools       | 40,961       | No         |
| Tool descriptions    | 1,060 tools       | ~18,000      | Yes        |
| Entity types (TCS)   | 79 types          | ~1,100       | Yes        |

\* Function schemas include parameter definitions, JSON Schema metadata, and descriptions, making them substantially larger per tool than plain text listings.

The LLM reasons over 79 canonical entity types instead of descriptions for 1,060 individual tools. Graph search then deterministically recovers the executable tool chain through shared types, adding no LLM cost.

## Pipeline overview

```
         TCS                              Direct tool selection
         ───                              ──────────────────────

     ┌─────────┐                          ┌─────────┐
     │  Query  │                          │  Query  │
     └────┬────┘                          └────┬────┘
          │                                    │
          ▼                                    ▼
  ┌───────────────┐                   ┌────────────────┐
  │ Predict entity│                   │ 1,060 tool     │
  │ types (LLM)   │                   │ schemas (LLM)  │
  └───────┬───────┘                   └────────┬───────┘
          │                                    │
          ▼                                    ▼
   ┌─────────────┐                     ┌──────────────┐
   │ 79 entity   │                     │   Context    │
   │ types       │                     │   overflow   │
   └──────┬──────┘                     └──────────────┘
          │                                    ✗
          ▼
  ┌───────────────┐
  │ Graph search  │
  └───────┬───────┘
          │
          ▼
   ┌─────────────┐
   │ Tool chain  │
   └─────────────┘
```

## How the benchmark was built

### Where do the tools come from?

The tools are derived directly from the official AAP MCP Server's OpenAPI specifications — the same specs that define the MCP server's real API surface. No tools were hand-crafted. The parser (`openapi_parser.py`) reads the 4 JSON specs and extracts every operation:

| Service    | Operations | Examples                                       |
|------------|:----------:|-------------------------------------------------|
| Controller | 615        | Job templates, inventories, hosts, credentials  |
| EDA        | 110        | Activations, rulebooks, event streams           |
| Galaxy     | 141        | Collections, namespaces, artifacts              |
| Gateway    | 194        | Authenticators, users, teams, service clusters   |
| **Total**  | **1,060**  |                                                 |

Each operation becomes a typed tool edge: `tool(input_types) -> output_types`. For example, `controller.inventories_hosts_list` takes an `Inventory` and produces `Host`. The 247 OpenAPI schema components collapse to 79 canonical entity types through deterministic heuristics (e.g., `PaginatedHostList`, `HostDetail`, `PatchedHost` all map to `Host`).

### How was the composition graph constructed?

The graph was built using **deterministic heuristics only** — no LLM was involved in graph construction. The parser infers entity types from:

- **Path structure:** `/api/v2/inventories/{id}/hosts/` implies `Inventory -> Host`
- **HTTP method + operationId suffix:** `*_list` = collection query, `*_retrieve` = single-item fetch, `*_create` = creation action
- **Schema references:** response schema refs identify the output entity type

This produces a typed composition graph where each tool is an edge connecting entity types. Graph search over this structure finds tool chains for a given source/target type pair. The full graph is frozen in `graph_snapshot.json` for reproducibility.

### Were the queries designed to match the graph?

No. The graph and queries were constructed in separate, sequential phases to avoid circularity:

1. **Graph construction:** OpenAPI specs were parsed and the typed composition graph was built. No benchmark queries existed at this point.
2. **Graph freeze:** The graph was exported to `graph_snapshot.json`. No further modifications to the parser or registry were made after this point.
3. **Query authoring:** 47 benchmark queries were written from representative AAP operator workflows — what a real platform operator would ask. Queries were authored based on domain knowledge, not by consulting graph paths.
4. **Annotation:** After both the graph and queries were finalized independently, each query was annotated with `source_type`, `target_type`, and `expected_tools` by running the frozen graph as an oracle. This is a mechanical lookup, not a design decision.

This separation means the graph was not tuned to handle the evaluation queries, and the queries were not shaped to fit the graph. Reviewers can verify this by inspecting the git history: graph construction commits precede query authoring commits.

## Results: TCS (type prediction + graph search) vs Direct Tool Selection

Three approaches were evaluated:

1. **TCS (type prediction + graph search):** The LLM receives a list of 79 entity types with short descriptions and predicts a source and target type for the query (~1,100 prompt tokens). Graph search then finds the tool chain connecting those types. The LLM does type classification, not tool selection — the graph deterministically recovers the executable tool chain.
2. **Text baseline (direct tool selection):** The LLM receives all 1,060 tools listed as text lines in the format `- tool_name: (input_types) → (output_types)` (~18,000 prompt tokens) and selects tools by name. This is the standard approach — present all available tools and let the model pick. No graph is involved.
3. **Function-calling baseline:** All 1,060 tools provided as function schemas with parameter definitions and JSON Schema metadata — not executable (prompt exceeds context window).

### Overall metrics

All metrics are computed over all 47 queries. When TCS fails to find a path (due to wrong type prediction), the query scores F1 = 0.

| Metric               | Text Baseline |            |            | TCS        |            |            |
|----------------------|:------------:|:----------:|:----------:|:----------:|:----------:|:----------:|
|                      | **Granite 8B** | **Qwen 14B** | **Haiku 4.5** | **Granite 8B** | **Qwen 14B** | **Haiku 4.5** |
| F1                   | 0.61         | 0.66       | 0.58       | **0.74**   | **0.80**   | **0.91**   |
| Precision            | 0.58         | 0.63       | 0.50       | **0.74**   | **0.81**   | **0.91**   |
| Recall               | 0.69         | 0.73       | 0.74       | **0.73**   | **0.80**   | **0.91**   |
| Hallucinated tools   | 3            | 2          | 0          | **0**      | **0**      | **0**      |
| Avg prompt tokens    | 17,780       | 17,784     | 24,228     | **1,092**  | **1,096**  | **1,226**  |

### TCS improvement over baseline

| Model            | Params      | Baseline F1 | TCS F1 | Delta    |
|------------------|:-----------:|:-----------:|:------:|:--------:|
| Granite 4.1      | 8B          | 0.61        | 0.74   | **+0.13** |
| Qwen3            | 14B         | 0.66        | 0.80   | **+0.14** |
| Claude Haiku 4.5 | proprietary | 0.58        | 0.91   | **+0.33** |

TCS improves F1 for all three models. The improvement is largest for Claude Haiku 4.5 (+0.33), which is the weakest model on the baseline but the strongest under TCS.

### Per-category F1

| Category   | Queries | Text Baseline |            |            | TCS        |            |            |
|------------|:-------:|:------------:|:----------:|:----------:|:----------:|:----------:|:----------:|
|            |         | **Granite 8B** | **Qwen 14B** | **Haiku 4.5** | **Granite 8B** | **Qwen 14B** | **Haiku 4.5** |
| clean      | 15      | 0.82         | 0.84       | 0.73       | **0.93**   | **0.87**   | **1.00**   |
| multihop   | 10      | 0.68         | 0.56       | 0.78       | **0.97**   | **0.87**   | **1.00**   |
| synonym    | 7       | 0.48         | 0.76       | 0.72       | 0.43       | **1.00**   | **1.00**   |
| ambiguous  | 5       | 0.20         | 0.42       | 0.00       | 0.00       | **0.60**   | **0.40**   |
| noisy      | 5       | 0.40         | 0.53       | 0.56       | **0.60**   | 0.40       | **1.00**   |
| multipath  | 5       | 0.67         | 0.60       | 0.53       | **1.00**   | **0.80**   | **0.80**   |

### TCS type prediction accuracy

| Metric           | Granite 8B   | Qwen3-14B   | Claude Haiku 4.5 |
|------------------|:-----------:|:-----------:|:----------------:|
| Source accuracy   | 77% (36/47) | 81% (38/47) | **91%** (43/47)  |
| Target accuracy   | 85% (40/47) | 91% (43/47) | **94%** (44/47)  |
| Exact match       | 72% (34/47) | 79% (37/47) | **91%** (43/47)  |
| Path found        | 98% (46/47) | 85% (40/47) | **100%** (47/47) |

Type prediction accuracy scales with model capability. Claude Haiku 4.5 achieves 91% exact match and 100% path found. Granite 8B achieves 72% exact match but still 98% path found — it often predicts a "nearby" wrong type that still connects to a valid path, though the wrong path yields wrong tools.

### Recall decomposition

End-to-end recall can be decomposed into two independent factors — model quality and graph robustness:

```
Recall_e2e = P(types correct) x Recall_correct + P(types wrong) x Recall_wrong
```

| Component          | Granite 8B | Qwen3-14B | Claude Haiku 4.5 |
|--------------------|:---------:|:---------:|:----------------:|
| P(types correct)   | 0.72      | 0.79      | 0.91             |
| P(types wrong)     | 0.28      | 0.21      | 0.09             |
| Recall_correct     | 1.000     | 1.000     | 1.000            |
| Recall_wrong       | 0.038     | 0.050     | 0.000            |
| **Predicted recall** | **0.734** | **0.798** | **0.915**      |
| **Actual recall**    | **0.734** | **0.798** | **0.915**      |
| Gap                | 0.000     | 0.000     | 0.000            |

**When types are correct, recall is perfect (1.000) for all three models.** The graph covers all 47 queries — the oracle evaluation confirms 100% F1 with ground-truth types.

**The decomposition fits exactly (gap = 0.000).** End-to-end recall is fully explained by type prediction accuracy and graph reachability. There is no unexplained variance.

**Recall_wrong is near zero.** Unlike the smaller benchmark domains where wrong type predictions sometimes still recover partial tool chains (Recall_wrong = 0.415 average), the AAP graph is sparse enough that wrong types rarely lead to useful paths. This means type prediction accuracy directly determines end-to-end performance.

This decomposition cleanly separates two independent factors: **model quality** (P(correct)) and **graph robustness to classification errors** (Recall_wrong). Improving TCS on this domain means improving the type classifier.

## Observations

**TCS outperforms the baseline for all three models.** Granite 8B goes from 0.61 to 0.74 F1; Qwen3-14B from 0.66 to 0.80; Claude Haiku 4.5 from 0.58 to 0.91.

**TCS inverts the model ranking.** On the text baseline, Qwen3-14B performs best (0.66) and Haiku worst (0.58). Under TCS, Haiku performs best (0.91) and Granite worst (0.74). The two tasks require different capabilities: the baseline rewards scanning long tool lists, while TCS rewards entity type classification. Under TCS, the model's ability to classify entity types — not its ability to select from a long list — determines performance.

**Token usage.** TCS uses ~1,100 avg prompt tokens vs ~18,000 for the text baseline (16x reduction). The function-calling representation requires 40,961 tokens, which exceeds Qwen3-14B's 40,960 token context window.

**Zero hallucinations under TCS.** The text baseline produced hallucinated tool names across all three models (2–3 per run). No model hallucinated tools under TCS — graph search only returns tools that exist in the graph.

**Multi-hop composition.** All three models show large TCS gains on multi-hop queries (requiring 2+ tools in sequence). Granite 8B achieves 0.97 F1 on multi-hop with TCS (vs 0.68 baseline) — the graph compensates for the smaller model's weaker reasoning by deterministically composing tool chains through shared types.

**Synonym queries expose model-specific weaknesses.** Granite 8B scores 0.43 F1 on synonym queries under TCS (worse than its 0.48 baseline), because it maps informal terms like "capacity pools" and "secrets" to wrong entity types. Qwen and Haiku both achieve 1.00 on this category. This suggests synonym handling depends on the model's semantic knowledge, which varies by training data.

## TCS failure modes

### Granite 4.1 8B: 13 of 47 queries (28%) with wrong tools

- **Wrong source for `Platform` queries:** The model frequently omits `Platform` as source, predicting the target type as both source and target (e.g., `Credential→Credential` instead of `Platform→Credential`). This produces a self-loop with no useful path. (4 queries)
- **Ambiguous queries:** All 5 ambiguous queries failed — the 8B model lacks the reasoning capacity to disambiguate vague requests. (5 queries)
- **Synonym mapping failures:** Informal terms like "capacity pools" → `InstanceGroup` and "event-driven handlers" → `Activation` are beyond the model's vocabulary mapping. (3 queries)
- **Wrong intermediate type:** "activation instance logs" predicted source as `ActivationInstance` instead of `Activation`, missing the first hop. (1 query)

### Qwen3-14B: 10 of 47 queries (21%) with wrong tools

- **`UnifiedJobTemplate` vs `JobTemplate`:** The model predicted `UnifiedJobTemplate` for queries about job templates, despite `UnifiedJobTemplate` not appearing in the available types list. The graph has `JobTemplate` as the canonical type; `UnifiedJobTemplate` is a separate supertype in the AAP schema. (3 queries)
- **`UnifiedJob` vs `Job`:** Same pattern — `UnifiedJob` predicted instead of `Job`. (2 queries)
- **Ambiguous entity:** "Tell me about the database server" mapped to `Platform→Database` instead of `Host→AnsibleFacts`. (1 query)
- **Reversed source/target:** "Grab the logs" mapped with source and target swapped. (1 query)
- **Other type errors:** Wrong source or target on noisy/ambiguous queries. (3 queries)

### Claude Haiku 4.5: 4 of 47 queries (9%) with wrong tools

- **Ambiguous queries:** "Tell me about the database server" mapped to `Platform→Instance`; "What's the status of the infrastructure project?" mapped to `Platform→Project` instead of `Project→ProjectUpdate`. (2 queries)
- **Parse error:** "Who has access to this?" produced unparseable output. (1 query)
- **Wrong source:** "Show the labels on the patching workflow template" mapped to `Platform→Label` instead of `WorkflowJobTemplate→Label`. (1 query)

All failures across all three models are type prediction errors, not graph structure issues. The oracle evaluation (ground-truth types) achieves 100% path resolution and 100% F1, confirming the graph covers all 47 queries. Improving the type classifier is the primary vector for improving end-to-end accuracy.

## Threats to validity

- **Three models evaluated.** Results are from Granite 4.1 8B, Qwen3-14B, and Claude Haiku 4.5. Additional models would strengthen generalization claims.
- **Single MCP server.** The benchmark uses one production MCP server (AAP). Generalization to other MCP servers with different API structures remains untested.
- **Heuristic graph construction.** Entity types and tool edges are inferred from OpenAPI path structure and operationId conventions. APIs that do not follow RESTful naming patterns may produce lower-quality graphs.
- **Query set size.** 47 queries across 6 categories. Larger query sets and additional category types (e.g., cross-service multi-hop) would strengthen coverage.
- **Routing only.** The benchmark evaluates routing quality (selecting the correct tools), not end-to-end task execution against a live AAP deployment.
- **Evaluation with additional models and MCP servers is future work.**

## Reproducibility

```bash
# TCS (type prediction + graph search)
SANDBOX_API_KEY_GRANITE41=<key> uv run python -m benchmarks.run_benchmark --domain aap_mcp granite-4-1-8b
SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.run_benchmark --domain aap_mcp qwen
SANDBOX_API_KEY_CLAUDE=<key> uv run python -m benchmarks.run_benchmark --domain aap_mcp claude-haiku

# Text baseline
SANDBOX_API_KEY_GRANITE41=<key> uv run python -m benchmarks.run_baseline --domain aap_mcp granite-4-1-8b
SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.run_baseline --domain aap_mcp qwen
SANDBOX_API_KEY_CLAUDE=<key> uv run python -m benchmarks.run_baseline --domain aap_mcp claude-haiku

# Function-calling baseline (will fail — context overflow)
SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.run_baseline_tools --domain aap_mcp qwen

# Oracle evaluation (no LLM, validates graph structure)
uv run python -m benchmarks.run_oracle_graph --domain aap_mcp
```

## Configuration

| Parameter         | Value                                        |
|-------------------|----------------------------------------------|
| Models            | Granite 4.1 8B, Qwen3-14B, Claude Haiku 4.5  |
| Tools in registry | 1,060                                        |
| Entity types      | 79                                           |
| Benchmark queries | 47                                           |
| Graph snapshot    | `graph_snapshot.json`                        |
