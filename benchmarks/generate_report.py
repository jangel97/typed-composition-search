import argparse
import json
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

DOMAIN_REGISTRIES = {}

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


def fmt_val(val, fmt_str: str = ".2f") -> str:
    if val is None:
        return "&mdash;"
    return f"{val:{fmt_str}}"


def f1_to_color(val) -> str:
    if val is None or val < 0:
        return "transparent"
    hue = int(val * 120)
    return f"hsla({hue}, 70%, 40%, 0.3)"


def order_strategies(strategies: list[dict]) -> list[dict]:
    by_key = {}
    for s in strategies:
        key = s.get("strategy_key", s.get("strategy", ""))
        by_key[key] = s
    ordered = []
    for key in STRATEGY_ORDER:
        if key in by_key:
            ordered.append(by_key[key])
    for s in strategies:
        key = s.get("strategy_key", s.get("strategy", ""))
        if key not in STRATEGY_ORDER:
            ordered.append(s)
    return ordered


def render_metrics_table(strategies: list[dict], metrics: list[tuple], title: str) -> str:
    strategies = order_strategies(strategies)
    names = [s.get("strategy_key", s.get("strategy", "?")) for s in strategies]

    rows_html = []
    for label, key, fmt_str, lower_is_better in metrics:
        values = [get_metric(s, key) for s in strategies]
        if all(v is None for v in values):
            continue
        best = find_best(values, lower_is_better)
        cells = ""
        for i, v in enumerate(values):
            cls = "val best" if i in best else "val"
            if v is None:
                cells += f'<td class="{cls} na">&mdash;</td>'
            else:
                cells += f'<td class="{cls}">{fmt_val(v, fmt_str)}</td>'
        rows_html.append(f"<tr><td class='label'>{label}</td>{cells}</tr>")

    if not rows_html:
        return ""

    header_cells = "".join(f"<th class='strategy'>{n}</th>" for n in names)
    return f"""
    <div class="card">
      <h3>{title}</h3>
      <table>
        <tr><th>Metric</th>{header_cells}</tr>
        {"".join(rows_html)}
      </table>
    </div>"""


def render_category_table(strategies: list[dict]) -> str:
    strategies = order_strategies(strategies)
    names = [s.get("strategy_key", s.get("strategy", "?")) for s in strategies]

    all_cats = sorted({cat for s in strategies for cat in s.get("category_f1", {})})
    if not all_cats:
        return ""

    header_cells = "".join(f"<th class='strategy'>{n}</th>" for n in names)
    rows = []
    for cat in all_cats:
        values = [s.get("category_f1", {}).get(cat) for s in strategies]
        best = find_best([v for v in values], lower_is_better=False)
        cells = ""
        for i, v in enumerate(values):
            if v is None or v < 0:
                cells += "<td class='val na'>&mdash;</td>"
            else:
                bg = f1_to_color(v)
                cls = "val best" if i in best else "val"
                cells += f"<td class='{cls} heat' style='background:{bg}'>{v:.2f}</td>"
        rows.append(f"<tr><td class='label'>{cat}</td>{cells}</tr>")

    return f"""
    <div class="card">
      <h3>F1 by Category</h3>
      <table>
        <tr><th>Category</th>{header_cells}</tr>
        {"".join(rows)}
      </table>
    </div>"""


def render_cross_model_table(domain: str, model_results: dict) -> str:
    if len(model_results) < 2:
        return ""

    models = sorted(model_results.keys())
    all_keys = set()
    for model in models:
        for s in model_results[model]["strategies"]:
            all_keys.add(s.get("strategy_key", s.get("strategy", "")))

    ordered_keys = [k for k in STRATEGY_ORDER if k in all_keys]
    for k in sorted(all_keys):
        if k not in ordered_keys:
            ordered_keys.append(k)

    header_cells = "".join(f"<th class='strategy'>{m}</th>" for m in models)
    rows = []
    for key in ordered_keys:
        values = []
        for model in models:
            strats = model_results[model]["strategies"]
            match = next((s for s in strats if s.get("strategy_key", s.get("strategy", "")) == key), None)
            values.append(match.get("f1") if match else None)
        best = find_best(values)
        cells = ""
        for i, v in enumerate(values):
            cls = "val best" if i in best else "val"
            if v is None:
                cells += f"<td class='{cls} na'>&mdash;</td>"
            else:
                cells += f"<td class='{cls}'>{v:.2f}</td>"
        rows.append(f"<tr><td class='label'>{key}</td>{cells}</tr>")

    return f"""
    <div class="card">
      <h3>Cross-Model Comparison (F1)</h3>
      <table>
        <tr><th>Strategy</th>{header_cells}</tr>
        {"".join(rows)}
      </table>
    </div>"""


