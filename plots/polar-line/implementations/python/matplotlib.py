""" pyplots.ai
polar-line: Polar Line Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Simulating hourly temperature patterns for two seasons
np.random.seed(42)

# Hours of day (24 hours = full circle)
hours = np.linspace(0, 2 * np.pi, 25)[:-1]  # 24 points (0-23 hours)

# Summer temperature pattern (warmer during day)
summer_temps = 20 + 8 * np.sin(hours - np.pi / 2) + np.random.randn(24) * 0.5

# Winter temperature pattern (cooler, smaller amplitude)
winter_temps = 5 + 5 * np.sin(hours - np.pi / 2) + np.random.randn(24) * 0.5

# Close the loop by appending first point
hours_closed = np.append(hours, hours[0])
summer_closed = np.append(summer_temps, summer_temps[0])
winter_closed = np.append(winter_temps, winter_temps[0])

# Create polar plot (square format works well for polar/radial plots)
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"})

# Plot both series
ax.plot(hours_closed, summer_closed, linewidth=3, color="#FFD43B", label="Summer", marker="o", markersize=8)
ax.plot(hours_closed, winter_closed, linewidth=3, color="#306998", label="Winter", marker="o", markersize=8)

# Configure theta axis (hours of day)
hour_labels = [f"{h}:00" for h in range(0, 24, 3)]
ax.set_xticks(np.linspace(0, 2 * np.pi, 8, endpoint=False))
ax.set_xticklabels(hour_labels, fontsize=16)

# Configure radial axis (temperature)
ax.set_ylim(0, 35)
ax.set_yticks([0, 10, 20, 30])
ax.set_yticklabels(["0°C", "10°C", "20°C", "30°C"], fontsize=14)

# Styling
ax.set_title(
    "Hourly Temperature Pattern · polar-line · matplotlib · pyplots.ai", fontsize=24, pad=40, fontweight="bold"
)
ax.legend(loc="upper left", bbox_to_anchor=(0.95, 0.95), fontsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Set radial label position
ax.set_rlabel_position(45)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
