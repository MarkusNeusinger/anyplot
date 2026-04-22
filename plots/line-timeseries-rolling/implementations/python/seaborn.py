""" pyplots.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Simulated daily temperature readings with 7-day rolling average
np.random.seed(42)

# Generate 180 days of temperature data with seasonal trend and noise
dates = pd.date_range(start="2024-01-01", periods=180, freq="D")

# Base temperature with seasonal variation (winter to spring/summer)
day_of_year = np.arange(180)
seasonal_trend = 5 + 15 * np.sin(2 * np.pi * (day_of_year - 30) / 365)
noise = np.random.normal(0, 3, 180)
temperature = seasonal_trend + noise

# Create DataFrame
df = pd.DataFrame({"date": dates, "temperature": temperature})

# Calculate 7-day rolling average
df["rolling_avg"] = df["temperature"].rolling(window=7, center=False).mean()

# Set seaborn style
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.1)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot raw data as thin, semi-transparent line
sns.lineplot(
    data=df, x="date", y="temperature", ax=ax, color="#306998", alpha=0.4, linewidth=1.5, label="Daily Temperature"
)

# Plot rolling average as prominent smooth line
sns.lineplot(data=df, x="date", y="rolling_avg", ax=ax, color="#FFD43B", linewidth=4, label="7-Day Rolling Average")

# Styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Temperature (°C)", fontsize=20)
ax.set_title("line-timeseries-rolling · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.tick_params(axis="both", labelsize=16)

# Rotate x-axis labels for readability
plt.xticks(rotation=30, ha="right")

# Legend styling
ax.legend(fontsize=16, loc="upper left", framealpha=0.9)

# Grid
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
