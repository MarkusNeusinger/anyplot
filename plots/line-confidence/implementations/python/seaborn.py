""" pyplots.ai
line-confidence: Line Plot with Confidence Interval
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Monthly sales forecast with 95% confidence interval
np.random.seed(42)

# Generate monthly data points
months = np.arange(1, 25)  # 24 months

# Create a realistic trend with seasonality
base_trend = 100 + months * 2.5  # Upward trend
seasonality = 15 * np.sin(2 * np.pi * months / 12)  # Annual cycle
noise = np.random.randn(len(months)) * 8

# Central forecast line
y_forecast = base_trend + seasonality + noise

# Confidence interval - widens further into future (uncertainty grows)
uncertainty = 5 + months * 0.8  # Growing uncertainty
y_lower = y_forecast - 1.96 * uncertainty
y_upper = y_forecast + 1.96 * uncertainty

# Create plot
sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(16, 9))

# Plot confidence band using fill_between (seaborn built on matplotlib)
ax.fill_between(months, y_lower, y_upper, alpha=0.3, color="#306998", label="95% Confidence Interval")

# Plot central line using seaborn's lineplot
sns.lineplot(x=months, y=y_forecast, ax=ax, color="#306998", linewidth=3, label="Forecast")

# Style
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Sales (Units)", fontsize=20)
ax.set_title("line-confidence · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")

# Set axis limits to show all data with padding
ax.set_xlim(0, 25)
ax.set_ylim(min(y_lower) - 10, max(y_upper) + 10)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
