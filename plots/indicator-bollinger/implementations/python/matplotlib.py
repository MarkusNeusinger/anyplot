""" anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
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

# Okabe-Ito palette - first color is always brand green
BRAND = "#009E73"
SECONDARY = "#C475FD"
TERTIARY = "#4467A3"

# Data - Generate realistic stock price data with Bollinger Bands
np.random.seed(42)
n_days = 120

# Generate realistic price movement using random walk
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.015, n_days)
price_base = 150
close = price_base * np.cumprod(1 + returns)

# Calculate Bollinger Bands (20-period SMA, 2 standard deviations)
window = 20
sma = pd.Series(close).rolling(window=window).mean()
std = pd.Series(close).rolling(window=window).std()
upper_band = sma + 2 * std
lower_band = sma - 2 * std

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot the filled area between bands (volatility envelope)
ax.fill_between(dates, lower_band, upper_band, alpha=0.15, color=TERTIARY, label="Volatility Band (±2σ)")

# Plot upper and lower bands
ax.plot(dates, upper_band, color=TERTIARY, linewidth=2, alpha=0.7)
ax.plot(dates, lower_band, color=TERTIARY, linewidth=2, alpha=0.7)

# Plot middle band (SMA) as dashed line
ax.plot(dates, sma, color=SECONDARY, linewidth=2.5, linestyle="--", label="SMA (20-day)")

# Plot closing price prominently in brand color
ax.plot(dates, close, color=BRAND, linewidth=3, label="Close Price")

# Style
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Price ($)", fontsize=20, color=INK)
ax.set_title("indicator-bollinger · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Format x-axis dates
fig.autofmt_xdate(rotation=30)
ax.xaxis.set_major_locator(plt.MaxNLocator(8))

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Grid - subtle y-axis only
ax.yaxis.grid(True, alpha=0.1, linewidth=0.8, color=INK_SOFT)

# Legend
leg = ax.legend(fontsize=16, loc="upper left", framealpha=0.95)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
