# Graph-Constrained Decomposition

## The weak claim (do not use)

> "There are fewer entity types than tools, so classification is easier."

This does not always hold. In our CI/CD domain, there are 51 entity types for
54 tools (94% ratio). The raw label space is essentially the same.

A reviewer can trivially counter: "You replaced tool explosion with entity
explosion."

## The strong claim

> Tool routing can be decomposed into a sequence of graph-constrained entity
> prediction problems. The graph reduces the effective search space, not
> necessarily the raw label space.

The benefit is **not** that there are fewer labels. The benefit is that
**graph reachability prunes the valid choices for each prediction**, reducing
the effective decision space seen by the model.

### Why this is different

Baseline tool selection:

```
Query → Choose among N tools (unconstrained)
```

Typed routing (reverse strategy):

```
Query
  │
  ▼
Predict target type
  │
  ▼  Reverse BFS
  │
reachable_sources = {A, B, C, D, E, F}    ← graph constraint
  │
  ▼
Predict source type among those few candidates
  │
  ▼  Forward BFS
  │
Tool path
```

After predicting the target, the effective source candidate set shrinks
dramatically because most types cannot reach a given target in the graph.
The second prediction is not over the full type space — it is over a
structurally constrained subset.

### Key metric: entity-level pruning

```
entity_pruning = 1 - (reachable_sources / total_entity_types)
```

For each query's target type, we compute how many source types can reach it
via reverse BFS. The ratio of reachable sources to total types measures how
much the graph constrains the second decision.

This metric is **independent of the LLM**. It is a property of the graph
topology. Whether you use Qwen, GPT, Llama, or any future model, the graph
constraint remains the same.

## Evidence

### Domain-level summary

| Domain  | Tools | Types | Types/Tools | Avg pruning | Median | P5  | P95 | Min | Max |
|---------|-------|-------|-------------|-------------|--------|-----|-----|-----|-----|
| k8s     |   135 |    41 |         30% |         63% |    51% | 41% | 85% | 41% | 100% |
| ansible |   108 |    40 |         37% |         67% |    75% | 45% | 88% | 43% | 90% |
| github  |   133 |    44 |         33% |         56% |    60% | 20% | 73% | 20% | 75% |
| cicd    |    54 |    51 |     **94%** |     **87%** |    86% | 76% | 98% | 76% | 98% |
| shopify |   170 |    61 |         36% |         78% |    75% | 62% | 92% | 62% | 97% |
| **ALL** |       |       |             |     **70%** |    75% |     |     |     |     |

140 queries across 5 domains. Overall median entity pruning: **75%**.

### CI/CD: the critical case

CI/CD has 51 entity types for 54 tools — almost identical label spaces. Yet it
achieves the **highest** entity pruning (87% average, 76% minimum).

Every single query has at least 76% entity pruning:

| Query | Target type | Reachable sources | Pruning |
|-------|-------------|------------------|---------|
| list_products | ProductList | 1 / 51 | 98% |
| describe_model | DataModelDescription | 1 / 51 | 98% |
| builder_releases | BuilderReleaseList | 1 / 51 | 98% |
| product_details | Product | 3 / 51 | 94% |
| product_repos | RepositoryList | 4 / 51 | 92% |
| synonym_versions | SeriesList | 4 / 51 | 92% |
| multihop_builder_base_images | BaseImageList | 5 / 51 | 90% |
| latest_drop | Drop | 6 / 51 | 88% |
| noisy_drop_artifacts | ArtifactCount | 7 / 51 | 86% |
| multihop_release_commits | CommitList | 8 / 51 | 84% |
| synonym_ci_status | CIData | 10 / 51 | 80% |
| noisy_broken_build | IntegrationTestList | 11 / 51 | 78% |
| multihop_sha_digest | SHADigest | 12 / 51 | 76% |

Even the hardest query (SHADigest, most connected target) prunes 76% of
source candidates. The model never chooses from more than 12 out of 51 types.

This proves the advantage comes from **graph topology**, not from having
fewer labels.

### Type-level reverse reachability

In Kubernetes (41 entity types):

| Target type | Sources that can reach it | % of total |
|-------------|--------------------------|------------|
| NodeMetrics | 24 | 59% |
| PodLogs | 20 | 49% |
| MachineConfig | 1 | 2% |
| Cluster | 0 | 0% (root) |

