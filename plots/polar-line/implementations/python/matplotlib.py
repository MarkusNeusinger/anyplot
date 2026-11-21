"""anyplot.ai
polar-line: Polar Line Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import os
import sys


# Remove current directory from sys.path to avoid import conflict with matplotlib.py
sys.path = [p for p in sys.path if os.path.abspath(p) != os.getcwd()]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter, MaxNLocator  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: theta
SERIES = ["Summer", "Winter"]  # role: radius

# Data: replace this block with your own table, for example df = pd.read_csv("temperatures.csv")
rng = np.random.RandomState(42)
hours = np.arange(24)
phase = 2 * np.pi * hours / 24
df = pd.DataFrame(
    {
        HOUR: hours,
        SERIES[0]: 20 + 8 * np.sin(phase - np.pi / 2) + rng.randn(24) * 0.5,
        SERIES[1]: 5 + 5 * np.sin(phase - np.pi / 2) + rng.randn(24) * 0.5,
    }
)

# Plot: reads only df and the constants above
HOURS_PER_DAY = 24  # the angular axis is a full day
r_top = np.ceil(df[SERIES].max().max() / 5) * 5 + 5

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, subplot_kw={"projection": "polar"}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

table = df.sort_values(HOUR)
theta = 2 * np.pi * table[HOUR].to_numpy() / HOURS_PER_DAY
for i, name in enumerate(SERIES):
    radius = table[name].to_numpy()
    # Close the loop: the day is cyclic, so the last hour joins the first
    ax.plot(
        np.append(theta, theta[0]),
        np.append(radius, radius[0]),
        linewidth=2,
        color=IMPRINT_PALETTE[i],
        label=name,
        marker="o",
        markersize=4.5,
    )

# Angular axis: hours of day
tick_hours = np.arange(0, HOURS_PER_DAY, 3)
ax.set_xticks(2 * np.pi * tick_hours / HOURS_PER_DAY)
ax.set_xticklabels([f"{h}:00" for h in tick_hours], fontsize=9, color=INK_SOFT)

# Radial axis: temperature
ax.set_ylim(0, r_top)
ax.yaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2, 5, 10]))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}°C"))
ax.tick_params(axis="y", labelsize=8, labelcolor=INK_SOFT)
ax.set_rlabel_position(45)

# Style
ax.set_title("polar-line · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=24)
ax.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.spines["polar"].set_color(INK_SOFT)

leg = ax.legend(loc="upper left", bbox_to_anchor=(0.98, 0.98), fontsize=9)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.5)
for text in leg.get_texts():
    text.set_color(INK_SOFT)

fig.subplots_adjust(left=0.08, right=0.8, top=0.88, bottom=0.08)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
