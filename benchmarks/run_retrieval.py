import argparse
import importlib
import json
import math
import time

from benchmarks.llm import MODELS, get_llm_config, llm_completion, get_embed_client
from benchmarks.metrics import avg, format_metric, format_pruning, format_tools
from benchmarks.report import BenchmarkReport


SYSTEM_PROMPT = """You are a tool selector.
Given a user query, select the tools needed to answer it, in execution order.

Available tools:
{tool_list}

Respond ONLY with a JSON list of tool names: ["tool_a", "tool_b"]"""


def tool_text(tool) -> str:
    inputs = ", ".join(tool.input_types)
    outputs = ", ".join(tool.output_types)
    return f"{tool.name}: ({inputs}) → ({outputs})"


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def embed_texts(client, texts: list[str], model: str) -> list[list[float]]:
    response = client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in response.data]


def retrieve_top_k(
    query_embedding: list[float],
    tool_embeddings: list[list[float]],
    tools: list,
    k: int,
) -> list:
    scored = []
    for i, emb in enumerate(tool_embeddings):
        sim = cosine_similarity(query_embedding, emb)
        scored.append((sim, i))
    scored.sort(reverse=True)
    return [tools[idx] for _, idx in scored[:k]]


def select_tools(
    config: dict,
    query: str,
    topk_tools: list,
) -> tuple[list[str], list[str], int, int, float]:
    tool_lines = "\n".join(f"- {tool_text(t)}" for t in topk_tools)
    system = SYSTEM_PROMPT.format(tool_list=tool_lines)
    valid_names = {t.name for t in topk_tools}

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


