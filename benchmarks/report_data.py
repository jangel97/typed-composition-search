import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DOMAIN_REGISTRIES = {}

STRATEGY_ORDER = [
    "oracle-graph", "model-types",
    "baseline", "retrieval", "graph", "graph-narrowed",
    "graph-probs", "graph-reverse", "graph-reverse-probs", "constrained-reverse",
]

CORE_METRICS = [
    ("Precision",       "precision",            ".2f",  False),
    ("Recall",          "recall",               ".2f",  False),
    ("F1",              "f1",                   ".2f",  False),
    ("Exact Match",     "_exact_match",         ".0%",  False),
    ("Hallucinated",    "hallucinated",         ".0f",  True),
    ("Pruning",         "pruning",              ".0%",  False),
    ("Avg Tools",       "avg_tools",            ".1f",  True),
    ("Path Found",      "path_found_pct",       ".0%",  False),
    ("Source Acc",      "source_accuracy",      ".0%",  False),
    ("Target Acc",      "target_accuracy",      ".0%",  False),
    ("Type Exact",      "exact_match_accuracy", ".0%",  False),
    ("Type Recall@k",   "type_recall_at_k",     ".2f",  False),
    ("Retrieval R@k",   "retrieval_recall_at_k",".2f",  False),
]

LATENCY_METRICS = [
    ("Avg (ms)",        "latency_avg",          ".0f",  True),
    ("P50 (ms)",        "latency_p50",          ".0f",  True),
    ("P95 (ms)",        "latency_p95",          ".0f",  True),
    ("Avg Prompt Tok",  "avg_prompt_tokens",    ".0f",  True),
    ("Avg Compl Tok",   "avg_completion_tokens", ".0f", True),
]

_EXCLUDE_FROM_BEST = {"baseline", "retrieval", "oracle-graph", "model-types"}


def _get_graph_metrics(domain: str) -> dict | None:
    if domain in DOMAIN_REGISTRIES:
        return DOMAIN_REGISTRIES[domain]
    try:
        import importlib
        reg_mod = importlib.import_module(f"benchmarks.{domain}.registry")
        reg = reg_mod.build_registry()
        metrics = reg._graph.metrics()
        metrics["tool_count"] = len(reg._tools)
        DOMAIN_REGISTRIES[domain] = metrics
        return metrics
    except Exception:
        return None


def _strategy_key(s: dict) -> str:
    return s.get("strategy_key", s.get("strategy", ""))


def get_metric(strategy: dict, key: str):
    if key == "_exact_match":
        n = strategy.get("exact_match_n")
        if n and n > 0:
            return strategy["exact_match"] / n
        return None
    val = strategy.get(key)
    if val is None or (isinstance(val, (int, float)) and val < 0):
        return None
    return val


def find_best(values: list, lower_is_better: bool = False) -> set[int]:
    valid = [(i, v) for i, v in enumerate(values) if v is not None]
    if not valid:
        return set()
    if lower_is_better:
        best_val = min(v for _, v in valid)
    else:
        best_val = max(v for _, v in valid)
    winners = {i for i, v in valid if v == best_val}
    if len(winners) == len(valid):
        return set()
    return winners


def order_strategies(strategies: list[dict]) -> list[dict]:
    by_key = {}
    for s in strategies:
        by_key[_strategy_key(s)] = s
    ordered = []
    for key in STRATEGY_ORDER:
        if key in by_key:
            ordered.append(by_key[key])
    for s in strategies:
        if _strategy_key(s) not in STRATEGY_ORDER:
            ordered.append(s)
    return ordered


def load_results(paths: list[Path]) -> dict:
    data = {}
    for p in paths:
        with open(p) as f:
            raw = json.load(f)
        domain = raw["meta"]["domain"]
        model = raw["meta"]["model"]
        if domain not in data:
            data[domain] = {}
        data[domain][model] = raw
    return data


# --- Preprocessing functions ---

