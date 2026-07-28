# Typed Composition Routing: Tool Selection via Entity Type Decomposition

*Workshop paper draft (~4-6 pages in NeurIPS format)*

---

## Abstract

As LLM agents integrate with large tool ecosystems, tool routing---determining which tools to invoke for a query---becomes a bottleneck. Direct tool selection requires the model to simultaneously identify relevant tools, infer multi-step compositions, and ensure structural validity. We propose Typed Composition Routing (TCR), which decomposes routing into semantic reasoning (predicting source and target entity types) and compositional reasoning (graph search over a typed composition graph). Across four LLMs, five domains (54--170 tools), and 140 queries, TCR improves F1 in all 20 model--domain combinations (avg +0.32) with zero hallucinated invocations. On a production MCP server with 1,060 tools, a lightweight encoder (475K parameters) achieves 96% recall while reducing prompt tokens by 99.7%. A granularity experiment across two domains reveals that the type ontology is a tunable design lever with a measurable crossover between routing benefit and classification cost.

---

## 1. Introduction

LLM agents increasingly rely on external tools, but as catalogs grow from tens to thousands of APIs, tool routing becomes fragile. Direct selection requires the model to solve a compound problem: identify relevant tools, infer valid compositions, and verify structural correctness---all in one step.

We observe that user intent is expressed over domain objects, not tools. "Get the logs for pods in production" refers to entity types (Namespace, PodLogs) without naming any tool. The tools connecting these entities follow from the type structure.

This motivates **Typed Composition Routing (TCR)**: decompose routing into (1) **semantic reasoning**---the LLM predicts source and target entity types---and (2) **compositional reasoning**---graph search generates structurally valid tool chains connecting those types. The composition graph is derived automatically from typed API specifications.

**Contributions:**
1. A decomposition of tool routing into entity type prediction + graph search, providing compositional validity guarantees and zero hallucinated invocations.
2. Empirical validation across 4 LLMs, 5 domains, and a 1,060-tool production system, showing consistent improvements over direct selection (avg F1 +0.32) and embedding retrieval.
3. Evidence that ontology granularity is a direct lever for routing quality, with a granularity experiment on two domains identifying the crossover point where classification cost exceeds routing benefit.

---

## 2. Method

### 2.1 Typed Composition Graph

Each tool is modeled as a typed transformation: tool *t* maps entity type *e_i* to *e_j*. The tool registry induces a directed graph *G = (E, T)* where entity types are nodes and tools are edges. A valid multi-step workflow is a path in *G*.

### 2.2 Routing Decomposition

Given a query *q*, TCR operates in two stages:

**Stage 1 (Semantic):** Predict source and target entity types:
  *f(q) -> (e_src, e_tgt)*

**Stage 2 (Compositional):** Graph search generates the set of structurally valid tool chains connecting those types:
  *Search(G, e_src, e_tgt) -> {[t_1, ..., t_l]}*

**Structural guarantee:** Every returned tool belongs to the registry and adjacent tools are type-compatible. Graph search cannot produce nonexistent tool invocations. For most queries, the candidate set contains exactly one chain; when multiple valid chains exist, intent-level selection among guaranteed-valid candidates is a separable concern.

**Example.** Given the query *"Get the logs for pods in the production namespace"*:
- **Stage 1:** The LLM predicts source type = Namespace, target type = PodLogs.
- **Stage 2:** Graph search finds the shortest path: Namespace -> Pod -> PodLogs.
- **Output:** [list_namespaced_pods, get_pod_logs] — a two-tool chain the user never named explicitly.

Direct selection must identify both tools and their ordering; TCR predicts only the chain endpoints.

### 2.3 Related Work

Existing tool-routing methods fall into three categories. *Direct selection* trains or prompts LLMs to choose tools from catalogs (ToolLLM, Gorilla, Toolformer, AnyTool). *Graph-constrained planning* adds structure---ControlLLM uses a bipartite resource-tool graph for multimodal routing; ToolNet and GNN4Plan incorporate co-occurrence or GNN-based graphs. *Agent frameworks* (HuggingGPT, ReAct) rely on LLM reasoning with no structural guarantees. In all cases, the prediction target remains the tool itself. TCR shifts the target to entity types, delegating composition to deterministic graph search.

