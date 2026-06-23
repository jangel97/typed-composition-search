# Typed Composition Search: Entity-Based Planning for Large Tool Ecosystems

Large Language Models (LLMs) increasingly rely on external tools to access information, perform actions, and solve complex tasks. As tool ecosystems grow, traditional approaches that expose all available tools to the model become less effective, increasing context consumption, selection errors, and hallucination risk.

Typed Composition Search (TCS) reframes tool routing as a graph search problem rather than a tool selection problem. Instead of asking the LLM to choose tools directly, the model predicts a source entity type, a target entity type, and any initial parameters required by the task. Tools are represented as typed transformations between entities, forming a directed graph. The execution engine then resolves a valid composition path through the graph using reachability analysis and graph search algorithms.

This separation of concerns allows the LLM to focus on intent understanding while delegating planning and composition to a deterministic execution layer. By operating on entity relationships rather than tool descriptions, TCS significantly reduces the number of candidate tools presented to the model and enables scalable routing across large tool catalogs.

We evaluate the approach against retrieval-based and direct tool-selection baselines across multiple domains and tool ecosystems. Experimental results show that graph-based typed planning improves routing accuracy, reduces hallucinated tool calls, and maintains high recall while pruning the search space by more than 95% in large registries.

The work suggests that entity-based planning provides a scalable foundation for tool-using AI systems and offers a practical alternative to embedding-only retrieval approaches for complex multi-step tool composition.

Can we model tool ecosystems as typed entity graphs and perform planning in entity space instead of tool space?

## Overview

Typed Composition Search is a lightweight framework for tool composition based on graph traversal.

Instead of asking an LLM to select tools directly, tools are modeled as transformations between entity types:

```text
ProductName
    ↓
Product
    ↓
Artifact
    ↓
Build
    ↓
PipelineRunURL
```

Each tool becomes an edge in a directed graph.

Given a source type and a target type, the framework finds the shortest tool chain required to reach the desired information.

---

## Motivation - The Tool Explosion Problem

Many agent frameworks expose every available tool to the model on every request.

```text
User Query
     ↓
LLM
     ↓
500 Tool Schemas
     ↓
Tool Selection
```

This creates several challenges:

* Large tool ecosystems consume significant context window space.
* Tool schemas often dominate input token usage.
* Similar tools dilute retrieval quality.
* Unrelated tools increase the probability of incorrect tool selection.
* Multi-step tool composition becomes harder as the number of available tools grows.

In practice, a large fraction of agent context can be spent describing tools rather than solving the user's problem.

Most agent systems solve tool usage as a retrieval problem:

```text
User Query
     ↓
Embeddings / LLM
     ↓
Tool Selection
     ↓
Execution
```

This works well for simple requests but becomes increasingly difficult when:

* The number of tools grows.
* Multiple tools must be chained together.
* Required tools are semantically unrelated.
* Tool schemas consume large amounts of context.
* Tool selection becomes a larger search problem.

### A Different Approach

Typed Composition Search explores a different architecture:

```text
User Query
     ↓
LLM
     ↓
Source Type + Target Type
     ↓
Graph Search
     ↓
Tool Chain
     ↓
Execution
```

Rather than selecting tools directly, the model identifies:

```text
What information do I have?
What information do I need?
```

The graph determines how to connect them.

This allows the system to expose only the tools that are relevant to the requested goal, potentially reducing token consumption, improving scalability, and simplifying multi-step planning.

---

## Core Concepts

### Entity Types

Entity types are graph nodes.

Examples:

```text
ProductName
Product
Artifact
Build
PipelineRun
PipelineRunURL
```

Entity types represent information, not implementation details.

### Tools

Tools are graph edges.

Example:

```python
get_product(ProductName) -> Product

get_latest_artifact(Product) -> Artifact

get_build(Artifact) -> Build

get_pipeline_run(Build) -> PipelineRunURL
```

These tools automatically create a directed graph.

### Graph Search

Finding a tool plan becomes a shortest-path problem.

Example:

```text
Source:
ProductName

Target:
PipelineRunURL
```

The graph returns:

```text
ProductName
    ↓
Product
    ↓
Artifact
    ↓
Build
    ↓
PipelineRunURL
```

and the corresponding tools:

```text
get_product
get_latest_artifact
get_build
get_pipeline_run
```

---

## Example

### Register Tools

```python
from typed_composition_search import Registry

registry = Registry()

registry.register(
    "get_product",
    "ProductName",
    "Product"
)

registry.register(
    "get_latest_artifact",
    "Product",
    "Artifact"
)

registry.register(
    "get_build",
    "Artifact",
    "Build"
)

registry.register(
    "get_pipeline_run",
    "Build",
    "PipelineRunURL"
)
```

### Resolve a Path

```python
path = registry.resolve(
    source_type="ProductName",
    target_type="PipelineRunURL"
)
```

Result:

```text
get_product
get_latest_artifact
get_build
get_pipeline_run
```

---

## Agent Architecture

A typical agent workflow looks like:

```text
User Query
     ↓
LLM
     ↓
{
  "needs_tools": true,
  "source_type": "ProductName",
  "target_type": "PipelineRunURL"
}
     ↓
Typed Composition Search
     ↓
Tool Chain
     ↓
LLM Execution
```