def preprocess_aggregate(data: dict) -> list[dict]:
    rows = []
    for domain in sorted(data.keys()):
        for model in sorted(data[domain].keys()):
            strats = data[domain][model]["strategies"]
            by_key = {_strategy_key(s): s for s in strats}

            bl = by_key.get("baseline", {})
            bl_f1 = bl.get("f1", 0)
            bl_hall = bl.get("hallucinated", 0)
            bl_tok = bl.get("avg_prompt_tokens", 0)
            bl_prec = bl.get("precision", 0)
            bl_rec = bl.get("recall", 0)

            graph_strats = [(k, s) for k, s in by_key.items() if k not in _EXCLUDE_FROM_BEST]
            if not graph_strats:
                continue
            best_key, best = max(graph_strats, key=lambda x: x[1].get("f1", 0))

            best_f1 = best.get("f1", 0)
            best_hall = best.get("hallucinated", 0)
            best_tok = best.get("avg_prompt_tokens", 0)
            best_prec = best.get("precision", 0)
            best_rec = best.get("recall", 0)

            rows.append({
                "domain": domain,
                "model": model,
                "best_key": best_key,
                "best_prec": best_prec,
                "prec_delta": best_prec - bl_prec,
                "best_rec": best_rec,
                "rec_delta": best_rec - bl_rec,
                "best_f1": best_f1,
                "f1_delta": best_f1 - bl_f1,
                "bl_hall": bl_hall,
                "best_hall": best_hall,
                "tok_save_pct": (1 - best_tok / bl_tok) * 100 if bl_tok > 0 else 0,
            })
    return rows


def preprocess_graph_structure(domains: list[str]) -> dict | None:
    all_metrics = {}
    for d in domains:
        m = _get_graph_metrics(d)
        if m:
            all_metrics[d] = m
    if not all_metrics:
        return None

    rows_spec = [
        ("Tools",                   lambda m: m.get("tool_count")),
        ("Types (nodes)",           lambda m: m["structural"]["node_count"]),
        ("Edges",                   lambda m: m["structural"]["edge_count"]),
        ("Components",              lambda m: m["structural"]["connected_components"]),
        ("Diameter",                lambda m: m["reachability"]["diameter"]),
        ("Avg Path Length",         lambda m: m["reachability"]["avg_shortest_path_length"]),
        ("Reachability",            lambda m: m["reachability"]["reachable_pairs_pct"]),
        ("Avg Branching Factor",    lambda m: m["search_space"]["avg_branching_factor"]),
        ("Max Branching Factor",    lambda m: m["search_space"]["max_branching_factor"]),
        ("Avg In-Degree",           lambda m: m["structural"]["avg_in_degree"]),
        ("Avg Out-Degree",          lambda m: m["structural"]["avg_out_degree"]),
        ("Max In-Degree",           lambda m: m["structural"]["max_in_degree"]),
        ("Max Out-Degree",          lambda m: m["structural"]["max_out_degree"]),
        ("Avg Reachable Targets",   lambda m: m["reachability"]["avg_reachable_targets_per_source"]),
        ("Avg Reachable Sources",   lambda m: m["reachability"]["avg_reachable_sources_per_target"]),
    ]

    available_domains = [d for d in domains if d in all_metrics]
    rows = []
    for label, getter in rows_spec:
        cells = []
        for d in available_domains:
            val = getter(all_metrics[d])
            cells.append(val)
        rows.append({"label": label, "values": cells})

    betweenness = []
    for d in available_domains:
        top = all_metrics[d]["centrality"]["top_betweenness"][:3]
        items = ", ".join(f"{e['type']} ({e['score']:.0f})" for e in top)
        betweenness.append({"domain": d, "items": items})

    return {
        "domains": available_domains,
        "rows": rows,
        "betweenness": betweenness,
    }


def preprocess_summary(strategies: list[dict]) -> dict | None:
    strategies = order_strategies(strategies)
    by_key = {_strategy_key(s): s for s in strategies}
    bl = by_key.get("baseline")
    if not bl:
        return None

    bl_f1 = bl.get("f1", 0)
    bl_hall = bl.get("hallucinated", 0)
    bl_tok = bl.get("avg_prompt_tokens", 0)

    graph_strats = [(k, s) for k, s in by_key.items() if k not in _EXCLUDE_FROM_BEST]
    if not graph_strats:
        return None

    best_key, best = max(graph_strats, key=lambda x: x[1].get("f1", 0))
    best_f1 = best.get("f1", 0)
    best_hall = best.get("hallucinated", 0)
    best_tok = best.get("avg_prompt_tokens", 0)

    f1_delta = best_f1 - bl_f1
    tok_pct = (1 - best_tok / bl_tok) * 100 if bl_tok > 0 else 0

    return {
        "best_key": best_key,
        "best_f1": best_f1,
        "bl_f1": bl_f1,
        "f1_delta": f1_delta,
        "best_hall": best_hall,
        "bl_hall": bl_hall,
        "tok_pct": tok_pct,
        "bl_tok": bl_tok,
        "best_tok": best_tok,
    }


