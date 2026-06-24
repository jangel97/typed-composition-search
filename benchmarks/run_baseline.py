import argparse
import importlib
import json
import time

from benchmarks.llm import MODELS, get_llm_config, llm_completion
from benchmarks.metrics import avg, format_metric, format_pruning, format_tools
from benchmarks.report import BenchmarkReport


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

    report = BenchmarkReport(total_tools, category_factory=lambda: {
        "total": 0, "exact": 0, "f1_vals": [], "hallucinated": 0,
    })

    all_exact = []
    all_tool_count_err = []
    all_hallucinated = 0

    for q in queries:
        expected_tools = set(q.get("expected_tools", []))

        valid_predicted, hallucinated, prompt_tok, completion_tok, latency_ms = select_tools(
            config, q["query"], system, valid_names,
        )
        report.record_latency(latency_ms, prompt_tok, completion_tok)

        cat = q.get("category", "clean")
        stats = report.category_stats[cat]
        stats["hallucinated"] += len(hallucinated)

        predicted_set = set(valid_predicted)
        n_selected = len(valid_predicted)
        resolved_tools = predicted_set
        precision, recall, f1 = report.record_tool_result(resolved_tools, expected_tools, n_selected, cat)

        report.record_query(
            q["id"], cat, expected_tools, resolved_tools,
            precision, recall, f1, latency_ms, n_selected,
            predicted_tools=valid_predicted,
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

        em_str = f"{'Y' if exact == 1 else 'N':>3}" if exact >= 0 else "  —"
        hall_str = f"{len(hallucinated):>4}" if hallucinated else "   0"

        prompt = q["query"][:82] + "..." if len(q["query"]) > 85 else q["query"]
        print(
            f"{q['id']:<30} {cat:<12} {prompt:<85} "
            f"{format_metric(precision)} {format_metric(recall)} {format_metric(f1)} {em_str} {hall_str} "
            f"{format_tools(n_selected)} {format_pruning(n_selected, total_tools)} {latency_ms:>6.0f}"
        )

    n = len(queries)
    print("─" * len(header))

    report.print_tool_accuracy("Tool Selection")

    n_with_expected = len(all_exact)
    if n_with_expected:
        print(f"  Exact Match:        {sum(all_exact)}/{n_with_expected} ({sum(all_exact)/n_with_expected:.0%})")
    print(f"  Hallucinated tools: {all_hallucinated} total across {n} queries")
    print(f"  Avg tool count err: {avg(all_tool_count_err):.1f}")

    report.print_pruning()
    report.print_latency()
    report.print_tokens()

    print(f"\nBy Category:")
    for cat in sorted(report.category_stats.keys()):
        s = report.category_stats[cat]
        f1_avg = avg(s["f1_vals"]) if s["f1_vals"] else -1
        f1_str = f"f1={f1_avg:.2f}" if f1_avg >= 0 else "f1=—"
        exact_count = s["exact"]
        n_expected = len(s["f1_vals"])
        em_str = f"em={exact_count}/{n_expected}" if n_expected else "em=—"
        print(f"  {cat:<12} {em_str}  {f1_str}  hall={s['hallucinated']}")

    return {
        **report.base_result_dict("baseline", hallucinated=all_hallucinated),
        "exact_match": sum(all_exact),
        "exact_match_n": n_with_expected,
        "avg_tool_count_err": avg(all_tool_count_err),
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
