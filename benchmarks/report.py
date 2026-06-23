from collections import defaultdict

from benchmarks.metrics import avg, std, percentile, tool_set_metrics


class BenchmarkReport:

    def __init__(self, total_tools: int, category_factory=None):
        self.total_tools = total_tools
        self.all_precision: list[float] = []
        self.all_recall: list[float] = []
        self.all_f1: list[float] = []
        self.all_tool_counts: list[int] = []
        self.all_latency: list[float] = []
        self.all_prompt_tokens: list[int] = []
        self.all_completion_tokens: list[int] = []
        self._n_queries = 0

        if category_factory:
            self.category_stats = defaultdict(category_factory)
        else:
            self.category_stats = defaultdict(
                lambda: {"total": 0, "f1_vals": []}
            )

    def record_tool_result(
        self,
        resolved_tools: set[str],
        expected_tools: set[str],
        n_tools: int,
        category: str,
    ) -> tuple[float, float, float]:
        self._n_queries += 1
        self.all_tool_counts.append(n_tools)
        stats = self.category_stats[category]
        stats["total"] = stats.get("total", 0) + 1

        if expected_tools and resolved_tools:
            precision, recall, f1 = tool_set_metrics(resolved_tools, expected_tools)
            self.all_precision.append(precision)
            self.all_recall.append(recall)
            self.all_f1.append(f1)
            stats.setdefault("f1_vals", []).append(f1)
        else:
            precision, recall, f1 = -1.0, -1.0, -1.0

        return precision, recall, f1

    def record_latency(self, latency_ms: float, prompt_tokens: int, completion_tokens: int):
        self.all_latency.append(latency_ms)
        self.all_prompt_tokens.append(prompt_tokens)
        self.all_completion_tokens.append(completion_tokens)

    def print_tool_accuracy(self, label: str = "Tool Accuracy"):
        if not self.all_precision:
            return
        n = len(self.all_precision)
        print(f"\n{label} ({n} queries with expected tools):")
        print(f"  Avg Precision:      {avg(self.all_precision):.2f} ± {std(self.all_precision):.2f}")
        print(f"  Avg Recall:         {avg(self.all_recall):.2f} ± {std(self.all_recall):.2f}")
        print(f"  Avg F1:             {avg(self.all_f1):.2f} ± {std(self.all_f1):.2f}")

    def print_pruning(self):
        avg_tools = avg(self.all_tool_counts)
        pruning = 1.0 - avg_tools / self.total_tools
        all_pruning = [1.0 - t / self.total_tools for t in self.all_tool_counts if t > 0]
        print(f"\nPruning:")
        print(f"  Avg tools selected: {avg_tools:.1f} ± {std(self.all_tool_counts):.1f} / {self.total_tools}")
        if all_pruning:
            print(f"  Avg pruning:       {pruning:.0%} ± {std(all_pruning):.0%}")
        else:
            print(f"  Avg pruning:       —")

    def print_latency(self, label: str = "Latency"):
        print(f"\n{label}:")
        print(f"  Avg:                {avg(self.all_latency):.0f}ms")
        print(f"  P50:                {percentile(self.all_latency, 50):.0f}ms")
        print(f"  P95:                {percentile(self.all_latency, 95):.0f}ms")

    def print_tokens(self):
        print(f"\nTokens:")
        print(f"  Avg prompt:         {avg(self.all_prompt_tokens):.0f}")
        print(f"  Avg completion:     {avg(self.all_completion_tokens):.0f}")

    def base_result_dict(self, strategy: str, hallucinated: int = 0) -> dict:
        avg_tools = avg(self.all_tool_counts)
        pruning = 1.0 - avg_tools / self.total_tools

        cat_f1 = {}
        for cat in sorted(self.category_stats.keys()):
            s = self.category_stats[cat]
            f1_vals = s.get("f1_vals", [])
            cat_f1[cat] = avg(f1_vals) if f1_vals else -1

        return {
            "strategy": strategy,
            "precision": avg(self.all_precision),
            "recall": avg(self.all_recall),
            "f1": avg(self.all_f1),
            "hallucinated": hallucinated,
            "avg_tools": avg_tools,
            "total_tools": self.total_tools,
            "pruning": pruning,
            "latency_avg": avg(self.all_latency),
            "latency_p50": percentile(self.all_latency, 50),
            "latency_p95": percentile(self.all_latency, 95),
            "avg_prompt_tokens": avg(self.all_prompt_tokens),
            "avg_completion_tokens": avg(self.all_completion_tokens),
            "category_f1": cat_f1,
            "n": self._n_queries,
        }
