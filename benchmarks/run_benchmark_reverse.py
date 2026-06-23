import argparse
import importlib
import math
import time
from collections import defaultdict

from benchmarks.llm import MODELS, get_llm_config, llm_completion
from benchmarks.run_benchmark import tool_set_metrics, percentile


Q1_TARGET_PROMPT = """Given the user query, which entity type does the user WANT TO OBTAIN or FIND?

Available entity types:
{type_list}

Respond with ONLY the entity type name, nothing else."""

Q2_SOURCE_PROMPT = """The user wants to obtain: {target_type} — {target_desc}

Given the user query, which entity type does the user ALREADY HAVE or START from?

Only these entity types can reach {target_type}:
{type_list}

Respond with ONLY the entity type name, nothing else."""


def build_type_list(entity_types: dict, type_names: list[str]) -> str:
    lines = []
    for name in type_names:
        desc = entity_types.get(name, "")
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)


def match_type_name(text: str, type_names: list[str]) -> str | None:
    text = text.strip()
    type_map = {name.lower(): name for name in type_names}
    if text.lower() in type_map:
        return type_map[text.lower()]
    return None


def predict_target(config, query, entity_types, type_names):
    type_list = build_type_list(entity_types, type_names)
    system = Q1_TARGET_PROMPT.format(type_list=type_list)

    start = time.monotonic()
    response = llm_completion(
        config,
        [
            {"role": "system", "content": system},
            {"role": "user", "content": query},
        ],
        max_tokens=20,
    )
    latency_ms = (time.monotonic() - start) * 1000

    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    text = response.choices[0].message.content.strip()
    matched = match_type_name(text, type_names)
    return matched, latency_ms, prompt_tokens, completion_tokens


def predict_source(config, query, target_type, target_desc, source_names, entity_types):
    type_list = build_type_list(entity_types, source_names)
    system = Q2_SOURCE_PROMPT.format(
        target_type=target_type,
        target_desc=target_desc,
        type_list=type_list,
    )

    start = time.monotonic()
    response = llm_completion(
        config,
        [
            {"role": "system", "content": system},
            {"role": "user", "content": query},
        ],
        max_tokens=20,
    )
    latency_ms = (time.monotonic() - start) * 1000

    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    text = response.choices[0].message.content.strip()
    matched = match_type_name(text, source_names)
    return matched, latency_ms, prompt_tokens, completion_tokens


