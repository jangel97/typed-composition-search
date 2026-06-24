import argparse
import importlib
import json
import time

from benchmarks.llm import MODELS, get_llm_config, llm_completion
from benchmarks.metrics import avg, format_metric, format_pruning, format_tools
from benchmarks.report import BenchmarkReport, query_graph_metrics


SYSTEM_PROMPT = """You are a type predictor for a tool composition system.

Given a user query, predict:
- source_type: The entity type the user already has or starts from
- target_type: The entity type the user wants to obtain

Available entity types:
{entity_types}

Respond ONLY with a JSON object:
{{"source_type": "...", "target_type": "..."}}"""


def build_system_prompt(entity_types: dict) -> str:
    lines = []
    for name, desc in sorted(entity_types.items()):
        lines.append(f"- {name}: {desc}")
    return SYSTEM_PROMPT.format(entity_types="\n".join(lines))


def predict_types(config: dict, query: str, system: str) -> tuple[dict, float, int, int]:
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


def run_benchmark(model_name: str, domain: str):
    reg_mod = importlib.import_module(f"benchmarks.{domain}.registry")
    queries_mod = importlib.import_module(f"benchmarks.{domain}.queries")
    build_registry = reg_mod.build_registry
    entity_types = reg_mod.ENTITY_TYPES
    queries = queries_mod.QUERIES

    config = get_llm_config(model_name)
    model_id = config["litellm_model"]
    registry = build_registry()
    total_tools = len(registry._tools)
    system = build_system_prompt(entity_types)

    print(f"\n=== {model_name} ({model_id}) ===")
    print(f"Total tools in registry: {total_tools}\n")

    header = (
        f"{'Query':<30} {'Category':<12} {'Prompt':<85} "
        f"{'Expected S→T':<25} {'Predicted S→T':<25} "
        f"{'Path':>4} {'Tools':>5} {'Prune':>6} {'Prec':>5} {'Rec':>5} {'F1':>5} {'ms':>6}"
    )
    print(header)
    print("─" * len(header))

    report = BenchmarkReport(total_tools, category_factory=lambda: {
        "total": 0, "path_found": 0, "type_exact": 0, "f1_vals": [],
    })

    source_correct = 0
    target_correct = 0
    type_exact = 0
    path_found_count = 0

    for q in queries:
        prediction, latency_ms, prompt_tok, completion_tok = predict_types(config, q["query"], system)
        report.record_latency(latency_ms, prompt_tok, completion_tok)
        pred_source = prediction.get("source_type", "?")
        pred_target = prediction.get("target_type", "?")

        cat = q.get("category", "clean")
        stats = report.category_stats[cat]

        expected_st = f"{q['source_type']}→{q['target_type']}"
        predicted_st = f"{pred_source}→{pred_target}"

        src_ok = pred_source == q["source_type"]
        tgt_ok = pred_target == q["target_type"]
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
        resolved_tools = {t.name for t in path.tools} if path else set()
        n_tools = len(path.tools) if path else 0
        precision, recall, f1 = report.record_tool_result(resolved_tools, expected_tools, n_tools, cat)
        report.record_query(
            q["id"], cat, expected_tools, resolved_tools,
            precision, recall, f1, latency_ms, n_tools,
            expected_source=q["source_type"], expected_target=q["target_type"],
            predicted_source=pred_source, predicted_target=pred_target,
            path_found=path_found,
            **query_graph_metrics(registry, pred_source, pred_target, path),
        )

        path_mark = "OK" if path_found else "MISS"
        prompt = q["query"][:82] + "..." if len(q["query"]) > 85 else q["query"]
        print(
            f"{q['id']:<30} {cat:<12} {prompt:<85} "
            f"{expected_st:<25} {predicted_st:<25} "
            f"{path_mark:>4} {format_tools(n_tools)} {format_pruning(n_tools, total_tools)} "
            f"{format_metric(precision)} {format_metric(recall)} {format_metric(f1)} {latency_ms:>6.0f}"
        )

    n = len(queries)
    print("─" * len(header))

    print(f"\nType Prediction ({n} queries):")
    print(f"  Source accuracy:     {source_correct}/{n} ({source_correct/n:.0%})")
    print(f"  Target accuracy:    {target_correct}/{n} ({target_correct/n:.0%})")
    print(f"  Exact match:         {type_exact}/{n} ({type_exact/n:.0%})")

    print(f"\nPath Resolution:")
    print(f"  Path found:         {path_found_count}/{n} ({path_found_count/n:.0%})")

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
        print(f"  {cat:<12} path={s['path_found']}/{n_cat}  type_exact={s['type_exact']}/{n_cat}  {f1_str}")

    return {
        **report.base_result_dict("graph"),
        "path_found": path_found_count,
        "path_found_pct": path_found_count / n,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="*", default=list(MODELS.keys()),
                        help="Models to benchmark (default: all). Options: " + ", ".join(MODELS.keys()))
    parser.add_argument("--domain", default="k8s",
                        help="Tool domain to benchmark (default: k8s). Must be a subpackage under benchmarks/.")
    args = parser.parse_args()

    for model_name in args.models:
        run_benchmark(model_name, args.domain)


if __name__ == "__main__":
    main()
