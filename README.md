# Typed Composition Search

## Problem

Most MCP/tool ecosystems treat tool selection as a retrieval problem: embed the user's query, find the nearest tools. This works for single-tool queries but breaks down on compositional ones.

Example: *"Who approved the latest build?"*

Retrieval finds tools related to "build" and "approval." But the actual execution requires chaining four tools — `get_latest_build → get_pipeline → get_ticket → get_approver` — most of which are semantically distant from the original query. Retrieval can't discover them.

The problem gets worse as tool ecosystems grow. The tools a query *needs* are determined by the execution plan, not by semantic similarity to the query.

## Idea

Tool selection is not a retrieval problem. It is a composition problem.

Model each tool as a typed transformation:

```
Tool = (Inputs, Outputs, Preconditions, Effects)
```

Build a capability graph where types are nodes and tools are edges. Reframe tool selection as: given an initial state and a goal state, find a path through the graph — a composition of tools that transforms one into the other.

The LLM's job is not to select tools. It is to extract intent: what do we have, and what do we want. A planner handles the rest.

## Results

We built a minimal framework and benchmarked it against a 57-tool DevOps registry with 7 compositional queries.

```text
57 tools → 82% average pruning → 100% recall
```

Every required tool was found across all queries. No tool that was structurally necessary for a valid composition was dropped.

Attempts to improve precision (excluding source tools, limiting search depth) reduced recall without exception. The baseline captures something structurally important.

See [DESIGN.md](DESIGN.md) for full results, variant experiments, and architecture discussion.

## Formalization

Let:

* `S₀` be the initial state
* `G` be the goal state
* `T` be a set of available tools

Each tool is modeled as:

```text
t = (Inputs, Outputs, Preconditions, Effects)
```

A tool is applicable when:

```text
Inputs(t) ⊆ S

Preconditions(t) ⊆ S
```

Applying a tool produces a new state:

```text
S' = S ∪ Outputs(t) ∪ Effects(t)
```

For the initial model, we assume monotonic state growth:

```text
S ⊆ S'
```

Tools never consume or invalidate facts.

This keeps the planning model simple and allows compositions to be represented as graph reachability problems.

### Capability Graph

A capability graph is derived automatically from tool signatures:

```text
Nodes = Types / Facts / Effects

Edges = Tools
```

Example:

```text
Product
    |
    | get_latest_build
    v
Build
    |
    | get_pipeline
    v
Pipeline
    |
    | get_ticket
    v
Ticket
    |
    | get_approver
    v
User
```

The planner's job is to discover compositions that transform an initial state into a goal state.

### Linear Composition

A composition is a sequence of tools:

```text
π = [t₁, t₂, ..., tₙ]
```

such that:

```text
S₀ --t₁--> S₁ --t₂--> ... --tₙ--> Sₙ
```

and:

```text
G ⊆ Sₙ
```

### Higher-Order Composition

Many real-world queries cannot be expressed as simple paths.

Examples:

```text
Count containers across all products
```

```text
Create a Jira ticket for every failed pipeline
```

```text
Send a Slack notification only if failures exist
```

To model these workflows, we introduce a small algebra of composition operators:

```text
compose
map
filter
reduce
if
exists
forall
parallel
```

Examples:

```text
reduce(
    sum,
    map(
        get_containers,
        list_products()
    )
)
```

```text
forall(
    create_jira,
    filter(
        is_failed,
        list_pipelines()
    )
)
```

```text
if(
    exists(failed_pipelines),
    send_slack,
    noop
)
```

These operators allow plans to represent iteration, aggregation, branching, and conditional execution.

### Program Synthesis View

Under this formulation, tool selection becomes a program synthesis problem.

Given:

```text
Γ = Context
G = Goal
```

find an expression:

```text
Γ ⊢ e : G
```

where `e` is constructed from:

```text
Tools
+
Composition Operators
```

Example:

```text
send_slack(
    summarize(
        list_artifacts(
            get_latest_drop(Product)
        )
    )
)
```

The objective is not to retrieve tools.

The objective is to synthesize an executable composition that satisfies the requested goal.

### Thesis

Tool retrieval is not fundamentally a similarity search problem.

It is a typed composition and planning problem.

Embeddings and LLMs may help infer intent, entities, and goals, but the selection of tools emerges from the synthesis of a valid composition over a graph of capabilities.
