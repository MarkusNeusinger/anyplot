""" pyplots.ai
line-markers: Line Plot with Markers
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - experimental measurements over time
np.random.seed(42)
time_points = np.arange(0, 12)

# Three series: Temperature readings from different sensors
sensor_a = 22 + np.cumsum(np.random.randn(12) * 0.5)
sensor_b = 20 + np.cumsum(np.random.randn(12) * 0.6)
sensor_c = 24 + np.cumsum(np.random.randn(12) * 0.4)

df = pd.DataFrame(
    {
        "Hour": np.tile(time_points, 3),
        "Temperature (°C)": np.concatenate([sensor_a, sensor_b, sensor_c]),
        "Sensor": ["Sensor A"] * 12 + ["Sensor B"] * 12 + ["Sensor C"] * 12,
    }
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Use custom palette starting with Python Blue and Yellow
custom_palette = ["#306998", "#FFD43B", "#4ECDC4"]

sns.lineplot(
    data=df,
    x="Hour",
    y="Temperature (°C)",
    hue="Sensor",
    style="Sensor",
    markers=True,
    dashes=False,
    markersize=14,
    linewidth=3,
    palette=custom_palette,
    ax=ax,
)

# Styling
ax.set_title("line-markers · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.set_xlabel("Hour", fontsize=20)
ax.set_ylabel("Temperature (°C)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Legend styling
ax.legend(fontsize=16, framealpha=0.9, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
