"""anyplot.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Library setup
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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
PVAL_THRESHOLD = 1.3  # -log10(0.05)
FC_THRESHOLD = 1.0  # log2(2): a two-fold change
NOT_SIG, DOWN, UP = "Not significant", "Down-regulated", "Up-regulated"
STATUS_COLORS = {NOT_SIG: MUTED, DOWN: IMPRINT_PALETTE[2], UP: IMPRINT_PALETTE[4]}  # gray, blue, red

# Columns: set these to your table's column names
LOG2FC = "Log2 fold change"  # role: log2_fold_change
NEGLOG10P = "-Log10(p-value)"  # role: neg_log10_pvalue

# Data: replace this block with your own table, for example df = pd.read_csv("results.csv")
np.random.seed(42)
n_genes = 500
log2_fold_change = np.random.normal(0, 0.8, n_genes)
# Larger fold changes tend to have lower p-values, which gives the volcano shape
base_pvalues = 10 ** (-(np.abs(log2_fold_change) ** 1.5) * np.random.uniform(0.8, 1.5, n_genes))
base_pvalues = np.clip(base_pvalues, 1e-10, 1.0)
df = pd.DataFrame({LOG2FC: log2_fold_change, NEGLOG10P: -np.log10(base_pvalues)})

# Plot: reads only df and the constants above
significant = df[NEGLOG10P] >= PVAL_THRESHOLD
status = np.select(
    [significant & (df[LOG2FC] > FC_THRESHOLD), significant & (df[LOG2FC] < -FC_THRESHOLD)], [UP, DOWN], default=NOT_SIG
)
df = df.assign(Status=status)
# Draw significant features last so they sit on top of the gray mass
df = df.iloc[np.argsort(df["Status"] != NOT_SIG, kind="stable")]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.scatterplot(
    data=df,
    x=LOG2FC,
    y=NEGLOG10P,
    hue="Status",
    hue_order=[NOT_SIG, DOWN, UP],
    palette=STATUS_COLORS,
    s=40,
    alpha=0.6,
    edgecolor="none",
    ax=ax,
)

# Threshold lines
ax.axhline(PVAL_THRESHOLD, color=INK_SOFT, linestyle="--", linewidth=1, alpha=0.6)
ax.axvline(FC_THRESHOLD, color=INK_SOFT, linestyle="--", linewidth=1, alpha=0.6)
ax.axvline(-FC_THRESHOLD, color=INK_SOFT, linestyle="--", linewidth=1, alpha=0.6)

# Style
ax.set_title("volcano-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(LOG2FC, fontsize=10)
ax.set_ylabel(NEGLOG10P, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
sns.despine(ax=ax)
legend = ax.legend(title="Significance status", fontsize=8, title_fontsize=9, loc="upper center", framealpha=0.95)
legend.get_frame().set_facecolor(ELEVATED_BG)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
