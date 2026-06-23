# Roadmap

## Phase 1: Validate

Prove the approach works across domains and at scale.

- **Expand query sets** — 100+ queries per category with confidence intervals, not point estimates from 25 queries
- **Second domain** — Ansible, CI/CD, or cloud APIs to prove the approach isn't K8s-specific
- **Statistical rigor** — multiple runs, variance analysis, significance tests on F1 differences
- **Explicit comparison to literature** — run on public benchmarks where GRAFT/ControlLLM report numbers, or align metrics to enable fair comparison
- **Failure taxonomy** — systematic analysis of where type prediction breaks (synonyms, ambiguity, implicit entities) and what the ceiling is

## Phase 2: Investigate graph metrics

Use graph-theoretic properties to understand, diagnose, and improve tool routing.

Potential directions:
- **Graph completeness analysis** — identify missing edges that cause path resolution failures (e.g., Service→PodLogs gap). Which entity pairs have high query frequency but no path?
- **Path redundancy** — where multiple paths exist between types, which does BFS pick vs which is best? Does shortest path always equal best path?
- **Centrality and bottlenecks** — which entity types are hubs (high degree)? Are bottleneck nodes (e.g., Pod, PodList) causing over-convergence of paths?
- **Graph diameter and hop distribution** — how deep are real query paths? Is there a hop count where type prediction accuracy drops?
- **Connectivity metrics** — weakly/strongly connected components. Are there isolated subgraphs that indicate missing cross-domain edges?
- **Type prediction difficulty** — correlate graph structure (fan-out, ambiguity of neighbors) with LLM prediction accuracy per type
- **Graph evolution** — as tools are added/removed, how does routing quality change? Can we detect regressions automatically?

## Phase 3: Framework

Make it easy for anyone to build their own typed tool router.

- **`typed-composition-search` as a standalone library** — pip-installable, clean API
- **Declarative tool registration** — YAML/JSON schema for defining tools, types, and edges without writing Python
- **Graph validation** — CLI tool that analyzes a tool registry for completeness gaps, unreachable types, disconnected components
- **Benchmark harness** — plug in your domain (tools + queries), run all three strategies (graph, baseline, retrieval), get comparison table
- **Integration guides** — how to plug into LangChain, LlamaIndex, or custom agent loops
- **Graph visualization** — render the tool graph for debugging and documentation
