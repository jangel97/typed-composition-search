# Typed Composition Routing: Tool Selection via Entity Type Decomposition

*Full conference paper draft (~9 pages in ICLR/NeurIPS format)*

---

## Abstract

As LLM agents integrate with increasingly large tool ecosystems, tool routing---determining which tools to invoke for a user query---becomes a critical bottleneck. Existing approaches formulate routing as direct tool selection, requiring the model to simultaneously identify relevant tools, infer multi-step compositions, and ensure structural validity. We propose Typed Composition Routing (TCR), a reformulation that decomposes routing into semantic reasoning (entity type prediction) and compositional reasoning (graph search over a typed composition graph). Tools are modeled as typed transformations between entity types; the LLM predicts source and target types, and deterministic graph search generates structurally valid tool chains. Across four LLMs, five domains (54--170 tools), and 140 queries, TCR improves F1 in all 20 model--domain combinations (avg +0.32) with zero hallucinated invocations. On a production MCP server with 1,060 tools, a lightweight trained encoder (475K parameters) achieves 93% recall while reducing prompt tokens by 97.7%. A granularity experiment across two domains reveals that the type ontology is a tunable design lever with a measurable crossover between routing benefit and classification cost, identifying the type system as a co-design parameter alongside the prediction model.

---

## 1. Introduction

Large Language Model (LLM) agents increasingly rely on external tools to answer questions and perform real-world tasks. As tool ecosystems grow from tens to hundreds or thousands of available APIs, a fundamental question arises: *how should an agent determine which tools to invoke for a given query?*

This problem---*tool routing*---is typically formulated as direct tool selection: given a natural language query, the LLM selects tools from the full catalog. The formulation is natural and works for small catalogs. But it requires the model to solve a compound problem in a single step: identify which tools are relevant, infer a valid multi-step composition, and verify that the resulting sequence is executable. As catalogs grow, this compound problem becomes increasingly brittle. Context windows fill with tool descriptions, the combinatorial space of possible tool sequences explodes, and the model has no structural signal to distinguish valid compositions from invalid ones. The result is missed tool chains, hallucinated tool invocations, and outputs whose compositional validity cannot be verified without execution.

We argue that these difficulties arise from formulating routing at the wrong level of abstraction. Direct tool selection conflates two fundamentally different reasoning tasks:

- **Semantic reasoning:** What domain entities does the user refer to?
- **Compositional reasoning:** What sequence of typed transformations connects those entities?

These tasks have different structure and are best solved by different mechanisms. Semantic reasoning---mapping natural language to domain concepts---is a strength of language models. Compositional reasoning---ensuring type-compatible tool sequences---is a structural constraint that can be solved exactly by graph algorithms.

A key observation motivates the reformulation: user intent is expressed over domain objects, not tools. "Get the logs for pods in the production namespace" refers to entity types (Namespace, PodLogs) without naming any tool. The tools connecting these entities follow deterministically from the composition graph.

We propose **Typed Composition Routing (TCR)**, which makes this decomposition explicit. Each tool is modeled as a typed transformation (e.g., get_pod_logs: Pod -> PodLogs). Tools form a directed composition graph through shared entity types. Given a query, the LLM predicts source and target entity types; graph search then generates structurally valid tool chains. Where direct routing maps *q -> {t_1, ..., t_k}*, TCR factorizes this into type prediction *q -> (e_src, e_tgt)* followed by candidate generation *(e_src, e_tgt) -> {[t_1, ..., t_l]}*.

This assumption---that tool ecosystems expose typed transformation graphs---holds naturally for typed API ecosystems (cloud platforms, infrastructure automation, enterprise services) where the composition graph can be derived automatically from OpenAPI specifications. Domains without typed interfaces fall outside this formulation.

**Contributions:**

1. A **reformulation of tool routing** that decomposes it into semantic reasoning (entity type prediction) and structural candidate generation (graph search), reducing the LLM's role from tool selection to entity type classification (\S3).

2. An **analytical recall decomposition** that separates end-to-end performance into type prediction accuracy and graph reachability, enabling failures to be attributed to one component or the other (\S3.3).

