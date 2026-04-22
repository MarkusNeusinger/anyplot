""" pyplots.ai
range-interval: Range Interval Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Data - Monthly temperature ranges for a temperate city
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Realistic temperature pattern (Northern Hemisphere temperate climate)
base_temps = np.array([-2, 0, 5, 11, 16, 20, 23, 22, 17, 11, 5, 0])
min_temps = base_temps + np.random.uniform(-3, 0, 12)
max_temps = base_temps + np.random.uniform(5, 10, 12)

# Create DataFrame for seaborn plotting
df = pd.DataFrame({"Month": months, "Min Temperature": min_temps, "Max Temperature": max_temps, "month_idx": range(12)})

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Draw vertical range bars connecting min and max temperatures
for i in range(len(df)):
    ax.plot(
        [i, i],
        [df.iloc[i]["Min Temperature"], df.iloc[i]["Max Temperature"]],
        color="#306998",
        linewidth=12,
        alpha=0.8,
        solid_capstyle="round",
        zorder=1,
    )

# Use seaborn scatterplot for min temperature markers
sns.scatterplot(
    data=df,
    x="month_idx",
    y="Min Temperature",
    color="#306998",
    s=250,
    edgecolor="white",
    linewidth=2,
    ax=ax,
    zorder=5,
    label="Min Temperature",
)

# Use seaborn scatterplot for max temperature markers
sns.scatterplot(
    data=df,
    x="month_idx",
    y="Max Temperature",
    color="#FFD43B",
    s=250,
    edgecolor="white",
    linewidth=2,
    ax=ax,
    zorder=5,
    label="Max Temperature",
)

# Configure axes
ax.set_xticks(range(len(months)))
ax.set_xticklabels(months)
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Temperature (°C)", fontsize=20)
ax.set_title("range-interval · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Add a horizontal reference line at freezing point
ax.axhline(y=0, color="#888888", linestyle="--", linewidth=1.5, alpha=0.5)

# Customize grid
ax.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Add legend with range bar explanation
legend_elements = [
    Line2D([0], [0], color="#306998", linewidth=8, label="Temperature Range"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#306998", markersize=12, label="Min Temperature"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#FFD43B", markersize=12, label="Max Temperature"),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=14)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
