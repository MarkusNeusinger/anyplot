""" pyplots.ai
line-timeseries: Time Series Line Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Daily temperature readings over one year
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")

# Simulate realistic temperature pattern with seasonal variation
day_of_year = np.arange(len(dates))
seasonal = 15 * np.sin(2 * np.pi * (day_of_year - 80) / 365)  # Peak in summer
baseline = 12  # Average temperature
noise = np.random.randn(len(dates)) * 3
temperature = baseline + seasonal + noise

# Create figure (16:9 aspect ratio for landscape)
fig, ax = plt.subplots(figsize=(16, 9))

# Plot
ax.plot(dates, temperature, linewidth=2.5, color="#306998", alpha=0.9)

# Smart date formatting based on time range
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonthday=15))

# Rotate labels to prevent overlap
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

# Labels and styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Temperature (°C)", fontsize=20)
ax.set_title("Daily Temperature 2024 · line-timeseries · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Grid for readability
ax.grid(True, alpha=0.3, linestyle="--", which="major")
ax.grid(True, alpha=0.15, linestyle=":", which="minor")

# Set axis limits with padding
ax.set_xlim(dates[0], dates[-1])
ax.margins(y=0.05)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
