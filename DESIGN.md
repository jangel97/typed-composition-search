# Design

## Goal

Provide a framework that builds a typed capability graph from tool declarations and uses it to filter MCP tools down to a small, structurally relevant set for a given query. The LLM still plans and reasons — it just gets a better toolbox.

## Hypothesis

Semantic retrieval works well for tools directly referenced by a query.

However, compositional queries often require intermediate tools that are not semantically similar to the user's request.

We hypothesize that bidirectional reachability over a typed capability graph can recover these intermediate tools more reliably than retrieval alone.

Even without a full planner, reducing 1000 tools to 20 structurally relevant ones and handing those to standard LLM tool calling is a meaningful improvement — and directly benchmarkable against embedding-only retrieval.

## Core Algorithm

The algorithm operates on types, then projects the result onto tools:

```text
Forward Reachability on Types
∩
Backward Reachability on Types
→
Project onto Tools
```

Concretely:

1. **Intent extraction** — LLM extracts initial types + goal types from the user's query (lightweight, doesn't need to be perfect)
2. **Forward reachability** — from initial types, walk the capability graph forward: what types are reachable given what we have?
3. **Backward reachability** — from goal types, walk the graph backward: what types could contribute to producing what we want?
4. **Intersection** — types reachable from both directions define a subgraph; the tools on those edges are the relevant set

This catches tools that retrieval misses (like `get_ticket` in the approver example) because they sit structurally between the initial and goal types, even though they're semantically distant from the query.

## Framework

The framework handles graph construction and reachability. Users just declare their tools with types.

### Tool Declaration

```python
from typed_composition_search import Registry

registry = Registry()

@registry.tool(inputs=["Build"], outputs=["Pipeline"])
def get_pipeline(build_id: str) -> Pipeline:
    ...

@registry.tool(inputs=["Pipeline"], outputs=["Ticket"])
def get_ticket(pipeline_id: str) -> Ticket:
    ...

@registry.tool(inputs=["Ticket"], outputs=["User"])
def get_approver(ticket_id: str) -> User:
    ...
```

### API

```python
# Filter tools to only those relevant for a query
tools = registry.relevant_tools(initial={"Product"}, goal={"User"})
# => {get_latest_build, get_pipeline, get_ticket, get_approver}

# Find a composition from initial state to goal
plan = registry.plan(initial={"Product"}, goal={"User"})
# => [get_latest_build, get_pipeline, get_ticket, get_approver]

# Get the full capability graph for inspection
graph = registry.graph()
```

### What the Framework Does

- Builds the capability graph automatically from tool declarations
- Runs forward/backward reachability to find relevant tools
- Finds compositions via graph search (BFS for MVP)
- Handles multi-input tools (tools requiring types from different branches)

### What the Framework Does Not Do

- Execute tools
- Call LLMs
- Integrate with MCP directly
- Infer types from tool descriptions (future work)

## Type System

### MVP: Object-Level Types

For the MVP, tools declare coarse object-level types:

```python
inputs=["Build"]
outputs=["Pipeline"]
```

This is sufficient to prove the reachability idea.

### Future: Field-Level Types

In real systems, composition happens through identifiers and fields:

```text
Build → build_id → Pipeline → pipeline_id → Ticket → User
```

The natural evolution is typed ports or field-level types, where tools declare which fields they consume and produce rather than only which object types they transform. This enables finer-grained reachability and catches cases where two tools both operate on `Build` but through different fields.

## Results

### Benchmark Setup

57 tools across 6 domains (CI/CD, Kubernetes, Git, Jira, Monitoring, Messaging) with cross-domain type connections. 7 compositional queries, each requiring 2-5 tools to satisfy, with ground truth defined as the minimal required tool set.

### Baseline Results

