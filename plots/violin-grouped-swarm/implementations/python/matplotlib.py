""" pyplots.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Response times across task types and expertise levels
np.random.seed(42)

categories = ["Simple", "Moderate", "Complex"]
groups = ["Novice", "Expert"]
colors = ["#306998", "#FFD43B"]  # Python Blue, Python Yellow

# Generate data: different distributions for each category-group combination
data = {}
positions = {}
width = 0.35  # Width of each violin

for i, cat in enumerate(categories):
    for j, grp in enumerate(groups):
        if grp == "Novice":
            if cat == "Simple":
                vals = np.random.normal(loc=1.2, scale=0.3, size=40)
            elif cat == "Moderate":
                vals = np.random.normal(loc=2.5, scale=0.5, size=40)
            else:  # Complex
                vals = np.random.normal(loc=4.5, scale=0.8, size=40)
        else:  # Expert
            if cat == "Simple":
                vals = np.random.normal(loc=0.8, scale=0.2, size=40)
            elif cat == "Moderate":
                vals = np.random.normal(loc=1.5, scale=0.3, size=40)
            else:  # Complex
                vals = np.random.normal(loc=2.5, scale=0.5, size=40)
        # Ensure positive values (response times can't be negative)
        vals = np.maximum(vals, 0.1)
        data[(cat, grp)] = vals
        # Calculate position: center position + offset for group
        offset = -width / 2 if j == 0 else width / 2
        positions[(cat, grp)] = i + offset

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Draw violins for each group
for j, grp in enumerate(groups):
    violin_data = [data[(cat, grp)] for cat in categories]
    pos = [i + (-width / 2 if j == 0 else width / 2) for i in range(len(categories))]

    parts = ax.violinplot(
        violin_data, positions=pos, widths=width * 0.9, showmeans=False, showmedians=True, showextrema=False
    )

    # Style the violins
    for pc in parts["bodies"]:
        pc.set_facecolor(colors[j])
        pc.set_edgecolor("black")
        pc.set_alpha(0.5)
        pc.set_linewidth(1.5)

    # Style median lines
    parts["cmedians"].set_color("black")
    parts["cmedians"].set_linewidth(2)

# Overlay swarm points
for cat in categories:
    for j, grp in enumerate(groups):
        vals = data[(cat, grp)]
        base_x = positions[(cat, grp)]

        # Create swarm-like jitter (beeswarm approximation)
        # Sort values and assign positions based on density
        sorted_indices = np.argsort(vals)
        n_points = len(vals)
        jitter = np.zeros(n_points)

        # Group points by value bins and spread horizontally
        bin_width = (vals.max() - vals.min()) / 20
        for idx in sorted_indices:
            val = vals[idx]
            # Find nearby points
            nearby = np.abs(vals - val) < bin_width
            nearby_count = np.sum(nearby & (np.arange(n_points) <= idx))
            # Alternate left and right
            if nearby_count % 2 == 0:
                jitter[idx] = (nearby_count // 2) * 0.015
            else:
                jitter[idx] = -((nearby_count + 1) // 2) * 0.015

        x_positions = base_x + jitter

        ax.scatter(x_positions, vals, s=40, c=colors[j], edgecolors="black", linewidths=0.5, alpha=0.8, zorder=3)

# Styling
ax.set_xticks(range(len(categories)))
ax.set_xticklabels(categories, fontsize=18)
ax.set_xlabel("Task Complexity", fontsize=20)
ax.set_ylabel("Response Time (seconds)", fontsize=20)
ax.set_title("violin-grouped-swarm · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Legend
legend_handles = [
    plt.Rectangle((0, 0), 1, 1, facecolor=colors[0], edgecolor="black", alpha=0.5, label=groups[0]),
    plt.Rectangle((0, 0), 1, 1, facecolor=colors[1], edgecolor="black", alpha=0.5, label=groups[1]),
]
ax.legend(handles=legend_handles, fontsize=16, title="Expertise", title_fontsize=18, loc="upper left")

# Grid
ax.grid(True, alpha=0.3, linestyle="--", axis="y")
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
