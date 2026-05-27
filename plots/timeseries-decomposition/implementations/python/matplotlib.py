""" anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = [
    "#009E73",  # bluish green (brand — first series)
    "#C475FD",  # vermillion
    "#4467A3",  # blue
    "#BD8233",  # reddish purple
]

# Data - Monthly retail sales over 6 years (72 months = 6 full annual cycles)
np.random.seed(42)
n_months = 72
dates = pd.date_range(start="2018-01-01", periods=n_months, freq="MS")

# Create realistic retail sales data with trend, seasonality, and noise
trend = np.linspace(100, 180, n_months) + np.cumsum(np.random.randn(n_months) * 0.5)
seasonal = 25 * np.sin(2 * np.pi * np.arange(n_months) / 12)  # Annual cycle
# Add holiday bump in December (month 12)
holiday_bump = np.array([15 if (i + 1) % 12 == 0 else 0 for i in range(n_months)])
seasonal = seasonal + holiday_bump
residual = np.random.randn(n_months) * 8
values = trend + seasonal + residual

# Create time series
ts = pd.Series(values, index=dates)

# Perform seasonal decomposition (additive model)
decomposition = seasonal_decompose(ts, model="additive", period=12)

# Create plot with 4 subplots
fig, axes = plt.subplots(4, 1, figsize=(16, 12), sharex=True, facecolor=PAGE_BG)

# Original series
axes[0].plot(dates, ts.values, color=IMPRINT[0], linewidth=2.5)
axes[0].set_facecolor(PAGE_BG)
axes[0].set_ylabel("Original (Sales USD)", fontsize=20, color=INK)
axes[0].tick_params(axis="y", labelsize=16, colors=INK_SOFT)
axes[0].grid(True, alpha=0.15, linewidth=0.8, color=INK)
axes[0].set_title(
    "timeseries-decomposition · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=15
)

# Trend component
axes[1].plot(dates, decomposition.trend, color=IMPRINT[1], linewidth=2.5)
axes[1].set_facecolor(PAGE_BG)
axes[1].set_ylabel("Trend (Sales USD)", fontsize=20, color=INK)
axes[1].tick_params(axis="y", labelsize=16, colors=INK_SOFT)
axes[1].grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Seasonal component
axes[2].plot(dates, decomposition.seasonal, color=IMPRINT[2], linewidth=2.5)
axes[2].set_facecolor(PAGE_BG)
axes[2].set_ylabel("Seasonal (Sales USD)", fontsize=20, color=INK)
axes[2].tick_params(axis="y", labelsize=16, colors=INK_SOFT)
axes[2].grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Residual component
axes[3].plot(dates, decomposition.resid, color=IMPRINT[3], linewidth=2.5)
axes[3].axhline(y=0, color=INK_SOFT, linestyle="-", linewidth=1, alpha=0.3)
axes[3].set_facecolor(PAGE_BG)
axes[3].set_ylabel("Residual (Sales USD)", fontsize=20, color=INK)
axes[3].set_xlabel("Date", fontsize=20, color=INK)
axes[3].tick_params(axis="both", labelsize=16, colors=INK_SOFT)
axes[3].grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Remove top and right spines
for ax in axes:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(INK_SOFT)
    ax.spines["bottom"].set_color(INK_SOFT)

# Adjust x-axis tick formatting
fig.autofmt_xdate(rotation=45, ha="right")
fig.axes[-1].tick_params(axis="x", labelsize=16)

# Adjust spacing between subplots
plt.tight_layout()
plt.subplots_adjust(hspace=0.15)

plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
