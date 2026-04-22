"""pyplots.ai
raincloud-basic: Basic Raincloud Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


# Data: Reaction times (ms) for three experimental conditions
np.random.seed(42)

# Control group: Normal distribution centered around 350ms
control = np.random.normal(350, 50, 80)

# Treatment A: Faster responses, clearly bimodal with distinct modes
treatment_a = np.concatenate(
    [
        np.random.normal(250, 25, 45),  # Fast responders - more separation
        np.random.normal(340, 25, 35),  # Slower subgroup
    ]
)

# Treatment B: Mixed results with some outliers
treatment_b = np.concatenate(
    [
        np.random.normal(300, 40, 60),
        np.random.normal(400, 25, 15),  # Slower subgroup
        np.array([500, 520, 480]),  # Outliers
    ]
)

categories = ["Control", "Treatment A", "Treatment B"]
data = [control, treatment_a, treatment_b]
colors = ["#306998", "#FFD43B", "#4CAF50"]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Layout: Cloud (violin) on TOP, boxplot in MIDDLE, rain (points) BELOW
# Using horizontal orientation with categories on y-axis
cloud_offset = 0.2  # Offset for cloud (positive = top)
rain_offset = -0.25  # Offset for rain (negative = below)
box_width = 0.1

for i, (d, color) in enumerate(zip(data, colors, strict=True)):
    pos = i + 1

    # Calculate KDE for half-violin (Silverman's rule for bandwidth)
    n = len(d)
    std = np.std(d)
    bw = 1.06 * std * n ** (-1 / 5)

    x_min, x_max = d.min() - 30, d.max() + 30
    x_vals = np.linspace(x_min, x_max, 200)

    # Gaussian kernel density estimation
    kde_vals = np.zeros_like(x_vals)
    for point in d:
        kde_vals += np.exp(-0.5 * ((x_vals - point) / bw) ** 2) / (bw * np.sqrt(2 * np.pi))
    kde_vals /= n

    # Normalize and scale violin width (height in horizontal orientation)
    kde_scaled = kde_vals / kde_vals.max() * 0.3

    # Draw half-violin (cloud) on TOP (above the boxplot)
    ax.fill_between(
        x_vals,
        pos + cloud_offset,
        pos + cloud_offset + kde_scaled,
        alpha=0.7,
        color=color,
        edgecolor="white",
        linewidth=1.5,
    )

    # Draw horizontal box plot in the middle
    bp = ax.boxplot([d], positions=[pos], widths=box_width, vert=False, patch_artist=True, showfliers=False, zorder=3)

    # Style box plot
    bp["boxes"][0].set_facecolor("white")
    bp["boxes"][0].set_edgecolor("#333333")
    bp["boxes"][0].set_linewidth(2)
    bp["medians"][0].set_color("#333333")
    bp["medians"][0].set_linewidth(2.5)
    for whisker in bp["whiskers"]:
        whisker.set_color("#333333")
        whisker.set_linewidth(1.5)
    for cap in bp["caps"]:
        cap.set_color("#333333")
        cap.set_linewidth(1.5)

    # Draw jittered points (rain) BELOW the boxplot
    jitter = np.random.uniform(-0.06, 0.06, len(d))
    ax.scatter(
        d,
        pos + rain_offset + jitter,
        s=110,  # Increased from 80 for better visibility
        alpha=0.6,
        color=color,
        edgecolor="white",
        linewidth=0.5,
        zorder=2,
    )

# Styling
ax.set_yticks([1, 2, 3])
ax.set_yticklabels(categories, fontsize=18)
ax.set_xlabel("Reaction Time (ms)", fontsize=20)
ax.set_ylabel("Experimental Condition", fontsize=20)
ax.set_title("raincloud-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set axis ranges with padding
all_data = np.concatenate(data)
ax.set_xlim(all_data.min() - 50, all_data.max() + 50)
ax.set_ylim(0.4, 3.8)

# Subtle grid on x-axis only
ax.xaxis.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Custom legend - positioned outside plot area
legend_elements = [
    Patch(facecolor=c, edgecolor="white", alpha=0.7, label=cat) for c, cat in zip(colors, categories, strict=True)
]
ax.legend(
    handles=legend_elements, fontsize=16, loc="upper left", bbox_to_anchor=(1.02, 1), framealpha=0.9, edgecolor="none"
)

# Clean up spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(1.5)
ax.spines["bottom"].set_linewidth(1.5)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