3. **Empirical validation** across four LLMs, five tool domains, and 140 queries, demonstrating consistent improvements over direct selection and embedding retrieval (avg F1 +0.32) with zero hallucinated invocations (\S5).

4. Evidence that the **type ontology is a tunable design lever**: a granularity experiment on a K8s subset (17 tools) and AAP (1,060 tools) shows that finer types improve oracle routing monotonically, while end-to-end performance has a crossover point determined by encoder capacity (\S5.4).

---

## 2. Related Work

| Method | Predicts | Graph | Training | Validity |
|---|---|---|---|---|
| Direct selection | Tools | No | No | No |
| Retrieval | Tools | No | No | No |
| Graph-based planning | Tools/Tasks | Yes | Yes | Yes |
| Agent reasoning | Tools | No | No | No |
| **TCR (ours)** | **Types** | **Yes** | **Optional*** | **Yes** |

*\*TCR's type prediction can use zero-shot LLM prompting (no training) or a lightweight trained encoder (475K params). The encoder is optional but improves latency and recall at production scale (\S5.3).*

### Direct Tool Selection

Most tool-routing systems formulate the problem as selecting tools directly from a catalog. ToolLLM, Gorilla, and Toolformer train or adapt LLMs to decide when and how to invoke APIs. ToolBench and API-Bank provide evaluation frameworks. ToolScope combines tool merging with hybrid retrieval. ToolGen reformulates selection as token generation. AnyTool introduces hierarchical category-based retrieval. Across these approaches, the final prediction target remains the tool itself.

### Graph-Constrained Planning

Several works incorporate graph structure. ControlLLM combines a bipartite graph of resource types with tools for multimodal task planning---the closest related work, but addressing multimodal resource routing (orchestrating vision, audio, and language models) rather than API tool routing over typed domain entities. ToolNet organizes tools in a weighted directed graph based on co-occurrence. GNN4Plan, GRAFT, and GAP integrate graph neural networks with LLMs. ToolFlow constructs parameter-level tool graphs for training data synthesis. These approaches demonstrate that graph structure improves compositional reasoning, but the LLM ultimately reasons about tools or tasks rather than predicting entity types.

### Compositional Agents

General-purpose agent frameworks (HuggingGPT, Chameleon, ReAct) rely on LLM reasoning for multi-step composition with no structural validity guarantees.

### The Remaining Gap

A common thread: the LLM's prediction target is the tool itself. AnyTool introduces organizational categories and ToolFlow uses type similarity, but neither reformulates the prediction target. Existing work improves tool routing *within* the tool-selection formulation. Our work questions the formulation itself---shifting the prediction target from tools to entity types, and delegating composition to deterministic graph search.

---

## 3. Method

### 3.1 Problem Formulation

Existing approaches formulate routing as direct selection:

*g(q) -> {t_1, ..., t_k} in T*

This requires the model to simultaneously identify relevant tools and produce a valid execution order.

We instead formulate routing over typed entities. Let *E = {e_1, ..., e_n}* denote entity types in a domain. Each tool is a typed transformation:

*t_k: e_i -> e_j,  where e_i, e_j in E*

### 3.2 Typed Composition Graph

The tool registry induces a directed graph *G = (E, T)* where entity types are nodes and tools are directed edges. An edge from *e_i* to *e_j* exists whenever a tool *t_k: e_i -> e_j* is available. Multiple tools may connect the same pair.

### 3.3 Routing Decomposition

Routing is decomposed into two stages:

**Stage 1 (Semantic):** The LLM predicts source and target entity types:

*f(q) -> (e_src, e_tgt)*

**Stage 2 (Compositional):** Deterministic graph search recovers the shortest valid composition:

*pi(q) = Path(G, f_src(q), f_tgt(q))*

Unlike retrieval or direct LLM selection---which can return tools outside the registry or propose sequences whose types are incompatible---graph search guarantees structural validity:

**Proposition 1 (Structural validity).** If *pi(q)* returns a non-empty sequence *[t_1, ..., t_l]*, then (i) every *t_i* belongs to the registry, and (ii) for every adjacent pair, the output type of *t_i* matches the input type of *t_{i+1}*. This follows directly from graph search traversing only registered edges.

