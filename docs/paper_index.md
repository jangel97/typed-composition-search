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
* Empirical evidence that structural constraints eliminate hallucinations



# 2. Background and Motivation

## 2.1 Tool Routing

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

The core insight: tool routing is not fundamentally a tool selection problem. It is an entity reasoning problem followed by graph reachability.

Entity types provide a stable abstraction layer because:

* Multiple tools map to the same entity pair (many-to-one compression)
* Entity names are semantically distinct (`Deployment` vs `Pod` is clearer than `get_deployment_pods` vs `list_pod_containers`)
* Entity relationships are domain-invariant — the graph structure generalizes across tools

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

## H4: Routing Performance Decomposes Into Type Prediction and Graph Reachability

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

## 6.4 Baselines

### Direct Tool Selection

All tools provided to the LLM.

### Retrieval

Embedding similarity.

### Graph Routing

Entity prediction followed by graph search.

## 6.5 Routing Strategies

### Graph

Single-shot type prediction.

### Graph-Reverse

Reverse BFS.

### Graph-Probs

Probabilistic type selection.

### Constrained-Reverse

Graph-constrained decoding.



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

Metrics:

* Precision
* Recall
* F1
* Exact Match

Best graph strategy outperforms baseline in all model/domain combinations.

## 7.3 Hallucination Reduction

Baseline strategies produce hallucinated tools across models (up to 8 per run).

In our experiments, all graph-constrained strategies produced zero hallucinations across all model/domain combinations.

## 7.4 Context Efficiency

Graph routing uses 70–90% fewer prompt tokens than baseline by presenting only path-relevant tools instead of the full catalog.

## 7.5 Type Prediction Performance

Metrics:

* Accuracy
* Recall@K
* Confusion Matrix

## 7.6 Graph Oracle Performance

Ground-truth types provided.

Measures:

* Path found rate
* Tool precision
* Tool recall
* Tool F1

## 7.7 Entity Types vs Tools

Analyze why entity prediction works even when the type count is close to the tool count.

Multiple tools map to the same entity relationships. Entity types are more semantically distinct and stable than tool names, making classification more reliable.



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

Analyze how planning direction (forward vs reverse) affects routing performance across domains.

Compare source-first and target-first type prediction accuracy to understand when each direction is more effective.



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

We propose a reformulation of tool routing as an entity reasoning problem.

Instead of directly selecting tools, the model predicts source and target entity types and recovers executable workflows through graph search.

Our results suggest that routing performance can largely be explained by two components:

```text
Tool Routing
=
Entity Classification
+
Graph Reachability
```

This decomposition provides a scalable, interpretable, and extensible foundation for tool routing in large tool ecosystems.
