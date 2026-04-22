""" pyplots.ai
histogram-cumulative: Cumulative Histogram
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Response times for a web API service (realistic scenario)
np.random.seed(42)
response_times = np.concatenate(
    [
        np.random.exponential(scale=50, size=300),  # Fast responses (majority)
        np.random.normal(loc=200, scale=30, size=100),  # Moderate responses
        np.random.normal(loc=400, scale=50, size=50),  # Slow responses
    ]
)
response_times = np.clip(response_times, 5, 600)  # Clip to realistic range (5-600ms)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot cumulative histogram using seaborn's histplot with cumulative=True
sns.histplot(
    response_times,
    bins=40,
    cumulative=True,
    stat="proportion",
    element="step",
    fill=True,
    color="#306998",
    alpha=0.7,
    linewidth=2.5,
    edgecolor="#306998",
    ax=ax,
)

# Add reference lines for common percentiles
percentiles = [50, 90, 95, 99]
percentile_values = np.percentile(response_times, percentiles)
colors = ["#FFD43B", "#FF8C00", "#FF4500", "#DC143C"]

for p, val, color in zip(percentiles, percentile_values, colors, strict=True):
    ax.axhline(y=p / 100, color=color, linestyle="--", linewidth=2, alpha=0.8)
    ax.axvline(x=val, color=color, linestyle="--", linewidth=2, alpha=0.8)
    ax.annotate(
        f"P{p}: {val:.0f}ms",
        xy=(val, p / 100),
        xytext=(val + 30, p / 100 + 0.03),
        fontsize=14,
        color=color,
        fontweight="bold",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": color, "alpha": 0.9},
    )

# Labels and styling
ax.set_xlabel("Response Time (ms)", fontsize=20)
ax.set_ylabel("Cumulative Proportion", fontsize=20)
ax.set_title("histogram-cumulative · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Set axis limits
ax.set_xlim(0, 600)
ax.set_ylim(0, 1.05)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
