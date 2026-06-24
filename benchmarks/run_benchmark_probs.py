import argparse
import importlib
import math
import time

from benchmarks.llm import MODELS, get_llm_config, llm_completion
from benchmarks.metrics import avg, build_type_list, match_type_name, format_metric, format_pruning, format_tools
from benchmarks.report import BenchmarkReport, query_graph_metrics


Q1_PROMPT = """The user's query describes something they HAVE (the starting point) and something they WANT (the goal).

The starting point is the entity the user can already identify — for example, they know a deployment name, a namespace, a pod name, a role name.
This is NOT what they want to find or obtain.

Example: "Get the logs for pods in the nginx deployment" → the user HAS a Deployment (they know "nginx"). They WANT logs. Answer: Deployment
Example: "Show me the events for pods in the api-gateway deployment" → the user HAS a Deployment. Answer: Deployment
Example: "What are the default variables for the database role?" → the user HAS a Role. Answer: Role

Given the user query, what entity type does the user HAVE (the starting point)?

Available entity types:
{type_list}

Respond with ONLY the entity type name, nothing else."""

Q2_PROMPT = """The user starts from: {source_type} — {source_desc}

Given the user query, which entity type does the user WANT TO OBTAIN or FIND?

Available entity types:
{type_list}

Respond with ONLY the entity type name, nothing else."""


DEFAULT_THRESHOLD = 0.15
DEFAULT_MAX_CANDIDATES = 5
FALLBACK_N = 3


def parse_completions(response, type_names: list[str]) -> list[tuple[str, float]]:
    """Extract type candidates from multiple completions, scored by aggregated sequence probability."""
    prob_sums: dict[str, float] = {}

    for choice in response.choices:
        text = choice.message.content.strip()
        matched = match_type_name(text, type_names)
        if not matched:
            continue

        if choice.logprobs and choice.logprobs.content:
            seq_prob = math.exp(sum(tok.logprob for tok in choice.logprobs.content))
        else:
            seq_prob = 1.0

        prob_sums[matched] = prob_sums.get(matched, 0.0) + seq_prob

    total = sum(prob_sums.values())
    if total == 0:
        return []

    candidates = [(name, p / total) for name, p in prob_sums.items()]
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates


def filter_candidates(
    candidates: list[tuple[str, float]],
    threshold: float = DEFAULT_THRESHOLD,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
) -> list[tuple[str, float]]:
    above = [(name, prob) for name, prob in candidates if prob >= threshold]
    if not above:
        return candidates[:FALLBACK_N]
    return above[:max_candidates]


def predict_source(config, query, entity_types, type_names, threshold, max_candidates):
    type_list = build_type_list(entity_types, type_names)
    system = Q1_PROMPT.format(type_list=type_list)

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
    candidates = [(matched, 1.0)] if matched else []
    return candidates, latency_ms, prompt_tokens, completion_tokens


