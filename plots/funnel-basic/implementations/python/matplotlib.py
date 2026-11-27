""" anyplot.ai
funnel-basic: Basic Funnel Chart
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Imprint palette: all eight positions, one per stage in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
STAGE = "Stage"  # role: stage
VISITORS = "Visitors"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("funnel.csv")
df = pd.DataFrame(
    {STAGE: ["Awareness", "Interest", "Consideration", "Intent", "Purchase"], VISITORS: [1000, 600, 400, 200, 100]}
)

# Plot: reads only df and the constants above
n = len(df)
values = df[VISITORS].to_numpy(dtype=float)
widths = values / values[0]
y_edges = np.linspace(n, 0, n + 1)
gap = 0.06

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i in range(n):
    y_top = y_edges[i] - gap / 2
    y_bot = y_edges[i + 1] + gap / 2
    w_top = widths[i]
    # Flat bottom on the last segment: it ends at its own data width
    w_bot = widths[i + 1] if i + 1 < n else widths[i]
    ax.fill_betweenx(
        [y_top, y_bot],
        [-w_top / 2, -w_bot / 2],
        [w_top / 2, w_bot / 2],
        facecolor=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        edgecolor=PAGE_BG,
        linewidth=1,
    )
    y_mid = (y_top + y_bot) / 2
    ax.text(
        0,
        y_mid,
        f"{values[i]:,.0f}\n{widths[i]:.0%}",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color="white",
        linespacing=1.3,
    )
    # Stage name in a column left of the widest segment
    ax.text(-0.56, y_mid, df[STAGE].iloc[i], ha="right", va="center", fontsize=10, color=INK)

# Style
ax.set_xlim(-0.95, 0.6)
ax.set_ylim(-0.1, n + 0.1)
ax.axis("off")
ax.set_title("funnel-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
fig.subplots_adjust(left=0.03, right=0.97, top=0.9, bottom=0.04)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