def run_retrieval(model_name: str, k: int, domain: str):
    reg_mod = importlib.import_module(f"benchmarks.{domain}.registry")
    queries_mod = importlib.import_module(f"benchmarks.{domain}.queries")
    build_registry = reg_mod.build_registry
    queries = queries_mod.QUERIES

    config = get_llm_config(model_name)
    model_id = config["litellm_model"]
    embed_client, embed_model = get_embed_client()

    registry = build_registry()
    total_tools = len(registry._tools)
    all_tools = list(registry._tools)

    print(f"\n=== RETRIEVAL (top-{k}): {model_name} ({model_id}) ===")
    print(f"Embedding model: {embed_model}")
    print(f"Total tools: {total_tools}, retrieving top-{k} per query\n")

    print("Embedding tools...", end=" ", flush=True)
    tool_texts = [tool_text(t) for t in all_tools]
    tool_embeddings = embed_texts(embed_client, tool_texts, embed_model)
    print("done.\n")

    header = (
        f"{'Query':<30} {'Category':<12} {'Prompt':<85} "
        f"{'R@k':>4} {'Prec':>5} {'Rec':>5} {'F1':>5} {'EM':>3} {'Hall':>4} {'Tools':>5} {'Prune':>6} {'ms':>6}"
    )
    print(header)
    print("─" * len(header))

    report = BenchmarkReport(total_tools, category_factory=lambda: {
        "total": 0, "exact": 0, "f1_vals": [], "hallucinated": 0, "retrieval_recall": [],
    })

    all_retrieval_recall = []
    all_exact = []
    all_tool_count_err = []
    all_hallucinated = 0

    for q in queries:
        expected_tools = set(q.get("expected_tools", []))
        cat = q.get("category", "clean")
        stats = report.category_stats[cat]

        query_embedding = embed_texts(embed_client, [q["query"]], embed_model)[0]
        topk_tools = retrieve_top_k(query_embedding, tool_embeddings, all_tools, k)
        topk_names = {t.name for t in topk_tools}

        if expected_tools:
            retrieval_hits = len(expected_tools & topk_names)
            retrieval_recall = retrieval_hits / len(expected_tools)
        else:
            retrieval_recall = -1
        all_retrieval_recall.append(retrieval_recall)
        if retrieval_recall >= 0:
            stats["retrieval_recall"].append(retrieval_recall)

        valid_predicted, hallucinated, prompt_tok, completion_tok, latency_ms = select_tools(
            config, q["query"], topk_tools,
        )
        report.record_latency(latency_ms, prompt_tok, completion_tok)

        stats["hallucinated"] += len(hallucinated)
        predicted_set = set(valid_predicted)
        n_selected = len(valid_predicted)
        precision, recall, f1 = report.record_tool_result(predicted_set, expected_tools, n_selected, cat)

        report.record_query(
            q["id"], cat, expected_tools, predicted_set,
            precision, recall, f1, latency_ms, n_selected,
            retrieval_recall=retrieval_recall,
            hallucinated_tools=hallucinated,
        )

        if expected_tools:
            exact = 1 if predicted_set == expected_tools else 0
            tool_count_err = abs(len(valid_predicted) - len(expected_tools))
            all_exact.append(exact)
            all_tool_count_err.append(tool_count_err)
            stats["exact"] += exact
        else:
            exact = -1

        all_hallucinated += len(hallucinated)

        rk_str = f"{retrieval_recall:>4.2f}" if retrieval_recall >= 0 else "   —"
        em_str = f"{'Y' if exact == 1 else 'N':>3}" if exact >= 0 else "  —"
        hall_str = f"{len(hallucinated):>4}" if hallucinated else "   0"

        prompt = q["query"][:82] + "..." if len(q["query"]) > 85 else q["query"]
        print(
            f"{q['id']:<30} {cat:<12} {prompt:<85} "
            f"{rk_str} {format_metric(precision)} {format_metric(recall)} {format_metric(f1)} {em_str} {hall_str} "
            f"{format_tools(n_selected)} {format_pruning(n_selected, total_tools)} {latency_ms:>6.0f}"
        )

    n = len(queries)
    print("─" * len(header))

    valid_rr = [r for r in all_retrieval_recall if r >= 0]
    from benchmarks.metrics import std
    print(f"\nRetrieval (top-{k}):")
    print(f"  Avg Recall@{k}:       {avg(valid_rr):.2f} ± {std(valid_rr):.2f}")

    report.print_tool_accuracy("Tool Selection")

    n_with_expected = len(all_exact)
    if n_with_expected:
        print(f"  Exact Match:        {sum(all_exact)}/{n_with_expected} ({sum(all_exact)/n_with_expected:.0%})")
    print(f"  Hallucinated tools: {all_hallucinated} total across {n} queries")
    print(f"  Avg tool count err: {avg(all_tool_count_err):.1f}")

    report.print_pruning()
    report.print_latency("Latency (LLM only)")
    report.print_tokens()

    print(f"\nBy Category:")
    for cat in sorted(report.category_stats.keys()):
        s = report.category_stats[cat]
        n_cat = s["total"]
        f1_avg = avg(s["f1_vals"]) if s["f1_vals"] else -1
        f1_str = f"f1={f1_avg:.2f}" if f1_avg >= 0 else "f1=—"
        exact_count = s["exact"]
        n_expected = len(s["f1_vals"])
        em_str = f"em={exact_count}/{n_expected}" if n_expected else "em=—"
        rr_avg = avg(s["retrieval_recall"]) if s["retrieval_recall"] else -1
        rr_str = f"r@{k}={rr_avg:.2f}" if rr_avg >= 0 else f"r@{k}=—"
        print(f"  {cat:<12} {em_str}  {f1_str}  {rr_str}  hall={s['hallucinated']}")

    return {
        **report.base_result_dict(f"retrieval (top-{k})", hallucinated=all_hallucinated),
        "exact_match": sum(all_exact),
        "exact_match_n": n_with_expected,
        "retrieval_recall_at_k": avg(valid_rr),
        "avg_tool_count_err": avg(all_tool_count_err),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="*", default=list(MODELS.keys()),
                        help="Models to benchmark (default: all). Options: " + ", ".join(MODELS.keys()))
    parser.add_argument("--top-k", type=int, default=10,
                        help="Number of tools to retrieve per query (default: 10)")
    parser.add_argument("--domain", default="k8s",
                        help="Tool domain to benchmark (default: k8s). Must be a subpackage under benchmarks/.")
    args = parser.parse_args()

    for model_name in args.models:
        run_retrieval(model_name, args.top_k, args.domain)


if __name__ == "__main__":
    main()
