""" pyplots.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Monthly airline passengers (classic time series dataset)
np.random.seed(42)
n_years = 10
n_months = n_years * 12
period = 12  # Monthly seasonality

# Create date range
dates = pd.date_range(start="2014-01-01", periods=n_months, freq="MS")

# Generate realistic passenger data with trend, seasonality, and noise
# Trend: gradual growth over time
trend_component = np.linspace(400, 700, n_months)

# Seasonality: summer peaks (higher in months 6-8), winter lows
month_effect = np.array([0.85, 0.80, 0.90, 0.95, 1.05, 1.15, 1.20, 1.18, 1.05, 0.95, 0.88, 0.95])
seasonal_component = np.tile(month_effect, n_years)

# Noise
noise = np.random.normal(0, 15, n_months)

# Combine: multiplicative model (trend * seasonal) + noise
values = trend_component * seasonal_component + noise

# Create DataFrame
df = pd.DataFrame({"date": dates, "passengers": values})
df = df.set_index("date")

# Manual seasonal decomposition (additive model)
# Step 1: Trend - rolling mean with window = period
trend = df["passengers"].rolling(window=period, center=True, min_periods=1).mean()

# Step 2: Detrended series
detrended = df["passengers"] - trend

# Step 3: Seasonal - average for each month
seasonal = detrended.groupby(detrended.index.month).transform("mean")

# Step 4: Residual
residual = df["passengers"] - trend - seasonal

# Set seaborn style
sns.set_theme(style="whitegrid")
sns.set_context("talk", font_scale=1.1)

# Create figure with 4 subplots (4800x2700 at dpi=300 -> 16x9)
fig, axes = plt.subplots(4, 1, figsize=(16, 9), sharex=True)
fig.subplots_adjust(hspace=0.15)

# Colors
python_blue = "#306998"
python_yellow = "#FFD43B"
trend_color = "#E07B39"
residual_color = "#5A9A5A"

# Plot 1: Original
sns.lineplot(x=df.index, y=df["passengers"], ax=axes[0], color=python_blue, linewidth=2)
axes[0].set_ylabel("Passengers\n(thousands)", fontsize=18)
axes[0].set_title("Original", fontsize=20, fontweight="bold", loc="left")
axes[0].tick_params(axis="both", labelsize=14)

# Plot 2: Trend
sns.lineplot(x=trend.index, y=trend.values, ax=axes[1], color=trend_color, linewidth=2.5)
axes[1].set_ylabel("Trend", fontsize=18)
axes[1].set_title("Trend", fontsize=20, fontweight="bold", loc="left")
axes[1].tick_params(axis="both", labelsize=14)

# Plot 3: Seasonal
sns.lineplot(x=seasonal.index, y=seasonal.values, ax=axes[2], color=python_yellow, linewidth=2)
axes[2].set_ylabel("Seasonal", fontsize=18)
axes[2].set_title("Seasonal", fontsize=20, fontweight="bold", loc="left")
axes[2].tick_params(axis="both", labelsize=14)
axes[2].axhline(y=0, color="gray", linestyle="--", linewidth=1, alpha=0.7)

# Plot 4: Residual
sns.lineplot(x=residual.index, y=residual.values, ax=axes[3], color=residual_color, linewidth=1.5)
axes[3].set_ylabel("Residual", fontsize=18)
axes[3].set_title("Residual", fontsize=20, fontweight="bold", loc="left")
axes[3].set_xlabel("Date", fontsize=18)
axes[3].tick_params(axis="both", labelsize=14)
axes[3].axhline(y=0, color="gray", linestyle="--", linewidth=1, alpha=0.7)

# Adjust grid for all axes
for ax in axes:
    ax.grid(True, alpha=0.3, linestyle="--")

# Main title
fig.suptitle("timeseries-decomposition · seaborn · pyplots.ai", fontsize=24, fontweight="bold", y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
