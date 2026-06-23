import argparse
import importlib
import math
import time

from benchmarks.llm import get_llm_config, llm_completion
from benchmarks.metrics import avg, std, build_type_list, format_metric, format_pruning, format_tools
from benchmarks.run_benchmark_probs import parse_completions, filter_candidates, DEFAULT_THRESHOLD, DEFAULT_MAX_CANDIDATES
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


def predict_target_constrained(config, query, entity_types, type_names, n):
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
        n=n,
        logprobs=True,
        temperature=0.7,
        extra_body={"guided_choice": type_names},
    )
    latency_ms = (time.monotonic() - start) * 1000

    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    candidates = parse_completions(response, type_names)
    return candidates, latency_ms, prompt_tokens, completion_tokens


def predict_source_constrained(config, query, target_type, target_desc, source_names, entity_types, n):
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
        n=n,
        logprobs=True,
        temperature=0.7,
        extra_body={"guided_choice": source_names},
    )
    latency_ms = (time.monotonic() - start) * 1000

    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    candidates = parse_completions(response, source_names)
    return candidates, latency_ms, prompt_tokens, completion_tokens


def run_benchmark_constrained(
    model_name: str,
    domain: str,
    n_completions: int = 5,
    threshold: float = DEFAULT_THRESHOLD,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
):
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

    print(f"\n=== CONSTRAINED-REVERSE (n={n_completions}, t={threshold}): {model_name} ({model_id}) ===")
    print(f"Total entity types: {len(type_names)}")
    print(f"Total tools: {total_tools}")
    print(f"Pipeline: Q1 target (guided_choice, n={n_completions}) → reverse BFS → Q2 source (guided_choice, n={n_completions}) → score → forward BFS\n")

    header = (
        f"{'Query':<30} {'Cat':<10} {'Expected S→T':<25} {'Best S→T':<25} "
        f"{'Score':>7} {'#Tgt':>4} {'#Src':>4} {'Path':>4} {'Tools':>5} {'Prune':>6} "
        f"{'Prec':>5} {'Rec':>5} {'F1':>5} {'Calls':>5} {'ms':>7}"
    )
    print(header)
    print("─" * len(header))

    report = BenchmarkReport(total_tools, category_factory=lambda: {
        "total": 0, "path_found": 0, "f1_vals": [],
        "target_in_topn": 0, "source_in_topn": 0,
    })

    target_in_topn = 0
    source_in_topn = 0
    path_found_count = 0
    all_llm_calls = []

    for q in queries:
        cat = q.get("category", "clean")
        stats = report.category_stats[cat]

        total_latency = 0.0
        total_prompt = 0
        total_completion = 0
        llm_calls = 0

        target_candidates, lat, ptok, ctok = predict_target_constrained(
            config, q["query"], entity_types, type_names, n_completions,
        )
        total_latency += lat
        total_prompt += ptok
        total_completion += ctok
        llm_calls += 1

        target_candidates = filter_candidates(target_candidates, threshold, max_candidates)
        n_tgt = len(target_candidates)

        tgt_in = any(name == q["target_type"] for name, _ in target_candidates)
        if tgt_in:
            target_in_topn += 1
            stats["target_in_topn"] += 1

        best_path = None
        best_score = float("-inf")
        best_source = "?"
        best_target = "?"
        src_found = False
        best_n_src = 0

        for tgt_name, tgt_prob in target_candidates:
            reverse_sources = registry.reverse_reachable_types(tgt_name)
            source_names = sorted(reverse_sources & set(entity_types.keys()))
            if not source_names:
                continue

            source_candidates, lat, ptok, ctok = predict_source_constrained(
                config, q["query"], tgt_name, entity_types.get(tgt_name, ""),
                source_names, entity_types, n_completions,
            )
            total_latency += lat
            total_prompt += ptok
            total_completion += ctok
            llm_calls += 1

            source_candidates = filter_candidates(source_candidates, threshold, max_candidates)

            if any(name == q["source_type"] for name, _ in source_candidates):
                src_found = True

            for src_name, src_prob in source_candidates:
                score = math.log(tgt_prob) + math.log(src_prob)
                if score > best_score:
                    path = registry.resolve(src_name, tgt_name)
                    if path is not None:
                        best_score = score
                        best_path = path
                        best_source = src_name
                        best_target = tgt_name
                        best_n_src = len(source_candidates)

        if src_found:
            source_in_topn += 1
            stats["source_in_topn"] += 1

        report.record_latency(total_latency, total_prompt, total_completion)
        all_llm_calls.append(llm_calls)

        path_found = best_path is not None
        if path_found:
            path_found_count += 1
            stats["path_found"] += 1

        expected_tools = set(q.get("expected_tools", []))
        resolved_tools = {t.name for t in best_path.tools} if best_path else set()
        n_tools = len(best_path.tools) if best_path else 0
        precision, recall, f1 = report.record_tool_result(resolved_tools, expected_tools, n_tools, cat)

        expected_st = f"{q['source_type']}→{q['target_type']}"
        predicted_st = f"{best_source}→{best_target}"
        path_mark = "OK" if path_found else "MISS"
        score_str = f"{best_score:>7.2f}" if best_score > float("-inf") else "     —"

        print(
            f"{q['id']:<30} {cat:<10} {expected_st:<25} {predicted_st:<25} "
            f"{score_str} {n_tgt:>4} {best_n_src:>4} {path_mark:>4} "
            f"{format_tools(n_tools)} {format_pruning(n_tools, total_tools)} "
            f"{format_metric(precision)} {format_metric(recall)} {format_metric(f1)} "
            f"{llm_calls:>5} {total_latency:>7.0f}"
        )

    n = len(queries)
    print("─" * len(header))

    print(f"\nOracle Metrics (n={n_completions}, threshold={threshold}):")
    print(f"  Target in candidates: {target_in_topn}/{n} ({target_in_topn/n:.0%})")
    print(f"  Source in candidates: {source_in_topn}/{n} ({source_in_topn/n:.0%})")

    print(f"\nPath Resolution:")
    print(f"  Path found:        {path_found_count}/{n} ({path_found_count/n:.0%})")

    report.print_tool_accuracy()
    report.print_pruning()

    print(f"\nCost:")
    print(f"  Avg LLM calls:     {avg(all_llm_calls):.1f}")
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
            f"tgt={s['target_in_topn']}/{n_cat}  "
            f"src={s['source_in_topn']}/{n_cat}  {f1_str}"
        )

    return {
        **report.base_result_dict(f"constrained (n={n_completions})"),
        "target_in_topn": target_in_topn,
        "source_in_topn": source_in_topn,
        "avg_llm_calls": avg(all_llm_calls),
        "path_found": path_found_count,
        "path_found_pct": path_found_count / n,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="*", default=["qwen"],
                        help="Models to benchmark (default: qwen)")
    parser.add_argument("--n-completions", type=int, default=5,
                        help="Number of completions per LLM call (default: 5)")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help=f"Confidence threshold (default: {DEFAULT_THRESHOLD})")
    parser.add_argument("--max-candidates", type=int, default=DEFAULT_MAX_CANDIDATES,
                        help=f"Max candidates to keep (default: {DEFAULT_MAX_CANDIDATES})")
    parser.add_argument("--domain", default="k8s",
                        help="Tool domain to benchmark (default: k8s)")
    args = parser.parse_args()

    for model_name in args.models:
        run_benchmark_constrained(model_name, args.domain, args.n_completions, args.threshold, args.max_candidates)


if __name__ == "__main__":
    main()
