"""anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 19  # number of histogram bins shared by every group
PAD = 5  # padding beyond the data range, in the units of the values

# Columns: set these to your table's column names
HEIGHT = "Height (cm)"  # role: values
AGE_GROUP = "Age group"  # role: group
FREQUENCY = "Frequency"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("heights.csv")
np.random.seed(42)
n_per_group = 200
group_names = ["Young Adults (18-25)", "Middle-Aged (40-50)", "Seniors (65+)"]
df = pd.DataFrame(
    {
        HEIGHT: np.concatenate(
            [
                np.random.normal(loc=172, scale=8, size=n_per_group),
                np.random.normal(loc=170, scale=9, size=n_per_group),
                np.random.normal(loc=166, scale=10, size=n_per_group),
            ]
        ),
        AGE_GROUP: np.repeat(group_names, n_per_group),
    }
)

# Plot: reads only df and the constants above
bin_edges = np.linspace(df[HEIGHT].min() - PAD, df[HEIGHT].max() + PAD, N_BINS + 1)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
title = "frequency-polygon-basic · python · matplotlib · anyplot.ai"

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, (group, rows) in enumerate(df.groupby(AGE_GROUP, sort=False)):
    counts, _ = np.histogram(rows[HEIGHT].dropna(), bins=bin_edges)

    # Extend to zero at both ends to close the polygon
    x_extended = np.concatenate([[bin_edges[0]], bin_centers, [bin_edges[-1]]])
    y_extended = np.concatenate([[0], counts, [0]])

    ax.plot(
        x_extended,
        y_extended,
        linewidth=2.5,
        color=IMPRINT_PALETTE[i],
        label=group,
        marker="o",
        markersize=4.5,
        markeredgecolor=PAGE_BG,
        markeredgewidth=0.6,
    )
    ax.fill(x_extended, y_extended, color=IMPRINT_PALETTE[i], alpha=0.15)

# Style
ax.set_xlabel(HEIGHT, fontsize=10, color=INK)
ax.set_ylabel(FREQUENCY, fontsize=10, color=INK)
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_ylim(bottom=0)

for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

leg = ax.legend(title=AGE_GROUP, fontsize=8, title_fontsize=8, loc="upper left", framealpha=0.95)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
