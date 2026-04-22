""" pyplots.ai
polar-line: Polar Line Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Set seaborn style and context for consistent styling
sns.set_theme(style="whitegrid", context="talk", font_scale=1.2)

# Data - Hourly temperature patterns for two seasons (cyclical data)
np.random.seed(42)
hours = np.linspace(0, 2 * np.pi, 24, endpoint=False)  # 24 hours in radians

# Summer pattern: warmer during day, cooler at night
summer_temps = 25 + 8 * np.sin(hours - np.pi / 2) + np.random.randn(24) * 0.5
# Winter pattern: cooler overall, less variation
winter_temps = 8 + 5 * np.sin(hours - np.pi / 2) + np.random.randn(24) * 0.5

# Close the loop for continuous line
hours_closed = np.append(hours, hours[0])
summer_closed = np.append(summer_temps, summer_temps[0])
winter_closed = np.append(winter_temps, winter_temps[0])

# Get seaborn color palette
palette = sns.color_palette("colorblind")
color_summer = palette[1]  # Orange
color_winter = palette[0]  # Blue

# Create polar plot (square format for circular plot)
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"})

# Plot lines with seaborn-style aesthetics
ax.plot(
    hours_closed, summer_closed, linewidth=3.5, color=color_summer, label="Summer", marker="o", markersize=10, alpha=0.9
)
ax.plot(
    hours_closed, winter_closed, linewidth=3.5, color=color_winter, label="Winter", marker="o", markersize=10, alpha=0.9
)

# Configure theta axis (hours of day)
hour_labels = [f"{h}:00" for h in range(0, 24, 3)]
ax.set_xticks(np.linspace(0, 2 * np.pi, 8, endpoint=False))
ax.set_xticklabels(hour_labels, fontsize=18)

# Configure radial axis (temperature)
ax.set_ylim(0, 40)
ax.set_yticks([10, 20, 30, 40])
ax.set_yticklabels(["10°C", "20°C", "30°C", "40°C"], fontsize=16)

# Title and legend
ax.set_title("Hourly Temperature Pattern · polar-line · seaborn · pyplots.ai", fontsize=24, pad=30, fontweight="bold")

# Legend positioned outside the plot
ax.legend(loc="upper right", bbox_to_anchor=(1.15, 1.05), fontsize=18, frameon=True, fancybox=True, shadow=True)

# Grid styling (seaborn whitegrid provides good defaults)
ax.grid(True, alpha=0.4, linestyle="-")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
