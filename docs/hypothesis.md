# Research Questions and Hypotheses

Direct tool routing asks the LLM to solve both semantic understanding and workflow composition simultaneously. We separate these concerns by assigning semantic reasoning to the LLM and compositional reasoning to a typed graph.

## Research Question

Can graph-constrained entity reasoning provide a better formulation for tool routing than direct tool selection?

---

# H0: Separation of Concerns

Semantic reasoning and compositional reasoning are distinct problems and
should be handled by different computational mechanisms.

LLMs are well suited for semantic entity prediction - understanding what a
user's query is about. Graph search is well suited for deterministic
composition - finding which tools connect the predicted entities.

Combining both yields a system where each component operates at the
abstraction level it was designed for: language models reason about meaning,
graphs reason about structure, tools execute transformations.

H1–H3 are experimental consequences of this premise.

---

# H1: Decomposition

We hypothesize that graph-constrained entity prediction followed by graph
search provides a more effective and more interpretable formulation for tool routing than direct tool
selection.

Instead of the LLM choosing from N tools in a single unconstrained decision,
the system separates two concerns:

- **The LLM predicts concepts** — what entity types the user's query is about
  (semantic understanding).
- **The graph composes the path** — which tools, in what order, through which
  intermediate types (compositional structure).

Rather than predicting executable tools directly, the model predicts entity
types. Tools become graph edges that realize transformations between entities.

```text
Baseline:      Query → Choose among N tools (unconstrained)

Typed routing: Query → Predict entity types → Graph search → Tool path
```

This separation allows each component to do what it is good at. The LLM
handles natural language understanding; the graph handles structural
composition. Adding more tools to the graph does not change the LLM's task.

**Expected observations:**

- Graph-constrained routing outperforms direct tool selection (baseline)
  in end-to-end F1 across models and domains.
- Graph-constrained routing produces zero hallucinated tools (tools are
  limited to valid graph paths).
- The approach consistently improves routing across the evaluated models
  and domains.

---

# H2: Graph Reachability Reduces the Effective Decision Space

Graph-constrained decomposition reduces the effective routing decision space
even when the total number of entity types is comparable to the number of
tools.

The benefit is **not** that there are fewer entity labels than tools — in some
domains the counts are nearly identical (CI/CD: 51 types, 54 tools). The
benefit is that **graph reachability constrains each prediction step**:

1. The LLM predicts the target entity type.
2. Reverse BFS computes which source types can reach that target.
3. The LLM predicts the source from this constrained set.

After step 1, most of the type space is pruned away. The second prediction
is over a small, structurally determined subset — not the full type space.

**Key metric:**

```
entity_pruning = 1 - (reachable_sources / total_entity_types)
```

Entity pruning quantifies the reduction of the effective search space
induced purely by graph reachability.

**Expected observations:**

- Entity-level pruning is high across all domains, regardless of the
  type-to-tool ratio.
- Domains with type counts close to tool counts still exhibit high
  entity pruning.
- The pruning is a property of the graph topology, independent of the
  LLM used for entity prediction.

---

# H3: Performance Decomposition

The primary source of routing error is incorrect entity prediction rather
than graph composition.

If the graph correctly models the domain, end-to-end recall can be
predicted from entity prediction accuracy and graph reachability.

This decomposition explains where routing failures originate and enables
independent optimization of semantic prediction and graph structure.

```
Recall_e2e = P(types correct) × Recall_correct + P(types wrong) × Recall_wrong
```

Where:

- **P(types correct)** = fraction of queries where the LLM predicts both
  source and target types correctly (measured by `model-types` strategy).
- **Recall_correct** = recall when ground-truth types are given to the graph
  (measured by `graph-perfect` strategy). Isolates graph quality.
- **Recall_wrong** = average recall on queries where the LLM predicted
  incorrect types. Measures graph robustness to type errors.

**Expected observations:**

- The decomposition accurately predicts actual end-to-end recall.
- When the gap between predicted and actual recall is small, failures can
  be attributed to either type prediction (improve the LLM/classifier) or
  graph coverage (improve the type ontology).

---

# Exploratory Questions

These are investigated as secondary analyses, not core claims.

## E1: Target-First Planning

Does predicting the target type first (reverse strategy) produce better
results than predicting the source first (forward strategy)?

Intuition: users describe desired outcomes ("I want inventory levels") more
reliably than starting points. Reverse BFS after target prediction also
provides stronger structural constraints for source prediction.

## E2: Retrieval-Augmented Entity Prediction

Can semantic retrieval over tool descriptions narrow the candidate type space
before entity prediction, improving classification accuracy?

## E3: Reduced Model Dependence

Do graph constraints reduce performance variance across different LLMs?
If the graph provides structural guarantees, the choice of model should
matter less than in unconstrained selection.

## E4: Graph Topology Ablation

Does the specific graph topology matter, or would any graph provide similar
benefits? Testing with shuffled or random graphs would isolate the causal
contribution of real API structure. (Planned for future work.)

---

# Null Hypotheses

Each hypothesis has a corresponding null:

**H0₁ (Decomposition):** Entity-type prediction followed by graph search
does not produce valid tool compositions — routing accuracy is no better
than direct tool selection or retrieval-based routing.

**H0₂ (Decision Space):** Graph reachability does not reduce the effective
decision space. The number of valid source candidates after target prediction
is not significantly smaller than the total number of entity types.

**H0₃ (Performance Decomposition):** End-to-end routing accuracy is not
explained by the product of type prediction accuracy and graph reachability.
The decomposition formula does not predict actual recall.

---

# Central Thesis

Tool routing is fundamentally an entity reasoning problem rather than a tool selection problem.
Tool composition emerges naturally from graph search over typed transformations.

The LLM performs semantic reasoning, while the graph performs compositional
reasoning. Each component does what it is good at.

This decomposition:

- Outperforms unconstrained tool selection across models and domains (H1).
- Reduces the effective decision space through graph reachability, independent
  of the LLM (H2).
- Enables interpretable failure analysis via the recall decomposition (H3).
