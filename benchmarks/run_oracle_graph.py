import argparse
import importlib

from benchmarks.metrics import avg, format_metric, format_pruning, format_tools
from benchmarks.report import BenchmarkReport, query_graph_metrics


def run_oracle_graph(domain: str):
    reg_mod = importlib.import_module(f"benchmarks.{domain}.registry")
    queries_mod = importlib.import_module(f"benchmarks.{domain}.queries")
    build_registry = reg_mod.build_registry
    queries = queries_mod.QUERIES

    registry = build_registry()
    total_tools = len(registry._tools)

    print(f"\n=== ORACLE-GRAPH: {domain} ===")
    print(f"Total tools in registry: {total_tools}")
    print(f"Pipeline: ground-truth source + target → BFS → compare tools\n")

    header = (
        f"{'Query':<30} {'Cat':<10} {'S→T':<25} "
        f"{'Path':>4} {'Tools':>5} {'Prune':>6} {'Prec':>5} {'Rec':>5} {'F1':>5}"
    )
    print(header)
    print("─" * len(header))

    report = BenchmarkReport(total_tools, category_factory=lambda: {
        "total": 0, "path_found": 0, "f1_vals": [],
    })

    path_found_count = 0

    for q in queries:
        cat = q.get("category", "clean")
        stats = report.category_stats[cat]

        source = q["source_type"]
        target = q["target_type"]

        path = registry.resolve(source, target)
        path_found = path is not None
        if path_found:
            path_found_count += 1
            stats["path_found"] += 1

        report.record_latency(0, 0, 0)

        expected_tools = set(q.get("expected_tools", []))
        resolved_tools = {t.name for t in path.tools} if path else set()
        n_tools = len(path.tools) if path else 0
        precision, recall, f1 = report.record_tool_result(resolved_tools, expected_tools, n_tools, cat)
        report.record_query(
            q["id"], cat, expected_tools, resolved_tools,
            precision, recall, f1, 0, n_tools,
            expected_source=source, expected_target=target,
            predicted_source=source, predicted_target=target,
            path_found=path_found,
            **query_graph_metrics(registry, source, target, path),
        )

        st = f"{source}→{target}"
        path_mark = "OK" if path_found else "MISS"
        print(
            f"{q['id']:<30} {cat:<10} {st:<25} "
            f"{path_mark:>4} {format_tools(n_tools)} {format_pruning(n_tools, total_tools)} "
            f"{format_metric(precision)} {format_metric(recall)} {format_metric(f1)}"
        )

    n = len(queries)
    print("─" * len(header))

    print(f"\nPath Resolution ({n} queries):")
    print(f"  Path found:        {path_found_count}/{n} ({path_found_count/n:.0%})")

    report.print_tool_accuracy()
    report.print_pruning()

    print(f"\nBy Category:")
    for cat in sorted(report.category_stats.keys()):
        s = report.category_stats[cat]
        n_cat = s["total"]
        f1_avg = avg(s["f1_vals"]) if s["f1_vals"] else -1
        f1_str = f"f1={f1_avg:.2f}" if f1_avg >= 0 else "f1=—"
        print(f"  {cat:<12} path={s['path_found']}/{n_cat}  {f1_str}")

    return {
        **report.base_result_dict("oracle-graph"),
        "path_found": path_found_count,
        "path_found_pct": path_found_count / n,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="k8s",
                        help="Tool domain to benchmark (default: k8s)")
    args = parser.parse_args()

    run_oracle_graph(args.domain)


if __name__ == "__main__":
    main()
