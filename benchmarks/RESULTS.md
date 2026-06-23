# Benchmark Results

## Strategies tested

| Strategy | How it works |
|----------|-------------|
| **Graph** | LLM predicts source_type + target_type → BFS resolves tool chain |
| **Graph-narrowed** | Embedding narrows entity types to top-k → LLM predicts from reduced set → BFS resolves |
| **Baseline** | All tools shown to LLM → LLM selects tools directly |
| **Retrieval** | Embedding retrieves top-k tools → LLM selects from candidates |

## Domains

| Domain | Tools | Entity types | Queries | Categories |
|--------|-------|-------------|---------|------------|
| K8s | 135 | 42 | 25 | clean, ambiguous, multihop, synonym, noisy |
| Ansible | 108 | 40 | 30 | clean, ambiguous, multihop, synonym, noisy, multipath |

---

# Run 1: Qwen3-14B + Nomic Embed Text v1.5

## Model configuration

| Component | Model | Details |
|-----------|-------|---------|
| **LLM** | Qwen/Qwen3-14B | temperature=0, thinking disabled |
| **Embedding** | nomic-ai/nomic-embed-text-v1.5 | Used by retrieval and graph-narrowed strategies |
| **Infrastructure** | Red Hat AI sandbox | API-served via vLLM, OpenAI-compatible endpoints |

## K8s results

### Strategy comparison

| Metric | Graph | Baseline | Retrieval (top-10) |
|--------|-------|----------|-------------------|
| **F1** | **0.90** | 0.62 | 0.59 |
| Precision | 0.90 | 0.54 | 0.67 |
| Recall | 0.95 | 0.84 | 0.57 |
| Exact match | 64% | 16% | 20% |
| Hallucinated tools | **0** | 9 | 2 |
| Pruning | 99% | 96% | — |

### F1 by category

| Category | Graph | Baseline | Retrieval |
|----------|-------|----------|-----------|
| Clean | 0.93 | 0.69 | 0.68 |
| Ambiguous | 0.87 | 0.47 | 0.40 |
| Multihop | 1.00 | 0.64 | 0.62 |
| Synonym | 0.80 | 0.68 | 0.56 |
| Noisy | 0.80 | 0.52 | 0.52 |

**Takeaway**: Graph dominates across all categories. K8s entity types (Pod, Deployment, Service) are well-known to the LLM, so type prediction accuracy is high. Zero hallucination is a structural guarantee.

## Ansible results

### Strategy comparison

| Metric | Graph | Baseline | Retrieval (top-10) |
|--------|-------|----------|-------------------|
| **F1** | 0.54 | 0.47 | **0.60** |
| Precision | 0.60 | 0.42 | 0.66 |
| Recall | 0.55 | 0.63 | 0.58 |
| Exact match | 23% | 10% | 17% |
| Hallucinated tools | **0** | 14 | 4 |

### F1 by category

| Category | Graph | Baseline | Retrieval |
|----------|-------|----------|-----------|
| Clean | 0.63 | 0.56 | 0.67 |
| Ambiguous | 0.56 | 0.22 | 0.44 |
| Multihop | 0.53 | 0.49 | 0.65 |
| Synonym | 0.52 | 0.38 | 0.56 |
| Noisy | 0.50 | 0.52 | 0.63 |
| Multipath | 0.00 | 0.50 | 0.67 |

**Takeaway**: Retrieval wins on Ansible. The LLM struggles with Ansible entity types — Play vs Task, RoleDefaults vs RoleVars, PlaybookRun vs Job are subtle distinctions that don't appear clearly in training data. When type prediction fails, the graph has no fallback.

## Label-set narrowing experiment (Ansible)

Hypothesis: reducing the number of entity types shown to the LLM (via embedding similarity) should improve type prediction accuracy by removing noise.

### k sweep

| Metric | Original (all 40) | k=5 | k=10 | k=15 |
|--------|-------------------|-----|------|------|
| **F1** | 0.54 | 0.57 | 0.58 | 0.58 |
| Type Recall@k | 1.00 | 0.72 | 0.83 | 0.92 |
| Both types in set | 30/30 | 16/30 | 22/30 | 26/30 |
| Type exact match | — | 40% | 47% | 50% |
| Path found | — | 70% | 77% | 80% |
| Avg prompt tokens | ~400 | 156 | 217 | 277 |

