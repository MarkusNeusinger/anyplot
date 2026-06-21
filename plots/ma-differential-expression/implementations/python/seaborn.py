""" anyplot.ai
ma-differential-expression: MA Plot for Differential Expression
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 88/100 | Updated: 2026-06-21
"""

import os
import sys


# Remove the script's own directory from sys.path so that sibling files
# (matplotlib.py, seaborn.py, etc.) don't shadow installed packages.
try:
    _here = os.path.realpath(os.path.dirname(__file__))
except NameError:
    _here = os.path.realpath(os.getcwd())
sys.path = [p for p in sys.path if p and os.path.realpath(p) != _here]

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ANYPLOT_AMBER = "#DDCC77"  # warning / caution (outside categorical pool)

# Semantic mapping: up=green (positive/gain), down=matte-red (loss/negative)
UP_COLOR = IMPRINT_PALETTE[0]  # #009E73 — first Imprint series, semantically "positive/up"
SIG_COLOR = IMPRINT_PALETTE[1]  # #C475FD lavender — significant but sub-threshold fold change
DOWN_COLOR = IMPRINT_PALETTE[4]  # #AE3030 matte red — semantic anchor for loss/negative
NSIG_COLOR = INK_MUTED  # theme-adaptive muted gray for background noise

LOESS_COLOR = IMPRINT_PALETTE[2]  # #4467A3 blue — trend overlay
THRESHOLD_COLOR = ANYPLOT_AMBER  # #DDCC77 — caution/threshold lines

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# --- Data ---
np.random.seed(42)
n_genes = 15000

mean_expression = np.random.exponential(scale=3, size=n_genes) + 1
log_fold_change = np.random.normal(0, 0.5, n_genes)

n_de = int(n_genes * 0.08)
de_indices = np.random.choice(n_genes, n_de, replace=False)
log_fold_change[de_indices] += np.random.choice([-1, 1], n_de) * np.random.uniform(1.5, 4, n_de)

p_values = np.ones(n_genes)
p_values[de_indices] = 10 ** (-np.random.uniform(2, 10, n_de))
p_values[~np.isin(np.arange(n_genes), de_indices)] = np.random.uniform(0.01, 1.0, n_genes - n_de)

significant = p_values < 0.05

status = np.where(
    ~significant,
    "Not significant",
    np.where(log_fold_change > 1, "Up-regulated", np.where(log_fold_change < -1, "Down-regulated", "Significant")),
)

# Gene names spread across expression range for spatial storytelling
gene_names = [None] * n_genes
top_gene_labels = ["BRCA1", "TP53", "MYC", "EGFR", "VEGFA", "IL6"]
sig_de_mask = significant & (np.abs(log_fold_change) > 1)
sig_de_indices = np.where(sig_de_mask)[0]
sig_de_expr = mean_expression[sig_de_indices]
sig_de_abs_lfc = np.abs(log_fold_change[sig_de_indices])

expr_min, expr_max = sig_de_expr.min(), sig_de_expr.max()
n_labels = len(top_gene_labels)
expr_edges = np.linspace(expr_min, expr_max + 0.01, n_labels + 1)
top_sig = []
for b in range(n_labels):
    in_bin = (sig_de_expr >= expr_edges[b]) & (sig_de_expr < expr_edges[b + 1])
    if not np.any(in_bin):
        continue
    bin_idx = np.where(in_bin)[0]
    best = bin_idx[np.argmax(sig_de_abs_lfc[bin_idx])]
    top_sig.append(sig_de_indices[best])

for i, idx in enumerate(top_sig[:n_labels]):
    gene_names[idx] = top_gene_labels[i]

df = pd.DataFrame(
    {
        "Mean Expression (A)": mean_expression,
        "Log₂ Fold Change (M)": log_fold_change,
        "Status": pd.Categorical(
            status, categories=["Not significant", "Significant", "Up-regulated", "Down-regulated"]
        ),
        "gene_name": gene_names,
    }
)

status_palette = {
    "Not significant": NSIG_COLOR,
    "Significant": SIG_COLOR,
    "Up-regulated": UP_COLOR,
    "Down-regulated": DOWN_COLOR,
}

