""" pyplots.ai
line-timeseries: Time Series Line Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Daily temperature readings over 3 months
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=90, freq="D")

# Create realistic temperature pattern with seasonal variation and noise
day_of_year = np.arange(90)
base_temp = 5 + 10 * np.sin(2 * np.pi * (day_of_year + 10) / 365)  # Seasonal trend
noise = np.random.randn(90) * 3
temperature = base_temp + noise

df = pd.DataFrame({"Date": dates, "Temperature (°C)": temperature})

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.lineplot(data=df, x="Date", y="Temperature (°C)", color="#306998", linewidth=3, ax=ax)

# Style adjustments for large canvas
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Temperature (°C)", fontsize=20)
ax.set_title("line-timeseries · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Smart date formatting for months
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))

# Rotate labels to prevent overlap
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

# Grid for readability
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
