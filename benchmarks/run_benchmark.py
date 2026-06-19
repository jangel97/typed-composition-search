from dataclasses import dataclass

from benchmarks.devops_queries import QUERIES, Query
from benchmarks.devops_registry import build_devops_registry
from typed_composition_search import Registry


@dataclass
class QueryResult:
    query: Query
    returned: set[str]
    required: set[str]
    total_tools: int

    @property
    def recall(self) -> float:
        if not self.required:
            return 1.0
        return len(self.required & self.returned) / len(self.required)

    @property
    def precision(self) -> float:
        if not self.returned:
            return 1.0
        return len(self.required & self.returned) / len(self.returned)

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)

    @property
    def pruning(self) -> float:
        return 1 - len(self.returned) / self.total_tools

    @property
    def missing(self) -> set[str]:
        return self.required - self.returned


def evaluate(
    registry: Registry,
    queries: list[Query],
    *,
    exclude_sources: bool = False,
    max_depth: int | None = None,
) -> list[QueryResult]:
    total = len(registry._tools)
    results = []
    for q in queries:
        relevant = registry.relevant_tools(
            q.initial, q.goal,
            exclude_sources=exclude_sources,
            max_depth=max_depth,
        )
        returned_names = {t.name for t in relevant}
        results.append(QueryResult(
            query=q,
            returned=returned_names,
            required=q.required_tools,
            total_tools=total,
        ))
    return results


def print_summary(label: str, results: list[QueryResult]) -> None:
    total = results[0].total_tools
    print(f"\n{'=' * 70}")
    print(f"  {label} ({total} tools)")
    print(f"{'=' * 70}\n")
    print(
        f"{'Query':<28} {'Sel':>4} {'Req':>4} "
        f"{'Recall':>7} {'Prec':>7} {'F1':>7} {'Prune':>7}"
    )
    print("-" * 70)

    for r in results:
        print(
            f"{r.query.name:<28} {len(r.returned):>4} {len(r.required):>4} "
            f"{r.recall:>6.0%} {r.precision:>6.0%} {r.f1:>6.0%} {r.pruning:>6.0%}"
        )

    avg_recall = sum(r.recall for r in results) / len(results)
    avg_precision = sum(r.precision for r in results) / len(results)
    avg_f1 = sum(r.f1 for r in results) / len(results)
    avg_pruning = sum(r.pruning for r in results) / len(results)

    print("-" * 70)
    print(
        f"{'AVERAGE':<28} {'':>4} {'':>4} "
        f"{avg_recall:>6.0%} {avg_precision:>6.0%} {avg_f1:>6.0%} {avg_pruning:>6.0%}"
    )

    missing_any = [r for r in results if r.missing]
    if missing_any:
        print("\n  MISSING TOOLS:")
        for r in missing_any:
            print(f"    {r.query.name}: {r.missing}")
    else:
        print("\n  All required tools found (recall = 100%)")


def main() -> None:
    registry = build_devops_registry()

    # Variant 1: baseline
    results_baseline = evaluate(registry, QUERIES)
    print_summary("Variant 1: Baseline", results_baseline)

    # Variant 2: exclude source tools (empty inputs)
    results_no_sources = evaluate(registry, QUERIES, exclude_sources=True)
    print_summary("Variant 2: Exclude source tools", results_no_sources)

    # Variant 3: max depth = 4
    results_depth = evaluate(registry, QUERIES, max_depth=4)
    print_summary("Variant 3: Max depth = 4", results_depth)

    # Comparison
    print(f"\n{'=' * 70}")
    print(f"  Comparison")
    print(f"{'=' * 70}\n")
    print(
        f"{'Query':<24} "
        f"{'Baseline':>10} {'NoSource':>10} {'Depth=4':>10}   "
        f"{'R1':>3} {'R2':>3} {'R3':>3}"
    )
    print("-" * 70)
    for rb, rn, rd in zip(results_baseline, results_no_sources, results_depth):
        print(
            f"{rb.query.name:<24} "
            f"{len(rb.returned):>4}/{rb.total_tools:<4} "
            f"{len(rn.returned):>4}/{rn.total_tools:<4} "
            f"{len(rd.returned):>4}/{rd.total_tools:<4}   "
            f"{rb.recall:>3.0%} {rn.recall:>3.0%} {rd.recall:>3.0%}"
        )


if __name__ == "__main__":
    main()
