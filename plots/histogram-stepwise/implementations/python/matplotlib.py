"""anyplot.ai
histogram-stepwise: Step Histogram
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
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
LINE_STYLES = ["-", "--", ":", "-."]  # outlines told apart by style as well as color
N_BINS = 24

# Columns: set these to your table's column names
VALUES = ["Brown trout", "Rainbow trout"]  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("fish.csv")
rng = np.random.default_rng(42)
df = pd.DataFrame({VALUES[0]: rng.normal(34, 4.5, 400), VALUES[1]: rng.gamma(shape=9, scale=3.2, size=400) + 8})

# Plot: reads only df and the constants above
edges = np.histogram_bin_edges(np.concatenate([df[c].dropna() for c in VALUES]), bins=N_BINS)
title = "histogram-stepwise · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
for i, column in enumerate(VALUES):
    ax.hist(
        df[column].dropna(),
        bins=edges,
        histtype="step",
        linewidth=2.5,
        color=IMPRINT_PALETTE[i],
        linestyle=LINE_STYLES[i % len(LINE_STYLES)],
        label=column,
    )

# Style
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.set_xlabel("Body length (cm)", fontsize=10, color=INK)
ax.set_ylabel("Number of fish", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.set_ylim(bottom=0)
ax.margins(x=0.02)

for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

leg = ax.legend(fontsize=8, loc="upper right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
