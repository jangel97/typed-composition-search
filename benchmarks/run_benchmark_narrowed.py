import argparse
import importlib
import json
import time

from benchmarks.llm import MODELS, get_llm_config, llm_completion, get_embed_client, embed_texts
from benchmarks.metrics import avg, std, format_metric, format_pruning, format_tools
from benchmarks.parallel import run_queries_parallel
from benchmarks.report import BenchmarkReport, query_graph_metrics
from benchmarks.run_benchmark import SYSTEM_PROMPT
from benchmarks.run_retrieval import cosine_similarity


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

    text = (response.choices[0].message.content or "").strip()
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

    report = BenchmarkReport(total_tools, category_factory=lambda: {
        "total": 0, "path_found": 0, "type_exact": 0, "f1_vals": [], "type_recall": [],
    })

    source_correct = 0
    target_correct = 0
    type_exact = 0
    path_found_count = 0
    all_type_recall_at_k = []

    def process_query(q):
        query_embedding = embed_texts(embed_client, [q["query"]], embed_model)[0]
        narrowed_names = narrow_types(query_embedding, type_embeddings, type_names, narrow_k)
        src_in = q["source_type"] in narrowed_names
        tgt_in = q["target_type"] in narrowed_names
        type_recall_k = (int(src_in) + int(tgt_in)) / 2.0
        system = build_narrowed_prompt(entity_types, narrowed_names)
        prediction, latency_ms, prompt_tok, completion_tok = predict_types(config, q["query"], system)
        pred_source = prediction.get("source_type", "?")
        pred_target = prediction.get("target_type", "?")
        path = registry.resolve(pred_source, pred_target)
        return {
            "q": q, "pred_source": pred_source, "pred_target": pred_target,
            "path": path, "type_recall_k": type_recall_k,
            "latency_ms": latency_ms, "prompt_tok": prompt_tok, "completion_tok": completion_tok,
        }

    results = run_queries_parallel(queries, process_query)

    for r in results:
        q = r["q"]
        pred_source, pred_target = r["pred_source"], r["pred_target"]
        path, latency_ms = r["path"], r["latency_ms"]
        type_recall_k = r["type_recall_k"]

        cat = q.get("category", "clean")
        stats = report.category_stats[cat]
        report.record_latency(latency_ms, r["prompt_tok"], r["completion_tok"])

        all_type_recall_at_k.append(type_recall_k)
        stats["type_recall"].append(type_recall_k)

        expected_src = q["source_type"]
        expected_tgt = q["target_type"]
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

        path_found = path is not None
        if path_found:
            path_found_count += 1
            stats["path_found"] += 1

        expected_tools = set(q.get("expected_tools", []))
        resolved_tools = {t.name for t in path.tools} if path else set()
        n_tools = len(path.tools) if path else 0
        precision, recall, f1 = report.record_tool_result(resolved_tools, expected_tools, n_tools, cat)
        report.record_query(
            q["id"], cat, expected_tools, resolved_tools,
            precision, recall, f1, latency_ms, n_tools,
            expected_source=expected_src, expected_target=expected_tgt,
            predicted_source=pred_source, predicted_target=pred_target,
            path_found=path_found, type_recall_k=type_recall_k,
            **query_graph_metrics(registry, pred_source, pred_target, path),
        )

        path_mark = "OK" if path_found else "MISS"
        tr_str = f"{type_recall_k:>5.2f}"

        prompt = q["query"][:67] + "..." if len(q["query"]) > 70 else q["query"]
        print(
            f"{q['id']:<30} {cat:<12} {prompt:<70} "
            f"{expected_st:<25} {predicted_st:<25} "
            f"{tr_str} {path_mark:>4} {format_metric(precision)} {format_metric(recall)} {format_metric(f1)} "
            f"{format_tools(n_tools)} {format_pruning(n_tools, total_tools)} {latency_ms:>6.0f}"
        )

    n = len(queries)
    print("─" * len(header))

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
        tr_avg = avg(s["type_recall"]) if s["type_recall"] else -1
        tr_str = f"tr@{narrow_k}={tr_avg:.2f}" if tr_avg >= 0 else f"tr@{narrow_k}=—"
        print(f"  {cat:<12} path={s['path_found']}/{n_cat}  type_exact={s['type_exact']}/{n_cat}  {f1_str}  {tr_str}")

    return {
        **report.base_result_dict(f"graph-narrowed (top-{narrow_k})"),
        "type_recall_at_k": avg(all_type_recall_at_k),
        "path_found": path_found_count,
        "path_found_pct": path_found_count / n,
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
