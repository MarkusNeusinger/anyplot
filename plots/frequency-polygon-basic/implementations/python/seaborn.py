""" pyplots.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Response times (ms) for three experimental conditions
np.random.seed(42)
n_per_group = 200

# Control group: centered around 450ms
control = np.random.normal(loc=450, scale=60, size=n_per_group)

# Treatment A: faster responses, centered around 380ms
treatment_a = np.random.normal(loc=380, scale=50, size=n_per_group)

# Treatment B: bimodal - some fast, some slow responders
treatment_b = np.concatenate(
    [
        np.random.normal(loc=350, scale=40, size=n_per_group // 2),
        np.random.normal(loc=500, scale=45, size=n_per_group // 2),
    ]
)

# Common bin edges for all groups (aligned for accurate comparison)
all_data = np.concatenate([control, treatment_a, treatment_b])
bins = np.linspace(all_data.min() - 10, all_data.max() + 10, 25)
bin_centers = (bins[:-1] + bins[1:]) / 2

# Compute frequencies for each group (extend to zero at ends for closed polygon)
ctrl_counts, _ = np.histogram(control, bins=bins)
ctrl_x = np.concatenate([[bins[0]], bin_centers, [bins[-1]]])
ctrl_y = np.concatenate([[0], ctrl_counts, [0]])

trt_a_counts, _ = np.histogram(treatment_a, bins=bins)
trt_a_x = np.concatenate([[bins[0]], bin_centers, [bins[-1]]])
trt_a_y = np.concatenate([[0], trt_a_counts, [0]])

trt_b_counts, _ = np.histogram(treatment_b, bins=bins)
trt_b_x = np.concatenate([[bins[0]], bin_centers, [bins[-1]]])
trt_b_y = np.concatenate([[0], trt_b_counts, [0]])

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Plot frequency polygons using seaborn's lineplot
# Control group - Python Blue
sns.lineplot(
    x=ctrl_x,
    y=ctrl_y,
    ax=ax,
    linewidth=3,
    color="#306998",
    label="Control",
    marker="o",
    markersize=8,
    markevery=slice(1, -1),
)
ax.fill_between(ctrl_x, ctrl_y, alpha=0.15, color="#306998")

# Treatment A - Python Yellow
sns.lineplot(
    x=trt_a_x,
    y=trt_a_y,
    ax=ax,
    linewidth=3,
    color="#FFD43B",
    label="Treatment A",
    marker="s",
    markersize=8,
    markevery=slice(1, -1),
)
ax.fill_between(trt_a_x, trt_a_y, alpha=0.15, color="#FFD43B")

# Treatment B - Teal (colorblind-safe)
sns.lineplot(
    x=trt_b_x,
    y=trt_b_y,
    ax=ax,
    linewidth=3,
    color="#2AA198",
    label="Treatment B",
    marker="^",
    markersize=8,
    markevery=slice(1, -1),
)
ax.fill_between(trt_b_x, trt_b_y, alpha=0.15, color="#2AA198")

# Styling
ax.set_xlabel("Response Time (ms)", fontsize=20)
ax.set_ylabel("Frequency", fontsize=20)
ax.set_title("frequency-polygon-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper right", framealpha=0.9)
ax.set_ylim(bottom=0)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
