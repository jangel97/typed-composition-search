# Related Work and Positioning

## The problem

LLM-based agents need to select and compose tools. As tool catalogs grow (100+), showing all tools to the LLM degrades accuracy, increases cost, and introduces hallucination risk. The field is actively exploring how to narrow tool selection.

## Existing approaches

### 1. Retrieval-based (embedding similarity)

Tools are embedded and retrieved by cosine similarity to the query. Used in production RAG systems and evaluated in [ToolScope (2025)](https://arxiv.org/html/2510.20036v2).

**Limitation:** Embeddings match surface vocabulary, not structural composition. Our benchmarks confirm this — retrieval (top-10) achieves F1=0.59 vs graph F1=0.90. Multi-hop queries fail because intermediate tools (e.g., `select_pod`) aren't semantically similar to the query.

### 2. Graph serialization into prompt (PLaG)

[PLaG (Lin et al., 2024)](https://arxiv.org/abs/2402.02805) serializes the tool dependency graph as text and includes it in the LLM prompt, asking the model to reason about the graph structure directly.

**Limitation:** Requires lengthy prompts and "struggles to align subtask relationships with tool transition semantics" (cited by GRAFT). Performance degrades with graph complexity. The LLM still bears the full reasoning burden.

### 3. LLM task decomposition + graph search (ControlLLM)

[ControlLLM (ECCV 2024)](https://arxiv.org/abs/2310.17796) uses a "Thoughts-on-Graph" paradigm: an LLM first decomposes the task into subtasks with typed inputs/outputs, then a graph search finds tool paths. Achieves 93% success vs 59% for baselines on multimodal tasks.

**Closest to our approach**, but significantly more complex: LLM does full task decomposition (not just type prediction), handles parallel scheduling, manages resource nodes, and targets multimodal pipelines. Our approach is a stripped-down version of this idea.

### 4. Trained graph models (GRAFT, GNN4Plan, GAP)

- [GRAFT (2026)](https://arxiv.org/html/2605.11706): Internalizes tool graphs into LLM parameters via tool-specific tokens and contrastive edge reconstruction. State-of-the-art EM on tool planning benchmarks.
- [GNN4Plan (Wu et al., NeurIPS 2024)](https://arxiv.org/abs/2405.19119): Uses graph neural networks for task planning, motivated by theoretical limitations of attention mechanisms on graph problems.
- [GAP (2025)](https://arxiv.org/html/2510.25320v1): Graph-based agent planning with reinforcement learning for parallel tool execution.

**Limitation:** All require training infrastructure — fine-tuning, GNNs, RL. Not practical for teams that want to use off-the-shelf models.

## Where we fit

The literature has a gap between retrieval (no structure) and trained models (heavy infrastructure):

```
Retrieval    →    [gap]    →    Trained models
(ToolScope)                    (GRAFT, GNN4Plan)
F1=0.59                        SOTA but needs training
no structure                   heavy infrastructure
```

We fill that gap with the simplest possible structural approach:

- **LLM only predicts source/target types** (2 strings) — not task decomposition, not tool selection, not graph reasoning
- **BFS on an external typed graph** resolves the tool chain — deterministic, no training
- **Zero hallucination by construction** — the graph can only return registered tools on valid paths
- **Works with any off-the-shelf LLM** — tested with Qwen 14B, no fine-tuning

GRAFT's own evaluation notes that constrained graph search achieves "perfect dependency legality (ELR=1.0)" but dismisses it due to "much lower EM." They didn't investigate whether better intent extraction (our type prediction step) could close that EM gap without training. That's our contribution.

## What we are NOT claiming

- We are not claiming a novel graph algorithm. BFS over typed edges is straightforward.
- We are not claiming to beat GRAFT/GNN4Plan on their benchmarks. We haven't run those benchmarks.
- We are not claiming this works for all domains. We've validated on K8s tooling (135 tools, 25 queries).

## What we ARE claiming

1. **The decomposition matters.** Separating intent extraction (LLM) from structural resolution (graph) outperforms both brute-force (F1=0.62) and retrieval-based (F1=0.59) approaches without any training.
2. **Small models suffice.** Qwen 14B achieves F1=0.90 on type prediction because the task is simple — predict 2 strings from a known vocabulary, not reason about 135 tools.
3. **Structural guarantees have practical value.** Zero hallucination and perfect multi-hop composition (F1=1.00) are properties that retrieval and brute-force cannot provide regardless of model size.
4. **This baseline is missing from the literature.** Papers jump from naive retrieval to trained models without establishing what a simple external graph can achieve.

## Key references

| Paper | Year | Approach | Training? |
|-------|------|----------|-----------|
| [ToolScope](https://arxiv.org/html/2510.20036v2) | 2025 | Embedding retrieval | No |
| [PLaG](https://arxiv.org/abs/2402.02805) | 2024 | Graph serialized in prompt | No |
| [ControlLLM](https://arxiv.org/abs/2310.17796) | 2024 | Task decomposition + graph search | No |
| [GNN4Plan](https://arxiv.org/abs/2405.19119) | 2024 | Graph neural networks | Yes |
| [GAP](https://arxiv.org/html/2510.25320v1) | 2025 | Graph planning + RL | Yes |
| [GRAFT](https://arxiv.org/html/2605.11706) | 2026 | Graph-tokenized LLM | Yes |
| **Ours** | 2025 | Type prediction + BFS | **No** |
