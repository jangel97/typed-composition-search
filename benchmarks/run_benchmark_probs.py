import argparse
import importlib
import math
import time
from collections import defaultdict

from benchmarks.llm import MODELS, get_llm_config, llm_completion
from benchmarks.run_benchmark import tool_set_metrics, percentile


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


def build_type_list(entity_types: dict, type_names: list[str]) -> str:
    lines = []
    for name in type_names:
        desc = entity_types.get(name, "")
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)


def match_type_name(text: str, type_names: list[str]) -> str | None:
    """Match generated text to a known type name (case-insensitive)."""
    text = text.strip()
    type_map = {name.lower(): name for name in type_names}
    if text.lower() in type_map:
        return type_map[text.lower()]
    return None


DEFAULT_THRESHOLD = 0.15
DEFAULT_MAX_CANDIDATES = 5
FALLBACK_N = 3


def parse_completions(response, type_names: list[str]) -> list[tuple[str, float]]:
    """Extract type candidates from multiple completions, scored by aggregated sequence probability.

    For each completion, exp(sum of token logprobs) gives P(sequence).
    Completions producing the same type are summed, then normalized across all types.
    This combines both frequency and per-token confidence.

    Returns (type_name, probability) pairs sorted by probability descending.
    """
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
    """Keep candidates above confidence threshold, capped at max. Falls back to top-N."""
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

    all_precision = []
    all_recall = []
    all_f1 = []
    all_tool_counts = []
    all_latency = []
    all_prompt_tokens = []
    all_completion_tokens = []
    all_llm_calls = []
    source_in_topn = 0
    target_in_topn = 0
    path_found_count = 0

    category_stats = defaultdict(lambda: {
        "total": 0, "path_found": 0, "f1_vals": [],
        "source_in_topn": 0, "target_in_topn": 0,
    })

    for q in queries:
        cat = q.get("category", "clean")
        stats = category_stats[cat]
        stats["total"] += 1

        total_latency = 0.0
        total_prompt = 0
        total_completion = 0
        llm_calls = 0

        # Q1: predict source
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

        # Q2: for each source candidate, predict target from reachable types
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

        all_latency.append(total_latency)
        all_prompt_tokens.append(total_prompt)
        all_completion_tokens.append(total_completion)
        all_llm_calls.append(llm_calls)

        path_found = best_path is not None
        if path_found:
            path_found_count += 1
            stats["path_found"] += 1

        expected_tools = set(q.get("expected_tools", []))
        if best_path and expected_tools:
            resolved_tools = {t.name for t in best_path.tools}
            precision, recall, f1 = tool_set_metrics(resolved_tools, expected_tools)
            n_tools = len(best_path.tools)
            all_precision.append(precision)
            all_recall.append(recall)
            all_f1.append(f1)
            stats["f1_vals"].append(f1)
        else:
            precision, recall, f1 = -1, -1, -1
            n_tools = len(best_path.tools) if best_path else 0

        all_tool_counts.append(n_tools)

        expected_st = f"{q['source_type']}→{q['target_type']}"
        predicted_st = f"{best_source}→{best_target}"
        path_mark = "OK" if path_found else "MISS"
        q_pruning = 1.0 - n_tools / total_tools if n_tools > 0 else -1
        score_str = f"{best_score:>7.2f}" if best_score > float("-inf") else "     —"
        tools_str = f"{n_tools:>5}" if n_tools > 0 else "    —"
        prune_str = f"{q_pruning:>5.0%}" if q_pruning >= 0 else "     —"
        prec_str = f"{precision:>5.2f}" if precision >= 0 else "    —"
        rec_str = f"{recall:>5.2f}" if recall >= 0 else "    —"
        f1_str = f"{f1:>5.2f}" if f1 >= 0 else "    —"

        print(
            f"{q['id']:<30} {cat:<10} {expected_st:<25} {predicted_st:<25} "
            f"{score_str} {path_mark:>4} {tools_str} {prune_str} {prec_str} {rec_str} {f1_str} {llm_calls:>5} {total_latency:>7.0f}"
        )

    n = len(queries)
    print("─" * len(header))

    avg = lambda xs: sum(xs) / len(xs) if xs else 0.0
    def std(xs):
        if len(xs) < 2:
            return 0.0
        m = avg(xs)
        return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

    print(f"\nOracle Metrics (threshold={threshold}):")
    print(f"  Source in candidates: {source_in_topn}/{n} ({source_in_topn/n:.0%})")
    print(f"  Target in candidates: {target_in_topn}/{n} ({target_in_topn/n:.0%})")

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

    print(f"\nCost:")
    print(f"  Avg LLM calls:     {avg(all_llm_calls):.1f}")
    print(f"  Avg latency:       {avg(all_latency):.0f}ms")
    print(f"  P50 latency:       {percentile(all_latency, 50):.0f}ms")
    print(f"  P95 latency:       {percentile(all_latency, 95):.0f}ms")
    print(f"  Avg prompt tokens: {avg(all_prompt_tokens):.0f}")
    print(f"  Avg compl tokens:  {avg(all_completion_tokens):.0f}")

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
            f"src={s['source_in_topn']}/{n_cat}  "
            f"tgt={s['target_in_topn']}/{n_cat}  {f1_str}"
        )

    return {
        "strategy": f"graph-probs (t={threshold})",
        "precision": avg(all_precision),
        "recall": avg(all_recall),
        "f1": avg(all_f1),
        "hallucinated": 0,
        "avg_tools": avg_tools,
        "total_tools": total_tools,
        "pruning": pruning,
        "source_in_topn": source_in_topn,
        "target_in_topn": target_in_topn,
        "avg_llm_calls": avg(all_llm_calls),
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
