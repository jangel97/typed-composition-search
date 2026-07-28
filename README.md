# Typed Composition Routing (TCR)

This repository contains the paper, benchmark suite, and evaluation results for:

**Typed Composition Routing: Decoupling Semantic Prediction from Compositional Tool Search**

TCR decomposes tool routing into two stages: (1) an LLM predicts source and target entity types from a natural-language query, and (2) deterministic graph search over a typed composition graph returns all structurally valid tool chains. This decomposition improves routing quality (+0.32 F1 across 20 model-domain combinations), eliminates hallucinated tool invocations by construction, and scales to registries with over 1,000 tools.

## Repository structure

```
docs/paper_v3/            Paper source (LaTeX, figures)
benchmarks/               5-domain benchmark suite
  k8s/                    Kubernetes (135 tools, 28 queries)
  ansible/                Ansible (108 tools, 28 queries)
  github/                 GitHub (133 tools, 28 queries)
  cicd/                   CI/CD (54 tools, 28 queries)
  shopify/                Shopify (170 tools, 28 queries)
  RESULTS.md              Summary of evaluation results
```

## Related repositories

| Repository | Description |
|---|---|
| [tcr-go](https://github.com/jangel97/tcr-go) | TCR routing library (Go) |
| [tcr-k8s-demo](https://github.com/jangel97/tcr-k8s-demo) | K8s benchmark: ontology experiments and evaluation pipeline |
| [tcr-aap-demo](https://github.com/jangel97/tcr-aap-demo) | AAP production-scale experiments and evaluation pipeline |
| [openshift-mcp-server](https://github.com/jangel97/openshift-mcp-server) | OpenShift MCP server fork with TCR integration |

## License

MIT
