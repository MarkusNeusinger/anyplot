""" anyplot.ai
line-markers: Line Plot with Markers
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "h"]  # one marker shape per series, in palette order

# Columns: set these to your table's column names
DAY = "Day"  # role: x
STATION = "Weather station"  # role: series
TEMPERATURE = ["Temperature (°C)"]  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("temperatures.csv")
# Daily mean temperature at three weather stations over 14 days
np.random.seed(42)
days = np.arange(1, 15)
coastal = 18 + np.cumsum(np.random.randn(14) * 0.8)
inland = 15 + np.cumsum(np.random.randn(14) * 1.2)
mountain = 10 + np.cumsum(np.random.randn(14) * 1.0)
df = pd.DataFrame(
    {
        DAY: np.tile(days, 3),
        STATION: np.repeat(["Coastal", "Inland", "Mountain"], 14),
        TEMPERATURE[0]: np.concatenate([coastal, inland, mountain]),
    }
)

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, layout="constrained")
ax.set_facecolor(PAGE_BG)
for i, (station, rows) in enumerate(df.groupby(STATION, sort=False)):
    rows = rows.sort_values(DAY)
    ax.plot(
        rows[DAY],
        rows[TEMPERATURE[0]],
        color=IMPRINT_PALETTE[i],
        linewidth=2.2,
        marker=MARKERS[i],
        markersize=8,
        markeredgecolor=PAGE_BG,
        markeredgewidth=1.2,
        label=station,
    )

# Style
ax.set_title("line-markers · python · matplotlib · anyplot.ai", fontsize=12, fontweight="bold", color=INK)
ax.set_xlabel(DAY, fontsize=10, color=INK)
ax.set_ylabel(TEMPERATURE[0], fontsize=10, color=INK)
ax.xaxis.set_major_locator(MaxNLocator(nbins=16, integer=True))
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, color=INK, linewidth=0.6)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
legend = ax.legend(title=STATION, fontsize=8, title_fontsize=8, loc="best", frameon=True)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
legend.get_frame().set_linewidth(0.6)
legend.get_title().set_color(INK)
plt.setp(legend.get_texts(), color=INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
