""" pyplots.ai
funnel-basic: Basic Funnel Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Polygon


# Set seed for reproducibility
np.random.seed(42)

# Data - Sales funnel example from specification
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]
max_value = values[0]

# Calculate percentages
percentages = [v / max_value * 100 for v in values]

# Seaborn styling
sns.set_theme(style="white")

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Color palette using Python Blue to Gold progression
colors = sns.color_palette(["#306998", "#4078A8", "#6AA8D1", "#FFD43B", "#E8C547"])

# Funnel parameters
n_stages = len(stages)
funnel_height = 0.8  # Total height of funnel
stage_gap = 0.02  # Gap between stages
stage_height = (funnel_height - (n_stages - 1) * stage_gap) / n_stages
center_x = 0.5

# Draw trapezoidal funnel segments
for i in range(n_stages):
    # Calculate widths - proportional to value relative to max
    top_width = values[i] / max_value * 0.8
    # Bottom width is the next stage's width, or smaller for last stage
    if i < n_stages - 1:
        bottom_width = values[i + 1] / max_value * 0.8
    else:
        bottom_width = values[i] / max_value * 0.8 * 0.6  # Narrower bottom for last stage

    # Calculate y positions (top to bottom)
    y_top = 1 - 0.1 - i * (stage_height + stage_gap)
    y_bottom = y_top - stage_height

    # Create trapezoid vertices (clockwise from top-left)
    vertices = [
        (center_x - top_width / 2, y_top),  # Top-left
        (center_x + top_width / 2, y_top),  # Top-right
        (center_x + bottom_width / 2, y_bottom),  # Bottom-right
        (center_x - bottom_width / 2, y_bottom),  # Bottom-left
    ]

    # Draw trapezoid using matplotlib Polygon
    trapezoid = Polygon(vertices, facecolor=colors[i], edgecolor="white", linewidth=3, closed=True)
    ax.add_patch(trapezoid)

    # Calculate center of trapezoid for label placement
    center_y = (y_top + y_bottom) / 2

    # Add stage name on the left
    ax.text(
        center_x - top_width / 2 - 0.05,
        center_y,
        stages[i],
        ha="right",
        va="center",
        fontsize=20,
        fontweight="bold",
        color="#333333",
    )

    # Add value and percentage label in center
    label_text = f"{values[i]:,} ({percentages[i]:.0f}%)"
    # Choose text color based on background brightness
    text_color = "white" if i < 3 else "#333333"
    ax.text(center_x, center_y, label_text, ha="center", va="center", fontsize=18, fontweight="bold", color=text_color)

    # Add conversion rate between stages
    if i < n_stages - 1:
        conversion_rate = values[i + 1] / values[i] * 100
        ax.text(
            center_x + top_width / 2 + 0.05,
            y_bottom,
            f"↓ {conversion_rate:.0f}%",
            ha="left",
            va="center",
            fontsize=14,
            color="#666666",
            style="italic",
        )

# Set axis limits and remove decorations
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect("equal")
ax.axis("off")

# Title
ax.set_title("funnel-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
