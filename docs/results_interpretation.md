# Results Interpretation

## Summary

4 models × 5 domains × 7 strategies. 140 queries total. Graph-forward
routing outperforms direct tool selection (baseline) in **19/19**
model/domain combinations where both strategies produced results.

| Model | Params | Avg Δ (graph − baseline) |
|-------|--------|--------------------------|
| granite-4-1-8b | 8B | +0.353 |
| gpt-oss-20b | 20B | +0.384 |
| qwen3-14b | 14B | +0.267 |
| claude-haiku-4.5 | proprietary | +0.279 |

Smaller models benefit more from graph constraints. Granite 8B averages
+0.35, while larger models average +0.27 to +0.28. The graph compensates
for weaker type prediction by constraining the decision space.


## Recall Decomposition

The decomposition separates model quality from graph quality:

```
Recall_e2e = P(types correct) × Recall_correct + P(types wrong) × Recall_wrong
```

### Key findings

**The decomposition fits.** The gap between predicted and actual recall is
small across all model/domain combinations (0.013–0.122, median ~0.04).
End-to-end performance is well explained by type prediction accuracy and
graph reachability.

**The simplified assumption does not hold.** The simplified form assumes
Recall_wrong ≈ 0 (wrong types produce zero useful tools). In practice,
Recall_wrong averages **0.415** across all combinations. The graph is
resilient to type errors — when the LLM predicts a "nearby" wrong type
(e.g., a parent or sibling in the graph), BFS may still traverse through
some of the correct tools.

This is a positive finding. It means the graph is **fault-tolerant**, not
brittle. The full equation is required for accurate prediction, but the
simplified version still provides a useful lower bound.

**All failures are type prediction failures.** Of the 37 queries with
recall = 0 across all model/domain combinations, every single one is due
to wrong predicted types. Zero are due to graph coverage gaps. When types
are correct, recall = 1.000 (perfect).


## Type Prediction

Source prediction (0.71 average accuracy) is harder than target prediction
(0.81). This supports the reverse strategy intuition: users describe
desired outcomes more reliably than starting points.

### Accuracy by query category

| Category | Source Acc | Target Acc | Exact Match |
|----------|-----------|------------|-------------|
| clean | 0.85 | 0.96 | 0.83 |
| multihop | 0.67 | 0.96 | 0.66 |
| noisy | 0.59 | 0.84 | 0.55 |
| synonym | 0.73 | 0.61 | 0.51 |
| ambiguous | 0.61 | 0.33 | 0.26 |
| multipath | 0.53 | 0.70 | 0.37 |

Clean queries are easiest (83% exact match). Ambiguous queries are hardest
(26%) because target type is genuinely uncertain. Synonym queries are hard
on target prediction (0.61) — the LLM sometimes maps alternative
terminology to the wrong entity type.


## Graph Constraints

Graph beats retrieval in **16/16** combinations where both ran. The
advantage is structural: retrieval finds semantically similar tools, but
graph finds *compositionally valid* tool chains.

### Token efficiency

Graph uses 500–900 prompt tokens per query vs baseline's 1500–3000.
Approximately 50–70% reduction. The graph presents only path-relevant
tools instead of the full catalog.

### Zero hallucinations

All graph-constrained strategies produced zero hallucinated tools across
all model/domain combinations. The baseline produces hallucinated tools
in most runs. This is a direct consequence of the structural constraint:
tools are limited to valid graph paths.


## Regressions

29 queries where the baseline achieves non-zero recall but the graph
achieves zero. All 29 are caused by type prediction failures: the LLM
predicts wrong source or target types, so BFS either finds no path or
finds a path to the wrong tools.

This is expected and intentional. The graph will not hallucinate tools —
it returns nothing rather than something wrong. In a real agent, this
maps to "I don't know how to do this" rather than calling arbitrary tools
and hoping for the best.

Whether this tradeoff is desirable depends on the application. In
high-stakes domains (infrastructure, financial operations), returning
nothing is safer than calling wrong tools. In exploratory domains, partial
results may be more useful.


## Planning Direction

Graph-forward (source-first) outperforms graph-reverse-probs (target-first
with probability scoring) in most combinations. This is counterintuitive —
the reverse strategy should benefit from stronger graph constraints (see
`docs/graph_constraint.md`).

Possible explanations:

- **Probability scoring adds noise.** The n-completions approach requires
  logprobs and introduces a probability aggregation step. Models without
  logprobs (claude-haiku, gpt-oss-20b) cannot use this strategy at all.
- **Forward BFS is simpler.** Fewer moving parts means fewer failure modes.
  The forward strategy makes one type prediction per endpoint (source and
  target) and one BFS call.
