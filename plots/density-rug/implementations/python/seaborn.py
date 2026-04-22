""" pyplots.ai
density-rug: Density Plot with Rug Marks
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Response times (ms) for a web application
np.random.seed(42)
# Create a realistic bimodal distribution: most requests are fast, some are slower
fast_responses = np.random.normal(loc=120, scale=25, size=180)
slow_responses = np.random.normal(loc=280, scale=40, size=70)
response_times = np.concatenate([fast_responses, slow_responses])
# Clip to realistic bounds
response_times = np.clip(response_times, 50, 400)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot KDE with fill
sns.kdeplot(data=response_times, ax=ax, fill=True, alpha=0.4, color="#306998", linewidth=3, bw_adjust=0.8)

# Add rug plot
sns.rugplot(data=response_times, ax=ax, color="#306998", alpha=0.6, height=0.05, linewidth=1.5)

# Styling
ax.set_xlabel("Response Time (ms)", fontsize=20)
ax.set_ylabel("Density", fontsize=20)
ax.set_title("density-rug · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
