from collections import defaultdict

from benchmarks.metrics import avg, std, percentile, tool_set_metrics


def query_graph_metrics(registry, pred_source: str, pred_target: str, path) -> dict:
    graph = registry._graph
    source_edges = graph._edges.get(pred_source, [])
    target_edges = graph._reverse_edges.get(pred_target, [])
    source_reachable = registry.reachable_types(pred_source)
    target_reverse = registry.reverse_reachable_types(pred_target)
    return {
        "path_length": len(path.tools) if path else None,
        "source_out_degree": len(source_edges),
        "target_in_degree": len(target_edges),
        "source_reachable": len(source_reachable),
        "target_reverse_reachable": len(target_reverse),
    }


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
        self._per_query: list[dict] = []

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

        if expected_tools:
            precision, recall, f1 = tool_set_metrics(resolved_tools, expected_tools)
            self.all_precision.append(precision)
            self.all_recall.append(recall)
            self.all_f1.append(f1)
            stats.setdefault("f1_vals", []).append(f1)
        else:
            precision, recall, f1 = -1.0, -1.0, -1.0

        return precision, recall, f1

    def record_query(
        self,
        query_id: str,
        category: str,
        expected_tools: set[str],
        resolved_tools: set[str],
        precision: float,
        recall: float,
        f1: float,
        latency_ms: float,
        n_tools: int,
        **extra,
    ):
        self._per_query.append({
            "id": query_id,
            "category": category,
            "expected_tools": sorted(expected_tools),
            "resolved_tools": sorted(resolved_tools),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "latency_ms": round(latency_ms, 1),
            "n_tools": n_tools,
            **extra,
        })

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
        if self.total_tools <= 0:
            return
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

    def print_recall_decomposition(self):
        """Print recall decomposition: Recall_e2e = P(correct) * R_correct + P(wrong) * R_wrong."""
        correct_recalls = []
        wrong_recalls = []
        for q in self._per_query:
            recall = q.get("recall", -1.0)
            if recall < 0:
                continue
            src_ok = q.get("predicted_source") == q.get("expected_source")
            tgt_ok = q.get("predicted_target") == q.get("expected_target")
            if src_ok and tgt_ok:
                correct_recalls.append(recall)
            else:
                wrong_recalls.append(recall)

        n_total = len(correct_recalls) + len(wrong_recalls)
        if n_total == 0:
            return

        p_correct = len(correct_recalls) / n_total
        p_wrong = len(wrong_recalls) / n_total
        r_correct = avg(correct_recalls) if correct_recalls else 0.0
        r_wrong = avg(wrong_recalls) if wrong_recalls else 0.0
        r_predicted = p_correct * r_correct + p_wrong * r_wrong
        r_actual = avg(correct_recalls + wrong_recalls)

        print(f"\nRecall Decomposition:")
        print(f"  Recall_e2e = P(correct) x R_correct + P(wrong) x R_wrong")
        print(f"  P(correct):         {p_correct:.2f} ({len(correct_recalls)}/{n_total})")
        print(f"  P(wrong):           {p_wrong:.2f} ({len(wrong_recalls)}/{n_total})")
        print(f"  R_correct:          {r_correct:.3f}")
        print(f"  R_wrong:            {r_wrong:.3f}")
        print(f"  Predicted recall:   {r_predicted:.3f}")
        print(f"  Actual recall:      {r_actual:.3f}")
        print(f"  Gap:                {abs(r_actual - r_predicted):.3f}")

    def base_result_dict(self, strategy: str, hallucinated: int = 0) -> dict:
        avg_tools = avg(self.all_tool_counts)
        pruning = (1.0 - avg_tools / self.total_tools) if self.total_tools > 0 else -1

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
            "per_query": self._per_query,
        }
