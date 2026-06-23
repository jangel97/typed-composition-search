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