**Corollary (Zero hallucinated tools).** *pi(q)* cannot return a tool not in *T*.

### 3.4 Recall Decomposition

End-to-end recall decomposes as:

*R = P_c * R_c + (1 - P_c) * R_wrong*

where *P_c* = probability both predicted types are correct, *R_c* = recall conditioned on correct predictions, *R_wrong* = recall conditioned on incorrect predictions.

This separates LLM quality (*P_c*) from graph quality (*R_c*) and provides two independent improvement levers: better type prediction improves *P_c*; richer graph connectivity improves *R_wrong*.

### 3.5 Graph-Constrained Reasoning

Once a target type is predicted, reverse reachability eliminates source types that cannot reach that target:

*pruning(e_tgt) = 1 - |R^{-1}(e_tgt)| / |E|*

Median entity pruning across domains is 75%: for a typical query, three-quarters of source candidates are structurally eliminated.

---

## 4. Experimental Setup

### 4.1 Domains

| Domain | Tools | Types | T/T% | Pruning |
|---|---|---|---|---|
| Kubernetes | 135 | 41 | 30% | 63% |
| Ansible | 108 | 40 | 37% | 67% |
| GitHub | 133 | 44 | 33% | 56% |
| CI/CD | 54 | 51 | 94% | 87% |
| Shopify | 170 | 61 | 35% | 78% |
| AAP MCP | 1,060 | 50 | 5% | -- |

Benchmark registries are constructed from API documentation. The AAP MCP domain is the official Ansible Automation Platform MCP Server (1,060 operations across four enterprise services), with its composition graph derived automatically from OpenAPI specifications.

### 4.2 Models

Four LLMs spanning different architectures and scales: Granite 4.1 8B (IBM, instruction-tuned), Qwen3-14B (Alibaba, open-weight), GPT-OSS-20B (an open-weight 20B-parameter model based on the GPT architecture), and Claude Haiku 4.5 (Anthropic, optimized for speed). All evaluated off-the-shelf without fine-tuning.

### 4.3 Queries

140 manually authored queries for benchmark domains (25--30 per domain) and 120 for AAP. Six categories: clean, multi-hop, noisy, synonym, ambiguous, multi-path. All queries were authored by the paper's authors, with annotations finalized before any evaluation runs to prevent post-hoc adjustment. We acknowledge this as a limitation; future work should validate with independently annotated queries or inter-annotator agreement studies.

### 4.4 Strategies

- **Baseline:** direct tool selection from complete catalog via prompt-based selection
- **Retrieval:** top-10 tools by embedding similarity (nomic-embed-text-v1.5)
- **TCR** (ours): entity type prediction followed by graph search
- **TCR + Encoder:** lightweight domain-specific classifier replaces the LLM
- **Oracle:** graph search with ground-truth entity types

### 4.5 Metrics

End-to-end: precision, recall, F1 over predicted and expected tool sets. Structural validity: hallucinated tool invocations. Type prediction: source accuracy, target accuracy, exact match. Graph: entity pruning.

---

## 5. Results

### 5.1 Main Results

TCR improves F1 in every model--domain combination (20/20, avg +0.32):

| Model | Baseline | Retrieval | TCR | Oracle |
|---|---|---|---|---|
| Granite 4.1 8B | 0.49 | 0.47 | **0.85** | 1.00 |
| Qwen3-14B | 0.58 | 0.58 | **0.84** | 1.00 |
| GPT-OSS-20B | 0.45 | 0.53 | **0.83** | 1.00 |
| Haiku 4.5 | 0.56 | 0.57 | **0.84** | 1.00 |

*Average F1 across 5 domains. All TCR outputs produce zero hallucinated tools. Full per-domain breakdown in Appendix A.*

Effect size: bootstrap 95% CI for the mean F1 improvement is [+0.27, +0.37]. Wilcoxon signed-rank: p < 10^-30 (560 query-level paired comparisons).

The improvement is consistent across all domains, with the largest gains where baseline performance is weakest (Ansible: +0.30 to +0.47). Embedding retrieval provides modest improvements over direct selection but does not enforce compositional validity and cannot recover multi-step chains whose intermediate tools lack lexical overlap with the query.