def preprocess_decomposition(strategies: list[dict]) -> dict | None:
    strategies = order_strategies(strategies)
    by_key = {_strategy_key(s): s for s in strategies}

    oracle = by_key.get("oracle-graph")
    model_types = by_key.get("model-types")
    graph = by_key.get("graph")

    if not oracle or not model_types:
        return None

    oracle_recall = oracle.get("recall")
    oracle_path_pct = oracle.get("path_found_pct")
    type_exact = model_types.get("exact_match_accuracy")
    source_acc = model_types.get("source_accuracy")
    target_acc = model_types.get("target_accuracy")

    if oracle_recall is None or type_exact is None:
        return None

    predicted_recall = type_exact * oracle_recall
    e2e_recall = graph.get("recall") if graph else None

    recall_wrong = None
    n_wrong = 0
    if graph:
        pq = graph.get("per_query", [])
        wrong_recalls = []
        for q in pq:
            ps = q.get("predicted_source", "?")
            pt = q.get("predicted_target", "?")
            es = q.get("expected_source", "?")
            et = q.get("expected_target", "?")
            if ps != es or pt != et:
                rec = q.get("recall", -1)
                if rec >= 0:
                    wrong_recalls.append(rec)
        if wrong_recalls:
            recall_wrong = sum(wrong_recalls) / len(wrong_recalls)
            n_wrong = len(wrong_recalls)

    predicted_recall_full = None
    if recall_wrong is not None:
        predicted_recall_full = type_exact * oracle_recall + (1 - type_exact) * recall_wrong

    predicted = predicted_recall_full if predicted_recall_full is not None else predicted_recall
    gap = (e2e_recall - predicted) if e2e_recall is not None else None

    return {
        "oracle_recall": oracle_recall,
        "oracle_path_pct": oracle_path_pct,
        "type_exact": type_exact,
        "source_acc": source_acc,
        "target_acc": target_acc,
        "predicted_recall": predicted_recall,
        "predicted_recall_full": predicted_recall_full,
        "e2e_recall": e2e_recall,
        "recall_wrong": recall_wrong,
        "n_wrong": n_wrong,
        "gap": gap,
    }


def preprocess_metrics_table(strategies: list[dict], metrics_spec: list[tuple]) -> dict | None:
    strategies = order_strategies(strategies)
    names = [_strategy_key(s) for s in strategies]

    rows = []
    for label, key, fmt_str, lower_is_better in metrics_spec:
        values = [get_metric(s, key) for s in strategies]
        if all(v is None for v in values):
            continue
        best = find_best(values, lower_is_better)
        rows.append({
            "label": label,
            "values": values,
            "fmt_str": fmt_str,
            "best_indices": best,
        })

    if not rows:
        return None
    return {"headers": names, "rows": rows}


def preprocess_category_table(strategies: list[dict]) -> dict | None:
    strategies = order_strategies(strategies)
    names = [_strategy_key(s) for s in strategies]

    all_cats = sorted({cat for s in strategies for cat in s.get("category_f1", {})})
    if not all_cats:
        return None

    categories = []
    for cat in all_cats:
        values = [s.get("category_f1", {}).get(cat) for s in strategies]
        best = find_best([v for v in values], lower_is_better=False)
        categories.append({
            "name": cat,
            "values": values,
            "best_indices": best,
        })

    return {"headers": names, "categories": categories}