def predict_target(config, query, source_type, source_desc, reachable_names, entity_types, threshold, max_candidates):
    type_list = build_type_list(entity_types, reachable_names)
    system = Q2_PROMPT.format(
        source_type=source_type,
        source_desc=source_desc,
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
    matched = match_type_name(text, reachable_names)
    candidates = [(matched, 1.0)] if matched else []
    return candidates, latency_ms, prompt_tokens, completion_tokens


def run_benchmark_probs(model_name: str, domain: str, threshold: float = DEFAULT_THRESHOLD, max_candidates: int = DEFAULT_MAX_CANDIDATES):
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

    print(f"\n=== GRAPH-PROBS (threshold={threshold}, max={max_candidates}): {model_name} ({model_id}) ===")
    print(f"Total entity types: {len(type_names)}")
    print(f"Total tools: {total_tools}")
    print(f"Pipeline: Q1 (source) → filter(≥{threshold}) → Q2 (target|source) → score → BFS\n")

    header = (
        f"{'Query':<30} {'Cat':<10} {'Expected S→T':<25} {'Best S→T':<25} "
        f"{'Score':>7} {'Path':>4} {'Tools':>5} {'Prune':>6} {'Prec':>5} {'Rec':>5} {'F1':>5} {'Calls':>5} {'ms':>7}"
    )
    print(header)
    print("─" * len(header))

    report = BenchmarkReport(total_tools, category_factory=lambda: {
        "total": 0, "path_found": 0, "f1_vals": [],
        "source_in_topn": 0, "target_in_topn": 0,
    })

    source_in_topn = 0
    target_in_topn = 0
    path_found_count = 0
    all_llm_calls = []

    for q in queries:
        cat = q.get("category", "clean")
        stats = report.category_stats[cat]

        total_latency = 0.0
        total_prompt = 0
        total_completion = 0
        llm_calls = 0

        source_candidates, lat, ptok, ctok = predict_source(
            config, q["query"], entity_types, type_names, threshold, max_candidates,
        )
        total_latency += lat
        total_prompt += ptok
        total_completion += ctok
        llm_calls += 1

        src_in = any(name == q["source_type"] for name, _ in source_candidates)
        if src_in:
            source_in_topn += 1
            stats["source_in_topn"] += 1

        best_path = None
        best_score = float("-inf")
        best_source = "?"
        best_target = "?"
        tgt_found = False

        for src_name, src_prob in source_candidates:
            reachable = registry.reachable_types(src_name)
            if not reachable:
                continue
            reachable_names = sorted(reachable & set(entity_types.keys()))
            if not reachable_names:
                continue

            target_candidates, lat, ptok, ctok = predict_target(
                config, q["query"], src_name, entity_types.get(src_name, ""),
                reachable_names, entity_types, threshold, max_candidates,
            )
            total_latency += lat
            total_prompt += ptok
            total_completion += ctok
            llm_calls += 1

            if any(name == q["target_type"] for name, _ in target_candidates):
                tgt_found = True

            for tgt_name, tgt_prob in target_candidates:
                score = math.log(src_prob) + math.log(tgt_prob)
                if score > best_score:
                    path = registry.resolve(src_name, tgt_name)
                    if path is not None:
                        best_score = score
                        best_path = path
                        best_source = src_name
                        best_target = tgt_name

        if tgt_found:
            target_in_topn += 1
            stats["target_in_topn"] += 1

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
        report.record_query(
            q["id"], cat, expected_tools, resolved_tools,
            precision, recall, f1, total_latency, n_tools,
            expected_source=q["source_type"], expected_target=q["target_type"],
            predicted_source=best_source, predicted_target=best_target,
            path_found=path_found,
            best_score=best_score if best_score > float("-inf") else None,
            llm_calls=llm_calls,
            **query_graph_metrics(registry, best_source, best_target, best_path),
        )

        expected_st = f"{q['source_type']}→{q['target_type']}"
        predicted_st = f"{best_source}→{best_target}"
        path_mark = "OK" if path_found else "MISS"
        score_str = f"{best_score:>7.2f}" if best_score > float("-inf") else "     —"

        print(
            f"{q['id']:<30} {cat:<10} {expected_st:<25} {predicted_st:<25} "
            f"{score_str} {path_mark:>4} {format_tools(n_tools)} {format_pruning(n_tools, total_tools)} "
            f"{format_metric(precision)} {format_metric(recall)} {format_metric(f1)} {llm_calls:>5} {total_latency:>7.0f}"
        )

    n = len(queries)
    print("─" * len(header))

    print(f"\nOracle Metrics (threshold={threshold}):")
    print(f"  Source in candidates: {source_in_topn}/{n} ({source_in_topn/n:.0%})")
    print(f"  Target in candidates: {target_in_topn}/{n} ({target_in_topn/n:.0%})")

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
            f"src={s['source_in_topn']}/{n_cat}  "
            f"tgt={s['target_in_topn']}/{n_cat}  {f1_str}"
        )

    return {
        **report.base_result_dict(f"graph-probs (t={threshold})"),
        "source_in_topn": source_in_topn,
        "target_in_topn": target_in_topn,
        "avg_llm_calls": avg(all_llm_calls),
        "path_found": path_found_count,
        "path_found_pct": path_found_count / n,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="*", default=["qwen"],
                        help="Models to benchmark (default: qwen). Logprobs required.")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help=f"Confidence threshold for candidates (default: {DEFAULT_THRESHOLD})")
    parser.add_argument("--max-candidates", type=int, default=DEFAULT_MAX_CANDIDATES,
                        help=f"Max candidates to keep (default: {DEFAULT_MAX_CANDIDATES})")
    parser.add_argument("--domain", default="k8s",
                        help="Tool domain to benchmark (default: k8s)")
    args = parser.parse_args()

    for model_name in args.models:
        run_benchmark_probs(model_name, args.domain, args.threshold, args.max_candidates)


if __name__ == "__main__":
    main()
