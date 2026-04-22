""" pyplots.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


# Data: Sales figures (in millions $) for products comparing Q1 vs Q4
# Deterministic data with well-spaced values to avoid label overlap
products = ["Product A", "Product B", "Product C", "Product D", "Product E", "Product F", "Product G", "Product H"]
q1_sales = [3.0, 6.5, 10.0, 13.5, 17.0, 20.5, 24.0, 27.5]
q4_sales = [5.5, 4.0, 14.0, 11.0, 20.0, 17.5, 28.0, 25.0]

# Calculate changes to determine colors
changes = [q4 - q1 for q1, q4 in zip(q1_sales, q4_sales, strict=True)]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Label collision avoidance: sort and adjust positions if too close
min_gap = 1.8

# Adjust Q1 labels (left side)
q1_indexed = sorted(enumerate(q1_sales), key=lambda x: x[1])
q1_label_pos = [0.0] * len(q1_sales)
for i, (orig_idx, val) in enumerate(q1_indexed):
    if i == 0:
        q1_label_pos[orig_idx] = val
    else:
        prev_idx = q1_indexed[i - 1][0]
        if val - q1_label_pos[prev_idx] < min_gap:
            q1_label_pos[orig_idx] = q1_label_pos[prev_idx] + min_gap
        else:
            q1_label_pos[orig_idx] = val

# Adjust Q4 labels (right side)
q4_indexed = sorted(enumerate(q4_sales), key=lambda x: x[1])
q4_label_pos = [0.0] * len(q4_sales)
for i, (orig_idx, val) in enumerate(q4_indexed):
    if i == 0:
        q4_label_pos[orig_idx] = val
    else:
        prev_idx = q4_indexed[i - 1][0]
        if val - q4_label_pos[prev_idx] < min_gap:
            q4_label_pos[orig_idx] = q4_label_pos[prev_idx] + min_gap
        else:
            q4_label_pos[orig_idx] = val

# Plot each slope line
x_positions = [0, 1]
for i, (product, q1, q4, change) in enumerate(zip(products, q1_sales, q4_sales, changes, strict=True)):
    # Color by direction: blue for increase, yellow/orange for decrease
    color = "#306998" if change >= 0 else "#FFD43B"
    ax.plot(x_positions, [q1, q4], marker="o", markersize=12, linewidth=3, color=color)

    # Labels at both endpoints with adjusted positions to avoid overlap
    ax.text(
        -0.05,
        q1_label_pos[i],
        f"{product}: ${q1:.1f}M",
        ha="right",
        va="center",
        fontsize=14,
        color=color,
        fontweight="bold",
    )
    ax.text(1.05, q4_label_pos[i], f"${q4:.1f}M", ha="left", va="center", fontsize=14, color=color, fontweight="bold")

# Style the axes
ax.set_xlim(-0.6, 1.6)
ax.set_xticks(x_positions)
ax.set_xticklabels(["Q1 2024", "Q4 2024"], fontsize=20, fontweight="bold")
ax.set_ylabel("Sales (Millions $)", fontsize=20)
ax.set_title("slope-basic · matplotlib · pyplots.ai", fontsize=24)

# Remove spines and set grid
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.tick_params(axis="y", labelsize=16)
ax.tick_params(axis="x", length=0)
ax.grid(True, axis="y", alpha=0.3, linestyle="--")

# Add legend for color coding
legend_elements = [
    Line2D([0], [0], color="#306998", linewidth=3, label="Increase"),
    Line2D([0], [0], color="#FFD43B", linewidth=3, label="Decrease"),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=16)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