def render_summary_card(strategies: list[dict]) -> str:
    strategies = order_strategies(strategies)
    by_key = {s.get("strategy_key", s.get("strategy", "")): s for s in strategies}
    bl = by_key.get("baseline")
    if not bl:
        return ""

    bl_f1 = bl.get("f1", 0)
    bl_hall = bl.get("hallucinated", 0)
    bl_tok = bl.get("avg_prompt_tokens", 0)

    _exclude = {"baseline", "retrieval", "oracle-graph", "model-types"}
    graph_strats = [(k, s) for k, s in by_key.items() if k not in _exclude]
    if not graph_strats:
        return ""

    best_key, best = max(graph_strats, key=lambda x: x[1].get("f1", 0))
    best_f1 = best.get("f1", 0)
    best_hall = best.get("hallucinated", 0)
    best_tok = best.get("avg_prompt_tokens", 0)

    f1_delta = best_f1 - bl_f1
    f1_sign = "+" if f1_delta >= 0 else ""
    f1_cls = "pos" if f1_delta >= 0 else "neg"

    hall_delta = bl_hall - best_hall
    tok_pct = (1 - best_tok / bl_tok) * 100 if bl_tok > 0 else 0

    items = []
    items.append(f"""
      <div class="summary-item">
        <div class="summary-value {f1_cls}">{f1_sign}{f1_delta:.2f}</div>
        <div class="summary-label">F1 improvement</div>
        <div class="summary-detail">{bl_f1:.2f} &rarr; {best_f1:.2f}</div>
      </div>""")
    items.append(f"""
      <div class="summary-item">
        <div class="summary-value pos">{best_hall}</div>
        <div class="summary-label">Hallucinations</div>
        <div class="summary-detail">baseline: {bl_hall}</div>
      </div>""")
    items.append(f"""
      <div class="summary-item">
        <div class="summary-value {'pos' if tok_pct > 0 else 'neg'}">{tok_pct:.0f}%</div>
        <div class="summary-label">Token savings</div>
        <div class="summary-detail">{bl_tok:.0f} &rarr; {best_tok:.0f} avg</div>
      </div>""")

    return f"""
    <div class="card summary-card">
      <h3>Best Graph Strategy vs Baseline</h3>
      <div class="summary-subtitle">Winner: <strong>{best_key}</strong> (F1 = {best_f1:.2f})</div>
      <div class="summary-grid">{"".join(items)}</div>
    </div>"""