def preprocess_per_query(strategies: list[dict], model: str) -> list[dict] | None:
    strategies = order_strategies(strategies)
    has_types = any("per_query" in s and s["per_query"] and "predicted_source" in s["per_query"][0]
                     for s in strategies)
    has_graph = any("per_query" in s and s["per_query"] and "path_length" in s["per_query"][0]
                     for s in strategies)

    sections = []
    for s in strategies:
        pq = s.get("per_query", [])
        if not pq:
            continue
        key = _strategy_key(s)
        show_types = has_types and "predicted_source" in pq[0]
        show_graph = has_graph and "path_length" in pq[0]

        queries = []
        for q in pq:
            row = {
                "id": q["id"],
                "category": q.get("category", ""),
                "f1": q.get("f1", -1),
                "recall": q.get("recall", -1),
                "precision": q.get("precision", -1),
                "expected_tools": ", ".join(q.get("expected_tools", [])),
                "resolved_tools": ", ".join(q.get("resolved_tools", [])),
            }
            if show_types:
                exp_st = f"{q.get('expected_source','?')}→{q.get('expected_target','?')}"
                pred_st = f"{q.get('predicted_source','?')}→{q.get('predicted_target','?')}"
                row["expected_st"] = exp_st
                row["predicted_st"] = pred_st
                row["type_match"] = exp_st == pred_st
            if show_graph:
                row["path_length"] = q.get("path_length")
                row["source_out_degree"] = q.get("source_out_degree", 0)
                row["source_reachable"] = q.get("source_reachable", 0)
            queries.append(row)

        table_id = f"pq-{model}-{key}".replace(" ", "-")
        sections.append({
            "key": key,
            "table_id": table_id,
            "n_queries": len(pq),
            "show_types": show_types,
            "show_graph": show_graph,
            "queries": queries,
        })

    return sections if sections else None


def preprocess_cross_model(domain: str, model_results: dict) -> dict | None:
    if len(model_results) < 2:
        return None

    models = sorted(model_results.keys())
    all_keys = set()
    for model in models:
        for s in model_results[model]["strategies"]:
            all_keys.add(_strategy_key(s))

    ordered_keys = [k for k in STRATEGY_ORDER if k in all_keys]
    for k in sorted(all_keys):
        if k not in ordered_keys:
            ordered_keys.append(k)

    rows = []
    for key in ordered_keys:
        values = []
        for model in models:
            strats = model_results[model]["strategies"]
            match = next((s for s in strats if _strategy_key(s) == key), None)
            values.append(match.get("f1") if match else None)
        best = find_best(values)
        rows.append({"key": key, "values": values, "best_indices": best})

    return {"models": models, "rows": rows}


def preprocess_recall_precision(domain: str, model_results: dict) -> list[dict]:
    models = sorted(model_results.keys())

    all_keys = set()
    for model in models:
        for s in model_results[model]["strategies"]:
            all_keys.add(_strategy_key(s))
    ordered_keys = [k for k in STRATEGY_ORDER if k in all_keys and k != "baseline"]

    sections = []
    for model in models:
        strats = model_results[model]["strategies"]
        by_key = {_strategy_key(s): s for s in strats}
        bl = by_key.get("baseline")
        bl_r = bl.get("recall") if bl else None
        bl_p = bl.get("precision") if bl else None

        rows = []
        if bl:
            rows.append({"key": "baseline", "recall": bl_r, "precision": bl_p,
                         "is_baseline": True})
        for key in ordered_keys:
            s = by_key.get(key)
            if not s:
                rows.append({"key": key, "recall": None, "precision": None})
            else:
                r = s.get("recall")
                p = s.get("precision")
                rows.append({
                    "key": key,
                    "recall": r,
                    "precision": p,
                    "r_delta": (r - bl_r) if r is not None and bl_r is not None else None,
                    "p_delta": (p - bl_p) if p is not None and bl_p is not None else None,
                })

        sections.append({"model": model, "rows": rows})
    return sections


