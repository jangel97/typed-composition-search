# Research Publication Proposal: Typed Composition Graphs for Tool Selection

## Summary

I propose publishing a workshop paper on a novel approach to LLM tool selection that I have been developing. The work reformulates tool routing — traditionally treated as a retrieval or direct selection problem — into entity classification over a typed composition graph. This approach achieves 98% tool pruning, zero hallucinations, and strong accuracy across multiple domains and models, including Granite.

The work aligns directly with Red Hat's AI strategy around Granite, RHEL AI, and the Model Context Protocol (MCP), and complements existing internal work on Tool RAG by the Emerging Technologies team.

## The Problem

As LLM-based agents scale to hundreds or thousands of tools, tool selection becomes a bottleneck. Current approaches (direct selection, retrieval-based) degrade as catalogs grow: larger decision spaces, higher hallucination rates, and increasing prompt complexity. The Red Hat Emerging Technologies team identified multi-step tool composition as an "open frontier" in their Tool RAG publications (Nov-Dec 2025).

## The Contribution

Instead of asking the LLM to select tools directly from a large catalog, the system:

1. The LLM predicts only the **entity types** involved in the task (~40 types instead of ~500 tools)
2. A **typed composition graph** resolves the tool execution path deterministically via graph search

This decomposes tool selection into two independent problems: entity classification (probabilistic, handled by the LLM) and path planning (deterministic, handled by the graph). The key result is:

```
Recall_e2e ≈ TypeAccuracy × Recall_oracle
```

All end-to-end performance is explained by how well the model classifies entity types. The graph itself is a near-lossless execution engine.

## Current Results

- **3 domains benchmarked**: Kubernetes (135 tools), Ansible (108 tools), GitHub (133 tools)
- **3 models benchmarked**: Qwen3-14B, Granite-4.1-8B, Claude Haiku
- **8 routing strategies** compared (baseline, retrieval, graph variants)
- **98% tool pruning** — the LLM never sees 500 tools, only ~40 types
- **Zero hallucinations** — only valid tools from the registry appear in paths
- **F1 up to 0.95** on well-structured domains (Kubernetes)
- **Recall decomposition validated** — errors come from type prediction, not graph resolution

## Strategic Alignment with Red Hat

### Granite and RHEL AI

The benchmarks already include Granite-4.1-8B. The typed composition approach is particularly valuable for smaller models: by reducing the problem from tool selection (500 options) to entity classification (40 options), small models can achieve accuracy comparable to larger ones. This directly supports the case for Granite in enterprise AI deployments.

### Tool RAG

The Emerging Technologies team published on Tool RAG (Nov-Dec 2025), identifying multi-step composition as an open problem. This work provides a complementary approach: while Tool RAG retrieves individual tools via semantic similarity, typed composition graphs model the structural relationships between tools, enabling multi-step workflow resolution. A combined approach (retrieval for type prediction, graph for composition) is a natural extension.

### Model Context Protocol (MCP)

Red Hat committed to MCP at Summit 2025. MCP describes tools with structured interfaces — typed inputs and outputs. Typed composition graphs are a natural layer on top of MCP: given MCP tool descriptions, the graph can be constructed automatically and used for intelligent routing.

### Open Source

The implementation is fully open source, consistent with Red Hat's values. The typed composition search library and all benchmark infrastructure are available for community use and extension.

## Publication Plan

### Target Venue

Workshop paper (4-6 pages) at a top ML/AI venue. Candidates:
- NeurIPS 2026 workshop on agents/tool use (deadlines likely Aug-Sep 2026)
- COLM 2026 Lifelong Agents Workshop
- EMNLP 2026 (special theme includes "agentic workflows, tool use")

Workshop papers are non-archival or lightly archival, meaning the work can be expanded into a full conference paper later.

### Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Benchmarks & analysis | 1 week | Re-run with decomposition, confidence intervals, failure analysis |
| Writing | 1-2 weeks | Draft the paper (4-6 pages) |
| Internal review | 1 week | Feedback from colleagues and Red Hat Research |
| Submission | — | Target nearest suitable deadline |

Estimated total: 3-4 weeks of focused effort, parallelizable with regular work.

### Red Hat Research

Red Hat has an internal research program ([research.redhat.com](https://research.redhat.com)) that connects Red Hat engineers with academic researchers to publish papers and bring research ideas into open source. It is not a separate R&D lab — it works by enabling engineers like us to collaborate with universities on topics relevant to Red Hat's strategy.

How it works:
- **Research Interest Groups (RIGs)**: monthly meetings (Americas, Europe, Israel) where Red Hat engineers and university researchers discuss current work and find collaborations. AI/ML is one of their active focus areas.
- **BU Collaboratory**: Red Hat's flagship academic partnership with Boston University, with over $20M in funding. It supports co-authored research, graduate fellowships, and incubation awards.
- **Low friction**: Red Hat employees regularly co-author papers at venues like ICLR, IEEE, ICSE, and others. Red Hat's open source culture means there is no heavy IP/legal approval process for publishing research.

I plan to:
- Reach out to the research team (academic@redhat.com) to present this work
- Attend a RIG meeting to find potential academic co-authors
- Connect with the Emerging Technologies team working on Tool RAG, since our approaches are complementary


## Expected Outcomes

- A published workshop paper at a recognized AI venue, with Red Hat affiliation
- Visibility for Red Hat's AI research capabilities in the tool-use/agents space
- A foundation for further work on intelligent tool routing for Granite and RHEL AI
- Potential academic collaborations through Red Hat Research
