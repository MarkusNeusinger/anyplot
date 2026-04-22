""" pyplots.ai
heatmap-calendar: Basic Calendar Heatmap
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - one year of daily activity (simulating GitHub-style contributions)
np.random.seed(42)
start_date = pd.Timestamp("2024-01-01")
end_date = pd.Timestamp("2024-12-31")
dates = pd.date_range(start=start_date, end=end_date, freq="D")

# Simulate daily activity with realistic patterns
# Higher activity on weekdays, lower on weekends, with some variation
base_activity = np.random.exponential(scale=3, size=len(dates))
weekday_boost = np.where(dates.weekday < 5, 1.5, 0.6)  # Weekdays higher
activity = (base_activity * weekday_boost).astype(int)
# Add some zero days and cap max
activity = np.clip(activity, 0, 15)
# Add more zeros for realism
zero_mask = np.random.random(len(dates)) < 0.15
activity[zero_mask] = 0

df = pd.DataFrame({"date": dates, "value": activity})

# Extract calendar components
df["weekday"] = df["date"].dt.weekday  # 0=Monday, 6=Sunday
df["month"] = df["date"].dt.month

# Calculate week number as continuous count from start of year
# This avoids issues with ISO week numbers crossing year boundaries
df["week_num"] = ((df["date"] - start_date).dt.days + start_date.weekday()) // 7

# Create pivot table for heatmap (weekdays as rows, weeks as columns)
pivot_df = df.pivot(index="weekday", columns="week_num", values="value")

# Weekday labels (Monday at top)
weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Create plot (16:9 aspect ratio for 4800x2700)
fig, ax = plt.subplots(figsize=(16, 9))

# Create heatmap with seaborn using Python-themed green colormap
sns.heatmap(
    pivot_df,
    ax=ax,
    cmap="Greens",
    linewidths=1.5,
    linecolor="white",
    cbar_kws={"label": "Daily Contributions", "shrink": 0.6, "aspect": 25, "pad": 0.02},
    vmin=0,
    vmax=15,
)

# Set weekday labels on y-axis
ax.set_yticks(np.arange(7) + 0.5)
ax.set_yticklabels(weekday_labels, fontsize=16, rotation=0)

# Create month labels for x-axis
# Find first week of each month
month_starts = df.groupby("month")["week_num"].min()
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

ax.set_xticks([month_starts[m] + 0.5 for m in range(1, 13)])
ax.set_xticklabels(month_labels, fontsize=16)

# Style adjustments
ax.set_xlabel("")
ax.set_ylabel("")
ax.set_title("heatmap-calendar · seaborn · pyplots.ai", fontsize=24, pad=20)

# Adjust colorbar label size
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=14)
cbar.ax.set_ylabel("Daily Contributions", fontsize=16)

# Remove top/right spines for cleaner look
ax.tick_params(top=False, bottom=False, left=False, right=False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
