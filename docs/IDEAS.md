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


## Graph Topology Predicts Strategy Effectiveness

### Finding

Benchmark results across 3 domains (k8s, ansible, github) and 3 models show that **graph strategy performance correlates with graph sparsity and path uniqueness, not graph size or path length**.

| Metric | K8S (best, F1=0.95) | GitHub (mid, F1=0.72) | Ansible (worst, F1=0.63) |
|---|---|---|---|
| Reachability | 2.7% | 9.1% | 6.4% |
| Avg Path Length | 2.54 | 3.92 | 3.06 |
| Diameter | 7 | 10 | 8 |
| Components | 14 | 3 | 6 |
| Avg Branching | 1.80 | 1.58 | 1.74 |

K8S has the most disconnected graph (14 components, 2.7% reachability) — most type pairs simply can't reach each other, making BFS highly deterministic. GitHub is the most connected (9.1% reachability, 3 components) with more path ambiguity.

### Counterintuitive Finding: Multihop Queries Outperform Clean

In k8s, multihop queries achieve F1=1.0 while clean queries get F1=0.93. Path length does NOT predict difficulty because BFS resolution is deterministic — it always finds the shortest path.

What predicts difficulty is **type prediction accuracy**, which correlates with:
- **Source out-degree**: high out-degree types (Namespace=24, Repo=22) mean more choices for the graph but don't affect the LLM — the LLM picks the type, the graph picks the path
- **Query explicitness**: multihop queries name entities explicitly ("pods in the nginx deployment" → Deployment), making type prediction easier despite longer paths

### Implication

All variance in graph strategy performance comes from the type prediction step, not from graph resolution. This means:
1. The graph itself is a reliable execution engine — improvements should focus on type prediction
2. Graph topology metrics can predict a priori whether the approach will work well for a given domain
3. Domains with sparser, more disconnected type graphs benefit most from the approach
4. A dedicated type classifier (encoder model) could replace the LLM for type prediction and make the approach both faster and more reliable

### Actionable Metrics for New Domains

Before deploying the approach on a new tool registry, compute:
- **Reachability %**: below 5% → expect strong results; above 10% → expect weaker gains
- **Connected components**: more components = more deterministic resolution
- **Max out-degree**: high-degree hub types are the main source of ambiguity
- **Betweenness centrality**: identifies bottleneck types where errors cascade


## Decomposed Benchmarking: LLM × Graph

### Motivation

Current benchmarks entangle two independent failure modes: the LLM predicting the wrong entity type, and the graph failing to resolve the correct tool path. When a query fails end-to-end, you can't attribute the failure to either component. Decomposing the benchmark into three layers isolates each source of error.

### Three Benchmarks

1. **LLM Type Prediction** — Given a query, does the model predict the correct source and target types? Measures type Recall@1 and Recall@K. No graph involved.

2. **Graph Resolution (Oracle)** — Given ground-truth source and target types, does BFS find the expected tools? This is deterministic — it either works or it doesn't. Measures graph coverage and path correctness independently of the LLM.

3. **End-to-End** — The current pipeline. Combines both components.

### Recall Decomposition

The exact expression for end-to-end recall is:

```
Recall_e2e = TypeAccuracy × Recall_oracle + (1 - TypeAccuracy) × Recall_wrong
```

where:
- `TypeAccuracy` = fraction of queries where both source and target types are predicted correctly
- `Recall_oracle` = average recall when ground-truth types are given to the graph (oracle benchmark)
- `Recall_wrong` = average recall when the predicted types are incorrect

Our working approximation:

```
Recall_e2e ≈ TypeAccuracy × Recall_oracle
```

This assumes `Recall_wrong ≈ 0`: when the LLM predicts wrong types, the graph resolves a wrong path that returns wrong tools, contributing approximately zero recall. This should be verified empirically by measuring recall on the subset of queries where type prediction failed.

### Why Only Recall Decomposes

Precision does not decompose multiplicatively. When type prediction fails, two things can happen:

1. **No path found** → no tools returned → precision is undefined, **excluded from the average**
2. **Wrong path found** → wrong tools → precision ≈ 0, counted in average

The exclusion changes the denominator. Queries that fail silently (no path) disappear from the precision average, inflating it. So `TypeAccuracy × Precision_oracle` underestimates actual precision.

F1 inherits this problem since it is the harmonic mean of precision and recall.

For the paper:
- **Claim** the recall decomposition (with empirical validation of `Recall_wrong ≈ 0`)
- **Report** oracle precision and F1 as reference metrics
- **Do not claim** a decomposition for precision or F1

