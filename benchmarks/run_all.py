import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from benchmarks.llm import MODELS, get_llm_config
from benchmarks.run_benchmark import run_benchmark
from benchmarks.run_baseline import run_baseline
from benchmarks.run_retrieval import run_retrieval
from benchmarks.run_benchmark_narrowed import run_benchmark_narrowed
from benchmarks.run_benchmark_probs import run_benchmark_probs
from benchmarks.run_benchmark_reverse import run_benchmark_reverse
from benchmarks.run_benchmark_reverse_probs import run_benchmark_reverse_probs
from benchmarks.run_benchmark_constrained import run_benchmark_constrained
from benchmarks.run_oracle_graph import run_oracle_graph
from benchmarks.run_model_types import run_model_types

STRATEGIES = [
    ("oracle-graph",        lambda m, d, p: run_oracle_graph(d)),
    ("model-types",         lambda m, d, p: run_model_types(m, d)),
    ("baseline",            lambda m, d, p: run_baseline(m, d)),
    ("retrieval",           lambda m, d, p: run_retrieval(m, p["top_k"], d)),
    ("graph",               lambda m, d, p: run_benchmark(m, d)),
    ("graph-narrowed",      lambda m, d, p: run_benchmark_narrowed(m, d, p["narrow_k"])),
    ("graph-probs",         lambda m, d, p: run_benchmark_probs(m, d, p["threshold"], p["max_candidates"])),
    ("graph-reverse",       lambda m, d, p: run_benchmark_reverse(m, d)),
    ("graph-reverse-probs", lambda m, d, p: run_benchmark_reverse_probs(m, d, p["n_completions"], p["threshold"], p["max_candidates"])),
    ("constrained-reverse", lambda m, d, p: run_benchmark_constrained(m, d, p["n_completions"], p["threshold"], p["max_candidates"])),
]


def run_all(
    models: list[str],
    domains: list[str],
    output_dir: Path,
    params: dict,
    force: bool = False,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    for model_name in models:
        config = get_llm_config(model_name, required=False)
        if config is None:
            env_key = MODELS.get(model_name, {}).get("env_key", "?")
            print(f"\n  Skipping {model_name} — {env_key} not set")
            continue
        model_id = config["litellm_model"]

        for domain in domains:
            existing = list(output_dir.glob(f"{model_name}_{domain}_*.json"))
            if existing and not force:
                print(f"\n  Skipping {model_name}/{domain} — results exist: {existing[0].name}")
                print(f"  Use --force to re-run")
                saved.append(existing[0])
                continue

            print(f"\n{'=' * 80}")
            print(f"  Running all strategies: {model_name} / {domain}")
            print(f"{'=' * 80}")

            strategy_results = []
            for key, runner in STRATEGIES:
                print(f"\n{'─' * 60}")
                print(f"  Strategy: {key}")
                print(f"{'─' * 60}")
                try:
                    result = runner(model_name, domain, params)
                    result["strategy_key"] = key
                    strategy_results.append(result)
                except Exception as e:
                    print(f"  ERROR: {key} failed: {e}")

            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            out_file = output_dir / f"{model_name}_{domain}_{ts}.json"
            data = {
                "meta": {
                    "model": model_name,
                    "model_id": model_id,
                    "domain": domain,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "params": params,
                },
                "strategies": strategy_results,
            }
            out_file.write_text(json.dumps(data, indent=2))
            saved.append(out_file)
            print(f"\n  Saved: {out_file}")

    return saved


def main():
    parser = argparse.ArgumentParser(description="Run all benchmark strategies and save results as JSON")
    parser.add_argument("--models", nargs="*", default=list(MODELS.keys()),
                        help=f"Models to benchmark (default: all). Options: {', '.join(MODELS.keys())}")
    parser.add_argument("--domains", nargs="*", default=["k8s", "ansible", "github", "cicd"],
                        help="Tool domains (default: k8s ansible github cicd)")
    parser.add_argument("--output-dir", type=Path, default=Path("benchmarks/results"),
                        help="Output directory for JSON results (default: benchmarks/results)")
    parser.add_argument("--force", action="store_true",
                        help="Re-run even if results already exist")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--narrow-k", type=int, default=10)
    parser.add_argument("--threshold", type=float, default=0.15)
    parser.add_argument("--max-candidates", type=int, default=5)
    parser.add_argument("--n-completions", type=int, default=5)
    args = parser.parse_args()

    params = {
        "top_k": args.top_k,
        "narrow_k": args.narrow_k,
        "threshold": args.threshold,
        "max_candidates": args.max_candidates,
        "n_completions": args.n_completions,
    }

    saved = run_all(args.models, args.domains, args.output_dir, params, args.force)
    print(f"\n{'=' * 80}")
    print(f"  Done. {len(saved)} result file(s):")
    for p in saved:
        print(f"    {p}")
    print(f"\n  Generate report: uv run python -m benchmarks.generate_report --open")


if __name__ == "__main__":
    main()
