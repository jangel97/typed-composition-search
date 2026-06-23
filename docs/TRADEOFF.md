# The Type Prediction Tradeoff

## Summary

The graph approach's effectiveness is directly proportional to how well the LLM can predict entity types. This is a structural property of the architecture, not a tuning issue.

## Two-step pipeline

The graph strategy decomposes tool selection into two steps:

1. **Type prediction** — LLM reads the query and predicts `source_type` and `target_type` from a known vocabulary
2. **Graph resolution** — BFS finds the shortest path between those types in the tool graph

Step 2 is deterministic and correct by construction. Step 1 is the single point of failure. When the LLM predicts wrong types, the graph produces a wrong path or no path at all. There is no graceful degradation — the graph either returns the right tool chain or misses entirely.

## Cross-domain evidence

We validated on two domains with the same architecture, same LLM (Qwen3-14B), and same benchmark harness:

| Metric | K8s (135 tools) | Ansible (108 tools) |
|--------|-----------------|---------------------|
| **Graph F1** | 0.90 | 0.54 |
| **Baseline F1** | 0.62 | 0.47 |
| **Retrieval F1** | 0.59 | 0.60 |
| Graph exact match | 0.64 | 0.23 |
| Graph hallucinations | 0 | 0 |

On K8s, the graph approach dominates. On Ansible, retrieval wins.

## Why the gap

The difference is type prediction accuracy, not graph structure. Both graphs are well-connected with clear paths between entity types. The difference is how well the LLM knows the entity vocabulary:

**K8s types are deeply embedded in LLM training data.** Pod, Deployment, Service, ConfigMap — these are unambiguous, well-documented concepts that appear extensively in training corpora. The LLM rarely confuses Pod with Deployment.

**Ansible types require domain-specific reasoning.** The distinction between Play and Task, RoleDefaults and RoleVars, PlaybookRun and Job is subtle. These concepts overlap in natural language — a "task" could be a Task, a Play, or even a Role depending on context. The LLM doesn't have strong priors here.

### Category breakdown

The Ansible results reveal where type prediction fails:

| Category | Graph F1 | Notes |
|----------|----------|-------|
| Clean | 0.63 | Straightforward queries, type prediction partially works |
| Ambiguous | 0.56 | Overlapping types cause misprediction |
| Multihop | 0.53 | Longer paths amplify type errors |
| Synonym | 0.52 | Vocabulary mapping adds another layer of difficulty |
| Noisy | 0.50 | Real-world language obscures entity types |
| Multipath | 0.00 | Complete failure — multiple valid types, LLM picks wrong one |

The multipath category (F1=0.00) is the clearest signal: when a query has multiple valid type interpretations, the LLM must pick exactly the right one. It has no mechanism to hedge.

## The core tradeoff

| Property | Graph | Retrieval |
|----------|-------|-----------|
| Structural guarantees | Yes — only registered tools on valid paths | No — LLM can hallucinate or select wrong tools |
| Multi-hop composition | Perfect when types are correct | Poor — embeddings match surface words, not chains |
| Graceful degradation | No — wrong types → wrong path or no path | Yes — partial matches still return some correct tools |
| Hallucination | Zero by construction | Possible (LLM selects from candidates) |
| Dependency on type vocabulary | Total — accuracy = f(LLM familiarity with types) | None — operates on tool descriptions directly |

## What this means

The graph approach is not universally better or worse. Its effectiveness is a function of one variable: **how well the LLM can map natural language to the entity type vocabulary**.

This leads to a testable prediction: for any domain, you can estimate graph approach viability by measuring type prediction accuracy in isolation. If the LLM can reliably predict source/target types (>85% accuracy), the graph approach will dominate. If type prediction is unreliable (<70%), retrieval will outperform it.

## Possible improvements

These are hypotheses, not validated results:

1. **Better type descriptions** — include definitions in the type prediction prompt so the LLM can reason about unfamiliar types
2. **Type aliases** — map common vocabulary to canonical types before prediction (e.g., "machines" → Host, "recipe" → Playbook)
3. **Few-shot examples** — include 3-5 example type predictions in the prompt to calibrate the LLM
4. **Confidence-based hybrid** — use graph when the LLM is confident in its type prediction, fall back to retrieval when confidence is low
5. **Larger models** — a model with better domain knowledge may predict Ansible types more accurately (but increases cost/latency)

None of these change the fundamental tradeoff. They shift the type prediction accuracy curve, which determines where the crossover point between graph and retrieval lies.
