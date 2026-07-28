"""Generate figures for the workshop paper (v3).

Usage:
    python figures.py              # all figures
    python figures.py method       # specific figure
    python figures.py scale crossover

Writes to docs/paper_v3/figures/
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np

FIGURES_DIR = Path(__file__).resolve().parent / "latex" / "figures"


# ── Figure 1: Method diagram (TCR pipeline) ──────────────────────────


def plot_method():
    fig, ax = plt.subplots(figsize=(14, 3.5))
    ax.set_xlim(-0.3, 14.3)
    ax.set_ylim(0, 3.5)
    ax.axis("off")

    box_style = dict(boxstyle="round,pad=0.4", linewidth=1.5)

    QUERY_X = 0.5
    STAGE1_X = 3.0
    STAGE2_X = 6.5
    FILTERED_X = 9.3
    STAGE3_X = 12.8

    def draw_arrow(x_from, x_to, y=2.0):
        ax.annotate(
            "",
            xy=(x_to, y),
            xytext=(x_from, y),
            arrowprops=dict(
                arrowstyle="-|>",
                mutation_scale=20,
                linewidth=2.0,
                color="#2c3e50",
                shrinkA=0,
                shrinkB=0,
            ),
        )

    # ── Arrows (x_from = right edge of source, x_to = left edge of target)
    draw_arrow(0.9, 2.03)    # Query → Stage 1
    draw_arrow(4.0, 5.61)    # Stage 1 → Stage 2
    draw_arrow(7.4, 8.59)    # Stage 2 → Filtered
    draw_arrow(10.0, 11.97)  # Filtered → Stage 3

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    ax.text(
        QUERY_X,
        2.0,
        '"Get containers\nin production"',
        fontsize=9,
        ha="center",
        va="center",
        style="italic",
        bbox=dict(
            **box_style,
            facecolor="#ecf0f1",
            edgecolor="#7f8c8d",
        ),
    )

    # ------------------------------------------------------------------
    # Stage 1
    # ------------------------------------------------------------------

    ax.text(
        STAGE1_X,
        2.0,
        "Stage 1\nEntity Type Prediction",
        fontsize=10,
        ha="center",
        va="center",
        fontweight="bold",
        color="white",
        bbox=dict(
            **box_style,
            facecolor="#3498db",
            edgecolor="#2980b9",
            alpha=0.9,
        ),
    )

    ax.text(
        STAGE1_X,
        0.75,
        "Learned Predictor",
        fontsize=9,
        ha="center",
        color="#7f8c8d",
    )

    ax.text(
        STAGE1_X,
        0.40,
        "Query → Entity Types",
        fontsize=8,
        ha="center",
        color="#95a5a6",
        fontfamily="monospace",
    )

    ax.plot(
        [STAGE1_X, STAGE1_X],
        [1.1, 1.5],
        "--",
        color="#bdc3c7",
        linewidth=1,
    )

    # ------------------------------------------------------------------
    # Predicted types
    # ------------------------------------------------------------------

    mid = (4.05 + 5.55) / 2  # centered between Stage1→Stage2 arrow endpoints

    ax.text(
        mid,
        2.85,
        "Predicted Entity Types",
        fontsize=7.5,
        ha="center",
        va="center",
        color="#7f8c8d",
    )
    ax.text(
        mid,
        2.42,
        "Source = Namespace\nTarget = Container",
        fontsize=7.5,
        ha="center",
        va="center",
        bbox=dict(
            boxstyle="round,pad=0.2",
            facecolor="#fef9e7",
            edgecolor="#f39c12",
        ),
        fontfamily="monospace",
    )

    # ------------------------------------------------------------------
    # Stage 2
    # ------------------------------------------------------------------

    ax.text(
        STAGE2_X,
        2.0,
        "Stage 2\nTyped Graph Search",
        fontsize=10,
        ha="center",
        va="center",
        fontweight="bold",
        color="white",
        bbox=dict(
            **box_style,
            facecolor="#2ecc71",
            edgecolor="#27ae60",
            alpha=0.9,
        ),
    )

    ax.text(
        STAGE2_X,
        0.65,
        "Deterministic\n(Algorithm 1)",
        fontsize=9,
        ha="center",
        color="#7f8c8d",
    )

    ax.plot(
        [STAGE2_X, STAGE2_X],
        [1.1, 1.5],
        "--",
        color="#bdc3c7",
        linewidth=1,
    )

    # ------------------------------------------------------------------
    # Filtered Tool Set
    # ------------------------------------------------------------------

    ax.text(
        FILTERED_X,
        2.65,
        "Filtered Tool Set",
        fontsize=8.5,
        ha="center",
        va="center",
        fontweight="bold",
        color="#c0392b",
    )

    ax.text(
        FILTERED_X,
        2.0,
        "list_namespaced_pods\nget_pod\ndelete_pod\nlist_pod_containers",
        fontsize=7.5,
        ha="center",
        va="center",
        fontfamily="monospace",
        bbox=dict(
            **box_style,
            facecolor="#fadbd8",
            edgecolor="#e74c3c",
        ),
    )

    ax.text(
        FILTERED_X,
        0.85,
        "Tools on valid\nNamespace → Container paths",
        fontsize=8,
        ha="center",
        va="center",
        bbox=dict(
            boxstyle="round,pad=0.2",
            facecolor="#fef9e7",
            edgecolor="#f39c12",
        ),
        fontfamily="monospace",
    )

    ax.plot(
        [FILTERED_X, FILTERED_X],
        [1.15, 1.5],
        "--",
        color="#bdc3c7",
        linewidth=1,
    )

    # ------------------------------------------------------------------
    # Arrow annotation: Filtered → Stage 3
    # ------------------------------------------------------------------

    arrow_mid = (10.35 + 11.75) / 2
    ax.text(
        arrow_mid,
        2.45,
        "Presented\nto the LLM",
        fontsize=8,
        ha="center",
        va="center",
        color="#8e44ad",
        fontweight="bold",
    )

    # ------------------------------------------------------------------
    # Stage 3
    # ------------------------------------------------------------------

    ax.text(
        STAGE3_X,
        2.0,
        "Stage 3\nLLM Tool Selection",
        fontsize=10,
        ha="center",
        va="center",
        fontweight="bold",
        color="white",
        bbox=dict(
            **box_style,
            facecolor="#9b59b6",
            edgecolor="#8e44ad",
            alpha=0.9,
        ),
    )

    ax.text(
        STAGE3_X,
        0.65,
        "LLM selects from a reduced set of\nstructurally valid tool candidates.",
        fontsize=8,
        ha="center",
        color="#7f8c8d",
    )

    ax.plot(
        [STAGE3_X, STAGE3_X],
        [1.1, 1.5],
        "--",
        color="#bdc3c7",
        linewidth=1,
    )

    # ------------------------------------------------------------------
    # Title
    # ------------------------------------------------------------------

    fig.suptitle(
        "Typed Composition Routing (TCR)",
        fontsize=12,
        fontweight="bold",
        y=0.98,
    )

    ax.text(
        7.0,
        0.1,
        "Every returned tool exists in the registry and adjacent tools are type-compatible.\nThe filtered tool set reduces prompt tokens and the LLM search space.",
        fontsize=9,
        ha="center",
        va="center",
        style="italic",
        color="#7f8c8d",
    )

    fig.tight_layout(rect=[0, 0.05, 1, 0.93])

    fig.savefig(FIGURES_DIR / "1_method.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "1_method.png", bbox_inches="tight", dpi=200)

    plt.close(fig)

    print("  1_method.pdf")


# ── Figure 2: Production scale reduction ─────────────────────────────


def plot_scale():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))

    # ---------------- Left panel: Tool reduction ----------------
    categories = ["Full Catalog", "TCR Candidates"]
    values = [1060, 6.1]
    colors = ["#e74c3c", "#2ecc71"]

    bars = ax1.bar(
        categories,
        values,
        color=colors,
        width=0.5,
        edgecolor="white",
        linewidth=1.5,
    )

    ax1.set_ylabel("Number of Tools", fontsize=10)
    ax1.set_title("Tool Count Reduction", fontweight="bold", fontsize=11)
    ax1.set_ylim(0, 1200)

    # Value labels
    for bar, label in zip(bars, ["1060", "6.1"]):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 25,
            label,
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )

    # Bar centers
    x0 = bars[0].get_x() + bars[0].get_width() / 2
    x1 = bars[1].get_x() + bars[1].get_width() / 2

    # Reduction annotation
    ax1.annotate(
        "99.4%\nreduction",
        xy=(x1, values[1] + 20),
        xytext=((x0 + x1) / 2, 700),
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="#2c3e50",
        arrowprops=dict(
            arrowstyle="->",
            lw=1.5,
            color="#2c3e50",
            connectionstyle="arc3,rad=-0.25",
        ),
    )

    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.grid(True, axis="y", alpha=0.3)

    # ---------------- Right panel: Token reduction ----------------
    categories2 = ["Full Catalog", "TCR (type names)"]
    values2 = [25433, 66]
    colors2 = ["#e74c3c", "#2ecc71"]

    bars2 = ax2.bar(
        categories2,
        values2,
        color=colors2,
        width=0.5,
        edgecolor="white",
        linewidth=1.5,
    )

    ax2.set_ylabel("Prompt Tokens", fontsize=10)
    ax2.set_title("Prompt Token Reduction", fontweight="bold", fontsize=11)
    ax2.set_ylim(0, 29000)

    # Value labels
    for bar, label in zip(bars2, ["25,433", "66"]):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 500,
            label,
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )

    # Bar centers
    x0 = bars2[0].get_x() + bars2[0].get_width() / 2
    x1 = bars2[1].get_x() + bars2[1].get_width() / 2

    # Reduction annotation
    ax2.annotate(
        "99.7%\nreduction",
        xy=(x1, values2[1] + 400),
        xytext=((x0 + x1) / 2, 17000),
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="#2c3e50",
        arrowprops=dict(
            arrowstyle="->",
            lw=1.5,
            color="#2c3e50",
            connectionstyle="arc3,rad=-0.25",
        ),
    )

    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.grid(True, axis="y", alpha=0.3)

    fig.suptitle(
        "Production Scale: AAP MCP Server (1,060 Tools)",
        fontsize=12,
        fontweight="bold",
    )

    fig.tight_layout()

    fig.savefig(FIGURES_DIR / "2_scale.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "2_scale.png", bbox_inches="tight", dpi=200)

    plt.close(fig)
    print("  2_scale.pdf")

# ── Figure 3: Granularity crossover ──────────────────────────────────


def _crossover_panel(ax, types, oracle_f1, granite_f1,
                     candidates, cands_ylim, title, y_lim):
    c_oracle = "#2c3e50"
    c_granite = "#16a085"
    c_cands = "#e67e22"

    ax.plot(types, oracle_f1, "s-", color=c_oracle, markersize=8,
            linewidth=2.2, label="Oracle / Opus", zorder=6)
    ax.plot(types, granite_f1, "D-.", color=c_granite, markersize=8,
            linewidth=2.2, label="Granite 4.1 8B", zorder=5)

    ax2 = ax.twinx()
    ax2.plot(types, candidates, "^-", color=c_cands, markersize=9,
             linewidth=1.5, alpha=0.6, label="Avg Candidates", zorder=4)
    ax2.set_ylabel("Avg Candidate Size", color=c_cands, fontsize=10)
    ax2.tick_params(axis="y", labelcolor=c_cands)
    ax2.set_ylim(0, cands_ylim)

    ax.set_xlabel("Number of Entity Types", fontsize=11)
    ax.set_ylabel("E2E Routing F1", fontsize=11)
    ax.set_title(title, fontweight="bold", fontsize=12)
    ax.set_ylim(0, y_lim)
    ax.set_xticks(types)
    ax.grid(True, alpha=0.3)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

    return ax2


def plot_crossover():
    fig, (ax_k8s, ax_aap) = plt.subplots(1, 2, figsize=(12, 4))

    _crossover_panel(
        ax_k8s,
        types=[6, 13, 21],
        oracle_f1=[0.449, 0.595, 0.706],
        granite_f1=[0.361, 0.509, 0.586],
        candidates=[4.9, 3.5, 2.5],
        cands_ylim=8,
        title="K8s (17 tools, 128 queries)",
        y_lim=1.0,
    )

    _crossover_panel(
        ax_aap,
        types=[8, 50, 88],
        oracle_f1=[0.031, 0.173, 0.230],
        granite_f1=[0.022, 0.110, 0.132],
        candidates=[116.0, 25.6, 21.5],
        cands_ylim=160,
        title="AAP (1,060 tools, 120 queries)",
        y_lim=0.35,
    )

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "3_crossover.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "3_crossover.png", bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("  3_crossover.pdf")


# ── Main ────────────────────────────────────────────────────────────


FIGURE_FUNCS = {
    "method": plot_method,
    "scale": plot_scale,
    "crossover": plot_crossover,
}


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 1:
        names = sys.argv[1:]
    else:
        names = list(FIGURE_FUNCS.keys())

    print(f"Generating {len(names)} figure(s):")
    for name in names:
        fn = FIGURE_FUNCS.get(name)
        if fn is None:
            print(f"  unknown: {name} (available: {', '.join(FIGURE_FUNCS)})")
            continue
        fn()

    print(f"\nFigures saved to {FIGURES_DIR}/")


if __name__ == "__main__":
    main()
