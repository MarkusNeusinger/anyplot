""" pyplots.ai
rug-basic: Basic Rug Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - response times with clusters and gaps
np.random.seed(42)
# Simulate response times with a bimodal pattern (fast and slow responses)
fast_responses = np.random.normal(loc=150, scale=30, size=80)
slow_responses = np.random.normal(loc=350, scale=50, size=40)
response_times = np.concatenate([fast_responses, slow_responses])

# Add a few outliers to show edge detection capability
outliers = np.array([50, 520, 550])
response_times = np.concatenate([response_times, outliers])

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Rug plot showing individual observations
sns.rugplot(x=response_times, height=0.15, lw=2.5, alpha=0.7, color="#306998", ax=ax)

# Styling
ax.set_xlabel("Response Time (ms)", fontsize=20)
ax.set_ylabel("")
ax.set_title("rug-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set y-axis limits to give the rug marks space
ax.set_ylim(0, 1)
ax.set_yticks([])

# Add subtle grid on x-axis only
ax.grid(True, axis="x", alpha=0.3, linestyle="--")

# Set x-axis to show full range with padding
ax.set_xlim(0, 600)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
