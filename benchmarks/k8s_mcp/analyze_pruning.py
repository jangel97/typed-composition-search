"""Analyze TCR pruning for the official kubernetes-mcp-server."""

from .registry import build_registry, ENTITY_TYPES


def analyze():
    reg = build_registry()
    tools = reg._tools
    graph = reg._graph

    print(f"Total tools: {len(tools)}")
    print(f"Entity types: {len(ENTITY_TYPES)}")
    print(f"Ratio: {len(ENTITY_TYPES)/len(tools):.0%}")
    print()

    all_types = set(ENTITY_TYPES.keys())

    # Example queries with predicted (source, target) types
    queries = [
        ("Show me the logs from pod nginx", "Pod", "PodLog"),
        ("List all pods in the cluster", "Cluster", "PodList"),
        ("Get resource usage for nodes", "Cluster", "NodeMetrics"),
        ("Start the build pipeline", "TektonPipeline", "TektonPipelineRun"),
        ("Show traffic graph for the frontend namespace", "Namespace", "MeshTrafficGraph"),
        ("Get guest info from the database VM", "VirtualMachine", "VMGuestInfo"),
        ("List Helm releases in production", "Namespace", "HelmReleaseList"),
        ("Get logs from the task run", "TektonTaskRun", "TektonTaskRunLog"),
        ("Delete the test pod", "Pod", "DeletionResult"),
        ("Show events in the staging namespace", "Namespace", "EventList"),
        ("Get the logs from a pod in the default namespace", "Namespace", "PodLog"),
        ("Execute a command in the web server pod", "Pod", "ExecResult"),
        ("Get Istio config for the API namespace", "Namespace", "IstioConfig"),
        ("Check overall mesh health", "Cluster", "MeshStatus"),
        ("Get node kubelet logs", "Node", "NodeLog"),
    ]

    print("=" * 80)
    print("PRUNING ANALYSIS")
    print("=" * 80)
    print()

    total_pruning = 0.0
    for query, src, tgt in queries:
        path = reg.resolve(src, tgt)
        reachable = reg.reachable_types(src)
        reachable_as_source = set()
        for t in tools:
            for inp in t.input_types:
                if inp == src:
                    reachable_as_source.update(t.output_types)

        # Tools that could be selected from this source
        candidate_tools = [t for t in tools if any(inp == src for inp in t.input_types)]

        # Entity pruning: what fraction of types are NOT reachable sources for this target
        reverse_reachable = reg.reverse_reachable_types(tgt)
        entity_pruning = 1.0 - len(reverse_reachable) / len(all_types)

        path_tools = [t.name for t in path.tools] if path else []

        print(f"Query: {query}")
        print(f"  Types: {src} → {tgt}")
        print(f"  Path: {' → '.join(path_tools) if path else 'NO PATH'}")
        print(f"  Candidate tools from {src}: {len(candidate_tools)} / {len(tools)} total")
        print(f"  Entity pruning (reverse reachable sources for {tgt}): {len(reverse_reachable)}/{len(all_types)} types reachable → {entity_pruning:.0%} pruned")
        print()
        total_pruning += entity_pruning

    avg_pruning = total_pruning / len(queries)
    print("=" * 80)
    print(f"Average entity pruning: {avg_pruning:.0%}")
    print()

    # Global stats
    print("GLOBAL GRAPH STATS")
    print("-" * 40)
    source_types = set()
    target_types = set()
    for t in tools:
        source_types.update(t.input_types)
        target_types.update(t.output_types)
    print(f"Source types (appear as inputs): {len(source_types)}")
    print(f"Target types (appear as outputs): {len(target_types)}")
    print(f"Types appearing as both: {len(source_types & target_types)}")
    print()

    # Per-source-type reachability
    print("REACHABILITY FROM KEY SOURCES")
    print("-" * 40)
    for src in ["Cluster", "Namespace", "Pod", "Node", "VirtualMachine", "TektonPipeline"]:
        reachable = reg.reachable_types(src)
        candidate = [t for t in tools if any(inp == src for inp in t.input_types)]
        print(f"  {src}: {len(candidate)} direct tools, reaches {len(reachable)} types")


if __name__ == "__main__":
    analyze()
