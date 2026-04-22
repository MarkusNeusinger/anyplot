""" pyplots.ai
histogram-stepwise: Step Histogram
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Simulating response times (ms) for two different services
np.random.seed(42)
service_a = np.random.exponential(scale=50, size=500) + 20  # Faster service
service_b = np.random.exponential(scale=80, size=500) + 40  # Slower service

# Create plot (4800x2700 px at 300 dpi = 16x9 inches)
fig, ax = plt.subplots(figsize=(16, 9))

# Step histograms - using histplot with element='step' and fill=False
sns.histplot(service_a, bins=30, element="step", fill=False, color="#306998", linewidth=3, label="Service A", ax=ax)

sns.histplot(service_b, bins=30, element="step", fill=False, color="#FFD43B", linewidth=3, label="Service B", ax=ax)

# Labels and styling
ax.set_xlabel("Response Time (ms)", fontsize=20)
ax.set_ylabel("Count", fontsize=20)
ax.set_title("histogram-stepwise · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper right")
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
