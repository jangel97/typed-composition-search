import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from benchmarks.llm import MODELS, get_llm_config
from benchmarks.run_benchmark import run_benchmark
from benchmarks.run_baseline import run_baseline
from benchmarks.run_retrieval import run_retrieval
from benchmarks.run_benchmark_reverse_probs import run_benchmark_reverse_probs
from benchmarks.run_oracle_graph import run_oracle_graph
from benchmarks.run_model_types import run_model_types
from benchmarks.run_baseline_tools import run_baseline_tools

STRATEGIES = [
    ("graph-perfect",        lambda m, d, p: run_oracle_graph(d)),
    ("model-types",         lambda m, d, p: run_model_types(m, d)),
    ("baseline",            lambda m, d, p: run_baseline(m, d)),
    ("baseline-tools",      lambda m, d, p: run_baseline_tools(m, d)),
    ("retrieval",           lambda m, d, p: run_retrieval(m, p["top_k"], d)),
    ("graph",               lambda m, d, p: run_benchmark(m, d)),
    ("graph-reverse-probs", lambda m, d, p: run_benchmark_reverse_probs(m, d, p["n_completions"], p["threshold"], p["max_candidates"])),
]


def _run_combo(model_name, model_id, domain, output_dir, params, parallel):
    strategy_results = []
    if parallel <= 1:
        for key, runner in STRATEGIES:
            print(f"\n  [{model_name}/{domain}] Strategy: {key}")
            try:
                result = runner(model_name, domain, params)
                result["strategy_key"] = key
                strategy_results.append(result)
            except Exception as e:
                print(f"  [{model_name}/{domain}] ERROR: {key} failed: {e}")
    else:
        print(f"\n  [{model_name}/{domain}] Running {len(STRATEGIES)} strategies with parallelism={parallel}")
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            futures = {}
            for key, runner in STRATEGIES:
                futures[pool.submit(runner, model_name, domain, params)] = key
            for future in as_completed(futures):
                key = futures[future]
                try:
                    result = future.result()
                    result["strategy_key"] = key
                    strategy_results.append(result)
                    print(f"  [{model_name}/{domain}] Completed: {key}")
                except Exception as e:
                    print(f"  [{model_name}/{domain}] ERROR: {key} failed: {e}")
        order = {k: i for i, (k, _) in enumerate(STRATEGIES)}
        strategy_results.sort(key=lambda r: order.get(r["strategy_key"], 999))

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
    print(f"\n  [{model_name}/{domain}] Saved: {out_file}")
    return out_file


def run_all(
    models: list[str],
    domains: list[str],
    output_dir: Path,
    params: dict,
    force: bool = False,
    parallel: int = 1,
    parallel_combos: int = 1,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    combos = []
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
                saved.append(existing[0])
                continue
            combos.append((model_name, model_id, domain))

    if not combos:
        return saved

    print(f"\n  {len(combos)} combo(s) to run: {', '.join(f'{m}/{d}' for m, _, d in combos)}")

    if parallel_combos <= 1:
        for model_name, model_id, domain in combos:
            out_file = _run_combo(model_name, model_id, domain, output_dir, params, parallel)
            saved.append(out_file)
    else:
        print(f"  Running {len(combos)} combos with parallelism={parallel_combos}")
        with ThreadPoolExecutor(max_workers=parallel_combos) as pool:
            futures = {
                pool.submit(_run_combo, m, mid, d, output_dir, params, parallel): (m, d)
                for m, mid, d in combos
            }
            for future in as_completed(futures):
                m, d = futures[future]
                try:
                    saved.append(future.result())
                except Exception as e:
                    print(f"  ERROR: {m}/{d} failed: {e}")

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
    parser.add_argument("--parallel", type=int, default=1,
                        help="Number of strategies to run in parallel per combo (default: 1)")
    parser.add_argument("--parallel-combos", type=int, default=1,
                        help="Number of model/domain combos to run in parallel (default: 1)")
    args = parser.parse_args()

    params = {
        "top_k": args.top_k,
        "narrow_k": args.narrow_k,
        "threshold": args.threshold,
        "max_candidates": args.max_candidates,
        "n_completions": args.n_completions,
    }

    saved = run_all(args.models, args.domains, args.output_dir, params, args.force, args.parallel, args.parallel_combos)
    print(f"\n{'=' * 80}")
    print(f"  Done. {len(saved)} result file(s):")
    for p in saved:
        print(f"    {p}")
    print(f"\n  Generate report: uv run python -m benchmarks.generate_report --open")


if __name__ == "__main__":
    main()
