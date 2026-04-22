""" pyplots.ai
parliament-basic: Parliament Seat Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set random seed for reproducibility
np.random.seed(42)

# Data: Corporate board composition by department (neutral context)
groups = ["Engineering", "Operations", "Finance", "Marketing", "Research", "Legal"]
seats = [85, 72, 45, 38, 22, 18]
total_seats = sum(seats)

# Use seaborn's colorblind-safe palette
colors = sns.color_palette("colorblind", n_colors=len(groups))

# Set seaborn style
sns.set_style("white")
sns.set_context("talk", font_scale=1.2)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Calculate parliament layout - semicircular arrangement with 5 rows
n_rows = 5
row_proportions = [(i + 1) for i in range(n_rows)]
total_prop = sum(row_proportions)
seats_per_row = [int(total_seats * p / total_prop) for p in row_proportions]
seats_per_row[-1] += total_seats - sum(seats_per_row)  # Adjust for rounding

# Create all seat positions in concentric arcs
all_positions = []
for row_idx, n_seats_row in enumerate(seats_per_row):
    radius = 0.4 + row_idx * 0.15
    angles = np.linspace(np.pi, 0, n_seats_row)
    for angle in angles:
        all_positions.append((radius * np.cos(angle), radius * np.sin(angle), row_idx))

# Sort positions left to right for natural group ordering
all_positions.sort(key=lambda p: (p[0], -p[1]))

# Build DataFrame for seaborn plotting
x_coords, y_coords, group_labels = [], [], []
seat_idx = 0
for group_idx, n_seats in enumerate(seats):
    for _ in range(n_seats):
        if seat_idx < len(all_positions):
            x_coords.append(all_positions[seat_idx][0])
            y_coords.append(all_positions[seat_idx][1])
            group_labels.append(groups[group_idx])
            seat_idx += 1

# Create DataFrame for seaborn
df = pd.DataFrame({"x": x_coords, "y": y_coords, "group": group_labels})

# Plot seats using seaborn scatterplot (uses hue for grouping)
sns.scatterplot(
    data=df,
    x="x",
    y="y",
    hue="group",
    hue_order=groups,
    palette="colorblind",
    s=350,
    edgecolor="white",
    linewidth=1.5,
    legend=False,
    ax=ax,
    zorder=2,
)

# Add majority threshold line
majority = total_seats // 2 + 1
ax.axhline(y=0, color="#666666", linestyle="--", linewidth=2, alpha=0.5, zorder=1)
ax.text(0.85, 0.02, f"Majority: {majority} seats", fontsize=14, color="#666666", ha="right", transform=ax.transAxes)

# Create legend with seat counts
legend_elements = [
    plt.scatter([], [], c=[colors[i]], s=200, label=f"{group}: {seat_count}")
    for i, (group, seat_count) in enumerate(zip(groups, seats, strict=True))
]
ax.legend(
    handles=legend_elements,
    loc="upper left",
    fontsize=14,
    frameon=True,
    facecolor="white",
    edgecolor="lightgray",
    title="Departments",
    title_fontsize=16,
)

# Style adjustments
ax.set_xlim(-1.1, 1.1)
ax.set_ylim(-0.15, 1.0)
ax.set_aspect("equal")
ax.axis("off")

# Title
ax.set_title("parliament-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Add total seats annotation
ax.text(0.5, -0.08, f"Total: {total_seats} seats", fontsize=18, ha="center", transform=ax.transAxes, color="#333333")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
