import argparse
import importlib
import json
import math
import time
from collections import defaultdict

from benchmarks.llm import MODELS, get_llm_config, llm_completion


SYSTEM_PROMPT = """You are a tool selector.
Given a user query, select the tools needed to answer it, in execution order.

Available tools:
{tool_list}

Respond ONLY with a JSON list of tool names: ["tool_a", "tool_b"]"""


def build_tool_prompt(registry) -> str:
    lines = []
    for tool in registry._tools:
        inputs = ", ".join(tool.input_types)
        outputs = ", ".join(tool.output_types)
        lines.append(f"- {tool.name}: ({inputs}) → ({outputs})")
    return SYSTEM_PROMPT.format(tool_list="\n".join(lines))


def select_tools(
    config: dict,
    query: str,
    system: str,
    valid_names: set[str],
) -> tuple[list[str], list[str], int, int, float]:
    start = time.monotonic()
    response = llm_completion(config, [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ])
    latency_ms = (time.monotonic() - start) * 1000

    text = response.choices[0].message.content.strip()
    start_idx = text.find("[")
    end_idx = text.rfind("]") + 1
    if start_idx == -1 or end_idx == 0:
        predicted = []
    else:
        try:
            predicted = json.loads(text[start_idx:end_idx])
        except json.JSONDecodeError:
            predicted = []

    hallucinated = [t for t in predicted if t not in valid_names]
    valid_predicted = [t for t in predicted if t in valid_names]

    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    return valid_predicted, hallucinated, prompt_tokens, completion_tokens, latency_ms


def tool_set_metrics(resolved: set[str], expected: set[str]) -> tuple[float, float, float]:
    if not resolved and not expected:
        return 1.0, 1.0, 1.0
    if not resolved or not expected:
        return 0.0, 0.0, 0.0
    tp = len(resolved & expected)
    precision = tp / len(resolved) if resolved else 0.0
    recall = tp / len(expected) if expected else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_vals):
        return sorted_vals[f]
    return sorted_vals[f] + (k - f) * (sorted_vals[c] - sorted_vals[f])