def render_decomposition_card(strategies: list[dict], model: str = "") -> str:
    strategies = order_strategies(strategies)
    by_key = {s.get("strategy_key", s.get("strategy", "")): s for s in strategies}

    oracle = by_key.get("oracle-graph")
    model_types = by_key.get("model-types")
    graph = by_key.get("graph")

    if not oracle or not model_types:
        return ""

    oracle_recall = oracle.get("recall")
    oracle_path_pct = oracle.get("path_found_pct")
    type_exact = model_types.get("exact_match_accuracy")
    source_acc = model_types.get("source_accuracy")
    target_acc = model_types.get("target_accuracy")

    if oracle_recall is None or type_exact is None:
        return ""

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

    type_item = f"""
      <div class="summary-item" style="grid-column: 1 / -1; max-width: 240px;">
        <div class="summary-value" style="color:#6366f1">{type_exact:.0%}</div>
        <div class="summary-label">Type Exact Match</div>
        <div class="summary-detail">src={source_acc:.0%} &nbsp; tgt={target_acc:.0%} &nbsp; path found={oracle_path_pct:.0%}</div>
      </div>"""

    recall_eq = f"Recall_e2e = TypeAccuracy &times; Recall_oracle + (1 - TypeAccuracy) &times; Recall_wrong"
    recall_cells = []

    oracle_cls = "pos" if oracle_recall >= 0.95 else ("neg" if oracle_recall < 0.8 else "")
    recall_cells.append(f"""
      <div class="summary-item">
        <div class="summary-value {oracle_cls}">{oracle_recall:.2f}</div>
        <div class="summary-label">Oracle Recall</div>
      </div>""")

    if recall_wrong is not None:
        rw_cls = "pos" if recall_wrong < 0.05 else "neg"
        recall_cells.append(f"""
      <div class="summary-item">
        <div class="summary-value {rw_cls}">{recall_wrong:.2f}</div>
        <div class="summary-label">Recall_wrong</div>
        <div class="summary-detail">n={n_wrong} queries</div>
      </div>""")

    if predicted_recall_full is not None:
        recall_cells.append(f"""
      <div class="summary-item">
        <div class="summary-value" style="color:#f59e0b">{predicted_recall_full:.2f}</div>
        <div class="summary-label">Predicted Recall</div>
        <div class="summary-detail">full equation</div>
      </div>""")
    else:
        recall_cells.append(f"""
      <div class="summary-item">
        <div class="summary-value" style="color:#f59e0b">{predicted_recall:.2f}</div>
        <div class="summary-label">Predicted Recall</div>
        <div class="summary-detail">assumes Recall_wrong&asymp;0</div>
      </div>""")

    if e2e_recall is not None:
        predicted = predicted_recall_full if predicted_recall_full is not None else predicted_recall
        gap = e2e_recall - predicted
        gap_cls = "pos" if abs(gap) < 0.05 else "neg"
        recall_cells.append(f"""
      <div class="summary-item">
        <div class="summary-value {gap_cls}">{e2e_recall:.2f}</div>
        <div class="summary-label">Actual E2E Recall</div>
        <div class="summary-detail">gap: {gap:+.2f}</div>
      </div>""")

    explanation = """
      <div style="font-size:12px; color:#9ca3af; line-height:1.6; margin-bottom:16px; padding:12px; background:#0f1117; border-radius:6px;">
        <p style="margin:0 0 8px 0;">
          The system has two stages: <strong style="color:#e0e0e0;">entity classification</strong> (LLM predicts source &amp; target types)
          and <strong style="color:#e0e0e0;">graph planning</strong> (BFS finds a tool path).
          Since wrong types almost always produce wrong tools (Recall_wrong &asymp; 0):
        </p>
        <p style="margin:0 0 12px 0; font-family:monospace; font-size:14px; color:#f59e0b;">
          Recall_e2e &asymp; TypeAccuracy &times; Recall_oracle
        </p>
        <p style="margin:0 0 4px 0;">
          <strong style="color:#e0e0e0;">Recall_oracle</strong> &mdash; recall when ground-truth types are given (graph quality, no LLM).
        </p>
        <p style="margin:0 0 4px 0;">
          <strong style="color:#e0e0e0;">Recall_wrong</strong> &mdash; recall when types were predicted incorrectly. Validates the &asymp; 0 assumption.
        </p>
        <p style="margin:0 0 4px 0;">
          <strong style="color:#e0e0e0;">Gap</strong> &mdash; difference between predicted and actual. Small gap = decomposition holds.
        </p>
        <p style="margin:8px 0 0 0;">
          <em>Precision and F1 do not decompose this way &mdash; when no path is found, the query is excluded
          from precision (changes the denominator). Oracle values shown as reference only.</em>
        </p>
      </div>"""

    return f"""
    <div class="card" style="border-left: 3px solid #f59e0b;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h3 style="margin-bottom:0;">Recall Decomposition</h3>
        <span style="font-size:12px; color:#6366f1; font-weight:600;">{model}</span>
      </div>
      {explanation}
      <div style="text-align:center; margin-bottom:16px;">{type_item}</div>
      <div style="margin-bottom:16px;">
        <div class="summary-grid">{"".join(recall_cells)}</div>
      </div>
    </div>"""


def _delta_cell(val, baseline_val) -> str:
    if val is None or baseline_val is None:
        return "<td class='val na'>&mdash;</td>"
    delta = val - baseline_val
    if delta > 0.005:
        cls = "val delta-pos"
        sign = "+"
    elif delta < -0.005:
        cls = "val delta-neg"
        sign = ""
    else:
        cls = "val"
        sign = ""
    return f"<td class='{cls}'>{val:.2f} <span class='delta'>({sign}{delta:.2f})</span></td>"


