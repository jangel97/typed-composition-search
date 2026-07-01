# AAP MCP Server Benchmark Results

Typed composition search (TCS) evaluated against the real [ansible/aap-mcp-server](https://github.com/ansible/aap-mcp-server) tool surface: **1,060 tools** derived from 4 OpenAPI specs across Controller, EDA, Galaxy, and Gateway services. 47 benchmark queries across 6 categories, evaluated with Qwen3-14B.

Rather than making the model better at selecting thousands of tools, we change the representation so it never has to.

## The scale problem

With 1,060 tools, a common approach of presenting all tools to the LLM hits a hard limit. For Qwen3-14B (40,960 token context), encoding the complete tool surface as function schemas produces a prompt of 40,961 tokens — exceeding the context window and preventing execution entirely.

TCS sidesteps this by replacing tool selection with type classification. The 1,060 tools collapse into 79 entity types. The LLM classifies source and target types from this compact list; graph search handles tool lookup deterministically.

| Representation       | Elements          | Prompt Tokens | Executable |
|----------------------|:-----------------:|:------------:|:----------:|
| Function schemas*    | 1,060 tools       | 40,961       | No         |
| Tool descriptions    | 1,060 tools       | 17,784       | Yes        |
| Entity types (TCS)   | 79 types          | 1,096        | Yes        |

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

1. **TCS (type prediction + graph search):** LLM predicts source/target entity types from a compact type list (~1,100 prompt tokens), then graph search over the composition graph finds tool chains connecting those types. The LLM does type classification, not tool selection — the graph deterministically recovers the executable tool chain.
2. **Text baseline:** All 1,060 tools listed as text lines in the prompt (~17,800 tokens), LLM picks tools directly by name.
3. **Function-calling baseline:** All 1,060 tools provided as function schemas — not executable (prompt exceeds context window).

### Overall metrics

| Metric               | Text Baseline | TCS |
|----------------------|:------------:|:------------:|
| F1                   | 0.67         | **0.97**     |
| Precision            | 0.64         | **0.97**     |
| Recall               | 0.75         | **0.96**     |
| Exact match          | 45% (21/47)  | **79%** (37/47) |
| Hallucinated tools   | 2            | **0**        |
| Avg prompt tokens    | 17,784       | **1,096**    |
| Avg tools returned   | 1.5          | **0.9**      |

### Per-category F1

| Category   | Queries | Text Baseline | TCS | Delta  |
|------------|:-------:|:------------:|:------------:|:------:|
| clean      | 15      | 0.84         | **1.00**     | +0.16  |
| multihop   | 10      | 0.56         | **0.96**     | +0.40  |
| synonym    | 7       | 0.76         | **1.00**     | +0.24  |
| ambiguous  | 5       | 0.42         | **0.75**     | +0.33  |
| noisy      | 5       | 0.53         | **1.00**     | +0.47  |
| multipath  | 5       | 0.60         | **1.00**     | +0.40  |

### TCS type prediction accuracy

| Metric           | Value       |
|------------------|:-----------:|
| Source accuracy   | 81% (38/47) |
| Target accuracy   | 91% (43/47) |
| Exact match       | 79% (37/47) |
| Path found        | 85% (40/47) |

## Observations

**Token usage.** TCS uses 1,096 avg prompt tokens vs 17,784 for the text baseline (16x reduction). The function-calling representation requires 40,961 tokens, which exceeds Qwen3-14B's 40,960 token context window.

**Tool accuracy.** TCS achieves 0.97 F1 vs 0.67 for the text baseline. The largest per-category gap is on multi-hop queries (0.96 vs 0.56) and noisy queries (1.00 vs 0.53).

**Hallucinations.** The text baseline produced 2 hallucinated tool names across 47 queries. TCS produced none — graph search only returns tools that exist in the graph.

**Multi-hop composition.** Queries requiring 2+ tools in sequence (e.g., "show host facts for hosts in the staging inventory" requires `inventories_hosts_list` then `hosts_ansible_facts_retrieve`) are where TCS shows the largest improvement. The composition graph chains tools through shared entity types; the text baseline requires the LLM to infer multi-step tool composition from flat descriptions.

**Noisy and synonym queries.** Type prediction abstracts away surface-level language variation. "What machines are managed?" and "List the hosts" both map to `Inventory → Host`, regardless of phrasing. The text baseline must match informal language directly to tool names.

## TCS failure modes

7 of 47 queries (15%) failed to find a path due to type prediction errors:

- **`UnifiedJobTemplate` vs `JobTemplate`:** The model predicted `UnifiedJobTemplate` for queries about job templates. The graph has `JobTemplate` as the canonical type; `UnifiedJobTemplate` is a separate supertype in the AAP schema. (3 queries affected)
- **`UnifiedJob` vs `Job`:** Same pattern — `UnifiedJob` predicted instead of `Job`. (2 queries)
- **Ambiguous entity:** "Tell me about the database server" was mapped to `Platform→Database` instead of `Host→AnsibleFacts`. (1 query)
- **Reversed source/target:** "Grab the logs" was mapped with source and target swapped. (1 query)

These failures are type prediction errors, not graph structure issues. The oracle evaluation (ground-truth types) achieves 100% path resolution and 100% F1, confirming the graph covers all 47 queries. Improving the type classifier is the primary vector for improving end-to-end accuracy.

## Threats to validity

- **Single model.** All results are from Qwen3-14B. Different models may produce different type prediction accuracy and different baseline performance.
- **Single MCP server.** The benchmark uses one production MCP server (AAP). Generalization to other MCP servers with different API structures remains untested.
- **Heuristic graph construction.** Entity types and tool edges are inferred from OpenAPI path structure and operationId conventions. APIs that do not follow RESTful naming patterns may produce lower-quality graphs.
- **Query set size.** 47 queries across 6 categories. Larger query sets and additional category types (e.g., cross-service multi-hop) would strengthen coverage.
- **Routing only.** The benchmark evaluates routing quality (selecting the correct tools), not end-to-end task execution against a live AAP deployment.
- **Evaluation with additional models and MCP servers is future work.**

## Reproducibility

```bash
# TCS (type prediction + graph search)
SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.run_benchmark --domain aap_mcp qwen

# Text baseline
SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.run_baseline --domain aap_mcp qwen

# Function-calling baseline (will fail — context overflow)
SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.run_baseline_tools --domain aap_mcp qwen

# Oracle evaluation (no LLM, validates graph structure)
uv run python -m benchmarks.run_oracle_graph --domain aap_mcp
```

## Configuration

| Parameter         | Value                |
|-------------------|----------------------|
| Model             | Qwen3-14B            |
| Tools in registry | 1,060                |
| Entity types      | 79                   |
| Benchmark queries | 47                   |
| Graph snapshot    | `graph_snapshot.json` |
