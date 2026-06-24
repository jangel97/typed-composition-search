# IDEAS

## OpenSource tool graph

OpenSource projects like ansible and k8s could have an opensource graph maintained by community. And people could build agents using small models with enhanced tool selection because of this


## Probabilistic Type Prediction via LogProbs

### Motivation

The current graph pipeline depends on a single source type and target type prediction:

```text
Query
  ↓
LLM
  ↓
SourceType + TargetType
  ↓
Graph Search
```

This creates a hard failure mode: if the LLM predicts the wrong type, graph resolution fails even when the correct type was considered internally by the model.

### Idea

Instead of using only the top-1 type prediction, capture the model's log probabilities (or top logprobs) for candidate entity types.

Example:

```text
Source Types

Role        0.52
Host        0.30
Playbook    0.12
```

```text
Target Types

RoleDefaults  0.48
RoleVars      0.34
HostVars      0.11
```

Generate multiple candidate type pairs:

```text
Role     -> RoleDefaults
Role     -> RoleVars
Host     -> RoleDefaults
...
```

The graph planner then evaluates all valid combinations and selects the highest-scoring path.

### Benefits

* Reduces dependence on a single LLM prediction.
* Converts hard failures into uncertainty-aware planning.
* Allows the graph to recover from near-miss predictions.
* Preserves deterministic graph execution.
* Naturally supports path ranking using model confidence.

### Possible Scoring

```text
path_score =
source_probability × target_probability
```

or

```text
path_score =
source_logprob + target_logprob
```

The highest-scoring valid path is selected.

### Evaluation

Measure:

* Source Recall@K
* Target Recall@K
* Both Types Recall@K
* Graph F1 using top-1 prediction
* Graph F1 using probabilistic candidate expansion

If Recall@K is significantly higher than top-1 accuracy, this would indicate that the correct types are often present among the model's alternatives and that graph planning can exploit this uncertainty to improve robustness.


## Type Prediction as a Simpler Proxy for Tool Selection

### Hypothesis

If an LLM struggles to correctly identify user intent at the type level (source/target entity types), it will also struggle to select the correct tools from a flat list — the intent understanding problem is the same, just expressed differently.

However, predicting types is a strictly simpler problem than predicting tools:
- Fewer candidates (~40 types vs ~135 tools)
- Higher-level abstraction (what the user wants, not how to get it)
- No need to reason about execution order or composability

### What to Validate

- Compare type prediction accuracy vs direct tool selection accuracy on the same queries and model
- If both fail on the same queries, it confirms intent understanding is the bottleneck, not the selection mechanism
- If types succeed where tools fail, it shows the graph decomposition genuinely simplifies the problem
- Measure per-category: are ambiguous/synonym queries hard for both, while clean queries are easy for both?

### Why It Matters

This would demonstrate that typed composition graphs don't just prune the search space — they reduce the cognitive load on the LLM by converting a complex multi-tool selection problem into two simpler classification problems over a smaller label space.
