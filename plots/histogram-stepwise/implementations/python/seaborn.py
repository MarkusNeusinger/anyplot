"""anyplot.ai
histogram-stepwise: Step Histogram
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
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

# Constants
N_BINS = 30  # shared bin count; seaborn uses common edges across the groups

# Columns: set these to your table's column names
VALUES = ["Response time (ms)"]  # role: values
SERVICE = "Service"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
rng = np.random.default_rng(42)
df = pd.DataFrame(
    {
        VALUES[0]: np.concatenate([rng.exponential(scale=50, size=500) + 20, rng.exponential(scale=80, size=500) + 40]),
        SERVICE: ["Service A"] * 500 + ["Service B"] * 500,
    }
)

# Plot: reads only df and the constants above
n_groups = df[SERVICE].nunique()

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.histplot(
    data=df,
    x=VALUES[0],
    hue=SERVICE,
    bins=N_BINS,
    element="step",
    fill=False,
    palette=IMPRINT_PALETTE[:n_groups],
    linewidth=1.8,
    ax=ax,
)

# Style
ax.set_title("histogram-stepwise · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(VALUES[0], fontsize=10)
ax.set_ylabel("Count", fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.set_ylim(bottom=0)
ax.yaxis.grid(True, linewidth=0.6)
ax.set_axisbelow(True)
sns.despine(ax=ax)
sns.move_legend(ax, "upper right", title=None, fontsize=8, frameon=True, framealpha=0.95)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
