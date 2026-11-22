""" anyplot.ai
point-and-figure-basic: Point and Figure Chart
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-22
"""

import os
import sys


# Remove the script's directory from sys.path to prevent shadowing the installed matplotlib package
if sys.path and sys.path[0] and "implementations" in sys.path[0]:
    sys.path.pop(0)

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# imprint semantic anchors: green for rising (X), red for falling (O)
X_COLOR = "#009E73"
O_COLOR = "#AE3030"

# Constants

REVERSAL = 3  # boxes of reversal that start a new column

# Column constants
DATE = "Date"  # role: date
HIGH = "High ($)"  # role: high
LOW = "Low ($)"  # role: low
CLOSE = "Close ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 300
close = 100.0 * np.cumprod(1 + np.random.normal(0.001, 0.02, n_days))
spread = np.abs(np.random.normal(0, 0.008, (2, n_days))) * close
df = pd.DataFrame(
    {DATE: pd.bdate_range("2025-01-02", periods=n_days), HIGH: close + spread[0], LOW: close - spread[1], CLOSE: close}
)

# Plot
# Box size: about 2% of the typical price, one significant figure (2.0 for this sample)
BOX_SIZE = float(f"{df[CLOSE].mean() * 0.02:.1g}")
MAJOR = 5 * BOX_SIZE  # labeled price ticks and gridlines
# Build P&F columns from the closing prices: (rising, first box, last box)
columns = []
col_type = None
col_start = col_end = None
for price in df[CLOSE]:
    if col_type is None:
        col_type = True
        col_start = col_end = np.floor(price / BOX_SIZE) * BOX_SIZE
    elif col_type:
        new_high = np.floor(price / BOX_SIZE) * BOX_SIZE
        if new_high > col_end:
            col_end = new_high
        elif price <= col_end - REVERSAL * BOX_SIZE:
            columns.append((col_type, col_start, col_end))
            col_type, col_start, col_end = False, col_end - BOX_SIZE, np.ceil(price / BOX_SIZE) * BOX_SIZE
    else:
        new_low = np.ceil(price / BOX_SIZE) * BOX_SIZE
        if new_low < col_end:
            col_end = new_low
        elif price >= col_end + REVERSAL * BOX_SIZE:
            columns.append((col_type, col_start, col_end))
            col_type, col_start, col_end = True, col_end + BOX_SIZE, np.floor(price / BOX_SIZE) * BOX_SIZE
columns.append((col_type, col_start, col_end))

n_cols = len(columns)
all_prices = [p for _, start, end in columns for p in (start, end)]
y_min = min(all_prices) - 2 * BOX_SIZE
y_max = max(all_prices) + 2 * BOX_SIZE

# Support: rises 45 degrees (one box per column) from the overall lowest low
lowest_col_idx, lowest_price = min(
    ((i, min(start, end)) for i, (_, start, end) in enumerate(columns)), key=lambda t: t[1]
)
# Resistance: falls 45 degrees (one box per column) from the top of the first column
first_col_high = max(columns[0][1], columns[0][2])

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Draw X and O symbols using patheffects for crisp separation between dense symbols
symbol_stroke = [pe.withStroke(linewidth=2, foreground=PAGE_BG)]
for col_idx, (kind, start, end) in enumerate(columns):
    lo, hi = min(start, end), max(start, end)
    char = "XO"[not kind]
    color = X_COLOR if kind else O_COLOR
    for box_price in np.arange(lo, hi + BOX_SIZE / 2, BOX_SIZE):
        ax.text(
            col_idx,
            box_price,
            char,
            fontsize=8,
            fontweight="bold",
            ha="center",
            va="center",
            color=color,
            path_effects=symbol_stroke,
        )

# Support trend line: 45° upward from the overall lowest low
support_x = np.array([lowest_col_idx, n_cols - 1])
support_y = np.array([lowest_price, lowest_price + (n_cols - 1 - lowest_col_idx) * BOX_SIZE])
ax.plot(support_x, support_y, color=X_COLOR, linewidth=0.8, linestyle="--", alpha=0.5, zorder=0)

# Resistance trend line: 45° downward from the top of the first column
resistance_x = np.array([0, n_cols - 1])
resistance_y = np.array([first_col_high, first_col_high - (n_cols - 1) * BOX_SIZE])
ax.plot(resistance_x, resistance_y, color=O_COLOR, linewidth=0.8, linestyle="--", alpha=0.5, zorder=0)

# Axes configuration
ax.set_xlim(-0.5, n_cols - 0.5)
ax.set_ylim(y_min, y_max)

# Major ticks at $10 intervals (labeled + gridlines); minor ticks at $2 box intervals (tick marks only)
major_ticks = np.arange(np.floor(y_min / MAJOR) * MAJOR, np.ceil(y_max / MAJOR) * MAJOR + MAJOR, MAJOR)
minor_ticks = np.arange(
    np.floor(y_min / BOX_SIZE) * BOX_SIZE, np.ceil(y_max / BOX_SIZE) * BOX_SIZE + BOX_SIZE, BOX_SIZE
)
ax.set_yticks(major_ticks)
ax.set_yticks(minor_ticks, minor=True)
ax.tick_params(axis="y", which="major", labelsize=8, colors=INK_SOFT, length=4)
ax.tick_params(axis="y", which="minor", length=2, colors=INK_SOFT, labelsize=0)
ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT)

# Style
ax.yaxis.grid(True, which="major", alpha=0.15, linewidth=0.6, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.set_xlabel("Column (Reversal Number)", fontsize=10, color=INK)
ax.set_ylabel(CLOSE, fontsize=10, color=INK)
ax.set_title("point-and-figure-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)

# Legend using color patches (avoids marker/text mismatch)
x_patch = mpatches.Patch(facecolor=X_COLOR, label="Rising (X)", edgecolor=PAGE_BG)
o_patch = mpatches.Patch(facecolor=O_COLOR, label="Falling (O)", edgecolor=PAGE_BG)
leg = ax.legend(handles=[x_patch, o_patch], fontsize=8, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
