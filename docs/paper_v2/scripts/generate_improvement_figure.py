"""Generate 3-panel figure: type prediction accuracy vs P, R, F1.

Shows that precision is high and stable (graph constraint), recall tracks
type prediction accuracy (the bottleneck), and F1 follows recall.
Includes baseline reference and projected fine-tuned region.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

RESULTS_DIR = Path(__file__).parent.parent.parent.parent / "benchmarks" / "results"
OUT_DIR = Path(__file__).parent.parent / "figures"

MODEL_LABELS = {
    "granite-4-1-8b": "Granite 8B",
    "qwen": "Qwen3-14B",
    "gpt-oss-20b": "GPT-OSS 20B",
    "claude-haiku": "Haiku 4.5",
}

MODEL_MARKERS = {
    "granite-4-1-8b": "s",
    "qwen": "D",
    "gpt-oss-20b": "^",
    "claude-haiku": "o",
}

MODEL_COLORS = {
    "granite-4-1-8b": "#e377c2",
    "qwen": "#2ca02c",
    "gpt-oss-20b": "#ff7f0e",
    "claude-haiku": "#1f77b4",
}


def load_results():
    results = {}
    for f in sorted(RESULTS_DIR.glob("*.json")):
        parts = f.stem.rsplit("_", 1)
        key = parts[0]
        results[key] = f

    data_points = []
    for key, fpath in results.items():
        with open(fpath) as fp:
            data = json.load(fp)

        model = data["meta"]["model"]
        domain = data["meta"]["domain"]

        graph_strategy = None
        baseline_strategy = None
        for s in data["strategies"]:
            if s["strategy"] == "graph":
                graph_strategy = s
            elif s["strategy"] == "baseline":
                baseline_strategy = s

        if not graph_strategy or not graph_strategy.get("per_query"):
            continue

        pq = graph_strategy["per_query"]
        n = len(pq)
        both_correct = sum(
            1 for q in pq
            if q["predicted_source"] == q["expected_source"]
            and q["predicted_target"] == q["expected_target"]
        )
        type_acc = both_correct / n

        data_points.append({
            "model": model,
            "domain": domain,
            "type_acc": type_acc,
            "tcr_f1": graph_strategy["f1"],
            "tcr_precision": graph_strategy["precision"],
            "tcr_recall": graph_strategy["recall"],
            "baseline_f1": baseline_strategy["f1"] if baseline_strategy else None,
            "baseline_precision": baseline_strategy["precision"] if baseline_strategy else None,
            "baseline_recall": baseline_strategy["recall"] if baseline_strategy else None,
        })

    return data_points


def generate_figure(data_points):
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.0), sharey=True, sharex=True)

    metrics = [
        ("Precision", "tcr_precision", "baseline_precision"),
        ("Recall", "tcr_recall", "baseline_recall"),
        ("F1", "tcr_f1", "baseline_f1"),
    ]

    x_all = np.array([d["type_acc"] for d in data_points])

    for idx, (metric_name, tcr_key, base_key) in enumerate(metrics):
        ax = axes[idx]
        y_all = np.array([d[tcr_key] for d in data_points])
        base_vals = [d[base_key] for d in data_points if d[base_key] is not None]
        avg_base = np.mean(base_vals)

        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_all, y_all)

        # Trend line extended into fine-tuned zone
        x_line = np.linspace(0.20, 1.0, 200)
        y_line = np.clip(slope * x_line + intercept, 0, 1)

        # Confidence band
        n = len(x_all)
        x_mean = np.mean(x_all)
        se_line = std_err * np.sqrt(1/n + (x_line - x_mean)**2 / np.sum((x_all - x_mean)**2))
        ax.fill_between(x_line,
                         np.clip(y_line - 1.96*se_line, 0, 1),
                         np.clip(y_line + 1.96*se_line, 0, 1),
                         alpha=0.08, color="#444444", zorder=1)

        # Trend line
        ax.plot(x_line, y_line, color="#444444", linewidth=1.5, linestyle="-", zorder=2)

        # Fine-tuned zone
        ax.axvspan(0.85, 1.0, alpha=0.10, color="#2ca02c", zorder=0)

        # Baseline reference
        ax.axhline(y=avg_base, color="#d62728", linewidth=1.2, linestyle=":", zorder=2)

        y_at_90 = np.clip(slope * 0.90 + intercept, 0, 1)
        y_at_95 = np.clip(slope * 0.95 + intercept, 0, 1)

        # Data points
        for d in data_points:
            ax.scatter(
                d["type_acc"], d[tcr_key],
                marker=MODEL_MARKERS[d["model"]],
                color=MODEL_COLORS[d["model"]],
                s=45, alpha=0.85, edgecolors="white", linewidth=0.4,
                zorder=4,
            )

        ax.set_title(f"{metric_name}", fontsize=10, fontweight="bold")
        r_text = f"$r$={r_value:.2f}"
        ax.text(0.97, 0.03, r_text, transform=ax.transAxes,
                fontsize=8, ha="right", va="bottom",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor="#cccccc"))

        ax.set_xlim(0.20, 1.02)
        ax.set_ylim(0.45, 1.02)
        ax.grid(True, alpha=0.15)
        ax.tick_params(labelsize=8)

        if idx == 0:
            ax.set_ylabel("Score (TCR)", fontsize=9)

        print(f"{metric_name}: slope={slope:.3f}, intercept={intercept:.3f}, "
              f"r={r_value:.3f}, p={p_value:.6f}, "
              f"proj@90%={y_at_90:.3f}, proj@95%={y_at_95:.3f}, "
              f"baseline_avg={avg_base:.3f}")

    # Shared x-label
    fig.text(0.5, -0.02, "Entity type prediction accuracy (both correct)",
             ha="center", fontsize=10)

    # Shared legend below plots
    model_handles = [
        plt.Line2D([0], [0], marker=MODEL_MARKERS[m], color="w",
                   markerfacecolor=MODEL_COLORS[m], markersize=6,
                   label=MODEL_LABELS[m])
        for m in ["granite-4-1-8b", "qwen", "gpt-oss-20b", "claude-haiku"]
    ]
    trend_handle = plt.Line2D([0], [0], color="#444444", linewidth=1.5,
                               label="Trend")
    baseline_handle = plt.Line2D([0], [0], color="#d62728", linewidth=1.2,
                                  linestyle=":", label="Baseline avg")
    zone_handle = plt.Line2D([0], [0], marker="s", color="w",
                              markerfacecolor="#2ca02c", markersize=8,
                              alpha=0.3, label="Trained predictor")

    fig.legend(handles=model_handles + [zone_handle, trend_handle, baseline_handle],
               loc="lower center", ncol=7, fontsize=7,
               bbox_to_anchor=(0.5, -0.14), handletextpad=0.3, columnspacing=0.8)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.08)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        out = OUT_DIR / f"improvement_path.{ext}"
        fig.savefig(out, dpi=300, bbox_inches="tight")
        print(f"Saved {out}")

    plt.close()


if __name__ == "__main__":
    data = load_results()
    print(f"Loaded {len(data)} model-domain combinations\n")
    generate_figure(data)