### 5.2 Recall Decomposition

| Model | P_c | R_c | R_wrong |
|---|---|---|---|
| Granite 8B | 0.54 | 0.95 | 0.33 |
| Qwen3 14B | 0.60 | 0.96 | 0.24 |
| GPT-OSS 20B | 0.62 | 0.92 | 0.29 |
| Haiku 4.5 | 0.65 | 0.95 | 0.30 |

When entity types are correct, recall averages 0.95---the graph reliably recovers correct workflows. Incorrect types still recover part of the workflow (R_wrong avg 0.29), because neighboring types share downstream graph paths.

### 5.3 Production Scale: 1,060 Tools

On the AAP MCP Server, presenting all tool schemas requires ~16,000 prompt tokens per query.

| Strategy | Recall | Tokens | Halluc. | Latency |
|---|---|---|---|---|
| Direct selection | 0.58 | 25,433 | 10 | --- |
| TCR + LLM predictor | 0.42 | 66 | 0 | 6,579 ms |
| TCR + Encoder (475K) | **0.93** | **66** | **0** | **6.8 ms** |

The trained encoder (frozen all-MiniLM-L6-v2 + dual-head MLP, 475K trainable parameters) achieves 93% recall at 6.8ms latency---three orders of magnitude faster than LLM prediction.

Per-category breakdown (AAP, 120 queries):

| Category | N | Encoder Recall | Candidates |
|---|---|---|---|
| Clean | 35 | 1.000 | 4.8 |
| Synonym | 20 | 0.900 | 5.6 |
| Multi-hop | 20 | 0.975 | 5.9 |
| Ambiguous | 15 | 0.933 | 8.6 |
| Noisy | 15 | 1.000 | 5.6 |
| Multi-path | 15 | 0.933 | 8.5 |

The encoder achieves perfect recall on clean and noisy queries. Multi-hop routing is handled entirely by graph search after the encoder predicts start and end types.

### 5.4 Ontology Granularity Experiment

We investigate whether the entity type system itself is a tunable lever for routing quality. On two domains at different scales, we construct three ontology variants---coarse, medium, fine---varying only the type system while keeping all tools and queries fixed.

**K8s subset (17 tools, 50 queries):**

The coarse ontology (6 types) merges aggressively: Deployment, Service, Node all become "Resource." The medium ontology (13 types) uses natural K8s distinctions. The fine ontology (21 types) splits by operation: inspecting a pod (-> PodDetail) differs from deleting one (-> Pod).

| | Coarse (6) | Medium (13) | Fine (21) |
|---|---|---|---|
| Oracle precision | 0.325 | 0.510 | **0.626** |
| Oracle recall | 1.000 | 1.000 | 1.000 |
| Oracle F1 | 0.442 | 0.608 | **0.713** |
| Avg candidates | 5.2 | 3.8 | **2.6** |
| Token reduction | 69.5% | 76.4% | **83.7%** |
| E2E exact match | 0.820 | **0.880** | 0.840 |
| E2E F1 | 0.391 | 0.550 | **0.647** |

At K8s scale, finer types are strictly better on both oracle and E2E metrics. E2E F1 improves from 0.39 to 0.65 despite a small dip in exact match (0.88 -> 0.84). The precision gains from smaller candidate sets (5.2 -> 2.6 tools) more than compensate for the classification penalty.

**AAP (1,060 tools, 120 queries):**

The coarse ontology (8 types) merges by domain (Job, Inventory, Credential...). Medium (50 types) uses the natural AAP resource types. Fine (88 types) splits self-loop operations: listing jobs (-> JobListing) differs from cancelling one (-> Job).

| | Coarse (8) | Medium (50) | Fine (88) |
|---|---|---|---|
| Oracle precision | 0.016 | 0.108 | **0.150** |
| Oracle recall | 0.958 | **1.000** | 0.988 |
| Oracle F1 | 0.031 | 0.173 | **0.230** |
| Avg candidates | 116.0 | 25.6 | **21.5** |
| Token reduction | 89.0% | 97.7% | **98.1%** |
| E2E exact match | 0.708 | **0.875** | 0.400 |
| E2E recall | 0.821 | **0.933** | 0.567 |
| E2E F1 | 0.025 | **0.164** | 0.144 |

