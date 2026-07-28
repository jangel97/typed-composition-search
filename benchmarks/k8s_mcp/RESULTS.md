# Kubernetes MCP Server Benchmark Results

Typed composition search (TCS) evaluated against the official [containers/kubernetes-mcp-server](https://github.com/containers/kubernetes-mcp-server) tool surface: **43 tools** across 6 toolsets (core, helm, tekton, kubevirt, kiali/istio), mapped to **37 entity types**. 30 benchmark queries across 4 categories, evaluated with Qwen3-14B.

Rather than making the model better at selecting from dozens of tools, we change the representation so it reasons over entity types instead.

## The scale problem

With 43 tools, the kubernetes-mcp-server is small enough that all three strategies fit within a typical LLM context window. Encoding the complete tool surface as function schemas produces ~2,369 prompt tokens — well within capacity. This domain tests whether TCS maintains accuracy at small scale, not whether it enables execution at large scale.

| Representation       | Elements          | Prompt Tokens | Executable |
|----------------------|:-----------------:|:------------:|:----------:|
| Function schemas     | 43 tools          | 2,369        | Yes        |
| Tool descriptions    | 43 tools          | 686          | Yes        |
| Entity types (TCS)   | 37 types          | 504          | Yes        |

## How the benchmark was built

### Where do the tools come from?

The tools are extracted from the Go source code of the official kubernetes-mcp-server. Each toolset registers tools with names, descriptions, and JSON Schema input parameters. Unlike the AAP benchmark (which parses OpenAPI specs automatically), entity types here were manually assigned by reading tool signatures.

| Toolset   | Tools | Examples                                        |
|-----------|:-----:|------------------------------------------------|
| Core      | 18    | Pod ops, resource CRUD, events, namespaces, nodes |
| Helm      | 3     | Install, list, uninstall releases               |
| Tekton    | 5     | Pipeline/task start, restart, logs               |
| KubeVirt  | 4     | VM lifecycle, clone, create, guest info          |
| Kiali     | 10    | Mesh traffic, status, Istio config, traces       |
| Selectors | 3     | Bridge tools (list → item resolution)            |
| **Total** | **43**|                                                  |

### How was the composition graph constructed?

Each tool was mapped to a typed edge: `tool(input_types) -> output_types`. For example, `pods_log` takes a `Pod` and produces `PodLog`. The toolsets form natural subgraphs — Tekton, KubeVirt, and Kiali tools are largely isolated from core Kubernetes tools. Specifying the source type immediately eliminates entire toolsets from consideration.

## Results: TCS (type prediction + graph search) vs Direct Tool Selection

Three approaches were evaluated:

1. **TCS (type prediction + graph search):** The LLM receives a list of 37 entity types with short descriptions and predicts a source and target type for the query (~504 prompt tokens). Graph search then finds the tool chain connecting those types.
2. **Text baseline (direct tool selection):** The LLM receives all 43 tools listed as text lines in the format `- tool_name: (input_types) → (output_types)` (~686 prompt tokens) and selects tools by name.
3. **Function-calling baseline:** All 43 tools provided as function schemas with parameter definitions (~2,369 prompt tokens). The LLM uses native tool-calling to select tools.

### Overall metrics

| Metric              | Text Baseline | Function Calling | TCS        |
|---------------------|:------------:|:----------------:|:----------:|
| F1                  | 0.78         | 0.76             | 0.76       |
| Precision           | 0.74         | 0.80             | 0.78       |
| Recall              | 0.94         | 0.74             | 0.77       |
| Exact match         | 43% (13/30)  | 70% (21/30)      | —          |
| Hallucinated tools  | 0            | 0                | **0**      |
| Avg prompt tokens   | 686          | 2,369            | **504**    |
| Avg tools selected  | 1.7          | 1.0              | 1.0        |

At 43 tools, all three strategies achieve comparable F1 (0.76–0.78). The tool surface is small enough that direct selection works well — this is the regime where TCS's structural advantages matter least.

### Per-category F1

| Category  | Queries | Text Baseline | Function Calling | TCS        |
|-----------|:-------:|:------------:|:----------------:|:----------:|
| clean     | 20      | 0.82         | **0.90**         | **0.90**   |
| multihop  | 4       | **0.63**     | 0.46             | 0.58       |
| synonym   | 3       | **0.69**     | 0.33             | 0.17       |
| noisy     | 3       | **0.78**     | 0.67             | 0.67       |

### TCS type prediction accuracy

| Metric           | Qwen3-14B       |
|------------------|:---------------:|
| Source accuracy   | 73% (22/30)     |
| Target accuracy   | 97% (29/30)     |
| Exact match       | 70% (21/30)     |
| Path found        | 83% (25/30)     |

Target prediction is near-perfect (97%). Source prediction is the bottleneck — Qwen confuses `Cluster` vs `Namespace` as starting point, and misses domain-specific sources like `TektonPipeline`.

### Recall decomposition

End-to-end recall can be decomposed into two independent factors — model quality and graph robustness:

```
Recall_e2e = P(types correct) x Recall_correct + P(types wrong) x Recall_wrong
```

| Component          | Qwen3-14B |
|--------------------|:---------:|
| P(types correct)   | 0.70      |
| P(types wrong)     | 0.30      |
| Recall_correct     | 1.000     |
| Recall_wrong       | 0.222     |
| **Predicted recall** | **0.767** |
| **Actual recall**    | **0.767** |
| Gap                | 0.000     |

**When types are correct, recall is perfect (1.000).** The graph covers all 30 queries.

**The decomposition fits exactly (gap = 0.000).** End-to-end recall is fully explained by type prediction accuracy and graph reachability.

**Recall_wrong = 0.222 indicates fault tolerance.** Wrong type predictions occasionally still recover partial tool chains through nearby graph paths — the 6 toolsets create enough connectivity that some wrong types still reach useful tools.

## Observations

**At 43 tools, direct selection is competitive.** All three strategies achieve F1 0.76–0.78. The tool surface is small enough that Qwen can scan the full list without degradation. This contrasts with the AAP MCP benchmark (1,060 tools), where TCS outperforms the baseline by +0.14 F1 — the advantage grows with scale.

**TCS uses the fewest prompt tokens.** 504 tokens for entity types vs 686 for text tool lists vs 2,369 for function schemas. Even at small scale, TCS is 4.7x more token-efficient than function calling.

**Zero hallucinations across all strategies.** With only 43 tools, Qwen does not hallucinate tool names in any strategy. At larger scale (AAP, 1,060 tools), the text baseline produces 2–3 hallucinated tools per run while TCS remains at zero by construction.

**Source prediction is harder than target prediction.** 97% target accuracy vs 73% source accuracy. Users describe what they want (target) more clearly than where they're starting from (source). This matches the pattern observed across all TCS benchmark domains.

**Text baseline over-selects.** The text baseline selects 1.7 tools on average vs 1.0 for function calling and TCS. This inflates recall (0.94) but hurts precision (0.74) and exact match (43%).

## TCS failure modes

### Qwen3-14B: 9 of 30 queries (30%) with wrong tools

- **Cluster vs Namespace confusion (4 queries):** "containers running in production" → `Cluster→PodList` instead of `Namespace→PodList`. "Something eating memory on nodes" → `Node→NodeMetrics` instead of `Cluster→NodeMetrics`. The model struggles with whether the user has a specific namespace or wants cluster-wide results.
- **Missing domain-specific source (2 queries):** "Start the CI build pipeline" → `Cluster→TektonPipelineRun` instead of `TektonPipeline→TektonPipelineRun`. The model doesn't recognise `TektonPipeline` as a source type for pipeline operations.
- **Synonym mapping (2 queries):** "worker machines" → `Cluster→NodeList` instead of `Cluster→NodeMetrics`. "apps deployed via Helm" → `Cluster→HelmReleaseList` instead of `Namespace→HelmReleaseList`.
- **Wrong target (1 query):** "resource consumption for all pods" → `PodList→PodMetrics` instead of `Cluster→PodMetrics`.

All failures are type prediction errors. The graph structure covers all 30 queries — confirmed by R_correct = 1.000.

## Threats to validity

- **Manual type assignment.** Entity types were assigned by reading Go source code, not extracted from OpenAPI specs. The type system reflects our interpretation of tool semantics.
- **Small tool surface.** 43 tools is well within the capacity of modern LLMs for direct selection. The pruning advantage of TCS is more pronounced at larger scale.
- **Small query set.** 30 queries across 4 categories. The clean category dominates (20/30).
- **Single model evaluated.** Results are from Qwen3-14B only. Additional models would strengthen generalization claims.
- **Routing only.** The benchmark evaluates routing quality (selecting the correct tools), not end-to-end task execution against a live Kubernetes cluster.

## Reproducibility

```bash
# TCS (type prediction + graph search)
SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.run_benchmark --domain k8s_mcp qwen

# Text baseline (direct tool selection)
SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.run_baseline --domain k8s_mcp qwen

# Function-calling baseline (native tool use)
SANDBOX_API_KEY_QWEN3=<key> uv run python -m benchmarks.run_baseline_tools --domain k8s_mcp qwen
```

## Configuration

| Parameter         | Value                                    |
|-------------------|------------------------------------------|
| Model             | Qwen3-14B                                |
| Tools in registry | 43                                       |
| Entity types      | 37                                       |
| Benchmark queries | 30                                       |
| Source             | containers/kubernetes-mcp-server (Go)    |
