""" pyplots.ai
line-confidence: Line Plot with Confidence Interval
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Simulated temperature forecast with 95% confidence interval
np.random.seed(42)
days = np.arange(1, 31)  # 30 days forecast

# Central forecast (mean temperature with slight trend)
base_temp = 15 + 0.3 * days + 3 * np.sin(days / 5)
y = base_temp + np.random.randn(30) * 0.5

# Confidence interval widens over time (typical for forecasts)
uncertainty = 1.5 + 0.15 * days
y_lower = y - uncertainty
y_upper = y + uncertainty

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Shaded confidence band (semi-transparent)
ax.fill_between(days, y_lower, y_upper, alpha=0.3, color="#306998", label="95% Confidence Interval")

# Central trend line (prominent)
ax.plot(days, y, color="#306998", linewidth=3, label="Forecast Mean")

# Styling
ax.set_xlabel("Days Ahead", fontsize=20)
ax.set_ylabel("Temperature (°C)", fontsize=20)
ax.set_title("line-confidence · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")

# Set axis limits for clean display
ax.set_xlim(1, 30)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
