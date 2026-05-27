""" anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-16
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

# Okabe-Ito palette
MACD_COLOR = "#4467A3"  # Blue (position 3)
SIGNAL_COLOR = "#AE3030"  # Orange (position 5)
POSITIVE_COLOR = "#009E73"  # Green (position 1)
NEGATIVE_COLOR = "#C475FD"  # Red-orange (position 2)

# Generate synthetic stock price data and calculate MACD
np.random.seed(42)

# Create 150 trading days of price data (need 120 for display + 26 for EMA warmup)
n_days = 150
dates = pd.date_range("2024-06-01", periods=n_days, freq="B")

# Generate realistic price movement with trend and volatility
returns = np.random.normal(0.0005, 0.015, n_days)
price = 100 * np.cumprod(1 + returns)


# Calculate EMAs for MACD
def ema(data, span):
    return pd.Series(data).ewm(span=span, adjust=False).mean().values


ema_12 = ema(price, 12)
ema_26 = ema(price, 26)

# Calculate MACD components
macd_line = ema_12 - ema_26
signal_line = ema(macd_line, 9)
histogram = macd_line - signal_line

# Use only the last 120 days (after EMAs have stabilized)
start_idx = 30
dates = dates[start_idx:]
macd_line = macd_line[start_idx:]
signal_line = signal_line[start_idx:]
histogram = histogram[start_idx:]

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), facecolor=PAGE_BG, gridspec_kw={"height_ratios": [2, 1]})

# Upper subplot: MACD and Signal lines
ax1.set_facecolor(PAGE_BG)
ax1.plot(dates, macd_line, color=MACD_COLOR, linewidth=3, label="MACD (12, 26)")
ax1.plot(dates, signal_line, color=SIGNAL_COLOR, linewidth=3, label="Signal (9)")
ax1.axhline(y=0, color=INK_SOFT, linestyle="--", linewidth=1.5, alpha=0.5)

ax1.set_ylabel("MACD Value", fontsize=20, color=INK)
ax1.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax1.spines[s].set_color(INK_SOFT)
ax1.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK_SOFT)

# Legend for upper subplot
leg1 = ax1.legend(fontsize=16, loc="upper left")
if leg1:
    leg1.get_frame().set_facecolor(ELEVATED_BG)
    leg1.get_frame().set_edgecolor(INK_SOFT)
    leg1.get_frame().set_alpha(0.95)
    plt.setp(leg1.get_texts(), color=INK_SOFT)

# Lower subplot: Histogram
ax2.set_facecolor(PAGE_BG)
colors = [POSITIVE_COLOR if h >= 0 else NEGATIVE_COLOR for h in histogram]
ax2.bar(dates, histogram, color=colors, alpha=0.8, width=0.8, label="Histogram")
ax2.axhline(y=0, color=INK_SOFT, linestyle="-", linewidth=1.5, alpha=0.7)

ax2.set_xlabel("Date", fontsize=20, color=INK)
ax2.set_ylabel("Histogram", fontsize=20, color=INK)
ax2.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax2.spines[s].set_color(INK_SOFT)
ax2.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK_SOFT)

# Format x-axis dates
fig.autofmt_xdate(rotation=45, ha="right")

# Main title
fig.suptitle("indicator-macd · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.96])

# Save to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
plt.savefig(os.path.join(script_dir, f"plot-{THEME}.png"), dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
