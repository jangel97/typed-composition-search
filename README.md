# Typed Composition Tool Search: Entity-Based Planning for Large Tool Ecosystems

Direct tool selection operates in a large and highly specific decision space that becomes increasingly difficult to model as tool ecosystems grow. In contrast, entity prediction provides a higher-level abstraction that is more stable, generalizable, and scalable. Once the relevant entities are identified, executable tool compositions can be recovered through search over a typed composition graph.

We therefore argue that tool routing is fundamentally an entity and relationship reasoning problem rather than a tool selection problem.

**Can tool routing be reformulated from tool selection into entity and relationship reasoning?**

This project explores that question.



## Overview

Most tool-using agents treat routing as a tool selection problem.

Given a user query, the model must choose one or more tools from a potentially large catalog:

```text
Query
  ↓
Tool Selection
  ↓
Execution
```

As tool ecosystems grow, this approach becomes increasingly challenging:

* Larger decision spaces
* Higher prompt complexity
* Increased hallucination risk
* Lower routing accuracy
* Poor scalability

This project investigates an alternative formulation.

Instead of selecting tools directly, the model first predicts the entities involved in the task and then uses graph search to recover a valid execution path.

```text
Query
  ↓
Entity Prediction
  ↓
Graph Search
  ↓
Tool Path
  ↓
Execution
```

In this formulation:

* Nodes represent entity types.
* Edges represent tools that transform one entity type into another.
* The language model predicts entities rather than tools.
* Graph search recovers executable tool compositions.

Tools become implementation details rather than the primary routing target.



## Example

User query:

```text
Get logs from pods in the nginx deployment
```

Traditional routing:

```text
Query
  ↓
Select tools directly
  ↓
get_deployment
get_pods
get_logs
```

Typed routing:

```text
Query
  ↓
Source: Deployment
Target: Logs
  ↓
Graph Search
  ↓
Deployment → Pod → Logs
  ↓
get_deployment
get_pods
get_logs
```

The model reasons about entities while graph search handles composition.



## Research Question

**Can tool routing be reformulated from tool selection into entity and relationship reasoning?**

More specifically:

* Is entity prediction easier than direct tool selection?
* Does graph structure improve routing accuracy?
* Does graph topology contribute useful information?
* Does this formulation scale better as tool catalogs grow?



## Hypotheses

### H1 — Entity Prediction

Entity prediction is easier than direct tool selection.

Rather than selecting from hundreds of tools, the model predicts a small set of entity types.

### H2 — Graph-Based Routing

Typed composition graphs improve routing accuracy by exploiting structural relationships between entities.

### H3 — Graph Structure Matters

Performance gains arise from graph topology itself rather than simply adding additional reasoning steps.

### H4 — Scalability

Entity-based routing scales more effectively than direct tool selection as tool ecosystems grow.



## Design Principles

### 1. Entities First

The system reasons about:

```text
What does the user have?
```

and

```text
What does the user want?
```

before reasoning about tools.

### 2. Tools as Transformations

Tools are modeled as typed transformations:

```text
Source Entity
    ↓
Tool
    ↓
Target Entity
```

Examples:

```text
Namespace → Pod
Pod → Logs
Repository → Pull Request
Deployment → ReplicaSet
```

### 3. Graph-Constrained Composition

Only tool paths that are valid under the graph can be executed.

This constrains the search space and reduces hallucinated tool chains.

### 4. Separation of Concerns

The language model performs semantic reasoning.

The graph performs structural reasoning.



## Evaluation

The framework is evaluated against common routing strategies:

### Direct Tool Selection

```text
Query → Tools
```

### Retrieval-Based Routing

```text
Query → Embeddings → Top-K Tools
```

### Typed Graph Routing

```text
Query → Entities → Graph Search → Tools
```

Metrics include:

* Precision
* Recall
* F1
* Exact Match
* Hallucination Rate
* Valid Path Rate
* Tool Pruning Efficiency



## Expected Contributions

1. Reformulating tool routing as an entity-classification problem.
2. A typed composition graph framework for tool composition.
3. Empirical evidence that entity-level abstractions simplify routing.
4. Analysis of the role of graph topology in routing performance.
5. Scalability analysis across large tool ecosystems.
6. Design principles for future tool-using agents.



## Current Status

Research prototype under active development.

Current work focuses on:

* Benchmark construction
* Multi-domain evaluation
* Graph topology ablations
* Scalability experiments
* Model comparison studies



## Central Thesis

The primary challenge in tool routing is not selecting tools.

It is identifying the entities involved in a task and the relationships between them.

By elevating routing from tool-level prediction to entity-level reasoning, the problem becomes simpler, more scalable, and more robust.

Graph search can then recover executable tool compositions from these entity predictions.