Oracle routing improves monotonically with finer types on both domains. But end-to-end performance reveals a **crossover**: at K8s scale (21 types), the encoder maintains 84% accuracy and finer types still help. At AAP scale (88 types), the encoder collapses to 40% exact match, dragging E2E F1 below the medium ontology (0.144 vs 0.164) despite better oracle routing (0.230 vs 0.173).

**The mechanism:** Finer types reduce tools-per-type-pair (7.5 -> 3.6 -> 3.2 on AAP), shrinking candidate sets. But each new type requires training data. The 38 fine types added to AAP had ~10 training examples each, insufficient for reliable classification. When the encoder correctly predicts fine types, it achieves F1 = 0.255 (the best of any variant). But it only gets 40% of queries right, versus medium's 88%.

**Practical implication:** The type system should be co-designed with the encoder's capacity. A design heuristic emerges: split types until each type-pair maps to roughly one tool, but stop before classification accuracy degrades below ~60% exact match---below that threshold, keyword matching against tool descriptions outperforms incorrect type routing.

---

## 6. Discussion

### Why does the decomposition help?

Three complementary mechanisms. First, the LLM's prediction target shifts from the tool catalog to a smaller entity type space, which graph reachability further constrains. Second, graph search restricts outputs to compositionally valid paths. Third, every returned workflow is structurally valid by construction, eliminating hallucinated invocations.

### Why multi-hop benefits most

To correctly route a k-hop query, direct selection must predict k tools in order. TCR predicts two entity types regardless of chain length---graph search recovers intermediate tools the user never mentioned. "Get the logs for pods in production" requires three tools, but the user refers only to chain endpoints (Namespace, PodLogs). This constant-complexity prediction explains why multi-hop queries show the largest gap between TCR and direct selection.

### Does TCR present a more tractable task?

Across all model--domain combinations, LLMs correctly predict both entity types in 61% of cases, compared to only 12% where direct tool selection achieves perfect results (F1 = 1.0). Users naturally describe domain objects ("pods", "payments", "credentials") rather than implementation mechanisms; entity type prediction aligns with how queries are already phrased.

### Error profile

The decomposition shifts errors from false positives to false negatives: TCR eliminates hallucinated tools and invalid compositions; remaining errors arise only from incorrect type predictions. Precision increases from 0.48 to 0.88 (+83%), while recall increases from 0.67 to 0.83. In safety-critical domains, returning no result is preferable to invoking incorrect tools.

### Relationship to retrieval

Retrieval-augmented selection ranks tools by embedding similarity. This is complementary: retrieval ranks individual tools, while composed queries require multi-step chains whose intermediate tools may have no lexical overlap with the query. "What is the last ARM artifact in the latest production drop" has high similarity to an artifact-retrieval tool, but prerequisite steps (listing drops, selecting a build) rank low---they are structurally necessary but semantically invisible. Retrieval can eliminate tools that a valid composition requires; graph search cannot.

### The granularity design space

The granularity experiment reveals that the type system is not just scaffolding but a continuous design parameter with a measurable optimum. Across both K8s and AAP, the same pattern holds: oracle performance improves monotonically with finer types (smaller candidate sets, higher precision), but end-to-end performance has a peak determined by the encoder's classification capacity. The crossover is visible at 88 types on AAP---the first empirical demonstration that finer types can hurt end-to-end routing despite improving oracle quality.

This yields a practical co-design heuristic: **split types until each type-pair maps to roughly one tool, but stop before classification accuracy degrades below ~60% exact match.** Below that threshold, the precision gained from smaller candidate sets is overwhelmed by the recall lost from misclassified types. For AAP, the natural 50-type ontology is the sweet spot---fine enough for 97.7% token reduction with 93% recall, coarse enough for 87.5% classification accuracy. This heuristic is specific to the encoder architecture and training data regime studied here, but the principle---co-optimize ontology expressiveness with classifier learnability---generalizes.

### Limitations