---

## 3. Experiments

### 3.1 Setup

**Domains:** Five benchmark domains (Kubernetes 135 tools, Ansible 108, GitHub 133, CI/CD 54, Shopify 170) plus production-scale AAP (1,060 tools, 50 entity types).

**Models:** Granite 4.1 8B (IBM), Qwen3-14B (Alibaba), GPT-OSS-20B (open-weight, GPT architecture), Claude Haiku 4.5 (Anthropic)---all evaluated zero-shot without fine-tuning.

**Baselines:** (1) Direct selection (full catalog in prompt), (2) Embedding retrieval (top-10 by cosine similarity), (3) Oracle (gold entity types).

**Queries:** 140 benchmark queries (6 categories: clean, multi-hop, noisy, synonym, ambiguous, multi-path) + 120 AAP queries. All queries and gold annotations were authored by the paper's authors following a fixed protocol: queries were written from API documentation without reference to the routing system, expected tool chains were determined by manual inspection of the type graph, and all annotations were finalized and frozen before any evaluation runs. No annotations were revised after observing system outputs. We acknowledge that author-authored benchmarks may unintentionally favor the proposed approach and note that independent annotation or inter-annotator agreement studies would strengthen future evaluations.

### 3.2 Main Results

TCR improves F1 in every model--domain combination (20/20):

| Model | Baseline | Retrieval | TCR | Oracle |
|---|---|---|---|---|
| Granite 4.1 8B | 0.49 | 0.47 | **0.85** | 1.00 |
| Qwen3-14B | 0.58 | 0.58 | **0.84** | 1.00 |
| GPT-OSS-20B | 0.45 | 0.53 | **0.83** | 1.00 |
| Haiku 4.5 | 0.56 | 0.57 | **0.84** | 1.00 |

*Average F1 across 5 domains. All TCR outputs produce zero hallucinated tools.*

The improvement is consistent (Wilcoxon signed-rank p < 10^-30). Largest gains appear where baseline performance is weakest (Ansible: +0.30 to +0.47), suggesting graph constraints are most valuable when unconstrained selection is hardest. Separate experiments with Gemini 2.5 Pro on three additional domains (K8s, AAP, Stripe) confirm the pattern: TCR achieves 88--91% type prediction exact match with zero hallucinations across all three.

### 3.3 Production Scale: 1,060 Tools

On the AAP MCP Server, presenting all tool schemas requires ~25,000 prompt tokens. TCR reduces this to ~66 tokens (entity type names).

| Strategy | Recall | Tokens | Halluc. | Latency |
|---|---|---|---|---|
| Direct selection | 0.58 | 25,433 | 10 | --- |
| TCR + LLM predictor | 0.42 | 66 | 0 | 6,579 ms |
| TCR + Encoder (475K params) | **0.96** | **66** | **0** | **6.8 ms** |

The trained encoder (frozen MiniLM + dual-head MLP) achieves 96% recall at 6.8ms---three orders of magnitude faster than LLM prediction. Average candidate set: 6.1 tools (99.4% reduction from 1,060).

### 3.4 Ontology Granularity Experiment

We test whether the entity type system itself is a tunable lever for routing quality. On a K8s subset (17 tools) and AAP (1,060 tools), we construct three ontology variants---coarse, medium, fine---varying only the type system while keeping tools and queries fixed.

**K8s (17 tools, 50 queries):**

| | Coarse (6 types) | Medium (13) | Fine (21) |
|---|---|---|---|
| Oracle F1 | 0.442 | 0.608 | **0.713** |
| Oracle recall | 0.920 | 0.960 | **0.980** |
| Oracle candidates | 5.2 | 3.8 | **2.6** |
| Token reduction | 69.5% | 76.4% | **83.7%** |
| E2E exact match | 0.820 | **0.880** | 0.840 |
| E2E F1 | 0.391 | 0.550 | **0.647** |

**AAP (1,060 tools, 120 queries):**