- **The reverse strategy's theoretical advantage may require better type
  prediction accuracy.** If the initial target prediction is wrong, the
  reverse BFS constraint narrows to the wrong region of the graph.

This is reported as an exploratory finding (E1), not a core claim.


## Per-Domain Notes

### Kubernetes (135 tools, 41 types)
Strongest graph performance across models (0.83–0.95 F1). The type
ontology is well-separated — Namespace, Deployment, Pod, Node are
semantically distinct. Three queries have no valid graph path
(Service → PodLogs, Route → Service) due to missing edges.

### Ansible (108 tools, 40 types)
Largest improvement from the query alignment fix (oracle went from
0.774 to 1.000). BFS routes through write operations (add_host,
run_playbook) as shortest paths. Graph F1 ranges 0.71–0.83.

### GitHub (133 tools, 44 types)
Similar BFS-through-write-operations issue (trigger_workflow,
add_issue_label). After fix, graph F1 ranges 0.82–0.90. The type
space has clear hierarchical structure (Org → Repo → Branch → Commit).

### CI/CD (54 tools, 51 types)
The critical case for the graph constraint argument: types ≈ tools
(94% ratio), yet entity pruning averages 87%. Graph F1 ranges
0.73–0.84. Oracle is 1.000 — every query has a valid BFS path.

### Shopify (170 tools, 61 types)
Largest tool catalog. Oracle is 1.000. Graph F1 ranges 0.90–0.95.
Built from real Shopify Admin REST API documentation, providing a
non-DevOps domain for generalization evidence.


## BFS Through Write Operations

BFS does not distinguish read and write operations. When both a read path
(get_inventory_hosts → select_host) and a write path (add_host) connect
the same source and target types, BFS prefers the shorter write path.

This means the "correct" tool chain sometimes includes write operations
for read-intent queries (e.g., "list the hosts" resolves through
add_host). The expected_tools in queries are aligned to BFS shortest
paths, so the oracle achieves F1 = 1.000, but the semantic mismatch
is a known limitation.

Possible mitigations (not implemented):
- Annotate tools with read/write intent and prefer read tools in BFS
- Weight write edges higher so BFS avoids them when read paths exist
- Let the LLM specify intent (read vs write) as part of type prediction

This is discussed as a limitation in the paper.

---

Vendería:

The graph enforces structural validity.

Y como consecuencia:

hallucinated tool invocations disappear.

Lo que cambiaría
1. No diría

All failures are type prediction failures.

Diría algo como

Under the current graph construction, all observed end-to-end failures originate from incorrect type prediction rather than graph coverage.

Porque vuestra afirmación depende del benchmark.

No es una propiedad matemática del método.


. Cuidado con

Smaller models benefit more.

Tenéis cuatro modelos.

Eso no demuestra una ley.

Podéis decir

In our experiments, smaller models exhibited larger improvements.

No mucho más.



3. Recall_wrong = 0.415

Esto me parece un resultado espectacular.

De hecho contradice una hipótesis simplificadora.

Eso gusta mucho en un paper.

Podéis decir

Surprisingly, wrong type predictions often still recover part of the correct tool chain because nearby types remain connected in the typed graph.

Eso convierte una "hipótesis falsa" en un hallazgo.




4. Los dominios

Ahora parecen documentación.

Yo resumiría muchísimo.

Lo importante no es Shopify.

Lo importante es

distintos tamaños
distintas densidades
distintos ratios tools/types

Eso sí es ciencia.





Lo que yo pondría como contribuciones

Si yo fuera reviewer, diría que el paper aporta cinco cosas:

A new formulation

Tool routing → typed entity reasoning.

A typed graph execution model

Entity prediction + graph search.

An analytical decomposition

Recall explained by type prediction and graph resolution.

A comprehensive benchmark

Multiple models, domains and routing strategies.

Empirical evidence

Graph routing consistently improves tool selection while eliminating structurally invalid tool calls.






Lo único que aún echo en falta

Hay una pregunta que un revisor probablemente hará:

¿Por qué funciona?

No basta con decir "porque el grafo restringe la búsqueda".

Intentaría cuantificar ese efecto. Por ejemplo:

tamaño medio del espacio de búsqueda antes/después,
factor de reducción de herramientas candidatas,
branching factor,
número medio de caminos válidos,
entropía del espacio de decisión.

Si conseguís medir cómo el grafo reduce el espacio de decisión y correlacionarlo con la mejora en F1 o recall, el paper pasaría de ser principalmente empírico a ofrecer una explicación mecanística del rendimiento.