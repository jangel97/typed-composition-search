# Hypotheses

## Research Question

Can tool routing be improved by decomposing tool selection into entity-level reasoning and graph search?

---

# Main Hypothesis (H1)

Entity type prediction is easier than direct tool selection.

Tool routing can be reformulated as a higher-level classification problem in which the model predicts entity types rather than individual tools.

Instead of selecting from hundreds of tools directly, the model predicts a small number of abstract entity types and relies on graph search to recover the execution path.

```text
Traditional routing

Query
  ↓
Tool Selection
  ↓
Execution
```

```text
Typed routing

Query
  ↓
Entity Classification
  ↓
Graph Search
  ↓
Tool Path
  ↓
Execution
```

The key claim is that entity types form a more stable and lower-complexity representation than tools.

Expected observations:

* Entity prediction accuracy exceeds direct tool-selection accuracy.
* Entity prediction remains stable as the number of tools grows.
* Errors in graph routing are strongly correlated with entity-classification failures.
* Many queries that fail under direct tool selection succeed when routed through entity predictions.

If this hypothesis is rejected, improvements observed later must be attributed primarily to graph constraints rather than problem decomposition.

---

# System Hypothesis (H2)

Typed composition graphs improve routing accuracy compared to retrieval-only and direct tool-selection approaches.

Once routing is decomposed into entity prediction, graph search can recover valid execution paths by exploiting structural relationships between entities.

In domains where tools compose through typed transformations, graph-based routing will outperform approaches based solely on semantic similarity or direct tool prediction.

Expected observations:

* Higher Precision
* Higher Recall
* Higher F1
* Lower hallucination rate
* Fewer unnecessary tool invocations
* Higher valid-path rate

This hypothesis evaluates whether the proposed routing framework is practically useful.

---

# Structure Hypothesis (H3)

Graph topology carries information that cannot be recovered from semantic similarity alone.

The performance gain of graph-based routing is not solely a consequence of better language understanding or additional processing stages.

If graph structure is replaced with random or corrupted connectivity, routing performance will significantly degrade.

Experimental variants:

```text
Real Graph
Shuffled Graph
Random Graph
```

Expected observations:

```text
Real Graph
    >
Shuffled Graph
    >
Random Graph
```

Measured by:

* Precision
* Recall
* F1
* Path validity
* Hallucination rate

This hypothesis tests whether graph structure itself contributes useful information.

---

# Scalability Hypothesis (H4)

Graph-based routing scales more effectively than direct tool selection.

As tool catalogs grow, direct tool selection becomes increasingly difficult due to larger label spaces and prompt sizes.

Because typed routing operates primarily over entity types, performance should degrade more slowly as the number of tools increases.

Expected observations:

* Smaller reduction in F1 as tools are added
* Stable routing performance with hundreds of tools
* Lower prompt complexity
* Reduced context-window requirements

This hypothesis evaluates whether typed routing remains practical in large tool ecosystems.

---

# Exploratory Questions

These questions are investigated as secondary analyses rather than core claims.

## E1: Target-First Planning

Do users specify desired outcomes more reliably than starting entities?

Expected observations:

* Higher path-found rate
* Improved recall
* Better source prediction after graph narrowing

---

## E2: Retrieval-Augmented Entity Prediction

Can semantic retrieval improve entity prediction by narrowing the candidate type space?

Expected observations:

* Better entity-classification accuracy
* Better routing accuracy
* Hybrid methods outperform retrieval-only approaches

---

## E3: Reduced Model Dependence

Do graph constraints reduce sensitivity to the underlying language model?

Expected observations:

* Smaller performance differences across models
* Lower hallucination variance
* More stable routing behavior

---

# Null Hypothesis (H0)

There is no statistically significant difference between:

* Entity-based routing
* Retrieval-based routing
* Direct tool-selection approaches

Any observed performance differences are attributable to chance.

---

# Expected Contributions

1. A reformulation of tool routing as an entity-classification problem.
2. A typed composition graph framework for recovering executable tool paths.
3. Empirical evidence that entity-level abstractions simplify tool routing.
4. A study of how graph topology influences routing quality.
5. A scalability analysis across large tool ecosystems.
6. Design principles for future tool-using agents.

---

# Central Thesis

The primary challenge in tool routing is not selecting tools.

It is identifying the correct entities and relationships involved in a task.

By elevating routing from tool-level prediction to entity-level reasoning, the problem becomes simpler, more scalable, and more robust.

Graph search can then recover executable tool compositions from these entity predictions.

Therefore, tool routing should be formulated as entity classification followed by constrained graph search, rather than as direct tool selection or retrieval alone.