### F1 by category across k values

| Category | Original | k=5 | k=10 | k=15 |
|----------|----------|-----|------|------|
| Clean | 0.63 | 0.74 | 0.77 | **0.77** |
| Noisy | 0.50 | 0.67 | 0.72 | **0.72** |
| Multihop | 0.53 | 0.49 | 0.61 | **0.61** |
| Ambiguous | 0.56 | 0.67 | 0.00 | 0.00 |
| Synonym | 0.52 | 0.33 | 0.33 | 0.50 |
| Multipath | 0.00 | 0.00 | 0.00 | 0.00 |

### Analysis

**What narrowing improves**: Clean (+0.14), noisy (+0.22), multihop (+0.08). When query vocabulary maps directly to type names, fewer labels means less confusion.

**What narrowing breaks**: Ambiguous queries crash from 0.56 to 0.00. Even when correct types are in the narrowed set (type recall@15=0.50 for ambiguous), the LLM picks wrong types. The embedding retrieval step and the LLM prediction step fail on the same queries — both struggle with indirect semantic mappings like "webserver configuration" → Role/RoleDefaults.

**Ceiling**: Narrowing plateaus at F1=0.58 regardless of k (k=10 and k=15 produce identical F1). The bottleneck shifts from label noise to semantic reasoning — the LLM can't bridge the gap between natural language and type vocabulary for ambiguous/synonym queries.

**Cost benefit**: Prompt tokens drop 30-60%, latency drops ~30%. Even where F1 doesn't improve, narrowing reduces cost.

---

# Key findings (across all runs)

1. **The graph approach is not universally better.** It dominates on well-known entity models (K8s F1=0.90) and fails on unfamiliar ones (Ansible F1=0.54). The determining factor is LLM familiarity with the type vocabulary.

2. **Zero hallucination is a structural guarantee.** The graph can only return registered tools on valid paths. Baseline and retrieval both produce hallucinated tools (9-14 per run for baseline). This matters for production safety.

3. **Retrieval is the most robust strategy.** It never wins by a large margin, but it never catastrophically fails either. F1=0.59 on K8s, F1=0.60 on Ansible — consistent performance regardless of domain familiarity.

4. **Label narrowing helps modestly.** F1 improves 0.54→0.58 on Ansible, with significant gains in clean/noisy categories. But it can't fix the fundamental problem of indirect semantic mapping.

5. **The bottleneck is type prediction, not graph resolution.** BFS is deterministic and correct by construction. Every failure traces back to the LLM mispredicting source_type or target_type.

6. **Multi-hop is a graph strength — when types are correct.** K8s multihop F1=1.00, Ansible multihop F1=0.53-0.61. The graph perfectly composes multi-step tool chains; the limitation is getting the right start and end types.

Embedding is working quite well now. The LLM isn't failing due to excessive typing; it's failing because it doesn't know the Ansible semantic space you've defined well enough.

---

# Open questions

These are the next experiments to run, ordered by expected impact:

1. **Different models** — Qwen3-14B may not be the best type predictor. A larger model or a different architecture might handle Ansible types better. The type prediction task is simple (predict 2 strings), so even a slower model might be viable if it's more accurate.

2. **Self-consistency** (Wang et al., 2023) — Sample type prediction 3-5 times at temperature ~0.7, majority vote. Zero prompt changes. Should stabilize predictions for queries where the LLM wavers between correct and incorrect types.

3. **Few-shot examples** — Include 3-5 example type predictions in the prompt. Could dramatically help Ansible where the mapping is unfamiliar.

4. **Chain-of-thought** — Force the LLM to reason: "What entity does the user have? What do they want?" before outputting types. Adds latency but might improve accuracy on ambiguous/synonym queries.

5. **Hybrid approach** — Use graph when type prediction confidence is high, fall back to retrieval when it's low. Gets the best of both: structural guarantees where possible, graceful degradation where needed.

6. **More queries** — Current results are from 25 (K8s) and 30 (Ansible) queries. Confidence intervals are wide. Need 100+ queries per domain for statistically significant comparisons.