# --- Plot ---
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
fig.patch.set_facecolor(PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Background layer: all 15k genes, small + transparent for density
sns.scatterplot(
    data=df,
    x="Mean Expression (A)",
    y="Log₂ Fold Change (M)",
    hue="Status",
    hue_order=["Not significant", "Significant", "Up-regulated", "Down-regulated"],
    palette=status_palette,
    size="Status",
    sizes={"Not significant": 6, "Significant": 14, "Up-regulated": 20, "Down-regulated": 20},
    alpha=0.3,
    edgecolor="none",
    legend="full",
    ax=ax,
)

# Emphasis layer: DE genes with subtle edge for definition
de_data = df[df["Status"].isin(["Up-regulated", "Down-regulated"])]
sns.scatterplot(
    data=de_data,
    x="Mean Expression (A)",
    y="Log₂ Fold Change (M)",
    hue="Status",
    hue_order=["Up-regulated", "Down-regulated"],
    palette={"Up-regulated": UP_COLOR, "Down-regulated": DOWN_COLOR},
    s=20,
    alpha=0.6,
    edgecolor=ELEVATED_BG,
    linewidth=0.3,
    legend=False,
    ax=ax,
)

# Reference lines
ax.axhline(y=0, color=INK_SOFT, linewidth=1.5, alpha=0.6, zorder=1)
ax.axhline(y=1, color=THRESHOLD_COLOR, linewidth=1.2, linestyle="--", alpha=0.85, zorder=1)
ax.axhline(y=-1, color=THRESHOLD_COLOR, linewidth=1.2, linestyle="--", alpha=0.85, zorder=1)

# Threshold annotations
xlim = ax.get_xlim()
x_lbl = xlim[1] * 0.97
ax.text(x_lbl, 1.10, "2-fold ↑", fontsize=7, color=THRESHOLD_COLOR, ha="right", fontstyle="italic")
ax.text(x_lbl, -1.24, "2-fold ↓", fontsize=7, color=THRESHOLD_COLOR, ha="right", fontstyle="italic")

# LOESS smoothing curve to reveal expression-dependent bias
sns.regplot(
    data=df,
    x="Mean Expression (A)",
    y="Log₂ Fold Change (M)",
    lowess=True,
    scatter=False,
    line_kws={"color": LOESS_COLOR, "linewidth": 2.0, "alpha": 0.85, "label": "LOESS trend"},
    ax=ax,
)

# Gene labels spread across expression range
labeled = df[df["gene_name"].notna()].copy()
label_positions = []
for _, row in labeled.iterrows():
    x_val = row["Mean Expression (A)"]
    y_val = row["Log₂ Fold Change (M)"]
    y_off = -22 if y_val > 0 else 22
    x_off = 18 if x_val < df["Mean Expression (A)"].median() else -18
    for px, py in label_positions:
        if abs(x_val - px) < 2 and abs(y_val - py) < 1:
            y_off = y_off + (28 if y_off > 0 else -28)
            break
    label_positions.append((x_val, y_val))
    ax.annotate(
        row["gene_name"],
        xy=(x_val, y_val),
        xytext=(x_off, y_off),
        textcoords="offset points",
        fontsize=7,
        fontweight="bold",
        color=INK,
        arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 0.9, "connectionstyle": "arc3,rad=0.2"},
        bbox={
            "boxstyle": "round,pad=0.2",
            "facecolor": ELEVATED_BG,
            "edgecolor": INK_SOFT,
            "alpha": 0.92,
            "linewidth": 0.6,
        },
    )

# Style
sns.despine(ax=ax)
ax.set_xlabel("Mean Expression (A)", fontsize=10, color=INK)
ax.set_ylabel("Log₂ Fold Change (M)", fontsize=10, color=INK)
ax.set_title(
    "ma-differential-expression · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", pad=10, color=INK
)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)

sns.move_legend(ax, "upper right", fontsize=8, framealpha=0.92, title="Gene Status", title_fontsize=8)

fig.subplots_adjust(left=0.10, right=0.97, top=0.91, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