def render_recall_precision_vs_baseline(domain: str, model_results: dict) -> str:
    models = sorted(model_results.keys())

    all_keys = set()
    for model in models:
        for s in model_results[model]["strategies"]:
            all_keys.add(s.get("strategy_key", s.get("strategy", "")))
    ordered_keys = [k for k in STRATEGY_ORDER if k in all_keys and k != "baseline"]

    sections = []
    for model in models:
        strats = model_results[model]["strategies"]
        by_key = {s.get("strategy_key", s.get("strategy", "")): s for s in strats}
        bl = by_key.get("baseline")
        bl_r = bl.get("recall") if bl else None
        bl_p = bl.get("precision") if bl else None

        header = "<tr><th>Strategy</th><th class='strategy'>Recall</th><th class='strategy'>Precision</th></tr>"
        rows = []
        if bl:
            rows.append(f"<tr class='baseline-row'><td class='label'>baseline</td>"
                        f"<td class='val'>{bl_r:.2f}</td>"
                        f"<td class='val'>{bl_p:.2f}</td></tr>")
        for key in ordered_keys:
            s = by_key.get(key)
            if not s:
                rows.append(f"<tr><td class='label'>{key}</td>"
                            f"<td class='val na'>&mdash;</td>"
                            f"<td class='val na'>&mdash;</td></tr>")
                continue
            r_cell = _delta_cell(s.get("recall"), bl_r)
            p_cell = _delta_cell(s.get("precision"), bl_p)
            rows.append(f"<tr><td class='label'>{key}</td>{r_cell}{p_cell}</tr>")

        sections.append(f"""
        <div class="recall-model">
          <h4>{model}</h4>
          <table>{header}{"".join(rows)}</table>
        </div>""")

    return f"""
    <div class="card">
      <h3>Recall &amp; Precision vs Baseline</h3>
      <div class="recall-grid">{"".join(sections)}</div>
    </div>"""


def render_per_query_table(strategies: list[dict], model: str) -> str:
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
        key = s.get("strategy_key", s.get("strategy", "?"))

        type_cols = ""
        type_header = ""
        graph_header = ""
        if has_types and "predicted_source" in pq[0]:
            type_header = "<th class='strategy'>Expected</th><th class='strategy'>Predicted</th>"
        if has_graph and "path_length" in pq[0]:
            graph_header = "<th class='strategy'>PathLen</th><th class='strategy'>SrcOut</th><th class='strategy'>SrcReach</th>"

        rows = []
        for q in pq:
            f1_val = q.get("f1", -1)
            if f1_val < 0:
                f1_cls = "na"
                f1_str = "&mdash;"
            else:
                f1_cls = "delta-pos" if f1_val >= 0.8 else ("delta-neg" if f1_val < 0.5 else "")
                f1_str = f"{f1_val:.2f}"

            rec_val = q.get("recall", -1)
            rec_cls = "delta-pos" if rec_val >= 0.8 else ("delta-neg" if 0 <= rec_val < 0.5 else "")
            rec_str = f"{rec_val:.2f}" if rec_val >= 0 else "&mdash;"

            prec_val = q.get("precision", -1)
            prec_str = f"{prec_val:.2f}" if prec_val >= 0 else "&mdash;"

            expected_str = ", ".join(q.get("expected_tools", []))
            resolved_str = ", ".join(q.get("resolved_tools", []))

            type_cells = ""
            if has_types and "predicted_source" in q:
                exp_st = f"{q.get('expected_source','?')}→{q.get('expected_target','?')}"
                pred_st = f"{q.get('predicted_source','?')}→{q.get('predicted_target','?')}"
                match_cls = "delta-pos" if exp_st == pred_st else "delta-neg"
                type_cells = f"<td class='val'>{exp_st}</td><td class='val {match_cls}'>{pred_st}</td>"

            graph_cells = ""
            if has_graph and "path_length" in q:
                pl = q.get("path_length")
                so = q.get("source_out_degree", 0)
                sr = q.get("source_reachable", 0)
                pl_str = str(pl) if pl is not None else "&mdash;"
                graph_cells = f"<td class='val'>{pl_str}</td><td class='val'>{so}</td><td class='val'>{sr}</td>"

            rows.append(f"""<tr>
                <td class='label'>{q['id']}</td>
                <td class='val'>{q.get('category','')}</td>
                {type_cells}
                <td class='val {rec_cls}'>{rec_str}</td>
                <td class='val'>{prec_str}</td>
                <td class='val {f1_cls}'>{f1_str}</td>
                {graph_cells}
                <td class='val' style='font-size:11px;max-width:200px;overflow:hidden;text-overflow:ellipsis'>{expected_str}</td>
                <td class='val' style='font-size:11px;max-width:200px;overflow:hidden;text-overflow:ellipsis'>{resolved_str}</td>
            </tr>""")

        table_id = f"pq-{model}-{key}".replace(" ", "-")
        sections.append(f"""
        <div class="pq-strategy">
          <div class="pq-toggle" onclick="var t=document.getElementById('{table_id}');t.style.display=t.style.display==='none'?'':'none'">
            ▸ {key} ({len(pq)} queries)
          </div>
          <table id="{table_id}" style="display:none">
            <tr>
              <th>Query</th><th class="strategy">Cat</th>
              {type_header}
              <th class="strategy">Recall</th><th class="strategy">Prec</th><th class="strategy">F1</th>
              {graph_header}
              <th class="strategy">Expected Tools</th><th class="strategy">Resolved Tools</th>
            </tr>
            {"".join(rows)}
          </table>
        </div>""")

    if not sections:
        return ""

    return f"""
    <div class="card">
      <h3>Per-Query Details</h3>
      {"".join(sections)}
    </div>"""