def preprocess_graph_eda(domain: str, model_results: dict) -> dict | None:
    all_pq = []
    for model in sorted(model_results.keys()):
        for s in model_results[model]["strategies"]:
            key = _strategy_key(s)
            if key in ("baseline", "retrieval", "oracle-graph", "model-types"):
                continue
            for q in s.get("per_query", []):
                if "path_length" in q and q.get("f1", -1) >= 0:
                    all_pq.append({**q, "model": model, "strategy": key})

    if not all_pq:
        return None

    by_path_len = defaultdict(list)
    by_out_degree = defaultdict(list)
    by_reachable = defaultdict(list)

    for q in all_pq:
        pl = q.get("path_length")
        if pl is not None:
            by_path_len[pl].append(q["f1"])

        so = q.get("source_out_degree", 0)
        if so <= 2:
            bucket = "1-2"
        elif so <= 5:
            bucket = "3-5"
        elif so <= 10:
            bucket = "6-10"
        else:
            bucket = "11+"
        by_out_degree[bucket].append(q["f1"])

        sr = q.get("source_reachable", 0)
        if sr <= 3:
            rb = "1-3"
        elif sr <= 10:
            rb = "4-10"
        elif sr <= 20:
            rb = "11-20"
        else:
            rb = "21+"
        by_reachable[rb].append(q["f1"])

    def _bucket_table(data, key_order=None):
        keys = key_order or sorted(data.keys())
        keys = [k for k in keys if k in data]
        rows = []
        for k in keys:
            vals = data[k]
            n = len(vals)
            avg_f1 = sum(vals) / n
            rows.append({"key": k, "n": n, "avg_f1": avg_f1})
        return rows

    return {
        "path_length": _bucket_table(by_path_len),
        "out_degree": _bucket_table(by_out_degree, ["1-2", "3-5", "6-10", "11+"]),
        "reachable": _bucket_table(by_reachable, ["1-3", "4-10", "11-20", "21+"]),
    }


def preprocess_failure_analysis(domain: str, model_results: dict) -> dict | None:
    models = sorted(model_results.keys())
    all_query_ids = set()
    for model in models:
        for s in model_results[model]["strategies"]:
            for q in s.get("per_query", []):
                all_query_ids.add(q["id"])

    if not all_query_ids:
        return None

    universal_failures = []
    graph_regressions = []

    for qid in sorted(all_query_ids):
        all_fail = True
        baseline_ok = False
        graph_fail = False

        for model in models:
            for s in model_results[model]["strategies"]:
                key = _strategy_key(s)
                for q in s.get("per_query", []):
                    if q["id"] != qid:
                        continue
                    rec = q.get("recall", -1)
                    if rec > 0:
                        all_fail = False
                    if key == "baseline" and rec > 0:
                        baseline_ok = True
                    if key not in ("baseline", "retrieval", "oracle-graph", "model-types") and rec <= 0:
                        graph_fail = True

        if all_fail:
            universal_failures.append(qid)
        if baseline_ok and graph_fail:
            graph_regressions.append(qid)

    if not universal_failures and not graph_regressions:
        return None

    return {
        "universal_failures": universal_failures,
        "graph_regressions": graph_regressions,
    }


def load_and_preprocess(result_dir: Path) -> dict:
    paths = sorted(result_dir.glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"No JSON files found in {result_dir}")

    print(f"Loading {len(paths)} result file(s)...")
    data = load_results(paths)

    domains = sorted(data.keys())
    all_models = sorted({m for d in data.values() for m in d})
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    domain_data = {}
    for domain in domains:
        model_results = data[domain]
        models_data = {}
        for model in sorted(model_results.keys()):
            meta = model_results[model]["meta"]
            strategies = model_results[model]["strategies"]
            n_queries = strategies[0]["n"] if strategies else "?"

            models_data[model] = {
                "meta": meta,
                "n_queries": n_queries,
                "summary": preprocess_summary(strategies),
                "decomposition": preprocess_decomposition(strategies),
                "core_metrics": preprocess_metrics_table(strategies, CORE_METRICS),
                "latency_metrics": preprocess_metrics_table(strategies, LATENCY_METRICS),
                "category_table": preprocess_category_table(strategies),
                "per_query": preprocess_per_query(strategies, model),
            }

        domain_data[domain] = {
            "models": models_data,
            "cross_model": preprocess_cross_model(domain, model_results),
            "recall_precision": preprocess_recall_precision(domain, model_results),
            "graph_eda": preprocess_graph_eda(domain, model_results),
            "failure_analysis": preprocess_failure_analysis(domain, model_results),
        }

    return {
        "generated_at": now,
        "domains": domains,
        "all_models": all_models,
        "aggregate_rows": preprocess_aggregate(data),
        "graph_structure": preprocess_graph_structure(domains),
        "domain_data": domain_data,
    }
