""" anyplot.ai
ohlc-bar: OHLC Bar Chart
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: finance semantic exception, up bars brand green, down bars matte red
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_UP = IMPRINT_PALETTE[0]
COLOR_DOWN = IMPRINT_PALETTE[4]

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open ($)"  # role: open
HIGH = "High ($)"  # role: high
LOW = "Low ($)"  # role: low
CLOSE = "Close ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 45
base_price = 150.0
returns = np.random.normal(0.001, 0.02, n_days)
close_prices = base_price * np.cumprod(1 + returns)
overnight_gaps = np.random.normal(0, 0.006, n_days)
open_prices = np.roll(close_prices, 1) * (1 + overnight_gaps)
open_prices[0] = base_price
df = pd.DataFrame(
    {
        DATE: pd.date_range(start="2024-01-02", periods=n_days, freq="B"),
        OPEN: open_prices,
        HIGH: np.maximum(open_prices, close_prices) * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
        LOW: np.minimum(open_prices, close_prices) * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
        CLOSE: close_prices,
    }
)

# Plot: reads only df and the constants above
positions = np.arange(len(df))
colors = np.where(df[CLOSE] >= df[OPEN], COLOR_UP, COLOR_DOWN)
tick_width = 0.3

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.vlines(positions, df[LOW], df[HIGH], colors=colors, linewidth=1.2)
ax.hlines(df[OPEN], positions - tick_width, positions, colors=colors, linewidth=1.2)
ax.hlines(df[CLOSE], positions, positions + tick_width, colors=colors, linewidth=1.2)

up_line = Line2D([0], [0], color=COLOR_UP, linewidth=1.5, label="Up (Close ≥ Open)")
down_line = Line2D([0], [0], color=COLOR_DOWN, linewidth=1.5, label="Down (Close < Open)")
ax.legend(handles=[up_line, down_line], fontsize=8, loc="best")

# Style
tick_positions = positions[:: max(1, len(df) // 8)]
ax.set_xticks(tick_positions, df[DATE].iloc[tick_positions].dt.strftime("%b %d"), rotation=45, ha="right")
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel("Northwind Robotics (NWRB) Price ($)", fontsize=10, color=INK)
ax.set_title("ohlc-bar · python · seaborn · anyplot.ai", fontsize=12, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

ax.set_xlim(-1, len(df))
y_min, y_max = df[LOW].min(), df[HIGH].max()
y_padding = (y_max - y_min) * 0.1
ax.set_ylim(y_min - y_padding, y_max + y_padding)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
