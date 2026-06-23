import argparse
import importlib
import time

from benchmarks.llm import get_llm_config, llm_completion
from benchmarks.metrics import avg, std, build_type_list, match_type_name, format_metric, format_pruning, format_tools
from benchmarks.report import BenchmarkReport


Q1_TARGET_PROMPT = """Given the user query, which entity type does the user WANT TO OBTAIN or FIND?

Available entity types:
{type_list}

Respond with ONLY the entity type name, nothing else."""

Q2_SOURCE_PROMPT = """The user wants to obtain: {target_type} — {target_desc}

Given the user query, which entity type does the user ALREADY HAVE or START from?

Only these entity types can reach {target_type}:
{type_list}

Respond with ONLY the entity type name, nothing else."""


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

    report = BenchmarkReport(total_tools, category_factory=lambda: {
        "total": 0, "path_found": 0, "f1_vals": [],
        "target_correct": 0, "source_correct": 0, "exact_match": 0,
    })

    target_correct = 0
    source_correct = 0
    exact_match = 0
    path_found_count = 0
    all_source_set_sizes = []

    for q in queries:
        cat = q.get("category", "clean")
        stats = report.category_stats[cat]

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

        report.record_latency(total_latency, total_prompt, total_completion)

        path = None
        if pred_source and pred_target:
            path = registry.resolve(pred_source, pred_target)

        path_found = path is not None
        if path_found:
            path_found_count += 1
            stats["path_found"] += 1

        expected_tools = set(q.get("expected_tools", []))
        resolved_tools = {t.name for t in path.tools} if path else set()
        n_tools = len(path.tools) if path else 0
        precision, recall, f1 = report.record_tool_result(resolved_tools, expected_tools, n_tools, cat)

        expected_st = f"{q['source_type']}→{q['target_type']}"
        pred_st = f"{pred_source or '?'}→{pred_target or '?'}"
        path_mark = "OK" if path_found else "MISS"

        print(
            f"{q['id']:<30} {cat:<10} {expected_st:<25} {pred_st:<25} "
            f"{n_sources:>4} {path_mark:>4} {format_tools(n_tools)} {format_pruning(n_tools, total_tools)} "
            f"{format_metric(precision)} {format_metric(recall)} {format_metric(f1)} {total_latency:>7.0f}"
        )

    n = len(queries)
    print("─" * len(header))

    print(f"\nType Prediction ({n} queries):")
    print(f"  Target accuracy:   {target_correct}/{n} ({target_correct/n:.0%})")
    print(f"  Source accuracy:   {source_correct}/{n} ({source_correct/n:.0%})")
    print(f"  Exact match:       {exact_match}/{n} ({exact_match/n:.0%})")
    print(f"  Avg source candidates: {avg(all_source_set_sizes):.1f} ± {std(all_source_set_sizes):.1f}")

    print(f"\nPath Resolution:")
    print(f"  Path found:        {path_found_count}/{n} ({path_found_count/n:.0%})")

    report.print_tool_accuracy()
    report.print_pruning()
    report.print_latency()
    report.print_tokens()

    print(f"\nBy Category:")
    for cat in sorted(report.category_stats.keys()):
        s = report.category_stats[cat]
        n_cat = s["total"]
        f1_avg = avg(s["f1_vals"]) if s["f1_vals"] else -1
        f1_str = f"f1={f1_avg:.2f}" if f1_avg >= 0 else "f1=—"
        print(
            f"  {cat:<12} path={s['path_found']}/{n_cat}  "
            f"tgt={s['target_correct']}/{n_cat}  "
            f"src={s['source_correct']}/{n_cat}  {f1_str}"
        )

    return {
        **report.base_result_dict("graph-reverse"),
        "exact_match": exact_match,
        "exact_match_n": n,
        "path_found": path_found_count,
        "path_found_pct": path_found_count / n,
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
