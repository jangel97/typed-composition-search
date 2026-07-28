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
    # ── Layout parameters (change these, everything else follows) ─────
    W, H = 16, 5
    ROW_Y = 2.8                # main box row
    ABOVE_Y = ROW_Y + 1.2     # labels above boxes
    ABOVE2_Y = ROW_Y + 0.85   # annotation boxes above arrow
    SUB1_Y = ROW_Y - 1.3      # first sub-annotation
    SUB2_Y = ROW_Y - 1.7      # second sub-annotation
    DASH_BOT = ROW_Y - 0.55   # dashed line bottom
    DASH_TOP = ROW_Y - 0.95   # dashed line top (lower y)
    BOTTOM_Y = 0.5             # footer text
    ARROW_PAD = 0.08           # gap between arrow tip and box edge

    # Font sizes
    FS_STAGE = 13
    FS_QUERY = 12
    FS_ANNOT = 11
    FS_MONO = 10
    FS_TITLE = 15
    FS_FOOTER = 11

    # Element x-positions (evenly spaced)
    positions = np.linspace(1.0, W - 1.0, 5)
    QUERY_X, STAGE1_X, STAGE2_X, FILTERED_X, STAGE3_X = positions
    FILTERED_X += 0.3

    # ── Setup ─────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(-0.3, W + 0.3)
    ax.set_ylim(0, H)
    ax.axis("off")

    box_style = dict(boxstyle="round,pad=0.4", linewidth=1.5)

    # ── Draw all boxes first (save references for arrow computation) ──

    query_txt = ax.text(
        QUERY_X, ROW_Y,
        '"Get containers\nin production"',
        fontsize=FS_QUERY, ha="center", va="center", style="italic",
        bbox=dict(**box_style, facecolor="#ecf0f1", edgecolor="#7f8c8d"),
    )

    stage1_txt = ax.text(
        STAGE1_X, ROW_Y,
        "Stage 1\nEntity Type Prediction",
        fontsize=FS_STAGE, ha="center", va="center",
        fontweight="bold", color="white",
        bbox=dict(**box_style, facecolor="#3498db", edgecolor="#2980b9", alpha=0.9),
    )
    ax.text(STAGE1_X, SUB1_Y, "Learned Predictor",
            fontsize=FS_ANNOT, ha="center", color="#7f8c8d")
    ax.text(STAGE1_X, SUB2_Y, "Query → Entity Types",
            fontsize=FS_MONO, ha="center", color="#95a5a6", fontfamily="monospace")
    ax.plot([STAGE1_X, STAGE1_X], [DASH_TOP, DASH_BOT],
            "--", color="#bdc3c7", linewidth=1)

    mid12 = (STAGE1_X + STAGE2_X) / 2
    ax.text(mid12, ABOVE_Y, "Predicted Entity Types",
            fontsize=FS_MONO, ha="center", va="center", color="#7f8c8d")
    ax.text(mid12, ABOVE2_Y, "Source = Namespace\nTarget = Container",
            fontsize=9, ha="center", va="center", fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#fef9e7", edgecolor="#f39c12"))

    stage2_txt = ax.text(
        STAGE2_X, ROW_Y,
        "Stage 2\nTyped Graph Search",
        fontsize=FS_STAGE, ha="center", va="center",
        fontweight="bold", color="white",
        bbox=dict(**box_style, facecolor="#2ecc71", edgecolor="#27ae60", alpha=0.9),
    )
    ax.text(STAGE2_X, SUB1_Y, "Deterministic\n(Algorithm 1)",
            fontsize=FS_ANNOT, ha="center", color="#7f8c8d")
    ax.plot([STAGE2_X, STAGE2_X], [DASH_TOP, DASH_BOT],
            "--", color="#bdc3c7", linewidth=1)

    ax.text(FILTERED_X, ABOVE_Y - 0.03, "Filtered Tool Set",
            fontsize=FS_ANNOT, ha="center", va="center",
            fontweight="bold", color="#c0392b")
    filtered_txt = ax.text(
        FILTERED_X, ROW_Y,
        "list_namespaced_pods\nget_pod\ndelete_pod\nlist_pod_containers",
        fontsize=FS_MONO, ha="center", va="center", fontfamily="monospace",
        bbox=dict(**box_style, facecolor="#fadbd8", edgecolor="#e74c3c"),
    )
    ax.text(FILTERED_X + 0.05, SUB1_Y, "Tools on valid\nNamespace → Container paths",
            fontsize=FS_MONO, ha="center", va="center", fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#fef9e7", edgecolor="#f39c12"))
    ax.plot([FILTERED_X, FILTERED_X], [DASH_TOP, DASH_BOT],
            "--", color="#bdc3c7", linewidth=1)

    mid_fs3 = (FILTERED_X + STAGE3_X) / 2
    ax.text(mid_fs3, ABOVE2_Y - 0.3, "Presented\nto the LLM",
            fontsize=FS_ANNOT, ha="center", va="center",
            color="#8e44ad", fontweight="bold")

    stage3_txt = ax.text(
        STAGE3_X, ROW_Y,
        "Stage 3\nLLM Tool Selection",
        fontsize=FS_STAGE, ha="center", va="center",
        fontweight="bold", color="white",
        bbox=dict(**box_style, facecolor="#9b59b6", edgecolor="#8e44ad", alpha=0.9),
    )
    ax.text(STAGE3_X, SUB1_Y + 0.08,
            "LLM selects from a reduced set of\nstructurally valid tool candidates.",
            fontsize=FS_MONO, ha="center", color="#7f8c8d")
    ax.plot([STAGE3_X, STAGE3_X], [DASH_TOP, DASH_BOT],
            "--", color="#bdc3c7", linewidth=1)

    fig.suptitle("Typed Composition Routing (TCR)",
                 fontsize=FS_TITLE, fontweight="bold", y=0.98)
    ax.text(
        W / 2, BOTTOM_Y,
        "Every returned tool exists in the registry and adjacent tools are type-compatible.\n"
        "The filtered tool set reduces prompt tokens and the LLM search space.",
        fontsize=FS_FOOTER, ha="center", va="center", style="italic", color="#7f8c8d",
    )

    # ── Render once to compute actual box sizes, then add arrows ──────
    fig.tight_layout(rect=[0, 0.05, 1, 0.93])
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def box_x_edges(txt):
        patch = txt.get_bbox_patch()
        bb = patch.get_window_extent(renderer)
        bb_data = bb.transformed(ax.transData.inverted())
        return bb_data.x0, bb_data.x1

    boxes = [query_txt, stage1_txt, stage2_txt, filtered_txt, stage3_txt]
    for i in range(len(boxes) - 1):
        _, x_right = box_x_edges(boxes[i])
        x_left, _ = box_x_edges(boxes[i + 1])
        ax.annotate(
            "",
            xy=(x_left - ARROW_PAD, ROW_Y),
            xytext=(x_right + ARROW_PAD, ROW_Y),
            arrowprops=dict(
                arrowstyle="-|>",
                mutation_scale=20,
                linewidth=2.0,
                color="#2c3e50",
                shrinkA=0,
                shrinkB=0,
            ),
        )

    fig.savefig(FIGURES_DIR / "1_method.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "1_method.png", bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("  1_method.pdf")


# ── Figure 2: Production scale reduction ─────────────────────────────


def plot_scale():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))

    # ---------------- Left panel: Tool reduction ----------------
    categories = ["Full Catalog", "Candidate Set"]
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

    # Value labels — small value gets larger font
    for bar, label, fs in zip(bars, ["1,060", "6.1"], [12, 14]):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 25,
            label,
            ha="center",
            va="bottom",
            fontsize=fs,
            fontweight="bold",
        )

    # Bar centers
    x0 = bars[0].get_x() + bars[0].get_width() / 2
    x1 = bars[1].get_x() + bars[1].get_width() / 2

    # Reduction annotation (no arrow)
    ax1.text(
        (x0 + x1) / 2, 600,
        "99.4%\nreduction",
        ha="center", va="center",
        fontsize=10, fontweight="bold", color="#2c3e50",
    )

    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.grid(True, axis="y", alpha=0.3)

    # ---------------- Right panel: Token reduction ----------------
    categories2 = ["Full Catalog", "Entity-Type Prompt"]
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

    # Value labels — small value gets larger font
    for bar, label, fs in zip(bars2, ["25,433", "66"], [12, 14]):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 500,
            label,
            ha="center",
            va="bottom",
            fontsize=fs,
            fontweight="bold",
        )

    # Bar centers
    x0 = bars2[0].get_x() + bars2[0].get_width() / 2
    x1 = bars2[1].get_x() + bars2[1].get_width() / 2

    # Reduction annotation (no arrow)
    ax2.text(
        (x0 + x1) / 2, 15000,
        "99.7%\nreduction",
        ha="center", va="center",
        fontsize=10, fontweight="bold", color="#2c3e50",
    )

    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.grid(True, axis="y", alpha=0.3)

    fig.suptitle(
        "Production-Scale Routing on the AAP MCP Server (1,060 Tools)",
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
