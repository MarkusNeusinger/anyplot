""" pyplots.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose


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
fig, axes = plt.subplots(4, 1, figsize=(16, 12), sharex=True)

# Color palette
color_original = "#306998"
color_trend = "#FFD43B"
color_seasonal = "#4B8BBE"
color_residual = "#FFE873"

# Original series
axes[0].plot(dates, ts.values, color=color_original, linewidth=2.5)
axes[0].set_ylabel("Original", fontsize=18)
axes[0].tick_params(axis="y", labelsize=14)
axes[0].grid(True, alpha=0.3, linestyle="--")
axes[0].set_title("timeseries-decomposition · matplotlib · pyplots.ai", fontsize=24, pad=15)

# Trend component
axes[1].plot(dates, decomposition.trend, color=color_trend, linewidth=2.5)
axes[1].set_ylabel("Trend", fontsize=18)
axes[1].tick_params(axis="y", labelsize=14)
axes[1].grid(True, alpha=0.3, linestyle="--")

# Seasonal component
axes[2].plot(dates, decomposition.seasonal, color=color_seasonal, linewidth=2.5)
axes[2].set_ylabel("Seasonal", fontsize=18)
axes[2].tick_params(axis="y", labelsize=14)
axes[2].grid(True, alpha=0.3, linestyle="--")

# Residual component
axes[3].plot(dates, decomposition.resid, color=color_residual, linewidth=2.5, alpha=0.8)
axes[3].axhline(y=0, color="#666666", linestyle="-", linewidth=1, alpha=0.5)
axes[3].set_ylabel("Residual", fontsize=18)
axes[3].set_xlabel("Date", fontsize=20)
axes[3].tick_params(axis="both", labelsize=14)
axes[3].grid(True, alpha=0.3, linestyle="--")

# Adjust x-axis tick formatting
plt.gcf().autofmt_xdate()

# Adjust spacing between subplots
plt.tight_layout()
plt.subplots_adjust(hspace=0.15)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