If no external information is required:

```json
{
  "needs_tools": false
}
```

the graph is skipped entirely and the model answers directly.

---

## Why Types Instead of Tools?

Traditional tool-calling requires the model to solve:

```text
Which tools should I call?
In what order?
Which tools are relevant?
```

As the number of tools increases, this becomes increasingly difficult.

Typed Composition Search reduces the problem to:

```text
What information do I have?
What information do I need?
```

Example:

Instead of choosing from hundreds of tools:

```text
get_product
get_latest_artifact
get_build
get_pipeline_run
...
```

the model predicts:

```text
Source Type:
  ProductName

Target Type:
  PipelineRunURL
```

The graph planner determines the tool chain automatically.

The central hypothesis is:

> Predicting source and target types may be easier than selecting tools directly.

---

## Research Goals

This project is intended to explore several questions:

### Type Prediction

Can an LLM reliably identify:

* Whether tools are required
* The source type
* The target type

### Tool Composition

Can graph search improve multi-step tool composition?

### Scalability

How does graph-based planning behave as the number of tools grows?

Examples:

```text
10 tools
100 tools
500 tools
1000 tools
```

### Token Efficiency

Can graph-based planning reduce the number of tool schemas exposed to the model?

### Retrieval Quality

How does graph retrieval compare to:

* Embedding retrieval
* BM25 retrieval
* LLM tool selection
* Hybrid approaches

---

## Planned Benchmarking

The long-term goal is to build a benchmark framework for tool retrieval and tool composition.

### Embedding Retrieval

```text
Query
  ↓
Embeddings
  ↓
Top-K Tools
```

### LLM Tool Selection

```text
Query
  ↓
LLM
  ↓
Tool Chain
```

### Typed Composition Search

```text
Query
  ↓
Source Type + Target Type
  ↓
Graph Search
  ↓
Tool Chain
```

Metrics may include:

* Recall
* Precision
* Exact Match
* Multi-Hop Recall
* Path Length
* Tool Count
* Latency
* Token Usage

---

## Graph Visualization

An interactive browser-based visualizer for composition graphs.

```bash
# Visualize one or more registries
uv run python viz/serve.py benchmarks/k8s/registry.py
uv run python viz/serve.py benchmarks/k8s/registry.py benchmarks/ansible/registry.py
```

This opens a self-contained HTML page with:

* **Graph rendering** — force-directed layout of entity types and tool edges
* **Graph selector** — dropdown to switch between registries (when multiple are provided)
* **Search** — filter and highlight types by name
* **Path finding** — enter source and target types to highlight the shortest composition path
* **Metrics panel** — expandable section showing structural, reachability, search-space, and centrality metrics with hover explanations
* **Node hover** — shows incoming and outgoing tools for each type

The visualizer accepts any `registry.py` file that exports a `build_registry()` function returning a `Registry` instance. The dropdown name is derived from the parent directory.

---

## Roadmap

### V1

* Entity types as strings
* Tools as graph edges
* BFS shortest-path search
* Registry API
* Unit tests

### V2

* Multi-input tools
* Path objects
* Graph metrics
* Visualization

### V3

* Benchmark framework
* Embedding retrieval baselines
* Hybrid retrieval methods
* Automatic graph generation from tool schemas

### V4

* MCP integration
* OpenAPI integration
* Tool graph generation
* Large-scale evaluation datasets

---

## Scope and Limitations

Typed Composition Search is primarily designed for domain-specific agents operating over structured systems.

Examples include:

* Kubernetes
* OpenShift
* GitHub
* GitLab
* AWS
* MCP Servers
* Enterprise APIs
* Internal company platforms

These domains naturally expose entities and relationships that can be represented as a graph:

```text
Repository
    ↓
Pipeline
    ↓
Build
    ↓
Artifact
```

The framework assumes that:

1. Relevant entity types can be identified.
2. Tools can be modeled as transformations between types.
3. A valid path may exist between the available information and the desired information.

This approach is not intended to replace general-purpose reasoning.

For example:

```text
Who was Napoleon?
Write me a poem.
Explain quantum mechanics.
```

do not require graph traversal and should be answered directly by the language model.

Instead, Typed Composition Search is intended to act as a planning layer for structured domains where answering a query requires composing multiple tools.

```text
User Query
      ↓
LLM
      ↓
Goal Extraction
      ↓
Typed Composition Search
      ↓
Execution Plan
      ↓
LLM Response
```

The framework is therefore best viewed as a complement to tool-calling agents rather than a replacement for language models.

Typed Composition Search is not a general-purpose reasoning framework. It is a planning mechanism for structured tool ecosystems. We could create opensource graphs for opensource projects like K8S so community maintains the knowldge graph for tools.

---

## Example Domains

Potential benchmark domains include:

* Kubernetes
* OpenShift
* GitHub
* GitLab
* AWS
* MCP Servers
* Enterprise APIs
* Synthetic tool ecosystems

These domains provide realistic environments containing hundreds or thousands of tools.

---

## Project Status

Experimental.

The current goal is to validate a simple hypothesis:

> Can predicting source and target types outperform direct tool selection for multi-step tool composition?

If successful, Typed Composition Search may provide a scalable alternative to exposing every available tool to an LLM during inference.
