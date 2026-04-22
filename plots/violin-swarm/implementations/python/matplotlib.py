""" pyplots.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Reaction times (ms) across 4 experimental conditions
np.random.seed(42)

conditions = ["Control", "Treatment A", "Treatment B", "Treatment C"]
n_per_group = 50

# Generate different distributions for each condition
data = {
    "Control": np.random.normal(450, 60, n_per_group),
    "Treatment A": np.random.normal(380, 45, n_per_group),
    "Treatment B": np.random.normal(420, 80, n_per_group),
    "Treatment C": np.concatenate(
        [np.random.normal(350, 30, n_per_group // 2), np.random.normal(450, 30, n_per_group // 2)]
    ),  # Bimodal
}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Prepare data for violin plot
violin_data = [data[cond] for cond in conditions]
positions = np.arange(len(conditions))

# Draw violin plot with transparency
parts = ax.violinplot(violin_data, positions=positions, showmeans=False, showmedians=False, showextrema=False)

# Style violins with Python Blue and transparency
for pc in parts["bodies"]:
    pc.set_facecolor("#306998")
    pc.set_edgecolor("#306998")
    pc.set_alpha(0.4)
    pc.set_linewidth(2)

# Overlay swarm points
for cond, pos in zip(conditions, positions, strict=True):
    y = data[cond]
    # Add jitter to spread points horizontally (swarm-like effect)
    # Calculate density-based jitter
    n_points = len(y)
    jitter = np.zeros(n_points)

    # Sort points and assign horizontal positions based on local density
    sorted_indices = np.argsort(y)
    sorted_y = y[sorted_indices]

    # Calculate jitter based on nearby point density
    bandwidth = (np.max(y) - np.min(y)) / 20
    for j, (idx, val) in enumerate(zip(sorted_indices, sorted_y, strict=True)):
        # Count nearby points
        nearby = np.sum(np.abs(sorted_y - val) < bandwidth)
        # Assign alternating jitter based on position within group
        local_idx = np.sum(np.abs(sorted_y[: j + 1] - val) < bandwidth) - 1
        max_jitter = 0.25 * (nearby / n_points) ** 0.5 + 0.05
        jitter[idx] = (local_idx % 2 * 2 - 1) * max_jitter * ((local_idx // 2 + 1) / (nearby / 2 + 1))

    x = np.full(n_points, pos) + jitter
    ax.scatter(x, y, s=80, alpha=0.8, color="#FFD43B", edgecolor="#306998", linewidth=1, zorder=3)

# Add median lines
for i, pos in enumerate(positions):
    median = np.median(violin_data[i])
    ax.hlines(median, pos - 0.2, pos + 0.2, color="#1a3d5c", linewidth=3, zorder=4)

# Styling
ax.set_xticks(positions)
ax.set_xticklabels(conditions, fontsize=18)
ax.set_xlabel("Experimental Condition", fontsize=20)
ax.set_ylabel("Reaction Time (ms)", fontsize=20)
ax.set_title("violin-swarm · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Set y-axis limits with padding
all_values = np.concatenate(violin_data)
y_min, y_max = np.min(all_values), np.max(all_values)
y_padding = (y_max - y_min) * 0.1
ax.set_ylim(y_min - y_padding, y_max + y_padding)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