TCR assumes tools can be modeled as typed transformations, which holds for typed API ecosystems but not for imperative operations without typed outputs. The current graph models unary transformations and sequential workflows only; multi-input dependencies would require hypergraph edges (one edge consuming multiple entity types), and parallel composition would require DAG search rather than path search. The core decomposition---predict types, then search---would still apply, but the graph formulation and search algorithm would need extension. When multiple tools share the same type signature (list vs. create on the same entity pair), intent-level selection among candidates remains. The composition graph must be maintained as tools evolve. The granularity crossover point likely depends on training data availability, model capacity, and domain structure---we demonstrate it on two domains but cannot yet predict it analytically.

Recall is bounded by annotation completeness, not just prediction quality. Even with perfect type prediction, tools whose type relationships are not explicitly modeled will be missed by graph search. For example, a generic listing tool that outputs `Resource` will not appear on a path targeting `VirtualMachine` unless the ontology encodes subtype relationships. In a 178-query evaluation on a production MCP server, perfect type prediction yielded 97.8% recall---the remaining 2.2% were annotation gaps where expected tools required implicit subtype or cross-domain relationships not captured in the graph. This suggests that annotation completeness is a first-order concern for deployment, and that subtype hierarchies or interface-based type matching could close this gap.

---

## 7. Conclusion

The standard formulation of tool routing asks the model to predict tools. Our results suggest this is the wrong prediction target. When the model predicts entity types instead and graph search handles composition, routing becomes simpler, more reliable, and more scalable---consistently outperforming direct selection across four language models, five benchmark domains, and a production system with over one thousand tools.

The decomposition eliminates hallucinated invocations by construction. The recall decomposition reveals that end-to-end performance separates cleanly into type prediction quality and graph reachability---two independent and actionable levers. A compact domain-specific classifier (475K parameters) achieves 93% recall on a 1,060-tool production registry, confirming that the semantic component can be served by lightweight models rather than frontier LLMs.

The granularity experiment adds a new dimension: the type ontology itself is a design lever with a measurable optimum. Finer types improve oracle routing monotonically, but end-to-end quality has a crossover point where classification cost exceeds routing benefit. This crossover---observed at 88 types on AAP---suggests that ontology design should be co-optimized with the type prediction model. The practical sweet spot balances type expressiveness against encoder learnability, and this balance depends on training data, model capacity, and domain structure.

More broadly, improving tool routing may require changing the prediction target---from tools to the domain abstractions that organize them---rather than building increasingly capable tool-selecting language models.

---

## References

*[To be populated from v2 reference list:*
- *Yao et al. (2023) - ReAct*
- *Shen et al. (2023) - HuggingGPT*
- *Li et al. (2025) - ToolScope*
- *Qin et al. (2024) - ToolLLM*
- *Patil et al. (2024) - Gorilla*
- *Schick et al. (2023) - Toolformer*
- *Xu et al. (2023) - ToolBench*
- *Li et al. (2023) - API-Bank*
- *Wang et al. (2025) - ToolGen*
- *Du et al. (2024) - AnyTool*
- *Zhang et al. (2024) - ControlLLM*
- *Lin et al. (2024) - PLaG*
- *Liu et al. (2024) - ToolNet*
- *Wang et al. (2024) - GNN4Plan*
- *Li et al. (2025) - GRAFT*
- *Li et al. (2025) - GAP*
- *Wang et al. (2025) - ToolFlow*
- *Lu et al. (2023) - Chameleon*
- *Shen et al. (2024) - TaskBench]*

---

## Appendix (not counted toward page limit)

### A. Full Per-Domain Results

