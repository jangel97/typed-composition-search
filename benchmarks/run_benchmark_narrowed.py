import argparse
import importlib
import json
import math
import time
from collections import defaultdict

from benchmarks.llm import MODELS, EMBED_CONFIG, get_llm_config, llm_completion, get_embed_client
from benchmarks.run_benchmark import SYSTEM_PROMPT, tool_set_metrics, percentile
from benchmarks.run_retrieval import cosine_similarity, embed_texts


def narrow_types(
    query_embedding: list[float],
    type_embeddings: list[list[float]],
    type_names: list[str],
    k: int,
) -> list[str]:
    scored = []
    for i, emb in enumerate(type_embeddings):
        sim = cosine_similarity(query_embedding, emb)
        scored.append((sim, i))
    scored.sort(reverse=True)
    return [type_names[idx] for _, idx in scored[:k]]


def build_narrowed_prompt(entity_types: dict, narrowed_names: list[str]) -> str:
    lines = []
    for name in sorted(narrowed_names):
        desc = entity_types.get(name, "")
        lines.append(f"- {name}: {desc}")
    return SYSTEM_PROMPT.format(entity_types="\n".join(lines))


def predict_types(config, query, system):
    start = time.monotonic()
    response = llm_completion(config, [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ])
    latency_ms = (time.monotonic() - start) * 1000
    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    text = response.choices[0].message.content.strip()
    start_idx = text.find("{")
    end_idx = text.rfind("}") + 1
    if start_idx == -1 or end_idx == 0:
        return {"source_type": "PARSE_ERROR", "target_type": "PARSE_ERROR"}, latency_ms, prompt_tokens, completion_tokens
    return json.loads(text[start_idx:end_idx]), latency_ms, prompt_tokens, completion_tokens


