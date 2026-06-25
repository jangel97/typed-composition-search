# Typed Composition Search: Entity-Based Planning for Large Tool Ecosystems

## Abstract

Large Language Model (LLM) agents increasingly rely on external tools to answer user queries and perform actions. Existing approaches typically frame tool routing as a tool selection problem, where the model directly chooses from a potentially large catalog of available tools. As tool ecosystems grow, this approach suffers from scalability, ambiguity, and degraded selection accuracy.

We propose an alternative formulation: tool routing as an entity reasoning problem. Instead of selecting tools directly, the model predicts the relevant source and target entity types implied by a query. Tool compositions are then recovered through search over a typed composition graph, where nodes represent entity types and edges represent tool transformations.

We evaluate this approach across multiple domains and routing strategies, comparing it against direct tool selection and retrieval-based baselines. Our results suggest that routing performance can be decomposed into type prediction accuracy and graph reachability, providing a simpler and more interpretable view of the tool routing problem.



# 1. Introduction

## 1.1 Motivation

Large language model agents increasingly interact with external tools.

Examples include:

* Kubernetes administration
* Infrastructure automation
* API integrations
* Cloud operations
* Software development assistants

As the number of available tools grows, direct tool selection becomes increasingly difficult.

## 1.2 Problem Statement

Existing systems typically solve:

```text
Query -> Tool Selection
```

This requires the model to choose among potentially hundreds of tools.

We argue that users rarely think in terms of tools.

Instead, they describe:

* entities
* resources
* relationships
* desired transformations

## 1.3 Main Idea

We reformulate routing as:

```text
Query
  ↓
Entity Types
  ↓
Typed Graph Search
  ↓
Tool Composition
```

## 1.4 Contributions

* Typed Composition Graph representation
* Entity-first routing framework
* Multi-domain, multi-model benchmark evaluation
* Decomposition analysis of routing performance
* Empirical evidence that structural constraints reduce hallucinations



# 2. Background and Motivation

## 2.1 What Is a Tool?

Existing systems treat a tool as an opaque function: a name, a description,
and a calling convention. Selection reduces to choosing the right function
from a catalog.

We redefine a tool as a **typed transformation** between entity types:

```text
Tool : SourceType → TargetType
```

A tool consumes one entity type and produces another. For example,
`list_pods` transforms a `Namespace` into a `PodList`. `get_pod_logs`
transforms a `Pod` into `Logs`.

This redefinition has a structural consequence: tools are no longer
prediction targets — they are **edges in a typed composition graph**. Nodes
are entity types. Edges are tools. Multi-step workflows become paths.

The LLM's job is no longer to select tools. It is to predict the source and
target entity types. The graph recovers the tool path.

## 2.2 Tool Routing

Definition of tool routing.

Single-step vs multi-step tool usage.

## 2.2 Existing Approaches

### Direct Tool Selection

LLM chooses tools directly from a catalog.

### Retrieval-Based Routing

Embedding similarity between query and tool descriptions.

### Hierarchical Routing

Multi-stage narrowing of candidate tools.

## 2.3 Why Entities Instead of Tools

Users describe entities and relationships, not tool names. Models reason about semantics. Tools are implementation details.

The core insight: tool routing can be **decomposed** into a sequence of graph-constrained entity prediction problems.

The benefit is not that there are fewer entity types than tools — in some domains the counts are nearly identical (CI/CD: 51 types, 54 tools). The benefit is that **graph reachability constrains each prediction step**, reducing the effective decision space:

* After predicting the target type, reverse reachability prunes the valid source candidates (56–87% entity pruning across domains (70% overall)).
* This constraint is a property of the graph topology, independent of the underlying LLM.
* Even in domains where types ≈ tools, the graph reduces the second decision to a small subset (CI/CD: ~6 candidates out of 51).

See `docs/graph_constraint.md` for the full argument and evidence.

## 2.4 Limitations of Existing Approaches

### Scalability

Large action spaces.

### Tool Ambiguity

Semantically similar tools.

### Multi-Hop Workflows

Intermediate tools often have little lexical overlap with the query.



# 3. Typed Composition Graphs

## 3.1 Tool Representation

Each tool is modeled as a typed transformation:

```text
SourceType -> TargetType
```

Examples:

```text
Namespace -> Pod
Pod -> Logs
Pod -> Events
```

## 3.2 Graph Construction

### Nodes

