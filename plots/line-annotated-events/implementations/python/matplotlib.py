"""anyplot.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-16
"""

import os

import matplotlib.dates as mdates
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

# Imprint palette: position 1 for the series, position 2 for the event markers
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
PRICE = "Price (USD)"  # role: value
EVENT_DATE = "Event date"  # role: event_date
EVENT_LABEL = "Event"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv").
# Event columns are filled only on the rows of the event dates and left empty elsewhere.
np.random.seed(42)
days = pd.date_range("2024-01-01", periods=365, freq="D")
closing = 150 * np.cumprod(1 + np.random.randn(365) * 0.015)
event_names = {
    "2024-02-15": "Q4 2023\nEarnings",
    "2024-05-10": "Q1 2024\nEarnings",
    "2024-07-22": "Product\nLaunch",
    "2024-08-08": "Q2 2024\nEarnings",
    "2024-11-14": "Q3 2024\nEarnings",
}
df = pd.DataFrame({DATE: days, PRICE: closing})
df[EVENT_LABEL] = days.strftime("%Y-%m-%d").map(event_names)
df[EVENT_DATE] = df[DATE].where(df[EVENT_LABEL].notna())

# Plot: reads only df and the constants above
events = df.dropna(subset=[EVENT_LABEL]).reset_index(drop=True)
low, high = df[PRICE].min(), df[PRICE].max()
LABEL_LEVELS = (0.88, 0.74)  # axes-fraction heights, alternated so neighbouring labels stay apart
marker_color = IMPRINT_PALETTE[1]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.plot(df[DATE], df[PRICE], linewidth=2.5, color=IMPRINT_PALETTE[0], label="Stock price", zorder=2)
ax.set_ylim(low - (high - low) * 0.05, high + (high - low) * 0.45)

for i, row in events.iterrows():
    ax.axvline(row[EVENT_DATE], color=marker_color, linestyle="--", linewidth=1.5, alpha=0.8, zorder=1)
    ax.annotate(
        row[EVENT_LABEL],
        xy=(row[EVENT_DATE], row[PRICE]),
        xycoords="data",
        xytext=(row[EVENT_DATE], LABEL_LEVELS[i % len(LABEL_LEVELS)]),
        textcoords=ax.get_xaxis_transform(),
        fontsize=8,
        ha="center",
        va="bottom",
        color=INK,
        bbox={"boxstyle": "round,pad=0.4", "facecolor": ELEVATED_BG, "edgecolor": marker_color, "linewidth": 1.0},
        arrowprops={"arrowstyle": "->", "color": marker_color, "lw": 1.0},
        zorder=3,
    )

# Style
title = "line-annotated-events · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel(PRICE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.margins(x=0.02)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK_SOFT)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
    ax.spines[side].set_linewidth(1.0)

event_key = mlines.Line2D([], [], color=marker_color, linestyle="--", linewidth=1.5, label="Event marker")
legend = ax.legend(
    handles=[ax.get_lines()[0], event_key], fontsize=8, loc="lower center", bbox_to_anchor=(0.74, 0.0), frameon=True
)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
plt.setp(legend.get_texts(), color=INK_SOFT)

fig.autofmt_xdate(rotation=30, ha="right")
fig.subplots_adjust(left=0.09, right=0.98, top=0.93, bottom=0.2)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
