import argparse
import importlib

from benchmarks.llm import MODELS, get_llm_config
from benchmarks.metrics import avg
from benchmarks.report import BenchmarkReport
from benchmarks.run_benchmark import build_system_prompt, predict_types


def run_model_types(model_name: str, domain: str):
    reg_mod = importlib.import_module(f"benchmarks.{domain}.registry")
    queries_mod = importlib.import_module(f"benchmarks.{domain}.queries")
    entity_types = reg_mod.ENTITY_TYPES
    queries = queries_mod.QUERIES

    config = get_llm_config(model_name)
    model_id = config["litellm_model"]
    system = build_system_prompt(entity_types)

    print(f"\n=== MODEL-TYPES: {model_name} ({model_id}) ===")
    print(f"Total entity types: {len(entity_types)}")
    print(f"Pipeline: query → LLM → predict source + target (no graph resolution)\n")

    header = (
        f"{'Query':<30} {'Cat':<10} {'Expected S→T':<25} {'Predicted S→T':<25} "
        f"{'Src':>3} {'Tgt':>3} {'Both':>4} {'ms':>7}"
    )
    print(header)
    print("─" * len(header))

    report = BenchmarkReport(0, category_factory=lambda: {
        "total": 0, "f1_vals": [],
        "source_correct": 0, "target_correct": 0, "exact_match": 0,
    })

    source_correct = 0
    target_correct = 0
    exact_match = 0

    for q in queries:
        cat = q.get("category", "clean")
        stats = report.category_stats[cat]

        prediction, latency_ms, ptok, ctok = predict_types(config, q["query"], system)
        report.record_latency(latency_ms, ptok, ctok)

        pred_source = prediction.get("source_type", "?")
        pred_target = prediction.get("target_type", "?")

        src_ok = pred_source == q["source_type"]
        tgt_ok = pred_target == q["target_type"]
        both_ok = src_ok and tgt_ok

        if src_ok:
            source_correct += 1
            stats["source_correct"] += 1
        if tgt_ok:
            target_correct += 1
            stats["target_correct"] += 1
        if both_ok:
            exact_match += 1
            stats["exact_match"] += 1

        report.record_tool_result(set(), set(), 0, cat)
        report.record_query(
            q["id"], cat, set(), set(),
            -1.0, -1.0, -1.0, latency_ms, 0,
            expected_source=q["source_type"], expected_target=q["target_type"],
            predicted_source=pred_source, predicted_target=pred_target,
            source_correct=src_ok, target_correct=tgt_ok, both_correct=both_ok,
        )

        expected_st = f"{q['source_type']}→{q['target_type']}"
        predicted_st = f"{pred_source}→{pred_target}"
        src_mark = "✓" if src_ok else "✗"
        tgt_mark = "✓" if tgt_ok else "✗"
        both_mark = "✓" if both_ok else "✗"

        print(
            f"{q['id']:<30} {cat:<10} {expected_st:<25} {predicted_st:<25} "
            f"{src_mark:>3} {tgt_mark:>3} {both_mark:>4} {latency_ms:>7.0f}"
        )

    n = len(queries)
    print("─" * len(header))

    print(f"\nType Prediction ({n} queries):")
    print(f"  Source accuracy:   {source_correct}/{n} ({source_correct/n:.0%})")
    print(f"  Target accuracy:   {target_correct}/{n} ({target_correct/n:.0%})")
    print(f"  Exact match:       {exact_match}/{n} ({exact_match/n:.0%})")

    report.print_latency()
    report.print_tokens()

    print(f"\nBy Category:")
    for cat in sorted(report.category_stats.keys()):
        s = report.category_stats[cat]
        n_cat = s["total"]
        print(
            f"  {cat:<12} src={s['source_correct']}/{n_cat}  "
            f"tgt={s['target_correct']}/{n_cat}  "
            f"exact={s['exact_match']}/{n_cat}"
        )

    return {
        **report.base_result_dict("model-types"),
        "source_correct": source_correct,
        "target_correct": target_correct,
        "exact_match": exact_match,
        "source_accuracy": source_correct / n,
        "target_accuracy": target_correct / n,
        "exact_match_accuracy": exact_match / n,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="*", default=["qwen"],
                        help="Models to benchmark (default: qwen)")
    parser.add_argument("--domain", default="k8s",
                        help="Tool domain to benchmark (default: k8s)")
    args = parser.parse_args()

    for model_name in args.models:
        run_model_types(model_name, args.domain)


if __name__ == "__main__":
    main()