def render_failure_analysis(domain: str, model_results: dict) -> str:
    models = sorted(model_results.keys())
    all_query_ids = set()
    for model in models:
        for s in model_results[model]["strategies"]:
            for q in s.get("per_query", []):
                all_query_ids.add(q["id"])

    if not all_query_ids:
        return ""

    universal_failures = []
    graph_regressions = []

    for qid in sorted(all_query_ids):
        all_fail = True
        baseline_ok = False
        graph_fail = False

        for model in models:
            for s in model_results[model]["strategies"]:
                key = s.get("strategy_key", s.get("strategy", ""))
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
        return ""

    items = []
    if universal_failures:
        ids = ", ".join(universal_failures)
        items.append(f"""
        <div class="failure-group">
          <h4>Universal Failures ({len(universal_failures)})</h4>
          <p>These queries fail across all strategies and models — fundamental limitations:</p>
          <div class="failure-ids">{ids}</div>
        </div>""")

    if graph_regressions:
        ids = ", ".join(graph_regressions)
        items.append(f"""
        <div class="failure-group">
          <h4>Graph Recall Regressions ({len(graph_regressions)})</h4>
          <p>Baseline finds these but graph strategies miss them — type prediction errors:</p>
          <div class="failure-ids">{ids}</div>
        </div>""")

    return f"""
    <div class="card">
      <h3>Failure Analysis</h3>
      {"".join(items)}
    </div>"""


def render_graph_eda(domain: str, model_results: dict) -> str:
    all_pq = []
    for model in sorted(model_results.keys()):
        for s in model_results[model]["strategies"]:
            key = s.get("strategy_key", s.get("strategy", ""))
            if key in ("baseline", "retrieval", "oracle-graph", "model-types"):
                continue
            for q in s.get("per_query", []):
                if "path_length" in q and q.get("f1", -1) >= 0:
                    all_pq.append({**q, "model": model, "strategy": key})

    if not all_pq:
        return ""

    from collections import defaultdict

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

    def make_table(title, data, key_label, key_order=None):
        keys = key_order or sorted(data.keys())
        keys = [k for k in keys if k in data]
        if not keys:
            return ""
        header = f"<tr><th>{key_label}</th><th class='strategy'>N</th><th class='strategy'>Avg F1</th><th class='strategy'>Avg Recall</th></tr>"
        rows = []
        for k in keys:
            vals = data[k]
            n = len(vals)
            avg_f1 = sum(vals) / n
            bg = f1_to_color(avg_f1)
            rows.append(f"<tr><td class='label'>{k}</td><td class='val'>{n}</td>"
                        f"<td class='val heat' style='background:{bg}'>{avg_f1:.2f}</td>"
                        f"<td class='val'>&mdash;</td></tr>")
        return f"<h4>{title}</h4><table>{header}{''.join(rows)}</table>"

    by_reachable_recall = defaultdict(list)
    for q in all_pq:
        sr = q.get("source_reachable", 0)
        if sr <= 3:
            rb = "1-3"
        elif sr <= 10:
            rb = "4-10"
        elif sr <= 20:
            rb = "11-20"
        else:
            rb = "21+"
        by_reachable_recall[rb].append(q.get("recall", 0))

    sections = []
    sections.append(make_table("F1 by Path Length", by_path_len, "Hops"))
    sections.append(make_table("F1 by Source Out-Degree", by_out_degree, "Out-Degree",
                               ["1-2", "3-5", "6-10", "11+"]))
    sections.append(make_table("F1 by Source Reachable Types", by_reachable, "Reachable",
                               ["1-3", "4-10", "11-20", "21+"]))

    return f"""
    <div class="card">
      <h3>Graph Metrics vs Performance</h3>
      <div class="eda-grid">{"".join(f'<div>{s}</div>' for s in sections if s)}</div>
    </div>"""