| | Coarse (8 types) | Medium (50) | Fine (88) |
|---|---|---|---|
| Oracle F1 | 0.031 | 0.173 | **0.230** |
| Oracle recall | 0.958 | **1.000** | 0.988 |
| Oracle candidates | 116.0 | 25.6 | **21.5** |
| Token reduction | 89.0% | 97.7% | **98.1%** |
| E2E exact match | 0.708 | **0.875** | 0.400 |
| E2E F1 | 0.025 | **0.164** | 0.144 |

Oracle routing improves monotonically with finer types on both domains---candidate sets shrink, precision rises. But end-to-end performance reveals a crossover: at K8s scale (21 types), finer types still help because the encoder maintains 84% accuracy. At AAP scale (88 types), the encoder collapses to 40% exact match, dragging E2E F1 below the medium ontology despite better oracle routing.

The mechanism: finer types reduce tools-per-type-pair (7.5 -> 3.6 -> 3.2 on AAP), shrinking candidate sets. But each new type requires training data. The 38 fine types added to AAP had only ~10 training examples each, insufficient for reliable classification. The crossover occurs where classification penalty exceeds routing benefit.

This has a practical implication: the type system should be designed to match the encoder's capacity. For AAP, the natural 50-type ontology is the sweet spot---fine enough for 99.7% token reduction with 96% recall, coarse enough for 87.5% classification accuracy.

---

## 4. Discussion

**Why is type prediction easier than tool selection?** Users naturally describe intent in terms of domain objects ("pods", "credentials", "inventories"), not implementation mechanisms ("list_namespaced_pods_v1"). Entity types are the vocabulary users already think in; tool names are an implementation detail. This means the LLM's prediction target aligns with how queries are phrased, rather than requiring a translation into an unfamiliar namespace. Empirically, LLMs correctly predict both entity types in 61% of queries, compared to only 12% where direct tool selection achieves perfect results. The smaller target space (|E| << |T|) and graph reachability constraints further reduce the effective prediction difficulty. Multi-hop queries benefit most because TCR predicts two types regardless of chain length.

**The granularity trade-off.** Finer types improve oracle routing monotonically but impose a classification tax. A practical co-design heuristic emerges: split types until each type-pair maps to roughly one tool, but stop before classification accuracy degrades below ~60% exact match. For AAP, the natural 50-type ontology is this sweet spot.

**Limitations and future work.** TCR assumes typed API ecosystems; imperative operations without typed inputs/outputs fall outside the formulation. When multiple tools share the same type signature (e.g., list vs. create), intent-level selection remains. The current formulation handles sequential workflows; multi-input dependencies would require hypergraph edges, and parallel composition would need DAG search. All queries were author-annotated; independently annotated benchmarks would strengthen the evaluation. Additionally, recall can be bounded by the graph annotations rather than prediction quality: even with perfect type prediction, tools whose type relationships are not explicitly modeled in the annotations will be missed. For example, a generic listing tool that outputs `Resource` will not appear on a path targeting `VirtualMachine` unless the ontology encodes subtype relationships. This suggests that annotation completeness---not just prediction accuracy---is a first-order concern for deployment.

---

## 5. Conclusion

Tool routing can be decomposed into semantic reasoning over entity types and compositional reasoning over a typed graph. This decomposition improves routing quality consistently (+0.32 F1 across 20 model--domain combinations), eliminates hallucinated invocations, and scales to production registries with 1,060 tools. A lightweight encoder (475K parameters) replaces the LLM for type prediction, achieving 96% recall at 6.8ms latency.

The granularity experiment reveals that the type system is not just scaffolding but a direct lever for routing quality. Finer types improve oracle performance monotonically, but end-to-end quality has a peak determined by the encoder's classification capacity. This crossover---visible at 88 types on AAP---suggests that ontology design should be co-optimized with the type prediction model, not treated as a fixed input.

More broadly, TCR suggests a modular architecture for tool-using agents, where each tool ecosystem exposes its own typed composition graph. Rather than reasoning over thousands of tool descriptions, an agent can route within the graph corresponding to the target API ecosystem, enabling scalable tool use across independently evolving open-source and proprietary systems. Improving tool routing may require changing the prediction target---from tools to the domain abstractions that organize them---rather than building increasingly capable tool-selecting language models.

---

## References

*[To be populated with the full reference list from v2]*
