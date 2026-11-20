"""anyplot.ai
scatter-matrix: Scatter Plot Matrix
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-09
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
VARIABLES = ["Annual Return (%)", "Volatility (%)", "P/E Ratio", "Dividend Yield (%)"]  # role: variables
SEGMENT = "Segment"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("stocks.csv")
np.random.seed(42)
n_per_segment = 40
df = pd.DataFrame(
    {
        VARIABLES[0]: np.concatenate(
            [
                np.random.exponential(8, n_per_segment) + 15,  # Growth: high return
                np.random.exponential(5, n_per_segment) + 8,  # Value: moderate return
                np.random.exponential(4, n_per_segment) + 5,  # Dividend: steady return
            ]
        ),
        VARIABLES[1]: np.concatenate(
            [
                np.random.exponential(3, n_per_segment) + 18,  # Growth: high volatility
                np.random.exponential(2, n_per_segment) + 12,  # Value: medium volatility
                np.random.exponential(1.5, n_per_segment) + 8,  # Dividend: low volatility
            ]
        ),
        VARIABLES[2]: np.concatenate(
            [
                np.random.exponential(5, n_per_segment) + 22,  # Growth: high multiples
                np.random.exponential(3, n_per_segment) + 12,  # Value: low multiples
                np.random.exponential(2, n_per_segment) + 16,  # Dividend: moderate multiples
            ]
        ),
        VARIABLES[3]: np.concatenate(
            [
                np.random.exponential(0.4, n_per_segment) + 0.5,  # Growth: low yield
                np.random.exponential(0.6, n_per_segment) + 1.5,  # Value: moderate yield
                np.random.exponential(0.8, n_per_segment) + 3.5,  # Dividend: high yield
            ]
        ),
        SEGMENT: np.repeat(["Growth", "Value", "Dividend"], n_per_segment),
    }
)

# Plot
sns.set_theme(
    style="whitegrid",
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
        "grid.linewidth": 0.5,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

n_groups = df[SEGMENT].nunique()

g = sns.pairplot(
    df,
    vars=VARIABLES,
    hue=SEGMENT,
    palette=IMPRINT_PALETTE[:n_groups],
    diag_kind="kde",
    plot_kws={"s": 14, "alpha": 0.7, "edgecolor": PAGE_BG, "linewidth": 0.3},
    diag_kws={"linewidth": 1.2, "fill": True, "alpha": 0.35, "common_norm": False},
    height=1.5,
    aspect=1.0,
)

# Exact square canvas: 6 x 6 in at 400 dpi = 2400 x 2400 px
g.figure.set_size_inches(6, 6)
g.figure.set_dpi(400)

for ax in g.axes.flatten():
    ax.tick_params(axis="both", labelsize=5.5, length=2, pad=1)
    ax.set_xlabel(ax.get_xlabel(), fontsize=7)
    ax.set_ylabel(ax.get_ylabel(), fontsize=7)
    ax.xaxis.set_major_locator(plt.MaxNLocator(3))
    ax.yaxis.set_major_locator(plt.MaxNLocator(3))

# One legend for the whole grid, centered below the matrix
sns.move_legend(
    g,
    "lower center",
    bbox_to_anchor=(0.5, 0.0),
    ncol=n_groups,
    title=SEGMENT,
    title_fontsize=8,
    fontsize=8,
    frameon=True,
    markerscale=1.2,
)

g.figure.suptitle("scatter-matrix · python · seaborn · anyplot.ai", fontsize=11, fontweight="medium", y=0.985)
g.figure.subplots_adjust(left=0.1, right=0.98, top=0.93, bottom=0.14, wspace=0.12, hspace=0.12)

g.figure.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