```text
Query                         Sel  Req  Recall    Prec      F1   Prune
----------------------------------------------------------------------
ticket_assignee                15    5   100%    33%    50%    74%
artifacts_to_slack             13    5   100%    38%    56%    77%
alert_pods                      6    2   100%    33%    50%    89%
build_diff                     12    2   100%    17%    29%    79%
alert_to_ticket                 4    2   100%    50%    67%    93%
scale_build_deployment         17    2   100%    12%    21%    70%
product_prs                     5    3   100%    60%    75%    91%
----------------------------------------------------------------------
AVERAGE                                  100%    35%    50%    82%
```

100% recall across all queries. Every required tool was found. Average pruning of 82% — from 57 tools down to 4-17 per query.

### Variant Experiments

Two modifications were tested to improve precision:

**Exclude source tools** (tools with no inputs): Precision jumped to 93% and pruning to 94%, but recall dropped to 91%. The `artifacts_to_slack` query broke because `list_slack_channels` is a source tool that is legitimately required — `send_slack_message` needs a `Channel` type that only source tools can provide.

**Max depth = 4**: Recall dropped to 97%. The `ticket_assignee` query (a 5-hop chain) was truncated, losing `get_latest_build`.

### Findings

1. **Recall = 100% in the baseline.** Bidirectional reachability never drops a required tool. This is the strongest result.

2. **Every attempt to improve precision reduced recall.** Excluding source tools and limiting depth both removed tools that were structurally necessary. The baseline is not accidentally working — it is capturing real compositional dependencies.

3. **Source tools are not noise.** We initially hypothesized that zero-input tools (like `list_slack_channels`, `list_namespaces`) were polluting the relevant set. The Slack example disproved this — source tools are legitimate composition entry points. The distinction between source and transformation tools is conceptually useful but not a valid filtering rule.

4. **Composition length is query-dependent.** A fixed max-depth imposes a prior on workflow complexity that removes valid plans. Depth limits are too blunt for structural filtering.

5. **Precision is not the job of reachability.** Reachability answers "could this tool participate in a valid composition?" — not "is this the most likely tool for this query?" These are different questions requiring different solutions.

### Conclusion

Bidirectional reachability over a typed capability graph achieves high recall while dramatically reducing the tool search space for compositional queries.

The over-selection in the baseline (35% precision) comes from source tools opening alternative paths, not from fundamental flaws in the algorithm. This is a ranking problem, not a structural one.

## Architecture

The results suggest a layered architecture where reachability provides completeness and a ranking layer provides relevance:

```text
Intent Types
↓
Bidirectional Reachability    (structural filter — high recall)
↓
Candidate Tool Set
↓
Semantic Ranking              (relevance ordering — high precision)
↓
LLM
```

Reachability eliminates tools that cannot participate in any valid composition from initial to goal types. Ranking (via embeddings, LLM scoring, or usage frequency) sorts the remaining candidates by relevance.

Each layer does what it is good at. Reachability provides soundness. Ranking provides relevance.

## Open Questions

1. **Can we automatically derive a useful capability graph from real MCP tool schemas?** If real tools expose enough type structure, this approach scales. If everything degenerates to `string` / `object` / `dict`, we need a semantic typing layer.

2. **Does the 100% recall hold on larger, messier registries?** The current benchmark has clean, hand-crafted types. Real MCP ecosystems will be noisier.

3. **What is the right ranking layer?** Embedding similarity, LLM scoring, and usage-frequency ranking are all candidates. The reachability layer is agnostic to this choice.

## Implementation

### Implemented

1. `Tool` dataclass — name, inputs, outputs
2. `Registry` — stores tools, builds capability graph
3. `CapabilityGraph` — forward/backward reachability with optional `exclude_sources` and `max_depth` parameters
4. `relevant_tools()` — bidirectional reachability, return the intersection
5. `plan()` — BFS over the graph to find a composition
6. 57-tool DevOps benchmark with 7 compositional queries and ground truth
7. Benchmark runner reporting recall, precision, F1, and pruning across variants

