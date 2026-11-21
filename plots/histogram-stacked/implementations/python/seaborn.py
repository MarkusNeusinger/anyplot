"""anyplot.ai
histogram-stacked: Stacked Histogram
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

# Columns: set these to your table's column names
SCORE = "Exam score (points)"  # role: values
CLASS = "Class"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(7)
class_specs = {"Class 10A": (74, 9, 140), "Class 10B": (66, 11, 170), "Class 10C": (82, 8, 110)}
df = pd.concat(
    [
        pd.DataFrame({SCORE: np.clip(rng.normal(mean, sd, n), 0, 100), CLASS: name})
        for name, (mean, sd, n) in class_specs.items()
    ],
    ignore_index=True,
)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Stack order: largest group at the bottom, one order kept in every bin
groups = df[CLASS].value_counts().index.tolist()

sns.histplot(
    data=df,
    x=SCORE,
    hue=CLASS,
    hue_order=groups,
    multiple="stack",
    binwidth=4,
    binrange=(0, 100),
    palette=IMPRINT_PALETTE[: len(groups)],
    edgecolor=PAGE_BG,
    linewidth=0.6,
    alpha=1.0,
    ax=ax,
)

# Style
ax.set_xlabel(SCORE, fontsize=10)
ax.set_ylabel("Number of students", fontsize=10)
ax.set_title("histogram-stacked · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium")
ax.tick_params(axis="both", labelsize=8)
ax.yaxis.grid(True, linewidth=0.8)
ax.set_axisbelow(True)
sns.despine(ax=ax)

legend = ax.get_legend()
legend.set_title(CLASS)
legend.get_title().set_fontsize(9)
for text in legend.get_texts():
    text.set_fontsize(8)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