def render_graph_structure(domains: list[str]) -> str:
    all_metrics = {}
    for d in domains:
        m = _get_graph_metrics(d)
        if m:
            all_metrics[d] = m
    if not all_metrics:
        return ""

    header_cells = "".join(f"<th class='strategy'>{d}</th>" for d in domains if d in all_metrics)

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

    rows = []
    for label, getter in rows_spec:
        cells = ""
        for d in domains:
            if d not in all_metrics:
                continue
            val = getter(all_metrics[d])
            if isinstance(val, float):
                cells += f"<td class='val'>{val:.2f}</td>"
            else:
                cells += f"<td class='val'>{val}</td>"
        rows.append(f"<tr><td class='label'>{label}</td>{cells}</tr>")

    betweenness_rows = []
    for d in domains:
        if d not in all_metrics:
            continue
        top = all_metrics[d]["centrality"]["top_betweenness"][:3]
        items = ", ".join(f"{e['type']} ({e['score']:.0f})" for e in top)
        betweenness_rows.append(f"<tr><td class='label'>{d}</td><td class='val' colspan='{len(all_metrics)-1}' style='text-align:left'>{items}</td></tr>")

    betweenness_section = ""
    if betweenness_rows:
        betweenness_section = f"""
        <h4 style="margin-top:16px; color:#9ca3af; font-size:12px;">Top Betweenness Centrality (hub types)</h4>
        <table>
          <tr><th>Domain</th><th style="text-align:left">Top Types</th></tr>
          {"".join(betweenness_rows)}
        </table>"""

    return f"""
    <div class="card">
      <h3>Graph Structure by Domain</h3>
      <table>
        <tr><th>Metric</th>{header_cells}</tr>
        {"".join(rows)}
      </table>
      {betweenness_section}
    </div>"""


def render_aggregate_table(data: dict) -> str:
    rows = []
    for domain in sorted(data.keys()):
        for model in sorted(data[domain].keys()):
            strats = data[domain][model]["strategies"]
            by_key = {s.get("strategy_key", s.get("strategy", "")): s for s in strats}

            bl = by_key.get("baseline", {})
            bl_f1 = bl.get("f1", 0)
            bl_hall = bl.get("hallucinated", 0)
            bl_tok = bl.get("avg_prompt_tokens", 0)

            graph_strats = [(k, s) for k, s in by_key.items() if k not in ("baseline", "retrieval", "oracle-graph", "model-types")]
            if not graph_strats:
                continue
            best_key, best = max(graph_strats, key=lambda x: x[1].get("f1", 0))
            best_f1 = best.get("f1", 0)
            best_hall = best.get("hallucinated", 0)
            best_tok = best.get("avg_prompt_tokens", 0)

            best_prec = best.get("precision", 0)
            best_rec = best.get("recall", 0)
            bl_prec = bl.get("precision", 0)
            bl_rec = bl.get("recall", 0)

            f1_delta = best_f1 - bl_f1
            prec_delta = best_prec - bl_prec
            rec_delta = best_rec - bl_rec
            tok_save = (1 - best_tok / bl_tok) * 100 if bl_tok > 0 else 0

            def _delta_cls(d):
                return "delta-pos" if d > 0.005 else ("delta-neg" if d < -0.005 else "")

            def _delta_fmt(v, d):
                sign = "+" if d > 0.005 else ""
                cls = _delta_cls(d)
                delta_span = f" <span class='delta'>({sign}{d:.2f})</span>" if abs(d) > 0.005 else ""
                return f'<td class="val {cls}">{v:.2f}{delta_span}</td>'

            hall_cls = "delta-pos" if best_hall < bl_hall else ("" if best_hall == bl_hall else "delta-neg")
            tok_cls = "delta-pos" if tok_save > 0 else "delta-neg"

            rows.append(f"""<tr data-model="{model}">
              <td class="label">{domain}</td>
              <td class="label">{model}</td>
              <td class="val">{best_key}</td>
              {_delta_fmt(best_prec, prec_delta)}
              {_delta_fmt(best_rec, rec_delta)}
              {_delta_fmt(best_f1, f1_delta)}
              <td class="val">{bl_hall}</td>
              <td class="val {hall_cls}">{best_hall}</td>
              <td class="val {tok_cls}">{tok_save:.0f}%</td>
            </tr>""")

    if not rows:
        return ""

    return f"""
    <div class="aggregate-section">
      <div class="card">
        <h3>All Results: Graph vs Baseline</h3>
        <table>
          <tr>
            <th>Domain</th><th>Model</th>
            <th class="strategy">Strategy</th>
            <th class="strategy">Precision</th>
            <th class="strategy">Recall</th>
            <th class="strategy">F1</th>
            <th class="strategy">BL Hall.</th>
            <th class="strategy">Graph Hall.</th>
            <th class="strategy">Token Savings</th>
          </tr>
          {"".join(rows)}
        </table>
      </div>
    </div>"""


