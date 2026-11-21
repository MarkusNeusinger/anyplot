""" anyplot.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"  # Imprint "muted" anchor

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_DOWN = IMPRINT_PALETTE[2]  # blue: down-regulated
COLOR_UP = IMPRINT_PALETTE[4]  # matte red: up-regulated
COLOR_NONSIG = MUTED  # gray: not significant

# Constants
PVALUE_THRESHOLD = 1.3  # -log10(0.05)
FC_THRESHOLD = 1.0  # log2(2): a 2-fold change
N_LABELS = 5  # top features named per direction

# Columns: set these to your table's column names
LOG2_FC = "Log₂ fold change"  # role: log2_fold_change
NEG_LOG10_P = "-Log₁₀ (p-value)"  # role: neg_log10_pvalue
GENE = "Gene"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("results.csv")
np.random.seed(42)
n_genes = 2000
fold_change = np.random.normal(0, 1.5, n_genes)
base_p = np.clip(np.random.exponential(0.3, n_genes), 1e-50, 1.0)
# Larger fold changes are more likely to be significant
p_values = np.clip(base_p * np.exp(-np.abs(fold_change) / 3 * 5), 1e-50, 1.0)
df = pd.DataFrame({LOG2_FC: fold_change, NEG_LOG10_P: -np.log10(p_values), GENE: [f"Gene_{i}" for i in range(n_genes)]})

# Plot: reads only df and the constants above
significant = df[NEG_LOG10_P] > PVALUE_THRESHOLD
is_up = significant & (df[LOG2_FC] > FC_THRESHOLD)
is_down = significant & (df[LOG2_FC] < -FC_THRESHOLD)
groups = [
    ("Not significant", ~is_up & ~is_down, COLOR_NONSIG, 14, 0.5),
    ("Down-regulated", is_down, COLOR_DOWN, 22, 0.8),
    ("Up-regulated", is_up, COLOR_UP, 22, 0.8),
]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for name, mask, color, size, alpha in groups:
    ax.scatter(
        df.loc[mask, LOG2_FC],
        df.loc[mask, NEG_LOG10_P],
        c=color,
        s=size,
        alpha=alpha,
        label=name,
        edgecolors="none",
        zorder=2,
    )

# Threshold lines
ax.axhline(PVALUE_THRESHOLD, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.7, zorder=3)
for sign in (-1, 1):
    ax.axvline(sign * FC_THRESHOLD, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.7, zorder=3)

# Name the strongest features of each direction
for mask, ha, dx in ((is_up, "left", 3), (is_down, "right", -3)):
    hits = df[mask]
    score = hits[NEG_LOG10_P] + hits[LOG2_FC].abs()
    for k, (_, row) in enumerate(hits.loc[score.nlargest(N_LABELS).index].sort_values(LOG2_FC).iterrows()):
        ax.annotate(
            row[GENE],
            (row[LOG2_FC], row[NEG_LOG10_P]),
            fontsize=7,
            ha=ha,
            va="bottom",
            xytext=(dx, 3 + 9 * (k % 3)),
            textcoords="offset points",
            color=INK,
        )

# Style
ax.set_xlabel(LOG2_FC, fontsize=10, color=INK)
ax.set_ylabel(NEG_LOG10_P, fontsize=10, color=INK)
ax.set_title("volcano-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=8, loc="lower right", framealpha=0.95)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
for text in leg.get_texts():
    text.set_color(INK_SOFT)

x_max = df[LOG2_FC].abs().max() * 1.25
ax.set_xlim(-x_max, x_max)
ax.set_ylim(0, df[NEG_LOG10_P].max() * 1.1)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
