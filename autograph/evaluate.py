"""Stage 4: Compare original typed graph vs auto-discovered graph.

Runs oracle evaluation on TaskBench chain queries under both graph
constructions and reports comparative metrics.
"""

import json
from pathlib import Path

from typed_composition_search import Registry

from benchmarks.taskbench.queries import load_queries
from benchmarks.taskbench.registry import build_registry

from .extract import extract_contracts, load_taskbench_tools
from .compatibility import infer_compatibility
from .build import build_graph


def _oracle_eval_original(reg: Registry, queries: list[dict]) -> dict:
    """Oracle eval with original coarse types — source/target from query."""
    correct = 0
    total = 0
    collapsed = 0
    tool_recalls = []

    for q in queries:
        total += 1
        path = reg.resolve(q["source_type"], q["target_type"])
        if path is None:
            tool_recalls.append(0.0)
            continue

        predicted = [t.name for t in path.tools]
        expected = q["expected_tools"]

        if len(predicted) < len(expected):
            collapsed += 1

        hits = sum(1 for t in expected if t in predicted)
        recall = hits / len(expected) if expected else 0
        tool_recalls.append(recall)

        if predicted == expected:
            correct += 1

    avg_recall = sum(tool_recalls) / len(tool_recalls) if tool_recalls else 0
    collapse_rate = collapsed / total if total else 0

    return {
        "total": total,
        "exact_match": correct,
        "exact_match_rate": round(correct / total, 4) if total else 0,
        "avg_tool_recall": round(avg_recall, 4),
        "collapse_rate": round(collapse_rate, 4),
    }


def _oracle_eval_auto(reg: Registry, queries: list[dict], contracts: list[dict]) -> dict:
    """Oracle eval with auto-discovered graph.

    For each query, finds the source/target type pair in the new graph that
    recovers the expected tool chain. This tests whether the graph *can*
    represent the workflow, not whether we can predict the right types.
    """
    contract_by_tool = {c["tool"]: c for c in contracts}

    correct = 0
    total = 0
    collapsed = 0
    no_path = 0
    tool_recalls = []

    for q in queries:
        total += 1
        expected = q["expected_tools"]

        first_tool = expected[0]
        last_tool = expected[-1]

        first_contract = contract_by_tool.get(first_tool)
        last_contract = contract_by_tool.get(last_tool)

        if not first_contract or not last_contract:
            tool_recalls.append(0.0)
            no_path += 1
            continue

        best_recall = 0.0
        best_predicted = []

        for src in first_contract.get("consumes", []):
            for tgt in last_contract.get("produces", []):
                path = reg.resolve(src, tgt)
                if path is None:
                    continue

                predicted = [t.name for t in path.tools if not t.name.startswith("_bridge:")]
                hits = sum(1 for t in expected if t in predicted)
                recall = hits / len(expected) if expected else 0

                if recall > best_recall:
                    best_recall = recall
                    best_predicted = predicted

        tool_recalls.append(best_recall)

        if not best_predicted:
            no_path += 1
        elif len(best_predicted) < len(expected):
            collapsed += 1

        if best_predicted == expected:
            correct += 1

    avg_recall = sum(tool_recalls) / len(tool_recalls) if tool_recalls else 0
    collapse_rate = collapsed / total if total else 0

    return {
        "total": total,
        "exact_match": correct,
        "exact_match_rate": round(correct / total, 4) if total else 0,
        "avg_tool_recall": round(avg_recall, 4),
        "collapse_rate": round(collapse_rate, 4),
        "no_path": no_path,
    }


def _graph_stats(reg: Registry, exclude_bridges: bool = False) -> dict:
    """Basic graph statistics."""
    graph = reg._graph
    nodes = graph._all_nodes()
    edges = graph._directed_edges()

    if exclude_bridges:
        edges = [(s, t, n) for s, t, n in edges if not n.startswith("_bridge:")]

    return {
        "entity_types": len(nodes),
        "edges": len(edges),
    }


def evaluate(
    domain: str = "huggingface",
    llm_config: dict | None = None,
    use_cache: bool = True,
    max_queries: int | None = None,
) -> dict:
    """Run comparative evaluation between original and auto-discovered graphs."""
    print(f"\n{'='*60}")
    print(f"Autograph Evaluation — {domain}")
    print(f"{'='*60}")

    # Original graph
    print("\n[1/4] Building original typed graph...")
    orig_reg = build_registry(domain)
    orig_stats = _graph_stats(orig_reg)
    print(f"  {orig_stats['entity_types']} entity types, {orig_stats['edges']} edges")

    # Extract contracts
    print("\n[2/4] Extracting semantic contracts...")
    tools = load_taskbench_tools(domain)
    if llm_config is None:
        llm_config = {"model": "gpt-4o-mini"}

    contracts = extract_contracts(tools, llm_config, domain=domain, use_cache=use_cache)
    print(f"  {len(contracts)} tool contracts extracted")

    for c in contracts[:3]:
        print(f"    {c['tool']}: consumes={c.get('consumes', [])}, produces={c.get('produces', [])}")

    # Infer compatibility
    print("\n[3/4] Inferring compositional compatibility...")
    compat = infer_compatibility(contracts, llm_config, domain=domain, use_cache=use_cache)
    compatible_count = sum(1 for e in compat if e.get("compatible", False))
    print(f"  {len(compat)} pairs evaluated, {compatible_count} compatible")

    # Build auto graph
    auto_reg = build_graph(tools, contracts, compat)
    auto_stats = _graph_stats(auto_reg)
    bridge_edges = sum(1 for _, _, n in auto_reg._graph._directed_edges() if n.startswith("_bridge:"))
    print(f"  Auto graph: {auto_stats['entity_types']} types, {auto_stats['edges']} edges ({bridge_edges} bridge)")

    # Load queries and evaluate
    print("\n[4/4] Running oracle evaluation...")
    queries = load_queries(domain, max_queries=max_queries)
    print(f"  {len(queries)} chain queries loaded")

    orig_results = _oracle_eval_original(orig_reg, queries)
    auto_results = _oracle_eval_auto(auto_reg, queries, contracts)

    # Print comparison
    print(f"\n{'─'*60}")
    print(f"{'Metric':<30} {'Original':>12} {'Auto':>12}")
    print(f"{'─'*60}")
    print(f"{'Entity types':<30} {orig_stats['entity_types']:>12} {auto_stats['entity_types']:>12}")
    print(f"{'Graph edges':<30} {orig_stats['edges']:>12} {auto_stats['edges']:>12}")
    print(f"{'Oracle exact match':<30} {orig_results['exact_match_rate']:>12.1%} {auto_results['exact_match_rate']:>12.1%}")
    print(f"{'Oracle avg tool recall':<30} {orig_results['avg_tool_recall']:>12.1%} {auto_results['avg_tool_recall']:>12.1%}")
    print(f"{'Collapse rate':<30} {orig_results['collapse_rate']:>12.1%} {auto_results['collapse_rate']:>12.1%}")
    if "no_path" in auto_results:
        print(f"{'No path found':<30} {'—':>12} {auto_results['no_path']:>12}")
    print(f"{'─'*60}")

    return {
        "domain": domain,
        "original": {"stats": orig_stats, "oracle": orig_results},
        "auto": {"stats": auto_stats, "oracle": auto_results},
    }


if __name__ == "__main__":
    results = evaluate(domain="huggingface", use_cache=True)
    print("\n" + json.dumps(results, indent=2))
