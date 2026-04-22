""" pyplots.ai
heatmap-calendar: Basic Calendar Heatmap
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


# Data - Generate one year of daily activity data (GitHub-style contributions)
np.random.seed(42)
start_date = pd.Timestamp("2024-01-01")
end_date = pd.Timestamp("2024-12-31")
dates = pd.date_range(start=start_date, end=end_date, freq="D")

# Create realistic activity pattern: weekdays more active, some random variation
values = []
for date in dates:
    # Base activity level
    base = np.random.poisson(3)
    # Weekdays (Mon-Fri) tend to have more activity
    if date.dayofweek < 5:
        base += np.random.poisson(2)
    # Some days have no activity
    if np.random.random() < 0.15:
        base = 0
    # Occasional high-activity days
    if np.random.random() < 0.05:
        base += np.random.randint(5, 15)
    values.append(base)

df = pd.DataFrame({"date": dates, "value": values})

# Prepare calendar layout data
df["week_of_year"] = (df["date"] - start_date).dt.days // 7
df["dayofweek"] = df["date"].dt.dayofweek  # 0=Monday, 6=Sunday
df["month"] = df["date"].dt.month

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9))

# Custom colormap: GitHub-style greens with light gray for 0
colors = ["#ebedf0", "#c6e48b", "#7bc96f", "#239a3b", "#196127"]
cmap = LinearSegmentedColormap.from_list("github", colors, N=256)

# Get unique weeks and create the grid
n_weeks = df["week_of_year"].max() + 1

# Create a 2D array for the heatmap (7 days x n_weeks)
heatmap_data = np.full((7, n_weeks), np.nan)

for _, row in df.iterrows():
    week_idx = int(row["week_of_year"])
    day_idx = int(row["dayofweek"])
    heatmap_data[day_idx, week_idx] = row["value"]

# Plot the heatmap using pcolormesh
x = np.arange(n_weeks + 1)
y = np.arange(8)
mesh = ax.pcolormesh(x, y, heatmap_data, cmap=cmap, vmin=0, vmax=df["value"].max(), edgecolors="white", linewidth=2)

# Set weekday labels on y-axis
weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ax.set_yticks(np.arange(7) + 0.5)
ax.set_yticklabels(weekday_labels, fontsize=16)

# Add month labels at the top
month_positions = []
month_labels = []
for month in range(1, 13):
    month_data = df[df["month"] == month]
    if len(month_data) > 0:
        first_week = month_data["week_of_year"].iloc[0]
        month_positions.append(first_week)
        month_labels.append(pd.Timestamp(2024, month, 1).strftime("%b"))

ax.set_xticks(month_positions)
ax.set_xticklabels(month_labels, fontsize=16)

# Move x-axis labels to top
ax.xaxis.tick_top()
ax.xaxis.set_label_position("top")

# Remove spines for cleaner look
for spine in ax.spines.values():
    spine.set_visible(False)

# Invert y-axis so Monday is at top
ax.invert_yaxis()

# Add colorbar for value interpretation
cbar = plt.colorbar(mesh, ax=ax, orientation="horizontal", pad=0.08, shrink=0.4, aspect=30)
cbar.ax.tick_params(labelsize=14)
cbar.set_label("Daily Activity (commits)", fontsize=16)

# Title
ax.set_title("heatmap-calendar · matplotlib · pyplots.ai", fontsize=24, pad=20)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
