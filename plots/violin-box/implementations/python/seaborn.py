"""anyplot.ai
violin-box: Violin Plot with Embedded Box Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-12
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

# Library setup: seaborn theme with theme-adaptive chrome
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

# Columns: set these to your table's column names
BATCH = "Manufacturing Batch"  # role: group
SCORE = "Quality Score (0-100)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
n_per_batch = 120
batch_a = np.random.normal(75, 8, n_per_batch)  # roughly normal
batch_b = np.concatenate(
    [np.random.normal(60, 5, n_per_batch // 2), np.random.normal(80, 5, n_per_batch // 2)]
)  # bimodal
batch_c = np.random.exponential(10, n_per_batch) + 50  # right-skewed
batch_d = 95 - np.random.exponential(10, n_per_batch)  # left-skewed
df = pd.DataFrame(
    {
        BATCH: np.repeat(["Batch A", "Batch B", "Batch C", "Batch D"], n_per_batch),
        SCORE: np.concatenate([batch_a, batch_b, batch_c, batch_d]),
    }
)

# Plot: reads only df and the constants above
n_groups = df[BATCH].nunique()
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

sns.violinplot(
    data=df,
    x=BATCH,
    y=SCORE,
    hue=BATCH,
    palette=IMPRINT_PALETTE[:n_groups],
    inner="box",
    inner_kws={"box_width": 4, "whis_width": 1.2, "color": INK},
    cut=0,
    linewidth=1.0,
    linecolor=INK_SOFT,
    saturation=0.9,
    legend=False,
    ax=ax,
)

# Style
ax.set_title("violin-box · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", pad=10)
ax.set_xlabel(BATCH, fontsize=10)
ax.set_ylabel(SCORE, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.set_axisbelow(True)
pad = 0.05 * (df[SCORE].max() - df[SCORE].min())
ax.set_ylim(df[SCORE].min() - pad, df[SCORE].max() + pad)
sns.despine(ax=ax)

fig.subplots_adjust(left=0.09, right=0.97, top=0.9, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
