"""anyplot.ai
range-interval: Range Interval Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-18
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: position 1 is the brand green used for the single series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Columns: set these to your table's column names
MONTH = "Month"  # role: category
LOW = "Minimum temperature (°C)"  # role: min_value
HIGH = "Maximum temperature (°C)"  # role: max_value

# Data: replace this block with your own table, for example df = pd.read_csv("ranges.csv")
# Monthly temperature ranges (low/high) for a coastal city, warmer in summer
np.random.seed(42)
base_temps = np.array([5, 7, 11, 15, 19, 23, 26, 25, 21, 16, 10, 6])
variation = np.random.uniform(3, 7, size=12)
low = base_temps - variation / 2 + np.random.uniform(-2, 2, size=12)
high = base_temps + variation / 2 + np.random.uniform(2, 5, size=12)
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        LOW: np.round(low, 1),
        HIGH: np.round(high, 1),
    }
)

# Plot: reads only df and the constants above
x = np.arange(len(df))
lows = df[LOW].to_numpy()
highs = df[HIGH].to_numpy()
midpoints = (lows + highs) / 2
pad = (np.nanmax(highs) - np.nanmin(lows)) * 0.12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Floating range bars: bottom at the minimum, height equal to the span
ax.bar(x, highs - lows, bottom=lows, width=0.6, color=BRAND, alpha=0.7, edgecolor=INK_SOFT, linewidth=1.0)

# Markers exactly on the two bounds, then the subordinate midpoint
ax.scatter(x, lows, s=70, color=BRAND, zorder=5, marker="v", linewidths=1.0, edgecolors=INK_SOFT, label="Minimum")
ax.scatter(x, highs, s=70, color=BRAND, zorder=5, marker="^", linewidths=1.0, edgecolors=INK_SOFT, label="Maximum")
ax.scatter(
    x, midpoints, s=40, color=INK_MUTED, zorder=6, marker="o", edgecolors=INK_SOFT, linewidths=0.8, label="Midpoint"
)

# Bound values next to each marker
for xi, lo, hi in zip(x, lows, highs, strict=True):
    ax.annotate(
        f"{lo:.0f}°", (xi, lo), textcoords="offset points", xytext=(0, -11), ha="center", fontsize=7, color=INK_SOFT
    )
    ax.annotate(
        f"{hi:.0f}°", (xi, hi), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=7, color=INK_SOFT
    )

# Style
ax.set_title("range-interval · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(MONTH, fontsize=10, color=INK)
ax.set_ylabel("Temperature (°C)", fontsize=10, color=INK)
ax.set_xticks(x, df[MONTH])
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.set_ylim(np.nanmin(lows) - pad, np.nanmax(highs) + pad)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

ax.grid(True, axis="y", alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

legend = ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
plt.setp(legend.get_texts(), color=INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
