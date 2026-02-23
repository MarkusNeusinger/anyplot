""" pyplots.ai
band-basic: Basic Band Plot
Library: matplotlib 3.10.8 | Python 3.14
Quality: 86/100 | Updated: 2026-02-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Daily temperature forecast with 95% confidence interval
np.random.seed(42)
days = np.arange(1, 31)

# Central forecast: seasonal warming pattern peaking mid-month
temp_forecast = 12 + 6 * np.sin(np.pi * days / 30) + 0.1 * days

# Confidence interval widens further into the forecast (common in weather models)
uncertainty = 0.8 + 0.12 * days
temp_lower = temp_forecast - uncertainty
temp_upper = temp_forecast + uncertainty

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

ax.fill_between(days, temp_lower, temp_upper, alpha=0.25, color="#306998", label="95% Confidence Interval")
ax.plot(days, temp_forecast, color="#306998", linewidth=3, label="Forecast Mean")
ax.plot(days, temp_lower, color="#306998", linewidth=1.5, linestyle="--", alpha=0.5)
ax.plot(days, temp_upper, color="#306998", linewidth=1.5, linestyle="--", alpha=0.5)

# Style
ax.set_xlabel("Day of Month", fontsize=20)
ax.set_ylabel("Temperature (\u00b0C)", fontsize=20)
ax.set_title("band-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
