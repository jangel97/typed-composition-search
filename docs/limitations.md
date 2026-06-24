# Limitations

## Can Tools Be Modeled as a Typed Composition Graph?

The core assumption of this work is that domain-specific tool registries can be represented as directed graphs where nodes are entity types and edges are tools with typed signatures (source_type → target_type). This section examines where that assumption holds and where it breaks.

### Where It Works

Entity-centric, CRUD-like tool domains are a natural fit:

- **Infrastructure tools** (k8s, ansible): tools transform one resource into another. `list_pods` takes a Namespace and returns Pods — the type signature is implicit in the API design.
- **API-driven platforms** (GitHub, Jira, Salesforce): resources have clear relationships (Repo → Issues → Comments). The tool graph mirrors the data model.
- **Data pipelines**: stages have typed inputs and outputs (CSV → DataFrame → Model → Predictions).
- **Query/retrieval systems**: a search tool takes a query type and returns a result type.

Common property: tools have a dominant input entity and a dominant output entity, and workflows are sequential compositions of these transformations.

### Where It Breaks

#### Side-effect tools with no typed output

Tools like "send_email", "restart_service", or "notify_slack" perform actions but don't return a meaningful entity. They are sinks in the graph — reachable but not composable further. The graph can include them as terminal nodes, but they cannot participate in multi-hop paths.

##### Mitigation: Terminal types

Model side-effect tools as edges to a synthetic terminal type (`Action`, `Void`, or a domain-specific sink like `Notification`). They become leaf nodes in the graph — reachable as targets but never used as sources for further composition. The graph already supports this naturally: a node with no outgoing edges is just a sink.

Many side-effect tools also return something useful that is easy to overlook: `send_email` returns a `MessageID`, `restart_service` returns a `ServiceStatus`, `create_issue` returns an `Issue`. In these cases a real typed output exists — it's a modeling decision to surface it, not a structural limitation. The question to ask when registering tools is: "does anything downstream ever need this output?" If yes, type it. If no, sink it.

#### Polymorphic tools

Some tools accept multiple input types. A `delete` tool that works on Pods, Services, and Deployments would need either:
- One edge per valid input type (graph explosion)
- A union type (adds complexity to the type system)
- A generic "Resource" supertype (loses specificity, increases ambiguity)

Real registries often have polymorphic tools. The current system handles this by registering one edge per type pair, but this inflates the graph.

#### Conditional and branching workflows

The graph models linear composition: A → B → C. Real workflows may require:
- Conditionals: "if the pod is failing, get logs; otherwise get metrics"
- Parallel execution: "get both the deployment status AND the service endpoints"
- Loops: "for each namespace, list all pods"

BFS finds a single shortest path. It cannot represent branching logic or parallel tool calls.

#### Glue operations

Operations like "filter", "format", "count", or "aggregate" are type-agnostic — they operate on any entity. They don't fit cleanly into a typed graph because their type signature is generic. Including them creates edges between every type pair, destroying the sparsity that makes the approach effective.

#### Ambiguous type boundaries

In some domains, the boundary between entity types is fuzzy. Is "container" a type, or is it a property of "pod"? Is "role_defaults" a separate type from "role_vars", or should both be "role_config"? The granularity of the type system directly affects graph topology and therefore performance — but the right granularity is domain-dependent and subjective.

#### Compound queries (multi-intent)

Queries like "give me logs of pod X and also give me name of deployment" contain multiple independent intents. Each intent maps to a different source→target path:

1. `Pod → PodLogs`
2. `Deployment → DeploymentName`

The graph resolves one source→target path at a time. A compound query that gets routed as a single intent will either resolve only one sub-query (losing the other) or predict a wrong type that tries to compromise between both intents.

This is not a rare edge case — real users naturally combine requests in a single utterance, especially in conversational interfaces.

##### Mitigation: Query Decomposition

Split compound queries into atomic sub-queries before type prediction. Each sub-query goes through the graph independently:

```
"give me logs of pod X and also give me name of deployment"
  ↓ decomposition (1 LLM call)
  ├─ "give me logs of pod X"       → Pod → PodLogs       → BFS → [get_pod_logs]
  └─ "give me name of deployment"  → Deployment → Name   → BFS → [get_deployment]
```

This keeps the graph as a single-path resolver — it doesn't need to change. The decomposition step is a lightweight LLM call (classify: single-intent or multi-intent, then split if needed).

Cost: one additional LLM call for detection, plus N graph resolutions instead of one. But since graph resolution is deterministic and free (no LLM), the overhead is minimal.

Alternative approaches:
- **Multi-target prediction**: predict multiple target types from a single query and run BFS for each. Avoids the decomposition LLM call but requires the type predictor to output a variable-length list.
- **Detect and route**: classify queries as single-intent vs multi-intent upfront. Single-intent goes through the graph; multi-intent gets a different pipeline (e.g. the LLM plans freely). This avoids forcing compound queries through a system not designed for them.

### What Properties Must a Domain Have?

For typed composition graphs to be effective, the tool domain should have:

| Property | Why it matters |
|---|---|
| Clear entity types | Types must be distinguishable by an LLM from a natural language query |
| Dominant input/output per tool | Tools need a primary type signature, not polymorphic interfaces |
| Sequential composition patterns | User workflows should follow A → B → C chains |
| Sparse type connectivity | Low reachability (< 10%) keeps BFS deterministic |
| Stable type system | Types shouldn't change frequently or be context-dependent |

### Scope of the Claim

This work does not claim that typed composition graphs are a universal solution for tool selection. The claim is narrower:

> For domains where tools have well-defined entity type signatures and user workflows follow sequential composition patterns, modeling tools as a typed graph reduces tool selection to entity classification — a simpler problem that scales independently of registry size.

Domains that lack these properties may require different approaches (retrieval-augmented selection, hierarchical tool organization, or hybrid methods).
