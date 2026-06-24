# Road to Paper

## Current State

We have a working system with benchmarks across 3 domains (k8s, ansible, github) and 3 models (qwen3-14b, granite-4.1-8b, claude-haiku). The core thesis is clear: the graph transforms tool selection into entity classification — a simpler, scalable problem.

## What's Missing

### 1. More Datasets

- Current 3 domains are all infrastructure/DevOps — a reviewer will ask if this generalizes
- Need at least one non-DevOps domain (e.g. data science pipelines, CRM workflows, financial APIs)
- More queries per domain — current ~30 queries each is thin for statistical claims
- Adversarial / out-of-distribution queries to test failure modes

### 2. Confidence Intervals

- All metrics (F1, recall, precision) are reported as point estimates
- Need bootstrap confidence intervals (95% CI) on all aggregate metrics
- Per-model and per-strategy comparisons need error bars
- Without CIs, a reviewer can't tell if F1=0.95 vs F1=0.72 is signal or noise

### 3. Statistical Significance

- Paired tests (McNemar or permutation test) for strategy comparisons: is graph better than baseline, or is the difference within noise?
- Effect sizes, not just p-values
- Multiple comparison correction if testing many strategy pairs (Bonferroni or Holm)
- The claim "graph topology predicts performance" needs a correlation test (Spearman) with a p-value, not just a table

### 4. Cross-Domain Validation

- Show the approach works across domains without domain-specific tuning
- Train type classifier on one domain, test on another (zero-shot transfer)
- Demonstrate that graph structure is the variable, not prompt engineering

### 5. Failure Analysis

- Systematic categorization of failure modes, not anecdotal
- Confusion matrix for type prediction (which types get confused with which)
- Per-query breakdown: where does the LLM fail, where does the graph fail, where do both fail
- Decomposed recall (Recall_total ≈ Recall_types × Recall_graph) — validate this equation empirically
- Error correlation: do all models fail on the same queries? (if yes, it's a query problem; if no, it's a model problem)

### 6. Related Work

- Tool selection literature: Toolformer, Gorilla, ToolBench, API-Bank
- Planning and composition: TaskMatrix, HuggingGPT, Chameleon
- Type systems in AI: how typed APIs have been used in program synthesis
- Graph-based reasoning: knowledge graphs for QA, GNN-based tool recommendation
- Search space reduction: retrieval-augmented tool selection, hierarchical tool organization
- Position the contribution: "existing work gives the LLM all tools and hopes it picks right; we constrain the problem structurally"