def run_baseline(model_name: str, domain: str):
    reg_mod = importlib.import_module(f"benchmarks.{domain}.registry")
    queries_mod = importlib.import_module(f"benchmarks.{domain}.queries")
    build_registry = reg_mod.build_registry
    queries = queries_mod.QUERIES

    config = get_llm_config(model_name)
    model_id = config["litellm_model"]
    registry = build_registry()
    total_tools = len(registry._tools)
    valid_names = {t.name for t in registry._tools}
    system = build_tool_prompt(registry)

    print(f"\n=== BASELINE: {model_name} ({model_id}) ===")
    print(f"Total tools in prompt: {total_tools}\n")

    header = (
        f"{'Query':<30} {'Category':<12} {'Prompt':<85} "
        f"{'Prec':>5} {'Rec':>5} {'F1':>5} {'EM':>3} {'Hall':>4} {'Tools':>5} {'Prune':>6} {'ms':>6}"
    )
    print(header)
    print("─" * len(header))

    all_precision = []
    all_recall = []
    all_f1 = []
    all_exact = []
    all_tool_counts = []
    all_tool_count_err = []
    all_hallucinated = 0
    all_latency = []
    all_prompt_tokens = []
    all_completion_tokens = []

    category_stats = defaultdict(lambda: {
        "total": 0, "exact": 0, "f1_vals": [], "hallucinated": 0,
    })

    for q in queries:
        expected_tools = set(q.get("expected_tools", []))

        valid_predicted, hallucinated, prompt_tok, completion_tok, latency_ms = select_tools(
            config, q["query"], system, valid_names,
        )

        cat = q.get("category", "clean")
        stats = category_stats[cat]
        stats["total"] += 1
        stats["hallucinated"] += len(hallucinated)

        predicted_set = set(valid_predicted)

        if expected_tools:
            precision, recall, f1 = tool_set_metrics(predicted_set, expected_tools)
            exact = 1 if predicted_set == expected_tools else 0
            tool_count_err = abs(len(valid_predicted) - len(expected_tools))
            all_precision.append(precision)
            all_recall.append(recall)
            all_f1.append(f1)
            all_exact.append(exact)
            all_tool_count_err.append(tool_count_err)
            stats["f1_vals"].append(f1)
            stats["exact"] += exact
        else:
            precision, recall, f1 = -1, -1, -1
            exact = -1

        all_tool_counts.append(len(valid_predicted))
        all_hallucinated += len(hallucinated)
        all_latency.append(latency_ms)
        all_prompt_tokens.append(prompt_tok)
        all_completion_tokens.append(completion_tok)

        n_selected = len(valid_predicted)
        q_pruning = 1.0 - n_selected / total_tools if n_selected > 0 else -1
        prec_str = f"{precision:>5.2f}" if precision >= 0 else "    —"
        rec_str = f"{recall:>5.2f}" if recall >= 0 else "    —"
        f1_str = f"{f1:>5.2f}" if f1 >= 0 else "    —"
        em_str = f"{'Y' if exact == 1 else 'N':>3}" if exact >= 0 else "  —"
        hall_str = f"{len(hallucinated):>4}" if hallucinated else "   0"
        tools_str = f"{n_selected:>5}"
        prune_str = f"{q_pruning:>5.0%}" if q_pruning >= 0 else "     —"

        prompt = q["query"][:82] + "..." if len(q["query"]) > 85 else q["query"]
        print(
            f"{q['id']:<30} {cat:<12} {prompt:<85} "
            f"{prec_str} {rec_str} {f1_str} {em_str} {hall_str} {tools_str} {prune_str} {latency_ms:>6.0f}"
        )

    n = len(queries)
    print("─" * len(header))

    avg = lambda xs: sum(xs) / len(xs) if xs else 0.0
    def std(xs):
        if len(xs) < 2:
            return 0.0
        m = avg(xs)
        return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

    n_with_expected = len(all_precision)

    print(f"\nTool Selection ({n_with_expected} queries with expected tools):")
    print(f"  Avg Precision:      {avg(all_precision):.2f} ± {std(all_precision):.2f}")
    print(f"  Avg Recall:         {avg(all_recall):.2f} ± {std(all_recall):.2f}")
    print(f"  Avg F1:             {avg(all_f1):.2f} ± {std(all_f1):.2f}")
    print(f"  Exact Match:        {sum(all_exact)}/{n_with_expected} ({sum(all_exact)/n_with_expected:.0%})" if n_with_expected else "")
    print(f"  Hallucinated tools: {all_hallucinated} total across {n} queries")
    print(f"  Avg tool count err: {avg(all_tool_count_err):.1f}")

    avg_tools = avg(all_tool_counts)
    pruning = 1.0 - avg_tools / total_tools
    all_pruning = [1.0 - t / total_tools for t in all_tool_counts if t > 0]
    print(f"\nPruning:")
    print(f"  Avg tools selected: {avg_tools:.1f} ± {std(all_tool_counts):.1f} / {total_tools}")
    print(f"  Avg pruning:       {pruning:.0%} ± {std(all_pruning):.0%}" if all_pruning else "  Avg pruning:       —")

    print(f"\nLatency:")
    print(f"  Avg:                {avg(all_latency):.0f}ms")
    print(f"  P50:                {percentile(all_latency, 50):.0f}ms")
    print(f"  P95:                {percentile(all_latency, 95):.0f}ms")

    print(f"\nTokens:")
    print(f"  Avg prompt:         {avg(all_prompt_tokens):.0f}")
    print(f"  Avg completion:     {avg(all_completion_tokens):.0f}")

    print(f"\nBy Category:")
    cat_f1 = {}
    for cat in sorted(category_stats.keys()):
        s = category_stats[cat]
        n_cat = s["total"]
        f1_avg = avg(s["f1_vals"]) if s["f1_vals"] else -1
        cat_f1[cat] = f1_avg
        f1_str = f"f1={f1_avg:.2f}" if f1_avg >= 0 else "f1=—"
        exact_count = s["exact"]
        n_expected = len(s["f1_vals"])
        em_str = f"em={exact_count}/{n_expected}" if n_expected else "em=—"
        print(f"  {cat:<12} {em_str}  {f1_str}  hall={s['hallucinated']}")

    avg_tools = avg(all_tool_counts)
    return {
        "strategy": "baseline",
        "precision": avg(all_precision),
        "recall": avg(all_recall),
        "f1": avg(all_f1),
        "exact_match": sum(all_exact),
        "exact_match_n": n_with_expected,
        "hallucinated": all_hallucinated,
        "avg_tools": avg_tools,
        "total_tools": total_tools,
        "pruning": 1.0 - avg_tools / total_tools,
        "avg_tool_count_err": avg(all_tool_count_err),
        "latency_avg": avg(all_latency),
        "latency_p50": percentile(all_latency, 50),
        "latency_p95": percentile(all_latency, 95),
        "avg_prompt_tokens": avg(all_prompt_tokens),
        "avg_completion_tokens": avg(all_completion_tokens),
        "category_f1": cat_f1,
        "n": n,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="*", default=list(MODELS.keys()),
                        help="Models to benchmark (default: all). Options: " + ", ".join(MODELS.keys()))
    parser.add_argument("--domain", default="k8s",
                        help="Tool domain to benchmark (default: k8s). Must be a subpackage under benchmarks/.")
    args = parser.parse_args()

    for model_name in args.models:
        run_baseline(model_name, args.domain)


if __name__ == "__main__":
    main()
