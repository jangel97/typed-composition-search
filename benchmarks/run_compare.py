import argparse

from benchmarks.llm import MODELS
from benchmarks.run_benchmark import run_benchmark
from benchmarks.run_baseline import run_baseline
from benchmarks.run_retrieval import run_retrieval
from benchmarks.run_benchmark_narrowed import run_benchmark_narrowed
from benchmarks.run_benchmark_probs import run_benchmark_probs
from benchmarks.run_benchmark_reverse import run_benchmark_reverse
from benchmarks.run_benchmark_reverse_probs import run_benchmark_reverse_probs


def fmt(val, fmt_str=".2f", na="—"):
    if val is None or val < 0:
        return na
    return f"{val:{fmt_str}}"


def print_comparison(results: list[dict]):
    all_cats = sorted({cat for r in results for cat in r.get("category_f1", {})})

    print("\n")
    print("=" * 80)
    print("  STRATEGY COMPARISON")
    print("=" * 80)

    names = [r["strategy"] for r in results]
    col_w = max(len(n) for n in names) + 4
    label_w = 22

    def row(label, key, fmt_str=".2f", getter=None):
        vals = []
        for r in results:
            if getter:
                v = getter(r)
            else:
                v = r.get(key)
            vals.append(v)
        best = max((v for v in vals if v is not None and v >= 0), default=None)
        cells = []
        for v in vals:
            s = fmt(v, fmt_str)
            if v is not None and v >= 0 and v == best and sum(1 for x in vals if x == best) < len(vals):
                s = f"*{s}*"
            cells.append(f"{s:>{col_w}}")
        print(f"  {label:<{label_w}}{''.join(cells)}")

    def row_low(label, key, fmt_str=".2f", getter=None):
        vals = []
        for r in results:
            if getter:
                v = getter(r)
            else:
                v = r.get(key)
            vals.append(v)
        best = min((v for v in vals if v is not None and v >= 0), default=None)
        cells = []
        for v in vals:
            s = fmt(v, fmt_str)
            if v is not None and v >= 0 and v == best and sum(1 for x in vals if x == best) < len(vals):
                s = f"*{s}*"
            cells.append(f"{s:>{col_w}}")
        print(f"  {label:<{label_w}}{''.join(cells)}")

    header_cells = "".join(f"{n:>{col_w}}" for n in names)
    print(f"\n  {'Metric':<{label_w}}{header_cells}")
    print("  " + "─" * (label_w + col_w * len(results)))

    row("Precision", "precision")
    row("Recall", "recall")
    row("F1", "f1")
    row("Exact Match", None, ".0%",
        getter=lambda r: r["exact_match"] / r["exact_match_n"] if r.get("exact_match_n") else None)
    row_low("Hallucinated", "hallucinated", ".0f")
    row("Pruning", "pruning", ".0%")
    row_low("Avg tools", "avg_tools", ".1f")
    row("Path found", "path_found_pct", ".0%")
    row("Type Recall@k", "type_recall_at_k")
    row("Recall@k", "retrieval_recall_at_k")

    print()
    print(f"  {'Latency':<{label_w}}{header_cells}")
    print("  " + "─" * (label_w + col_w * len(results)))
    row_low("Avg (ms)", "latency_avg", ".0f")
    row_low("P50 (ms)", "latency_p50", ".0f")
    row_low("P95 (ms)", "latency_p95", ".0f")

    print()
    print(f"  {'Tokens':<{label_w}}{header_cells}")
    print("  " + "─" * (label_w + col_w * len(results)))
    row_low("Avg prompt", "avg_prompt_tokens", ".0f")
    row_low("Avg completion", "avg_completion_tokens", ".0f")

    if all_cats:
        print()
        print(f"  {'F1 by Category':<{label_w}}{header_cells}")
        print("  " + "─" * (label_w + col_w * len(results)))
        for cat in all_cats:
            vals = []
            for r in results:
                v = r.get("category_f1", {}).get(cat)
                if v is None:
                    v = -1
                vals.append(v)
            best = max((v for v in vals if v >= 0), default=None)
            cells = []
            for v in vals:
                s = fmt(v)
                if v >= 0 and v == best and sum(1 for x in vals if x == best) < len(vals):
                    s = f"*{s}*"
                cells.append(f"{s:>{col_w}}")
            print(f"  {cat:<{label_w}}{''.join(cells)}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Compare all benchmark strategies side-by-side")
    parser.add_argument("--model", default="qwen",
                        help="Model to benchmark (default: qwen). Options: " + ", ".join(MODELS.keys()))
    parser.add_argument("--domain", default="k8s",
                        help="Tool domain (default: k8s)")
    parser.add_argument("--top-k", type=int, default=10,
                        help="Top-k for retrieval strategy (default: 10)")
    parser.add_argument("--narrow-k", type=int, default=10,
                        help="Top-k entity types for narrowed graph strategy (default: 10)")
    parser.add_argument("--threshold", type=float, default=0.15,
                        help="Confidence threshold for probabilistic graph strategy (default: 0.15)")
    parser.add_argument("--max-candidates", type=int, default=5,
                        help="Max candidates for probabilistic graph strategy (default: 5)")
    parser.add_argument("--n-completions", type=int, default=5,
                        help="Number of completions for probabilistic strategies (default: 5)")
    args = parser.parse_args()

    results = []

    print("\n" + "=" * 80)
    print(f"  Running GRAPH benchmark...")
    print("=" * 80)
    results.append(run_benchmark(args.model, args.domain))

    print("\n" + "=" * 80)
    print(f"  Running GRAPH-NARROWED benchmark...")
    print("=" * 80)
    results.append(run_benchmark_narrowed(args.model, args.domain, args.narrow_k))

    print("\n" + "=" * 80)
    print(f"  Running BASELINE benchmark...")
    print("=" * 80)
    results.append(run_baseline(args.model, args.domain))

    print("\n" + "=" * 80)
    print(f"  Running GRAPH-PROBS benchmark...")
    print("=" * 80)
    results.append(run_benchmark_probs(args.model, args.domain, args.threshold, args.max_candidates))

    print("\n" + "=" * 80)
    print(f"  Running GRAPH-REVERSE benchmark...")
    print("=" * 80)
    results.append(run_benchmark_reverse(args.model, args.domain))

    print("\n" + "=" * 80)
    print(f"  Running GRAPH-REVERSE-PROBS benchmark...")
    print("=" * 80)
    results.append(run_benchmark_reverse_probs(args.model, args.domain, args.n_completions, args.threshold, args.max_candidates))

    print("\n" + "=" * 80)
    print(f"  Running BASELINE benchmark...")
    print("=" * 80)
    results.append(run_baseline(args.model, args.domain))

    print("\n" + "=" * 80)
    print(f"  Running RETRIEVAL benchmark...")
    print("=" * 80)
    results.append(run_retrieval(args.model, args.top_k, args.domain))

    print_comparison(results)


if __name__ == "__main__":
    main()