def generate_html(data: dict) -> str:
    domains = sorted(data.keys())
    all_models = sorted({m for d in data.values() for m in d})
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    model_tabs = "<div class='tab model-tab active' data-model='all'>All</div>"
    for m in all_models:
        model_tabs += f"<div class='tab model-tab' data-model='{m}'>{m}</div>"

    tabs = ""
    sections = ""
    for i, domain in enumerate(domains):
        active = " active" if i == 0 else ""
        tabs += f"<div class='tab domain-tab{active}' data-domain='{domain}'>{domain}</div>"
        display = "" if i == 0 else "display:none;"

        model_results = data[domain]
        content = ""
        for model in sorted(model_results.keys()):
            meta = model_results[model]["meta"]
            strategies = model_results[model]["strategies"]
            n_queries = strategies[0]["n"] if strategies else "?"

            content += f"""
            <div class="model-section" data-model="{model}">
            <h2>{meta.get('model_id', model)}</h2>
            <div class="meta">
              <span>Model: {model}</span>
              <span>Queries: {n_queries}</span>
              <span>Run: {meta.get('timestamp', '?')[:19]}</span>
            </div>"""
            content += render_summary_card(strategies)
            content += render_decomposition_card(strategies, model)
            content += render_metrics_table(strategies, CORE_METRICS, "Core Metrics")
            content += render_metrics_table(strategies, LATENCY_METRICS, "Latency &amp; Tokens")
            content += render_category_table(strategies)
            content += render_per_query_table(strategies, model)
            content += "</div>"

        content += render_cross_model_table(domain, model_results)
        content += render_recall_precision_vs_baseline(domain, model_results)
        content += render_graph_eda(domain, model_results)
        content += render_failure_analysis(domain, model_results)

        sections += f"""
        <div class="domain-section" id="domain-{domain}" style="{display}">
          {content}
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Benchmark Report</title>
<style>
body {{
  font-family: system-ui, -apple-system, sans-serif;
  background: #0f1117;
  color: #e0e0e0;
  margin: 0;
  padding: 0;
}}
.container {{
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}}
.card {{
  background: #1a1d27;
  border: 1px solid #2a2d3a;
  border-radius: 10px;
  padding: 24px;
  margin-bottom: 24px;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}}
th {{
  text-align: left;
  color: #9ca3af;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 11px;
  padding: 8px 12px;
  border-bottom: 1px solid #2a2d3a;
}}
th.strategy {{
  text-align: right;
}}
td {{
  padding: 6px 12px;
  border-bottom: 1px solid #1f2233;
}}
td.val {{
  text-align: right;
}}
td.best {{
  color: #34d399;
  font-weight: 600;
}}
td.label {{
  color: #9ca3af;
  font-weight: 500;
  white-space: nowrap;
}}
td.na {{
  color: #555;
}}
td.heat {{
  border-radius: 4px;
}}
td.delta-pos {{
  color: #34d399;
}}
td.delta-neg {{
  color: #f87171;
}}
.delta {{
  font-size: 11px;
  opacity: 0.7;
}}
.baseline-row td {{
  color: #9ca3af;
  font-style: italic;
}}
.recall-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 20px;
}}
.recall-model h4 {{
  font-size: 13px;
  color: #c0c0c0;
  margin: 0 0 8px 0;
}}
.pq-toggle {{
  cursor: pointer;
  color: #6366f1;
  font-size: 13px;
  padding: 4px 0;
  user-select: none;
}}
.pq-toggle:hover {{
  color: #818cf8;
}}
.pq-strategy {{
  margin-bottom: 8px;
}}
.failure-group {{
  margin-bottom: 16px;
}}
.failure-group h4 {{
  font-size: 13px;
  color: #f87171;
  margin: 0 0 4px 0;
}}
.failure-group p {{
  font-size: 12px;
  color: #9ca3af;
  margin: 0 0 8px 0;
}}
.failure-ids {{
  font-size: 12px;
  color: #e0e0e0;
  background: #0f1117;
  padding: 8px 12px;
  border-radius: 6px;
  font-family: monospace;
}}
.eda-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}}
.eda-grid h4 {{
  font-size: 12px;
  color: #9ca3af;
  margin: 0 0 8px 0;
}}
h1 {{
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
}}
h2 {{
  font-size: 18px;
  font-weight: 600;
  color: #c0c0c0;
  margin: 32px 0 12px 0;
}}
h3 {{
  font-size: 14px;
  font-weight: 600;
  color: #6366f1;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}}
.meta {{
  font-size: 12px;
  color: #555;
  margin-bottom: 16px;
}}
.meta span {{
  margin-right: 16px;
}}
.tabs {{
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
}}
.tab {{
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  background: #1a1d27;
  border: 1px solid #2a2d3a;
  color: #9ca3af;
  font-size: 13px;
  user-select: none;
}}
.tab.active {{
  background: #6366f1;
  border-color: #6366f1;
  color: #fff;
}}
.tab:hover {{
  border-color: #6366f1;
}}
.summary-card {{
  border-left: 3px solid #6366f1;
}}
.summary-subtitle {{
  font-size: 13px;
  color: #9ca3af;
  margin-bottom: 16px;
}}
.summary-subtitle strong {{
  color: #6366f1;
}}
.summary-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
}}
.summary-item {{
  text-align: center;
  padding: 12px;
  background: #0f1117;
  border-radius: 8px;
}}
.summary-value {{
  font-size: 28px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}}
.summary-value.pos {{ color: #34d399; }}
.summary-value.neg {{ color: #f87171; }}
.summary-label {{
  font-size: 12px;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 4px;
}}
.summary-detail {{
  font-size: 11px;
  color: #555;
  margin-top: 2px;
}}
.aggregate-section {{
  margin-bottom: 32px;
}}
.filter-bar {{
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
}}
.filter-label {{
  font-size: 13px;
  color: #9ca3af;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}
</style>
</head>
<body>
<div class="container">
  <h1>Benchmark Report</h1>
  <div class="meta">
    <span>Generated: {now}</span>
    <span>Domains: {', '.join(domains)}</span>
  </div>
  <div class="filter-bar">
    <span class="filter-label">Model:</span>
    <div class="tabs" style="display:inline-flex;">{model_tabs}</div>
  </div>
  {render_aggregate_table(data)}
  {render_graph_structure(domains)}
  <div class="tabs">{tabs}</div>
  {sections}
</div>
<script>
document.querySelectorAll('.domain-tab').forEach(tab => {{
  tab.addEventListener('click', () => {{
    document.querySelectorAll('.domain-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    document.querySelectorAll('.domain-section').forEach(s => s.style.display = 'none');
    document.getElementById('domain-' + tab.dataset.domain).style.display = '';
  }});
}});
document.querySelectorAll('.model-tab').forEach(tab => {{
  tab.addEventListener('click', () => {{
    document.querySelectorAll('.model-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    var sel = tab.dataset.model;
    document.querySelectorAll('.model-section').forEach(s => {{
      s.style.display = (sel === 'all' || s.dataset.model === sel) ? '' : 'none';
    }});
    document.querySelectorAll('tr[data-model]').forEach(r => {{
      r.style.display = (sel === 'all' || r.dataset.model === sel) ? '' : 'none';
    }});
  }});
}});
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate HTML benchmark report from JSON results")
    parser.add_argument("files", nargs="*", default=None,
                        help="JSON result files (default: benchmarks/results/*.json)")
    parser.add_argument("--output", type=Path, default=Path("benchmarks/report.html"),
                        help="Output HTML file (default: benchmarks/report.html)")
    parser.add_argument("--open", action="store_true",
                        help="Open report in browser after generating")
    args = parser.parse_args()

    if args.files:
        paths = [Path(f) for f in args.files]
    else:
        paths = sorted(Path("benchmarks/results").glob("*.json"))

    if not paths:
        print("No result files found. Run benchmarks first:")
        print("  uv run python -m benchmarks.run_all --models qwen --domains k8s")
        return

    print(f"Loading {len(paths)} result file(s)...")
    data = load_results(paths)

    html = generate_html(data)
    args.output.write_text(html)
    print(f"Report written to {args.output}")

    if args.open:
        webbrowser.open(f"file://{args.output.resolve()}")


if __name__ == "__main__":
    main()
