"""anyplot.ai
ohlc-bar: OHLC Bar Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — position 1 for up bars, position 5 (red) for down bars
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_UP = IMPRINT_PALETTE[0]
COLOR_DOWN = IMPRINT_PALETTE[4]

# Constants
TICK_FRACTION = 0.4  # open/close tick length as a fraction of the spacing between bars

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open (USD)"  # role: open
HIGH = "High (USD)"  # role: high
LOW = "Low (USD)"  # role: low
CLOSE = "Close (USD)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=[DATE])
np.random.seed(42)
n_days = 45
base_price = 150.0
dates = pd.bdate_range(start="2024-06-01", periods=n_days)
returns = np.random.normal(0.001, 0.02, n_days)  # daily returns with a slight upward bias
close_prices = base_price * np.cumprod(1 + returns)
high_add = np.random.uniform(0.5, 3.0, n_days)
low_sub = np.random.uniform(0.5, 3.0, n_days)
# Open is the previous close with a small gap
open_prices = np.roll(close_prices, 1) * (1 + np.random.uniform(-0.005, 0.005, n_days))
open_prices[0] = base_price
df = pd.DataFrame(
    {
        DATE: dates,
        OPEN: open_prices,
        HIGH: np.maximum(open_prices, close_prices) + high_add,
        LOW: np.minimum(open_prices, close_prices) - low_sub,
        CLOSE: close_prices,
    }
)

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

x = mdates.date2num(df[DATE])
tick_len = TICK_FRACTION * np.median(np.diff(x)) if len(x) > 1 else TICK_FRACTION
is_up = (df[CLOSE] >= df[OPEN]).to_numpy()
colors = np.where(is_up, COLOR_UP, COLOR_DOWN)
line_width = 1.3

ax.vlines(x, df[LOW], df[HIGH], colors=colors, linewidth=line_width, capstyle="round", zorder=3)
ax.hlines(df[OPEN], x - tick_len, x, colors=colors, linewidth=line_width, capstyle="butt", zorder=3)
ax.hlines(df[CLOSE], x, x + tick_len, colors=colors, linewidth=line_width, capstyle="butt", zorder=3)

# Style
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel("Price (USD)", fontsize=10, color=INK)
ax.set_title("ohlc-bar · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Weekly date labels
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MONDAY))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Grid behind the bars
ax.set_axisbelow(True)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.xaxis.grid(True, alpha=0.08, linewidth=0.8, color=INK)

# Price axis spans the lows and highs with a little padding, never forced to zero
y_min, y_max = df[LOW].min(), df[HIGH].max()
y_pad = (y_max - y_min) * 0.06
ax.set_ylim(y_min - y_pad, y_max + y_pad)
ax.set_xlim(x.min() - 2 * tick_len, x.max() + 2 * tick_len)

legend = ax.legend(
    handles=[
        Line2D([0], [0], color=COLOR_UP, linewidth=2, label="Up (Close ≥ Open)"),
        Line2D([0], [0], color=COLOR_DOWN, linewidth=2, label="Down (Close < Open)"),
    ],
    fontsize=8,
    loc="lower left",
)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
for text in legend.get_texts():
    text.set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
