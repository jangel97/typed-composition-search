import argparse
import json
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

STRATEGY_ORDER = [
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

    graph_strats = [(k, s) for k, s in by_key.items() if k != "baseline" and k != "retrieval"]
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

            graph_strats = [(k, s) for k, s in by_key.items() if k not in ("baseline", "retrieval")]
            if not graph_strats:
                continue
            best_key, best = max(graph_strats, key=lambda x: x[1].get("f1", 0))
            best_f1 = best.get("f1", 0)
            best_hall = best.get("hallucinated", 0)
            best_tok = best.get("avg_prompt_tokens", 0)

            f1_delta = best_f1 - bl_f1
            tok_save = (1 - best_tok / bl_tok) * 100 if bl_tok > 0 else 0

            f1_cls = "delta-pos" if f1_delta >= 0 else "delta-neg"
            f1_sign = "+" if f1_delta >= 0 else ""
            hall_cls = "delta-pos" if best_hall < bl_hall else ("" if best_hall == bl_hall else "delta-neg")
            tok_cls = "delta-pos" if tok_save > 0 else "delta-neg"

            rows.append(f"""<tr>
              <td class="label">{domain}</td>
              <td class="label">{model}</td>
              <td class="val">{bl_f1:.2f}</td>
              <td class="val best">{best_f1:.2f}</td>
              <td class="val {f1_cls}">{f1_sign}{f1_delta:.2f}</td>
              <td class="val">{best_key}</td>
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
            <th class="strategy">Baseline F1</th>
            <th class="strategy">Best Graph F1</th>
            <th class="strategy">&Delta; F1</th>
            <th class="strategy">Strategy</th>
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

    tabs = ""
    sections = ""
    for i, domain in enumerate(domains):
        active = " active" if i == 0 else ""
        tabs += f"<div class='tab{active}' data-domain='{domain}'>{domain}</div>"
        display = "" if i == 0 else "display:none;"

        model_results = data[domain]
        content = ""
        for model in sorted(model_results.keys()):
            meta = model_results[model]["meta"]
            strategies = model_results[model]["strategies"]
            n_queries = strategies[0]["n"] if strategies else "?"

            content += f"""
            <h2>{meta.get('model_id', model)}</h2>
            <div class="meta">
              <span>Model: {model}</span>
              <span>Queries: {n_queries}</span>
              <span>Run: {meta.get('timestamp', '?')[:19]}</span>
            </div>"""
            content += render_summary_card(strategies)
            content += render_metrics_table(strategies, CORE_METRICS, "Core Metrics")
            content += render_metrics_table(strategies, LATENCY_METRICS, "Latency &amp; Tokens")
            content += render_category_table(strategies)

        content += render_cross_model_table(domain, model_results)
        content += render_recall_precision_vs_baseline(domain, model_results)

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
</style>
</head>
<body>
<div class="container">
  <h1>Benchmark Report</h1>
  <div class="meta">
    <span>Generated: {now}</span>
    <span>Models: {', '.join(all_models)}</span>
    <span>Domains: {', '.join(domains)}</span>
  </div>
  {render_aggregate_table(data)}
  <div class="tabs">{tabs}</div>
  {sections}
</div>
<script>
document.querySelectorAll('.tab').forEach(tab => {{
  tab.addEventListener('click', () => {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    document.querySelectorAll('.domain-section').forEach(s => s.style.display = 'none');
    document.getElementById('domain-' + tab.dataset.domain).style.display = '';
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