| Model | Domain | Base P | Base R | Base F1 | TCR P | TCR R | TCR F1 | Delta |
|---|---|---|---|---|---|---|---|---|
| Granite 8B | Kubernetes | 0.49 | 0.66 | 0.53 | 0.93 | 0.85 | 0.87 | +0.33 |
| | Ansible | 0.27 | 0.51 | 0.34 | 0.83 | 0.83 | 0.81 | +0.47 |
| | GitHub | 0.35 | 0.49 | 0.36 | 0.95 | 0.88 | 0.90 | +0.54 |
| | CI/CD | 0.44 | 0.68 | 0.51 | 0.91 | 0.72 | 0.78 | +0.27 |
| | Shopify | 0.63 | 0.85 | 0.69 | 0.93 | 0.90 | 0.90 | +0.22 |
| Qwen3 14B | Kubernetes | 0.60 | 0.70 | 0.60 | 0.94 | 0.90 | 0.91 | +0.31 |
| | Ansible | 0.36 | 0.52 | 0.41 | 0.73 | 0.69 | 0.71 | +0.30 |
| | GitHub | 0.54 | 0.66 | 0.56 | 0.88 | 0.78 | 0.82 | +0.25 |
| | CI/CD | 0.49 | 0.63 | 0.52 | 0.87 | 0.88 | 0.84 | +0.33 |
| | Shopify | 0.83 | 0.81 | 0.79 | 0.96 | 0.90 | 0.92 | +0.13 |
| GPT-OSS 20B | Kubernetes | 0.52 | 0.62 | 0.55 | 0.89 | 0.81 | 0.83 | +0.28 |
| | Ansible | 0.25 | 0.46 | 0.32 | 0.79 | 0.74 | 0.76 | +0.44 |
| | GitHub | 0.43 | 0.61 | 0.46 | 0.95 | 0.87 | 0.89 | +0.44 |
| | CI/CD | 0.49 | 0.70 | 0.54 | 0.84 | 0.79 | 0.79 | +0.25 |
| | Shopify | 0.36 | 0.53 | 0.39 | 0.92 | 0.89 | 0.90 | +0.51 |
| Haiku 4.5 | Kubernetes | 0.49 | 0.81 | 0.58 | 0.94 | 0.90 | 0.91 | +0.33 |
| | Ansible | 0.22 | 0.56 | 0.30 | 0.78 | 0.74 | 0.75 | +0.45 |
| | GitHub | 0.53 | 0.76 | 0.59 | 0.88 | 0.91 | 0.88 | +0.29 |
| | CI/CD | 0.48 | 0.75 | 0.55 | 0.71 | 0.83 | 0.73 | +0.18 |
| | Shopify | 0.74 | 0.91 | 0.80 | 0.96 | 0.94 | 0.95 | +0.15 |

### B. Type Prediction by Category

| Category | Source Acc | Target Acc | Both |
|---|---|---|---|
| Clean | 0.82 | 0.95 | 0.81 |
| Multi-hop | 0.65 | 0.96 | 0.64 |
| Noisy | 0.57 | 0.84 | 0.54 |
| Synonym | 0.71 | 0.61 | 0.50 |
| Ambiguous | 0.58 | 0.32 | 0.25 |
| Multi-path | 0.53 | 0.69 | 0.38 |

### C. Granularity Experiment Details

**K8s ontology variants:**

| Level | Types | Strategy |
|---|---|---|
| Coarse | 6 | Merge aggressively: Deployment, Service, Node -> "Resource" |
| Medium | 13 | Natural K8s resource kinds |
| Fine | 21 | Split by operation: PodDetail, PodLog, PodCreation |

**AAP ontology variants:**

| Level | Types | Strategy |
|---|---|---|
| Coarse | 8 | Merge by domain: Job, Inventory, Credential, Platform, Identity, Workflow, EDA, Auth |
| Medium | 50 | Natural AAP resource types |
| Fine | 88 | Split self-loops: _list -> *Listing, _retrieve -> *Detail |

### D. Correlation Analysis

| Variable pair | r (K8s) | r (AAP) |
|---|---|---|
| candidate_count vs precision | -0.81 | -0.41 |
| n_types vs candidate_count | -0.37 | -0.63 |
| tools_per_pair vs precision | -0.35 | -0.38 |

The weaker correlation on AAP reflects the compressed precision range at production scale---most queries have precision below 0.10 regardless of candidate count.

### E. Encoder Architecture

Frozen sentence encoder (all-MiniLM-L6-v2, 384 dims) + shared MLP hidden layer (256 dims) + two classification heads (source type, target type). Total trainable parameters: ~143K (K8s, 13 types) to ~475K (AAP, 50 types). Training: 5-fold stratified CV, 200 epochs, cosine annealing LR schedule.