### Why It Matters

- **Isolates where to invest**: if oracle recall is 0.98 but type accuracy is 0.70, improving the graph won't help — you need a better type classifier.
- **Clean claim for paper**: if oracle recall ≈ 1.0, the graph is a lossless execution engine and all loss comes from the type prediction step.
- **Separates concerns**: the decomposition separates the system into two independently measurable components (entity prediction and graph planning), explaining where errors come from instead of only reporting end-to-end numbers.
- **Per-domain diagnostics**: a domain where oracle recall is low needs graph restructuring; a domain where type accuracy is low needs better prompts or a finetuned classifier.


## Core Thesis: Problem Transformation, Not Tool Improvement

### The Reframing

The contribution of the typed composition graph is NOT "improving tool selection recall." The correct framing:

> **The graph transforms the problem of tool selection into a problem of entity classification — a strictly simpler and more scalable task.**

This is a stronger claim than "the graph helps." It says the graph changes what the LLM needs to do.

### Two Independent Components

The system has two distinct components with separate responsibilities:

| Component | Responsibility | Nature |
|---|---|---|
| **Semantic classification (LLM)** | Query → Source Type, Query → Target Type | Probabilistic, model-dependent |
| **Graph planning (BFS)** | Source + Target → Tool Path | Deterministic, model-independent |

When oracle recall is high (graph finds the right tools given correct types):

```
Recall_total ≈ TypeAccuracy × Recall_oracle
```

The bottleneck is entity prediction, not graph resolution. However, oracle recall varies by domain (k8s: 0.97, github: 0.92, ansible: 0.75), so the graph is not always lossless — some domains need graph restructuring too.

### What the Graph Actually Provides

The graph's value is not in recall — it's in problem reduction:

- **Automatic composition**: multi-tool paths are resolved without the LLM reasoning about ordering
- **Zero hallucinations**: only real tools from the registry appear in paths
- **Search space reduction**: the LLM classifies over ~40 types instead of selecting from ~500 tools
- **Semantic complexity bounding**: the difficulty of the LLM task stays constant as the tool registry grows

### Scalability Argument

This explains why the system works at 500 tools:

1. The LLM never sees 500 tools — it only sees ~40 types
2. The semantic complexity is bounded by the type system, not the tool count
3. The graph resolves composition deterministically
4. Adding tools to an existing type doesn't increase LLM difficulty at all

### The Real Scientific Question

The interesting question is not:

> "How well does the LLM select tools?"

but:

> "How well can a model infer source and target entity types from a natural language query?"

Because once the types are correct, the rest is classical graph search.

### Implication for Model Choice

If entity classification is the only bottleneck, the LLM can be replaced by a specialized classifier trained on the domain. Going from 90% to 98% type accuracy with a finetuned encoder would lift the entire system without touching the graph. This makes the architecture modular: improve the classifier, improve the system.


## Domain Familiarity Effect

### Observation

Benchmark results reveal that type prediction accuracy depends on how well entity types are represented in the LLM's training data.

```text
Graph F1 (best model per domain)

k8s       0.95   — entity types widely documented
cicd      0.84   — mixed (some generic, some domain-specific)
github    0.75   — entity types well-known
ansible   0.63   — entity types niche, terminology ambiguous
```

Domains with well-known types (Kubernetes: `Pod`, `Deployment`, `Namespace`) achieve significantly higher F1 than domains with niche types (Ansible: `Playbook`, `Role`, `Inventory`). When entity types fall outside the model's training distribution, type prediction becomes the bottleneck — not the graph structure.

The Ansible oracle-graph achieves 0.77 F1, confirming the graph itself is sound. The gap between oracle (0.77) and best LLM prediction (0.63) represents headroom lost to poor type classification.

### Workaround: Finetuned Encoder for Type Prediction

Since TCS decouples type prediction from tool execution, the type predictor can be replaced with any classifier. For niche domains, a small finetuned encoder trained on (query, source_type, target_type) examples can replace the LLM for the routing step.

```text
Default:   Query → LLM (type prediction) → Graph → LLM (execution)
Encoder:   Query → Encoder (type prediction) → Graph → LLM (execution)
```

Type prediction is fundamentally a classification task over a fixed label set — not a generation task. Encoders are purpose-built for this.

Expected benefits:

* Higher type accuracy on niche domains compared to zero-shot LLM prediction.
* Faster and cheaper routing (encoder forward pass vs LLM call).
* Ability to improve routing independently by retraining the encoder.

The Ansible domain is the evaluation target for this approach.
