""" pyplots.ai
area-stacked: Stacked Area Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Monthly website traffic sources over 24 months
np.random.seed(42)
months = np.arange(1, 25)

# Simulate traffic growth with realistic patterns
base_organic = 45000 + np.cumsum(np.random.randn(24) * 800 + 300)
base_direct = 30000 + np.cumsum(np.random.randn(24) * 600 + 200)
base_social = 15000 + np.cumsum(np.random.randn(24) * 400 + 250)
base_referral = 10000 + np.cumsum(np.random.randn(24) * 300 + 100)

# Ensure all values are positive
organic = np.maximum(base_organic, 5000)
direct = np.maximum(base_direct, 3000)
social = np.maximum(base_social, 2000)
referral = np.maximum(base_referral, 1000)

# Stack data (largest at bottom for easier reading)
categories = ["Organic Search", "Direct", "Social Media", "Referral"]
data = np.vstack([organic, direct, social, referral])

# Colors: Python Blue, Python Yellow, then colorblind-safe additions
colors = ["#306998", "#FFD43B", "#4DAF4A", "#984EA3"]

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

ax.stackplot(months, data, labels=categories, colors=colors, alpha=0.85)

# X-axis formatting (show as months)
tick_positions = [1, 6, 12, 18, 24]
tick_labels = ["Jan 2023", "Jun 2023", "Dec 2023", "Jun 2024", "Dec 2024"]
ax.set_xticks(tick_positions)
ax.set_xticklabels(tick_labels)

# Labels and styling
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Monthly Visitors", fontsize=20)
ax.set_title("area-stacked · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Legend (outside plot, upper right)
ax.legend(loc="upper left", fontsize=16, framealpha=0.9)

# Ensure y-axis starts at zero
ax.set_ylim(bottom=0)
ax.set_xlim(1, 24)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