def run_benchmark_narrowed(model_name: str, domain: str, narrow_k: int):
    reg_mod = importlib.import_module(f"benchmarks.{domain}.registry")
    queries_mod = importlib.import_module(f"benchmarks.{domain}.queries")
    build_registry = reg_mod.build_registry
    entity_types = reg_mod.ENTITY_TYPES
    queries = queries_mod.QUERIES

    config = get_llm_config(model_name)
    model_id = config["litellm_model"]
    embed_client, embed_model = get_embed_client()

    registry = build_registry()
    total_tools = len(registry._tools)

    type_names = sorted(entity_types.keys())
    type_texts = [f"{name}: {entity_types[name]}" for name in type_names]

    print(f"\n=== GRAPH-NARROWED (top-{narrow_k}): {model_name} ({model_id}) ===")
    print(f"Embedding model: {embed_model}")
    print(f"Total entity types: {len(type_names)}, narrowing to top-{narrow_k} per query\n")

    print("Embedding entity types...", end=" ", flush=True)
    type_embeddings = embed_texts(embed_client, type_texts, embed_model)
    print("done.\n")

    header = (
        f"{'Query':<30} {'Cat':<12} {'Prompt':<70} "
        f"{'Expected S→T':<25} {'Predicted S→T':<25} "
        f"{'TR@k':>5} {'Path':>4} {'Prec':>5} {'Rec':>5} {'F1':>5} {'Tools':>5} {'Prune':>6} {'ms':>6}"
    )
    print(header)
    print("─" * len(header))

    source_correct = 0
    target_correct = 0
    type_exact = 0
    path_found_count = 0
    all_precision = []
    all_recall = []
    all_f1 = []
    all_tool_counts = []
    all_latency = []
    all_prompt_tokens = []
    all_completion_tokens = []
    all_type_recall_at_k = []

    category_stats = defaultdict(lambda: {
        "total": 0, "path_found": 0, "type_exact": 0, "f1_vals": [], "type_recall": [],
    })

    for q in queries:
        cat = q.get("category", "clean")
        stats = category_stats[cat]
        stats["total"] += 1

        query_embedding = embed_texts(embed_client, [q["query"]], embed_model)[0]
        narrowed_names = narrow_types(query_embedding, type_embeddings, type_names, narrow_k)

        expected_src = q["source_type"]
        expected_tgt = q["target_type"]
        src_in = expected_src in narrowed_names
        tgt_in = expected_tgt in narrowed_names
        type_recall_k = (int(src_in) + int(tgt_in)) / 2.0
        all_type_recall_at_k.append(type_recall_k)
        stats["type_recall"].append(type_recall_k)

        system = build_narrowed_prompt(entity_types, narrowed_names)
        prediction, latency_ms, prompt_tok, completion_tok = predict_types(
            config, q["query"], system,
        )
        all_latency.append(latency_ms)
        all_prompt_tokens.append(prompt_tok)
        all_completion_tokens.append(completion_tok)

        pred_source = prediction.get("source_type", "?")
        pred_target = prediction.get("target_type", "?")

        expected_st = f"{expected_src}→{expected_tgt}"
        predicted_st = f"{pred_source}→{pred_target}"

        src_ok = pred_source == expected_src
        tgt_ok = pred_target == expected_tgt
        if src_ok:
            source_correct += 1
        if tgt_ok:
            target_correct += 1
        if src_ok and tgt_ok:
            type_exact += 1
            stats["type_exact"] += 1

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

        path_mark = "OK" if path_found else "MISS"
        q_pruning = 1.0 - n_tools / total_tools if n_tools > 0 else -1
        tr_str = f"{type_recall_k:>5.2f}"
        prec_str = f"{precision:>5.2f}" if precision >= 0 else "    —"
        rec_str = f"{recall:>5.2f}" if recall >= 0 else "    —"
        f1_str = f"{f1:>5.2f}" if f1 >= 0 else "    —"
        tools_str = f"{n_tools:>5}" if n_tools > 0 else "    —"
        prune_str = f"{q_pruning:>5.0%}" if q_pruning >= 0 else "     —"

        prompt = q["query"][:67] + "..." if len(q["query"]) > 70 else q["query"]
        print(
            f"{q['id']:<30} {cat:<12} {prompt:<70} "
            f"{expected_st:<25} {predicted_st:<25} "
            f"{tr_str} {path_mark:>4} {prec_str} {rec_str} {f1_str} {tools_str} {prune_str} {latency_ms:>6.0f}"
        )

    n = len(queries)
    print("─" * len(header))

    avg = lambda xs: sum(xs) / len(xs) if xs else 0.0
    def std(xs):
        if len(xs) < 2:
            return 0.0
        m = avg(xs)
        return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

    print(f"\nLabel Narrowing (top-{narrow_k} of {len(type_names)} types):")
    print(f"  Avg Type Recall@{narrow_k}:  {avg(all_type_recall_at_k):.2f} ± {std(all_type_recall_at_k):.2f}")
    src_in_count = sum(1 for q, tr in zip(queries, all_type_recall_at_k) if tr >= 0.5)
    both_in_count = sum(1 for tr in all_type_recall_at_k if tr == 1.0)
    print(f"  Source in top-{narrow_k}:    {src_in_count}/{n}")
    print(f"  Both in top-{narrow_k}:      {both_in_count}/{n}")

    print(f"\nType Prediction ({n} queries):")
    print(f"  Source accuracy:    {source_correct}/{n} ({source_correct/n:.0%})")
    print(f"  Target accuracy:   {target_correct}/{n} ({target_correct/n:.0%})")
    print(f"  Exact match:       {type_exact}/{n} ({type_exact/n:.0%})")

    print(f"\nPath Resolution:")
    print(f"  Path found:        {path_found_count}/{n} ({path_found_count/n:.0%})")

    if all_precision:
        print(f"\nTool Accuracy (queries with expected tools):")
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
        tr_avg = avg(s["type_recall"]) if s["type_recall"] else -1
        tr_str = f"tr@{narrow_k}={tr_avg:.2f}" if tr_avg >= 0 else f"tr@{narrow_k}=—"
        print(f"  {cat:<12} path={s['path_found']}/{n_cat}  type_exact={s['type_exact']}/{n_cat}  {f1_str}  {tr_str}")

    return {
        "strategy": f"graph-narrowed (top-{narrow_k})",
        "precision": avg(all_precision),
        "recall": avg(all_recall),
        "f1": avg(all_f1),
        "hallucinated": 0,
        "avg_tools": avg_tools,
        "total_tools": total_tools,
        "pruning": pruning,
        "type_recall_at_k": avg(all_type_recall_at_k),
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
    parser.add_argument("models", nargs="*", default=list(MODELS.keys()),
                        help="Models to benchmark (default: all)")
    parser.add_argument("--narrow-k", type=int, default=10,
                        help="Number of entity types to narrow to (default: 10)")
    parser.add_argument("--domain", default="k8s",
                        help="Tool domain to benchmark (default: k8s)")
    args = parser.parse_args()

    for model_name in args.models:
        run_benchmark_narrowed(model_name, args.domain, args.narrow_k)


if __name__ == "__main__":
    main()
