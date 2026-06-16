""" anyplot.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-16
"""

import os

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=365, freq="D")
base_price = 150
returns = np.random.randn(365) * 0.015
prices = base_price * np.cumprod(1 + returns)

# Event dates and labels
events = [
    (pd.Timestamp("2024-02-15"), "Q4 2023\nEarnings"),
    (pd.Timestamp("2024-05-10"), "Q1 2024\nEarnings"),
    (pd.Timestamp("2024-07-22"), "Product\nLaunch"),
    (pd.Timestamp("2024-08-08"), "Q2 2024\nEarnings"),
    (pd.Timestamp("2024-11-14"), "Q3 2024\nEarnings"),
]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Main line in brand color
ax.plot(dates, prices, linewidth=3, color=BRAND, label="Stock Price", zorder=2)

# Event markers with alternating heights
event_color = "#C475FD" if THEME == "light" else "#2ABCCD"
heights = [0.85, 0.70, 0.85, 0.70, 0.85]

for i, (event_date, event_label) in enumerate(events):
    # Vertical dashed line for event
    ax.axvline(x=event_date, color=event_color, linestyle="--", linewidth=2.5, alpha=0.7, zorder=1)

    # Text annotation with FancyBboxPatch-style box
    y_pos = ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * heights[i]
    ax.annotate(
        event_label,
        xy=(event_date, prices[dates.get_loc(event_date)]),
        xytext=(event_date, y_pos),
        fontsize=14,
        ha="center",
        va="bottom",
        color=INK,
        bbox={"boxstyle": "round,pad=0.5", "facecolor": ELEVATED_BG, "edgecolor": event_color, "linewidth": 1.5, "alpha": 0.95},
        arrowprops={"arrowstyle": "->", "color": event_color, "lw": 1.5, "alpha": 0.7},
    )

# Styling
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Price (USD)", fontsize=20, color=INK)
ax.set_title("line-annotated-events · matplotlib · anyplot.ai", fontsize=24, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)

# Grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK_SOFT)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
    ax.spines[s].set_linewidth(1.2)

# Legend with proper Line2D proxy for event marker
event_line = mlines.Line2D([], [], color=event_color, linestyle="--", linewidth=2.5, label="Event Marker", alpha=0.7)
ax.legend(
    handles=[ax.get_lines()[0], event_line],
    fontsize=16,
    loc="upper left",
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    framealpha=0.95,
)

# Format x-axis for date readability
fig.autofmt_xdate(rotation=30, ha="right")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
