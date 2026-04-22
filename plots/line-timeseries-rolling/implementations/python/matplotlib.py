""" pyplots.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Daily temperature readings with 7-day rolling average
np.random.seed(42)

# Generate 180 days of temperature data (6 months)
dates = pd.date_range("2024-01-01", periods=180, freq="D")

# Create seasonal temperature pattern with noise
# Base seasonal pattern: winter -> spring -> summer
day_of_year = np.arange(180)
seasonal = 5 + 15 * np.sin(2 * np.pi * (day_of_year - 30) / 365)  # Seasonal trend
noise = np.random.normal(0, 3, 180)  # Daily variation
temperature = seasonal + noise

# Create DataFrame and calculate rolling average
df = pd.DataFrame({"date": dates, "temperature": temperature})
df["rolling_avg"] = df["temperature"].rolling(window=7, center=True).mean()

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Raw data - thin, semi-transparent line
ax.plot(df["date"], df["temperature"], linewidth=1.5, alpha=0.5, color="#306998", label="Daily Temperature")

# Rolling average - prominent smooth line
ax.plot(df["date"], df["rolling_avg"], linewidth=3.5, color="#FFD43B", label="7-Day Rolling Average")

# Labels and styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Temperature (°C)", fontsize=20)
ax.set_title("line-timeseries-rolling · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
