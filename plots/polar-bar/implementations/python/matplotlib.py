"""anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-13
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, MaxNLocator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per stacked category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DIRECTION = "Wind direction"  # role: direction
SPEED_CLASS = "Wind speed"  # role: extra
FREQUENCY = "Frequency (%)"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
speed_classes = {
    "Calm (0-5 m/s)": [12, 8, 15, 6, 18, 10, 22, 14],
    "Moderate (5-10 m/s)": [8, 5, 10, 4, 12, 7, 15, 9],
    "Strong (>10 m/s)": [4, 2, 5, 2, 6, 3, 8, 4],
}
df = pd.DataFrame(
    {
        DIRECTION: directions * len(speed_classes),
        SPEED_CLASS: [name for name in speed_classes for _ in directions],
        FREQUENCY: [value for values in speed_classes.values() for value in values],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=DIRECTION, columns=SPEED_CLASS, values=FREQUENCY, sort=False)
n_directions = len(table.index)
angles = np.linspace(0, 2 * np.pi, n_directions, endpoint=False)
width = 2 * np.pi / n_directions * 0.8  # slightly less than a full sector for visual separation
totals = table.sum(axis=1)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, subplot_kw={"projection": "polar"}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

bottom = np.zeros(n_directions)
for i, speed in enumerate(table.columns):
    values = table[speed].fillna(0).to_numpy()
    ax.bar(
        angles,
        values,
        width=width,
        bottom=bottom,
        color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        edgecolor=INK_SOFT,
        linewidth=1.0,
        label=speed,
        alpha=0.9,
    )
    bottom = bottom + values

# Compass orientation: first direction at the top, clockwise
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_xticks(angles)
ax.set_xticklabels(table.index, fontsize=9, fontweight="bold", color=INK)

# Radial axis starts at zero; tick values come from the data range
ax.set_ylim(0, totals.max() * 1.1)
ax.yaxis.set_major_locator(MaxNLocator(nbins=4, prune="upper"))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.tick_params(axis="y", labelsize=7, labelcolor=INK_SOFT)
ax.set_rlabel_position(45)

ax.grid(True, alpha=0.15, linestyle="-", linewidth=0.8, color=INK_SOFT)
ax.spines["polar"].set_visible(False)

ax.set_title("polar-bar · python · matplotlib · anyplot.ai", fontsize=12, pad=18, fontweight="bold", color=INK)

leg = ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=7, title=SPEED_CLASS, title_fontsize=8)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)
plt.setp(leg.get_title(), color=INK)

fig.subplots_adjust(left=0.06, right=0.72, top=0.9, bottom=0.06)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