def run_benchmark_reverse(model_name: str, domain: str):
    reg_mod = importlib.import_module(f"benchmarks.{domain}.registry")
    queries_mod = importlib.import_module(f"benchmarks.{domain}.queries")
    build_registry = reg_mod.build_registry
    entity_types = reg_mod.ENTITY_TYPES
    queries = queries_mod.QUERIES

    config = get_llm_config(model_name)
    model_id = config["litellm_model"]
    registry = build_registry()
    total_tools = len(registry._tools)

    type_names = sorted(entity_types.keys())

    print(f"\n=== GRAPH-REVERSE: {model_name} ({model_id}) ===")
    print(f"Total entity types: {len(type_names)}")
    print(f"Total tools: {total_tools}")
    print(f"Pipeline: Q1 (target) → reverse BFS (sources) → Q2 (source) → forward BFS\n")

    header = (
        f"{'Query':<30} {'Cat':<10} {'Expected S→T':<25} {'Predicted S→T':<25} "
        f"{'#Src':>4} {'Path':>4} {'Tools':>5} {'Prune':>6} {'Prec':>5} {'Rec':>5} {'F1':>5} {'ms':>7}"
    )
    print(header)
    print("─" * len(header))

    all_precision = []
    all_recall = []
    all_f1 = []
    all_tool_counts = []
    all_latency = []
    all_prompt_tokens = []
    all_completion_tokens = []
    target_correct = 0
    source_correct = 0
    exact_match = 0
    path_found_count = 0
    all_source_set_sizes = []

    category_stats = defaultdict(lambda: {
        "total": 0, "path_found": 0, "f1_vals": [],
        "target_correct": 0, "source_correct": 0, "exact_match": 0,
    })

    for q in queries:
        cat = q.get("category", "clean")
        stats = category_stats[cat]
        stats["total"] += 1

        total_latency = 0.0
        total_prompt = 0
        total_completion = 0

        pred_target, lat, ptok, ctok = predict_target(
            config, q["query"], entity_types, type_names,
        )
        total_latency += lat
        total_prompt += ptok
        total_completion += ctok

        pred_source = None
        n_sources = 0

        if pred_target:
            tgt_ok = pred_target == q["target_type"]
            if tgt_ok:
                target_correct += 1
                stats["target_correct"] += 1

            reverse_sources = registry.reverse_reachable_types(pred_target)
            source_names = sorted(reverse_sources & set(entity_types.keys()))
            n_sources = len(source_names)
            all_source_set_sizes.append(n_sources)

            if source_names:
                pred_source, lat, ptok, ctok = predict_source(
                    config, q["query"], pred_target, entity_types.get(pred_target, ""),
                    source_names, entity_types,
                )
                total_latency += lat
                total_prompt += ptok
                total_completion += ctok

                if pred_source == q["source_type"]:
                    source_correct += 1
                    stats["source_correct"] += 1
                if pred_source == q["source_type"] and tgt_ok:
                    exact_match += 1
                    stats["exact_match"] += 1

        all_latency.append(total_latency)
        all_prompt_tokens.append(total_prompt)
        all_completion_tokens.append(total_completion)

        path = None
        if pred_source and pred_target:
            path = registry.resolve(pred_source, pred_target)

        path_found = path is not None
        if path_found:
            path_found_count += 1
            stats["path_found"] += 1

        expected_tools = set(q.get("expected_tools", []))
        if path and expected_tools:
            resolved_tools = {t.name for t in path.tools}
            precision, recall, f1 = tool_set_metrics(resolved_tools, expected_tools)
            n_tools = len(path.tools)
            all_precision.append(precision)
            all_recall.append(recall)
            all_f1.append(f1)
            stats["f1_vals"].append(f1)
        else:
            precision, recall, f1 = -1, -1, -1
            n_tools = len(path.tools) if path else 0

        all_tool_counts.append(n_tools)

        expected_st = f"{q['source_type']}→{q['target_type']}"
        pred_st = f"{pred_source or '?'}→{pred_target or '?'}"
        path_mark = "OK" if path_found else "MISS"
        prec_str = f"{precision:>5.2f}" if precision >= 0 else "    —"
        rec_str = f"{recall:>5.2f}" if recall >= 0 else "    —"
        f1_str = f"{f1:>5.2f}" if f1 >= 0 else "    —"

        q_pruning = 1.0 - n_tools / total_tools if n_tools > 0 else -1
        tools_str = f"{n_tools:>5}" if n_tools > 0 else "    —"
        prune_str = f"{q_pruning:>5.0%}" if q_pruning >= 0 else "     —"

        print(
            f"{q['id']:<30} {cat:<10} {expected_st:<25} {pred_st:<25} "
            f"{n_sources:>4} {path_mark:>4} {tools_str} {prune_str} {prec_str} {rec_str} {f1_str} {total_latency:>7.0f}"
        )

    n = len(queries)
    print("─" * len(header))

    avg = lambda xs: sum(xs) / len(xs) if xs else 0.0
    def std(xs):
        if len(xs) < 2:
            return 0.0
        m = avg(xs)
        return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

    print(f"\nType Prediction ({n} queries):")
    print(f"  Target accuracy:   {target_correct}/{n} ({target_correct/n:.0%})")
    print(f"  Source accuracy:   {source_correct}/{n} ({source_correct/n:.0%})")
    print(f"  Exact match:       {exact_match}/{n} ({exact_match/n:.0%})")
    print(f"  Avg source candidates: {avg(all_source_set_sizes):.1f} ± {std(all_source_set_sizes):.1f}")

    print(f"\nPath Resolution:")
    print(f"  Path found:        {path_found_count}/{n} ({path_found_count/n:.0%})")

    if all_precision:
        print(f"\nTool Accuracy:")
        print(f"  Avg Precision:     {avg(all_precision):.2f} ± {std(all_precision):.2f}")
        print(f"  Avg Recall:        {avg(all_recall):.2f} ± {std(all_recall):.2f}")
        print(f"  Avg F1:            {avg(all_f1):.2f} ± {std(all_f1):.2f}")

    avg_tools = avg(all_tool_counts)
    pruning = 1.0 - avg_tools / total_tools
    all_pruning = [1.0 - t / total_tools for t in all_tool_counts if t > 0]
    print(f"\nPruning:")
    print(f"  Avg tools selected: {avg_tools:.1f} ± {std(all_tool_counts):.1f} / {total_tools}")
    print(f"  Avg pruning:       {pruning:.0%} ± {std(all_pruning):.0%}" if all_pruning else "  Avg pruning:       —")

    print(f"\nLatency:")
    print(f"  Avg:               {avg(all_latency):.0f}ms")
    print(f"  P50:               {percentile(all_latency, 50):.0f}ms")
    print(f"  P95:               {percentile(all_latency, 95):.0f}ms")

    print(f"\nTokens:")
    print(f"  Avg prompt:        {avg(all_prompt_tokens):.0f}")
    print(f"  Avg completion:    {avg(all_completion_tokens):.0f}")

    print(f"\nBy Category:")
    cat_f1 = {}
    for cat in sorted(category_stats.keys()):
        s = category_stats[cat]
        n_cat = s["total"]
        f1_avg = avg(s["f1_vals"]) if s["f1_vals"] else -1
        cat_f1[cat] = f1_avg
        f1_str = f"f1={f1_avg:.2f}" if f1_avg >= 0 else "f1=—"
        print(
            f"  {cat:<12} path={s['path_found']}/{n_cat}  "
            f"tgt={s['target_correct']}/{n_cat}  "
            f"src={s['source_correct']}/{n_cat}  {f1_str}"
        )

    return {
        "strategy": "graph-reverse",
        "precision": avg(all_precision),
        "recall": avg(all_recall),
        "f1": avg(all_f1),
        "hallucinated": 0,
        "avg_tools": avg_tools,
        "total_tools": total_tools,
        "pruning": pruning,
        "exact_match": exact_match,
        "exact_match_n": n,
        "latency_avg": avg(all_latency),
        "latency_p50": percentile(all_latency, 50),
        "latency_p95": percentile(all_latency, 95),
        "avg_prompt_tokens": avg(all_prompt_tokens),
        "avg_completion_tokens": avg(all_completion_tokens),
        "category_f1": cat_f1,
        "path_found": path_found_count,
        "path_found_pct": path_found_count / n,
        "n": n,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="*", default=["qwen"],
                        help="Models to benchmark (default: qwen)")
    parser.add_argument("--domain", default="k8s",
                        help="Tool domain to benchmark (default: k8s)")
    args = parser.parse_args()

    for model_name in args.models:
        run_benchmark_reverse(model_name, args.domain)


if __name__ == "__main__":
    main()
