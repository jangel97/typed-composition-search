# AAP MCP Server Benchmark

Typed composition search benchmark built from the real [ansible/aap-mcp-server](https://github.com/ansible/aap-mcp-server) OpenAPI specifications. Unlike the other benchmark domains in this project, which use hand-curated tool registries, this benchmark derives its tools and entity types directly from a production MCP server's API surface.

## Data source

The benchmark parses 4 OpenAPI JSON specs from the official AAP MCP server (`~/aap-mcp-server/data/`):

| Service    | Operations | Description                                      |
|------------|------------|--------------------------------------------------|
| Controller | 615        | Job templates, inventories, hosts, credentials   |
| EDA        | 110        | Activations, rulebooks, event streams            |
| Galaxy     | 141        | Collections, namespaces, artifacts               |
| Gateway    | 194        | Authenticators, users, teams, service clusters    |
| **Total**  | **1,060**  |                                                  |

After adding auto-generated `select_*` bridging tools for list-to-item resolution, the registry contains **1,125 tools** and **70 entity types**.

## Files

| File                   | Purpose                                                       |
|------------------------|---------------------------------------------------------------|
| `openapi_parser.py`    | Parses OpenAPI specs, infers entity types and input/output edges |
| `registry.py`          | Builds the TCS `Registry`, generates selectors, freezes graph |
| `queries.py`           | 47 benchmark queries across 6 categories                      |
| `graph_snapshot.json`  | Frozen graph artifact for reproducibility                     |

## Running

```bash
# Oracle evaluation (no LLM, validates graph structure)
uv run python -m benchmarks.run_oracle_graph --domain aap_mcp

# LLM-based type prediction (requires model API keys)
uv run python -m benchmarks.run_benchmark --domain aap_mcp qwen

# Freeze/re-export the graph
uv run python -m benchmarks.aap_mcp.registry freeze benchmarks/aap_mcp/graph_snapshot.json
```

## Methodology: graph-query independence

The graph and the benchmark queries were constructed in separate, sequential phases to avoid circularity:

1. **Graph construction (Phase 1-2):** The OpenAPI specs were parsed and the typed composition graph was built using deterministic heuristics on path structure, HTTP methods, and schema references. No LLM was involved in graph construction.

2. **Graph freeze (Phase 3):** The graph was frozen and exported to `graph_snapshot.json`. No modifications to the parser or registry were made after this point.

3. **Query authoring (Phase 4):** Benchmark queries were written from representative AAP operator workflows based on domain knowledge and typical automation tasks. Queries were authored independently of the graph implementation. The query set was not designed to match or exercise specific graph paths.

4. **Annotation (mechanical step):** After both the graph and queries were finalized independently, each query was annotated with `source_type`, `target_type`, and `expected_tools` by running the frozen graph as an oracle. This is a lookup, not a design decision. Queries for which the frozen graph finds no valid path are retained as data points that reveal graph coverage gaps.

This separation means the graph's structure was not informed by the evaluation queries, and the queries were not shaped to fit the graph. Reviewers can verify this by inspecting the git history: graph construction commits precede query authoring commits.
