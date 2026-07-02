import argparse
import importlib
import time
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from benchmarks.metrics import avg, format_metric, format_pruning, format_tools
from benchmarks.parallel import run_queries_parallel
from benchmarks.report import BenchmarkReport, query_graph_metrics


DEFAULT_MODEL_PATH = str(
    Path(__file__).parent / "aap_mcp" / "encoder_model"
)


def build_pair_text(source: str, target: str, entity_types: dict) -> str:
    src_desc = entity_types.get(source, "")
    tgt_desc = entity_types.get(target, "")
    return f"Source: {source} — {src_desc}. Target: {target} — {tgt_desc}."


def compute_reachable_pairs(registry, entity_types):
    pairs = set()
    type_names = sorted(entity_types.keys())
    for src in type_names:
        for tgt in type_names:
            if registry.resolve(src, tgt) is not None:
                pairs.add((src, tgt))
    return pairs


def run_benchmark_encoder(model_path: str, domain: str):
    reg_mod = importlib.import_module(f"benchmarks.{domain}.registry")
    queries_mod = importlib.import_module(f"benchmarks.{domain}.queries")
    build_registry = reg_mod.build_registry
    entity_types = reg_mod.ENTITY_TYPES
    queries = queries_mod.QUERIES

    registry = build_registry()
    total_tools = len(registry._tools)

    model = SentenceTransformer(model_path)

    print("Computing reachable type pairs...", end=" ", flush=True)
    valid_pairs = compute_reachable_pairs(registry, entity_types)
    pair_labels = sorted(valid_pairs)
    pair_texts = [build_pair_text(s, t, entity_types) for s, t in pair_labels]
    print(f"{len(pair_labels)} pairs")

    print("Encoding pair texts...", end=" ", flush=True)
    pair_embeddings = model.encode(pair_texts, convert_to_tensor=True, show_progress_bar=False)
    print("done")

    print(f"\n=== Encoder: {Path(model_path).name} ===")
    print(f"Reachable type pairs: {len(pair_labels)}")
    print(f"Total tools in registry: {total_tools}\n")

    header = (
        f"{'Query':<30} {'Category':<12} {'Prompt':<85} "
        f"{'Expected S→T':<25} {'Predicted S→T':<25} "
        f"{'Sim':>5} {'Path':>4} {'Tools':>5} {'Prune':>6} {'Prec':>5} {'Rec':>5} {'F1':>5} {'ms':>6}"
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

    def process_query(q):
        start = time.monotonic()
        query_emb = model.encode([q["query"]], convert_to_tensor=True, show_progress_bar=False)
        similarities = cos_sim(query_emb, pair_embeddings)[0]
        best_idx = similarities.argmax().item()
        best_sim = similarities[best_idx].item()
        latency_ms = (time.monotonic() - start) * 1000

        pred_source, pred_target = pair_labels[best_idx]
        path = registry.resolve(pred_source, pred_target)
        return {
            "q": q,
            "pred_source": pred_source,
            "pred_target": pred_target,
            "path": path,
            "similarity": best_sim,
            "latency_ms": latency_ms,
        }

    results = run_queries_parallel(queries, process_query, max_workers=1)

    for r in results:
        q = r["q"]
        pred_source, pred_target = r["pred_source"], r["pred_target"]
        path, latency_ms = r["path"], r["latency_ms"]
        similarity = r["similarity"]
        report.record_latency(latency_ms, 0, 0)

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

        path_found = path is not None
        if path_found:
            path_found_count += 1
            stats["path_found"] += 1

        expected_tools = set(q.get("expected_tools", []))
        resolved_tools = {t.name for t in path.tools} if path else set()
        n_tools = len(path.tools) if path else 0
        precision, recall, f1 = report.record_tool_result(
            resolved_tools, expected_tools, n_tools, cat,
        )
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
            f"{similarity:>5.2f} {path_mark:>4} {format_tools(n_tools)} {format_pruning(n_tools, total_tools)} "
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
    report.print_recall_decomposition()
    report.print_pruning()
    report.print_latency()

    print(f"\nBy Category:")
    for cat in sorted(report.category_stats.keys()):
        s = report.category_stats[cat]
        n_cat = s["total"]
        f1_avg = avg(s["f1_vals"]) if s["f1_vals"] else -1
        f1_str = f"f1={f1_avg:.2f}" if f1_avg >= 0 else "f1=—"
        print(f"  {cat:<12} path={s['path_found']}/{n_cat}  type_exact={s['type_exact']}/{n_cat}  {f1_str}")

    return {
        **report.base_result_dict("encoder"),
        "path_found": path_found_count,
        "path_found_pct": path_found_count / n,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", default=DEFAULT_MODEL_PATH,
                        help="Path to finetuned encoder (from finetune_encoder.py)")
    parser.add_argument("--domain", default="aap_mcp",
                        help="Tool domain to benchmark (default: aap_mcp)")
    args = parser.parse_args()

    run_benchmark_encoder(args.model_path, args.domain)


if __name__ == "__main__":
    main()