Entity types.

### Edges

Tools.

## 3.3 Composition

Tool chains correspond to paths in the graph.

Example:

```text
Namespace
    ↓
Pod
    ↓
Logs
```

## 3.4 Reachability

Valid workflows become graph reachability problems.



# 4. Entity-Based Routing

## 4.1 Problem Reformulation

Traditional routing:

```text
Query -> Tools
```

Proposed routing:

```text
Query -> Types -> Graph Search -> Tools
```

## 4.2 Type Prediction

Predict:

* Source type
* Target type

from natural language.

## 4.3 Path Recovery

Recover executable workflows using graph search.

### Forward Search

Source → Target

### Reverse Search

Target → Source

### Constrained Search

Search within valid subgraphs.



# 5. Research Hypotheses

## H1: Tool Routing Can Be Reformulated as Entity Reasoning

In tool ecosystems with typed resources, predicting entity types and recovering tool compositions through graph search is sufficient to solve the routing problem.

## H2: Structural Constraints Reduce Hallucinations

Restricting tool selection to valid graph paths significantly reduces hallucinated tool invocations and invalid tool compositions.

## H3: Entity Types Provide a More Stable Decision Space Than Tools

Multiple tools often operate over the same entity relationships. Entity types are more semantically distinct and generalizable than tool names, making entity prediction a more reliable decision boundary even when the type count is similar to the tool count.

## H4: Graph-Constrained Decomposition Reduces the Effective Decision Space

Graph-constrained decomposition reduces the effective routing decision space even when the total number of entity types is comparable to the number of tools. After one entity type is predicted, graph reachability prunes the valid candidates for the other entity. This structural advantage is independent of the raw type-to-tool ratio and independent of the underlying language model.

Key metric: `entity_pruning = 1 - (reachable_sources / total_entity_types)`. Measured at 56–87% across 5 domains (140 queries). See `docs/graph_constraint.md`.

## H5: Routing Performance Decomposes Into Type Prediction and Graph Reachability

End-to-end routing accuracy can be explained as the product of type prediction accuracy and graph path coverage, providing an interpretable diagnostic for failure analysis.



# 6. Experimental Setup

## 6.1 Domains

### Kubernetes

Infrastructure operations. 135 tools, 127 entity types.

### Ansible

Automation workflows. 108 tools, 93 entity types.

### GitHub

Repository and CI/CD operations. 119 tools, 103 entity types.

### CI/CD (Konflux)

Product release pipelines. (additional domain)

## 6.2 Models

Evaluate across model families to demonstrate that the approach is model-agnostic.

* Qwen3-14B (open, 14B parameters)
* IBM Granite 4.1 8B (open, 8B parameters)
* Claude Haiku 4.5 (proprietary)
* GPT-OSS 20B (open, 20B parameters)

Varying model size and provider reduces the risk that results are explained by a specific model's capabilities.

## 6.3 Dataset Construction

Each query contains:

* Natural language request
* Expected source type
* Expected target type
* Expected tool chain

## 6.4 Routing Strategies

Six strategies, each earning its place in the analysis:

### Baseline (Direct Tool Selection)

All tools provided to the LLM. Establishes the performance floor and hallucination rate of unconstrained selection.

### Retrieval

Embedding similarity between query and tool descriptions. Represents the standard RAG approach to tool routing.

### Graph-Forward

Predict source type → reachable types → predict target type → BFS path resolution. Demonstrates the core reformulation (H1) and structural constraint effect (H2).

### Graph-Reverse-Probs

Predict target type (n completions) → reverse BFS → predict source type (n completions) → probability scoring → forward BFS. Best-performing strategy; demonstrates the effect of planning direction (Section 8.3).

### Oracle-Graph

Ground-truth source and target types provided; only graph resolution is evaluated. Isolates graph reachability from type prediction to support the decomposition analysis (H4).

### Model-Types

Evaluates type prediction accuracy in isolation (no graph resolution). Complements Oracle-Graph to complete the decomposition: end-to-end performance ≈ type prediction × graph reachability.

### Exploratory Variants (Appendix)

Graph-Narrowed (embedding pre-filtering), Graph-Probs (forward with probability scoring), Graph-Reverse (reverse without probabilities), and Constrained-Reverse (structured decoding) were evaluated but are reported in the appendix as they do not contribute additional analytical insight beyond the six core strategies.



# 7. Results

