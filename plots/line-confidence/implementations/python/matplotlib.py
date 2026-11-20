"""anyplot.ai
line-confidence: Line Plot with Confidence Interval
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os
import sys


sys.path.pop(0)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CONFIDENCE_LEVEL = 95  # percent covered by the band

# Columns: set these to your table's column names
DAYS = "Days ahead"  # role: x
TEMP = "Temperature (°C)"  # role: y
LOWER = "Lower bound (°C)"  # role: y_lower
UPPER = "Upper bound (°C)"  # role: y_upper

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
rng = np.random.default_rng(42)
n_days = 30
day = np.arange(1, n_days + 1)
mean_temp = 15 + 0.3 * day + 3 * np.sin(day / 5) + rng.normal(0, 0.5, n_days)
margin = 1.5 + 0.15 * day  # forecast uncertainty grows with the horizon
df = pd.DataFrame({DAYS: day, TEMP: mean_temp, LOWER: mean_temp - margin, UPPER: mean_temp + margin})

# Plot: reads only df and the constants above
title = "Temperature Forecast · line-confidence · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Band in a light tone of the line's color, semi-transparent so the grid shows through
ax.fill_between(
    df[DAYS],
    df[LOWER],
    df[UPPER],
    color=IMPRINT_PALETTE[0],
    alpha=0.25,
    linewidth=0,
    label=f"{CONFIDENCE_LEVEL}% confidence interval",
)
ax.plot(df[DAYS], df[TEMP], color=IMPRINT_PALETTE[0], linewidth=2.5, label="Forecast mean", zorder=3)

# Style
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.set_xlabel(DAYS, fontsize=10, color=INK)
ax.set_ylabel(TEMP, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.set_xlim(df[DAYS].min(), df[DAYS].max())

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(INK_SOFT)
    ax.spines[spine].set_linewidth(0.8)

ax.yaxis.grid(True, alpha=0.2, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

leg = ax.legend(fontsize=8, loc="upper left", framealpha=0.95)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
