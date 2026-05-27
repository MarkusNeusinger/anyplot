""" anyplot.ai
point-and-figure-basic: Point and Figure Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-20
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito: green for rising (X), vermillion for falling (O)
X_COLOR = "#009E73"
O_COLOR = "#C475FD"

# Data: synthetic stock price with upward drift
np.random.seed(42)
n_days = 300
close = 100.0 * np.cumprod(1 + np.random.normal(0.001, 0.02, n_days))

# P&F parameters
box_size = 2.0
reversal = 3

# Build P&F columns
columns = []
current_col = None
current_price = None

for price in close:
    if current_col is None:
        current_col = {
            "type": "X",
            "start": np.floor(price / box_size) * box_size,
            "end": np.floor(price / box_size) * box_size,
        }
        current_price = current_col["end"]
        continue

    if current_col["type"] == "X":
        new_high = np.floor(price / box_size) * box_size
        if new_high > current_col["end"]:
            current_col["end"] = new_high
            current_price = new_high
        elif price <= current_price - reversal * box_size:
            columns.append(current_col.copy())
            current_col = {
                "type": "O",
                "start": current_col["end"] - box_size,
                "end": np.ceil(price / box_size) * box_size,
            }
            current_price = current_col["end"]
    else:
        new_low = np.ceil(price / box_size) * box_size
        if new_low < current_col["end"]:
            current_col["end"] = new_low
            current_price = new_low
        elif price >= current_price + reversal * box_size:
            columns.append(current_col.copy())
            current_col = {
                "type": "X",
                "start": current_col["end"] + box_size,
                "end": np.floor(price / box_size) * box_size,
            }
            current_price = current_col["end"]

if current_col is not None:
    columns.append(current_col)

n_cols = len(columns)
all_prices = [p for col in columns for p in [col["start"], col["end"]]]
y_min = min(all_prices) - 2 * box_size
y_max = max(all_prices) + 2 * box_size

# Find the most significant buy signal: X column exceeding prior X column peak by most boxes
prev_x_high = None
best_breakout = None
for i, col in enumerate(columns):
    if col["type"] == "X":
        col_high = max(col["start"], col["end"])
        if prev_x_high is not None and col_high > prev_x_high:
            excess = col_high - prev_x_high
            if best_breakout is None or excess > best_breakout[3]:
                best_breakout = (i, prev_x_high, col_high, excess)
        prev_x_high = col_high

# Trend line anchors
# Support: from overall lowest low, rising 45° (one box per column to the right)
all_lows = [(i, min(col["start"], col["end"])) for i, col in enumerate(columns)]
lowest_col_idx, lowest_price = min(all_lows, key=lambda x: x[1])

# Resistance: from top of first column, falling 45° (one box per column to the right)
first_col_high = max(columns[0]["start"], columns[0]["end"])

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Draw X and O symbols using patheffects for crisp separation between dense symbols
symbol_stroke = [pe.withStroke(linewidth=2, foreground=PAGE_BG)]
for col_idx, col in enumerate(columns):
    lo = min(col["start"], col["end"])
    hi = max(col["start"], col["end"])
    char = "X" if col["type"] == "X" else "O"
    color = X_COLOR if col["type"] == "X" else O_COLOR
    for box_price in np.arange(lo, hi + box_size / 2, box_size):
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
support_x = np.array([0, n_cols - 1])
support_y = np.array(
    [lowest_price - lowest_col_idx * box_size, lowest_price + (n_cols - 1 - lowest_col_idx) * box_size]
)
ax.plot(support_x, support_y, color=X_COLOR, linewidth=0.8, linestyle="--", alpha=0.5, zorder=0)

# Resistance trend line: 45° downward from the top of the first column
resistance_x = np.array([0, n_cols - 1])
resistance_y = np.array([first_col_high, first_col_high - (n_cols - 1) * box_size])
ax.plot(resistance_x, resistance_y, color=O_COLOR, linewidth=0.8, linestyle="--", alpha=0.5, zorder=0)

# Axes configuration
ax.set_xlim(-0.5, n_cols - 0.5)
ax.set_ylim(y_min, y_max)

# Major ticks at $10 intervals (labeled + gridlines); minor ticks at $2 box intervals (tick marks only)
major_ticks = np.arange(np.floor(y_min / 10) * 10, np.ceil(y_max / 10) * 10 + 10, 10)
minor_ticks = np.arange(
    np.floor(y_min / box_size) * box_size, np.ceil(y_max / box_size) * box_size + box_size, box_size
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
ax.set_ylabel("Price ($)", fontsize=10, color=INK)
ax.set_title("point-and-figure-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)

# Annotate the most prominent buy signal — X column breakout above prior X peak (narrative focal point)
if best_breakout is not None:
    b_col, _, b_col_high, _ = best_breakout
    text_offset = 2.5 if b_col < n_cols * 0.65 else -3.5
    ax.annotate(
        "Buy Signal\n(Column Breakout)",
        xy=(b_col, b_col_high),
        xytext=(b_col + text_offset, b_col_high + 4),
        fontsize=7,
        fontweight="bold",
        color=X_COLOR,
        ha="center",
        arrowprops={"arrowstyle": "->", "color": X_COLOR, "lw": 0.8},
        bbox={"facecolor": ELEVATED_BG, "edgecolor": X_COLOR, "alpha": 0.9, "boxstyle": "round,pad=0.3"},
    )

# Legend using color patches (avoids marker/text mismatch)
x_patch = mpatches.Patch(facecolor=X_COLOR, label="Rising (X)", edgecolor=PAGE_BG)
o_patch = mpatches.Patch(facecolor=O_COLOR, label="Falling (O)", edgecolor=PAGE_BG)
leg = ax.legend(handles=[x_patch, o_patch], fontsize=8, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
