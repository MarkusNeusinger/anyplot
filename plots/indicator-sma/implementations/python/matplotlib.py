"""anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-19
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: price first, then one position per SMA in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Price ($)"  # role: close
SMA_SHORT = "SMA 20"  # role: sma_short
SMA_MEDIUM = "SMA 50"  # role: sma_medium
SMA_LONG = "SMA 200"  # role: sma_long

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=[DATE])
np.random.seed(42)
n_days = 300
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")  # business days
returns = np.random.normal(0.0003, 0.015, n_days) + np.sin(np.linspace(0, 3 * np.pi, n_days)) * 0.001
close = 150 * np.cumprod(1 + returns)

df = pd.DataFrame({DATE: dates, CLOSE: close})
df[SMA_SHORT] = df[CLOSE].rolling(window=20).mean()
df[SMA_MEDIUM] = df[CLOSE].rolling(window=50).mean()
df[SMA_LONG] = df[CLOSE].rolling(window=200).mean()

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(df[DATE], df[CLOSE], color=IMPRINT_PALETTE[0], linewidth=2.5, label=CLOSE, alpha=0.85, zorder=4)
for i, (col, z) in enumerate([(SMA_SHORT, 3), (SMA_MEDIUM, 2), (SMA_LONG, 1)], start=1):
    ax.plot(df[DATE], df[col], color=IMPRINT_PALETTE[i], linewidth=2.0, label=col, zorder=z)

# Style
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel(CLOSE, fontsize=10, color=INK)
ax.set_title("indicator-sma · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Date formatting with month locator
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
fig.autofmt_xdate(rotation=30)

# Grid: y-axis only for a line chart
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

low, high = df[CLOSE].min(), df[CLOSE].max()
ax.set_ylim(low - 0.05 * (high - low), high + 0.3 * (high - low))  # headroom keeps the legend off the lines
leg = ax.legend(fontsize=8, loc="upper right", ncol=4)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.17)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
