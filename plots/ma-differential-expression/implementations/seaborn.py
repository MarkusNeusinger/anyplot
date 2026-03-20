""" pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 94/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Seaborn theme and style
sns.set_theme(style="ticks", context="talk", font_scale=1.1)
palette = sns.color_palette("colorblind")
TEAL = palette[0]  # colorblind-safe blue/teal
GRAY = "#C0C0C0"
ACCENT = palette[2]  # green for LOESS
DARK = "#2C3E50"
THRESHOLD_COLOR = palette[4]  # muted purple for threshold lines

# Data - Simulated RNA-seq differential expression results (~15,000 genes)
np.random.seed(42)
n_genes = 15000

mean_expression = np.random.exponential(scale=3, size=n_genes) + 1
log_fold_change = np.random.normal(0, 0.5, n_genes)

# Add truly differentially expressed genes (~8% of genes)
n_de = int(n_genes * 0.08)
de_indices = np.random.choice(n_genes, n_de, replace=False)
log_fold_change[de_indices] += np.random.choice([-1, 1], n_de) * np.random.uniform(1.5, 4, n_de)

# Simulate p-values: DE genes get small p-values, others get uniform
p_values = np.ones(n_genes)
p_values[de_indices] = 10 ** (-np.random.uniform(2, 10, n_de))
p_values[~np.isin(np.arange(n_genes), de_indices)] = np.random.uniform(0.01, 1.0, n_genes - n_de)

significant = p_values < 0.05

# Categorize genes for seaborn hue mapping
status = np.where(
    ~significant,
    "Not significant",
    np.where(log_fold_change > 1, "Up-regulated", np.where(log_fold_change < -1, "Down-regulated", "Significant")),
)

# Gene names for top hits - spread across expression range for better storytelling
gene_names = [None] * n_genes
top_gene_labels = ["BRCA1", "TP53", "MYC", "EGFR", "VEGFA", "IL6"]
sig_de_mask = significant & (np.abs(log_fold_change) > 1)
sig_de_indices = np.where(sig_de_mask)[0]
sig_de_expr = mean_expression[sig_de_indices]
sig_de_abs_lfc = np.abs(log_fold_change[sig_de_indices])

# Use evenly-spaced expression bins across full range to spread labels
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

# Color palette for categories - colorblind-safe
status_palette = {
    "Not significant": GRAY,
    "Significant": sns.desaturate(TEAL, 0.6),
    "Up-regulated": TEAL,
    "Down-regulated": palette[3],  # red from colorblind palette
}

# Plot using seaborn's hue-based scatter
fig, ax = plt.subplots(figsize=(16, 9))

sns.scatterplot(
    data=df,
    x="Mean Expression (A)",
    y="Log₂ Fold Change (M)",
    hue="Status",
    hue_order=["Not significant", "Significant", "Up-regulated", "Down-regulated"],
    palette=status_palette,
    size="Status",
    sizes={"Not significant": 20, "Significant": 40, "Up-regulated": 55, "Down-regulated": 55},
    alpha=0.3,
    edgecolor="none",
    legend="full",
    ax=ax,
)

# Emphasize up/down-regulated with white edges via a second scatter layer
de_data = df[df["Status"].isin(["Up-regulated", "Down-regulated"])]
sns.scatterplot(
    data=de_data,
    x="Mean Expression (A)",
    y="Log₂ Fold Change (M)",
    hue="Status",
    hue_order=["Up-regulated", "Down-regulated"],
    palette={"Up-regulated": TEAL, "Down-regulated": palette[3]},
    s=55,
    alpha=0.6,
    edgecolor="white",
    linewidth=0.4,
    legend=False,
    ax=ax,
)

# Reference lines
ax.axhline(y=0, color=DARK, linewidth=2, alpha=0.5)
ax.axhline(y=1, color=THRESHOLD_COLOR, linewidth=1.5, linestyle="--", alpha=0.7)
ax.axhline(y=-1, color=THRESHOLD_COLOR, linewidth=1.5, linestyle="--", alpha=0.7)
ax.text(ax.get_xlim()[1] * 0.97, 1.12, "2-fold ↑", fontsize=12, color=THRESHOLD_COLOR, ha="right", fontstyle="italic")
ax.text(ax.get_xlim()[1] * 0.97, -1.35, "2-fold ↓", fontsize=12, color=THRESHOLD_COLOR, ha="right", fontstyle="italic")

# LOESS smoothing curve using seaborn regplot with lowess
sns.regplot(
    data=df,
    x="Mean Expression (A)",
    y="Log₂ Fold Change (M)",
    lowess=True,
    scatter=False,
    line_kws={"color": ACCENT, "linewidth": 3, "alpha": 0.85, "label": "LOESS trend"},
    ax=ax,
)

# Label top differentially expressed genes - spread across expression range
labeled = df[df["gene_name"].notna()].copy()
label_positions = []
for _, row in labeled.iterrows():
    x_val = row["Mean Expression (A)"]
    y_val = row["Log₂ Fold Change (M)"]
    # Place labels outward from the dense center: above for up-regulated, below for down
    y_off = -30 if y_val > 0 else 30
    x_off = 25 if x_val < df["Mean Expression (A)"].median() else -25
    # Avoid overlapping previously placed labels
    for px, py in label_positions:
        if abs(x_val - px) < 2 and abs(y_val - py) < 1:
            y_off = y_off + (35 if y_off > 0 else -35)
            break
    label_positions.append((x_val, y_val))
    ax.annotate(
        row["gene_name"],
        xy=(x_val, y_val),
        xytext=(x_off, y_off),
        textcoords="offset points",
        fontsize=13,
        fontweight="bold",
        color=DARK,
        arrowprops={"arrowstyle": "->", "color": DARK, "lw": 1.2, "connectionstyle": "arc3,rad=0.2"},
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": DARK, "alpha": 0.85, "linewidth": 0.8},
    )

# Style - use seaborn's despine
sns.despine(ax=ax)
ax.set_xlabel("Mean Expression (A)", fontsize=20)
ax.set_ylabel("Log₂ Fold Change (M)", fontsize=20)
ax.set_title("ma-differential-expression · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=15)
ax.tick_params(axis="both", labelsize=16)
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color="#888888")

# Refine legend with seaborn
sns.move_legend(ax, "upper right", fontsize=13, framealpha=0.92, title="Gene Status", title_fontsize=14)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