In Shopify (61 entity types):

| Target type | Sources that can reach it | % of total |
|-------------|--------------------------|------------|
| InventoryLevelList | 23 | 38% |
| FulfillmentEventList | 21 | 34% |
| ProductList | 2 | 3% |
| AssetList | 5 | 8% |

Even the most reachable targets are accessible from a minority of source
types. The graph structure naturally partitions the type space.

## Why the Reverse strategy works

This explains why the reverse strategy (graph-reverse-probs) outperforms
forward strategies:

| Step | Forward strategy | Reverse strategy |
|------|-----------------|-----------------|
| 1 | Predict source (unconstrained) | Predict target (unconstrained) |
| 2 | Graph narrows reachable targets | Reverse BFS narrows reachable sources |
| 3 | Predict target (constrained) | Predict source (**highly constrained**) |

The reverse strategy benefits more from graph constraints because:

- **Target types are more predictable from queries** — users typically
  describe what they want (the output), not where they start.
- **Reverse reachability is more selective** — most targets are reachable
  from relatively few sources (median pruning 75%).
- **The hard decision (source prediction) is made over a small set** —
  after predicting the target, the graph reduces the source candidates to
  a manageable classification problem.

## Connection to the recall decomposition

The recall decomposition separates **model quality** from **graph robustness**:

```
Recall_e2e = P(correct) × Recall_correct + P(wrong) × Recall_wrong
```

The graph constraint argument explains two things:

1. **Why P(correct) can be high even when the type space is large**: each
   prediction is over a constrained subset, not the full type space. The
   graph effectively makes entity prediction easier.

2. **Why Recall_wrong > 0**: when the model predicts a "wrong" type that
   is structurally close in the graph (e.g., a parent or sibling type),
   reverse reachability may still include the correct source, recovering
   some of the right tools. The graph is tolerant to nearby errors.

## Model independence

The entity pruning numbers are a **property of the graph**, not of any
particular LLM. They hold regardless of which model performs the entity
prediction:

- Replace Qwen with GPT-6 → same pruning ratios.
- Replace Claude with Llama 5 → same pruning ratios.
- Use a fine-tuned encoder instead of an LLM → same pruning ratios.

This makes the graph constraint a **method-level contribution**, not a
model-level finding. It is a structural property of the typed composition
graph that any entity predictor can exploit.

## Paper framing

### Central narrative

Instead of:

> ~~Tool routing is an entity classification problem.~~

Use:

> **Tool routing can be decomposed into a sequence of graph-constrained
> entity prediction problems.**

The word "decomposed" connects to everything in the paper:
- Decomposition of the routing problem (entity prediction + graph search)
- Decomposition of recall (P(correct) × Recall_correct + ...)
- Decomposition of decision complexity (unconstrained → constrained)

### Hypothesis (H4)

> Graph-constrained decomposition reduces the effective routing decision
> space even when the total number of entity types is comparable to the
> number of tools.
>
> After one entity type is predicted, graph reachability prunes the valid
> candidates for the other entity, reducing the effective decision space.
> This structural advantage is independent of the raw type-to-tool ratio
> and independent of the underlying language model.

### Claims to make

1. The typed graph **decomposes** tool selection into two structurally
   constrained decisions (source and target type prediction).
2. Graph reachability reduces the effective candidate set for each
   decision (56–87% average entity pruning across domains (70% overall)).
3. This advantage holds even when types ≈ tools (CI/CD: 51 types,
   54 tools, 87% average entity pruning).
4. The pruning is a property of the **graph topology**, independent of
   the LLM used for entity prediction.
5. The decomposition provides interpretable diagnostics: failures can be
   attributed to type prediction errors or graph coverage gaps.

### Claims to avoid

- ~~"There are fewer types than tools."~~ (Not always true.)
- ~~"Entity classification is easier than tool selection."~~ (Requires
  nuance — BothAcc can be lower than baseline F1 due to compounding two
  exact-match predictions.)
- ~~"The graph always finds the right tools."~~ (It depends on type
  prediction quality.)

### Suggested metrics to report

For each domain, and per query:

```
entity_pruning = 1 - (reachable_sources / total_entity_types)
```

Report:
- Average pruning ratio
- Median pruning ratio
- P5 and P95
- Distribution (histogram or box plot)
- CI/CD as a highlighted case study