## 7.1 Routing Decomposition

Evaluate:

```text
Recall_e2e ≈ Recall_types × Recall_graph
```

Analyze how much of the final performance is explained by:

* type prediction quality
* graph reachability quality

This is the central analytical result: routing performance is interpretable and decomposable.

## 7.2 End-to-End Routing Performance

Compare baseline, retrieval, graph-forward, and graph-reverse-probs across all model/domain combinations.

Metrics: Precision, Recall, F1, Exact Match.

Graph-reverse-probs outperforms baseline in all 9+ model/domain combinations. Graph-forward vs graph-reverse-probs contrast shows the effect of planning direction.

## 7.3 Hallucination Reduction

Baseline produces hallucinated tools across models (up to 8 per run).

In our experiments, all graph-constrained strategies (graph-forward and graph-reverse-probs) produced zero hallucinations across all model/domain combinations.

## 7.4 Context Efficiency

Graph routing uses 70–90% fewer prompt tokens than baseline by presenting only path-relevant tools instead of the full catalog.

## 7.5 Type Prediction Performance (Model-Types)

Evaluate type prediction accuracy in isolation using the model-types strategy.

Metrics: Source accuracy, Target accuracy, Exact match (both correct).

This isolates the "entity classification" component of the decomposition.

## 7.6 Graph Oracle Performance (Oracle-Graph)

Ground-truth types provided; evaluate graph resolution in isolation.

Metrics: Path found rate, Tool precision, Tool recall, Tool F1.

This isolates the "graph reachability" component of the decomposition.

## 7.7 Graph-Constrained Decision Space

Analyze how graph reachability reduces the effective decision space for entity prediction, even when the type count is close to the tool count.

Per-query entity pruning statistics across all domains. CI/CD as case study: 51 types ≈ 54 tools, yet 87% average entity pruning (76–98% range). The graph constraint is a structural property independent of the LLM.

This section connects the graph constraint to why the reverse strategy outperforms forward: reverse BFS after target prediction yields highly constrained source candidates.



# 8. Analysis

## 8.1 Error Taxonomy

### Wrong Source Type

### Wrong Target Type

### Missing Graph Path

### Ambiguous Queries

## 8.2 Cross-Model Variance

Analyze whether graph constraints reduce performance variance across models.

Baseline F1 variance vs graph F1 variance per domain.

## 8.3 Planning Direction

Compare graph-forward (source-first) vs graph-reverse-probs (target-first) to analyze how planning direction affects routing performance across domains.

Source-first vs target-first type prediction accuracy, and when each direction is more effective.



# 9. Related Work

## 9.1 Tool Routing

Prior work on tool selection.

## 9.2 Retrieval-Based Systems

Embedding approaches.

## 9.3 Graph-Based Planning

Graph-guided agents.

## 9.4 Positioning

Existing approaches treat routing as tool selection.

We instead treat routing as:

```text
Entity Reasoning
+
Graph Reachability
```



# 10. Limitations

## 10.1 Typed Graph Assumption

Not all tools expose clear input/output types.

## 10.2 Side-Effect Tools

Actions without meaningful outputs.

Examples:

* send_email
* restart_service

## 10.3 Dynamic Systems

Runtime-generated resources.

## 10.4 Ontology Quality

Performance depends on type definitions.



# 11. Future Work

## Scalability Study

Evaluate routing accuracy as tool catalogs grow from 10 to 500+ tools.

## Graph Topology Ablation

Shuffled and random graph experiments to isolate the causal effect of graph structure.

## Hybrid Retrieval + Graph Search

Combine semantic similarity with reachability constraints.

## Dynamic Graph Construction

Automatic graph extraction from API specifications (OpenAPI, GraphQL schemas).

## Specialized Type Encoders

Fine-tuned models for entity type prediction.



# 12. Conclusion

We propose that tool routing can be decomposed into a sequence of graph-constrained entity prediction problems.

Instead of selecting tools directly from a large catalog, the model predicts entity types while the graph constrains each decision step. Graph reachability reduces the effective decision space by 56–87% across domains — a structural property independent of the underlying language model.

End-to-end routing performance decomposes cleanly into two factors:

```text
Recall_e2e = P(types correct) × Recall_graph + P(types wrong) × Recall_wrong
```

This decomposition separates model quality from graph robustness, providing interpretable diagnostics for failure analysis and a principled path for improving either component independently.
