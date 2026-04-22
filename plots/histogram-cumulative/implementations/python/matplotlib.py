""" pyplots.ai
histogram-cumulative: Cumulative Histogram
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - exam scores with realistic distribution
np.random.seed(42)
scores = np.concatenate(
    [
        np.random.normal(65, 10, 300),  # Average performers
        np.random.normal(85, 5, 150),  # High performers
        np.random.normal(45, 8, 50),  # Lower performers
    ]
)
# Clip to realistic exam score range
scores = np.clip(scores, 0, 100)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Cumulative histogram with step display
n, bins, patches = ax.hist(
    scores,
    bins=30,
    cumulative=True,
    density=True,
    histtype="step",
    linewidth=3,
    color="#306998",
    label="Cumulative Distribution",
)

# Add filled area under the step function for better visibility
ax.hist(scores, bins=30, cumulative=True, density=True, histtype="stepfilled", alpha=0.3, color="#306998")

# Add reference lines at common percentiles
percentiles = [25, 50, 75, 90]
for p in percentiles:
    pct_value = np.percentile(scores, p)
    ax.axhline(y=p / 100, color="#FFD43B", linestyle="--", linewidth=2, alpha=0.7)
    ax.axvline(x=pct_value, color="#FFD43B", linestyle="--", linewidth=2, alpha=0.7)

    # Position annotations to avoid overlap and clipping
    if p == 90:
        xytext = (pct_value - 15, p / 100 - 0.06)
        ha = "right"
    elif p == 75:
        xytext = (pct_value - 15, p / 100 + 0.02)
        ha = "right"
    else:
        xytext = (pct_value + 3, p / 100 + 0.03)
        ha = "left"

    ax.annotate(
        f"{p}th percentile (score ≈ {pct_value:.0f})",
        xy=(pct_value, p / 100),
        xytext=xytext,
        fontsize=14,
        color="#333333",
        ha=ha,
    )

# Labels and styling
ax.set_xlabel("Exam Score", fontsize=20)
ax.set_ylabel("Cumulative Proportion", fontsize=20)
ax.set_title("histogram-cumulative · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0, 100)
ax.set_ylim(0, 1.05)
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="lower right")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
