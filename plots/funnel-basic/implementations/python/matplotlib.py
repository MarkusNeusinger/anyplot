""" pyplots.ai
funnel-basic: Basic Funnel Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt


# Data - Sales funnel example from specification
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]

# Colors for each stage - distinct colors for visual differentiation
colors = ["#306998", "#4A8BBF", "#FFD43B", "#FFB347", "#FF6B6B"]

# Calculate widths proportional to first stage value
max_value = values[0]
widths = [v / max_value for v in values]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Funnel parameters
n_stages = len(stages)
stage_height = 0.8 / n_stages  # Total funnel height is 80% of plot
gap = 0.02  # Small gap between stages
y_start = 0.9  # Start from top

# Draw funnel segments as trapezoids
for i in range(n_stages):
    # Current stage width
    w_top = widths[i]
    # Next stage width (or smaller for last stage)
    w_bottom = widths[i + 1] if i < n_stages - 1 else widths[i] * 0.6

    # Calculate y positions
    y_top = y_start - i * (stage_height + gap)
    y_bottom = y_top - stage_height

    # Calculate x positions (centered)
    x_center = 0.5
    x_top_left = x_center - w_top / 2
    x_top_right = x_center + w_top / 2
    x_bottom_left = x_center - w_bottom / 2
    x_bottom_right = x_center + w_bottom / 2

    # Create trapezoid vertices
    trapezoid = patches.Polygon(
        [(x_top_left, y_top), (x_top_right, y_top), (x_bottom_right, y_bottom), (x_bottom_left, y_bottom)],
        closed=True,
        facecolor=colors[i],
        edgecolor="white",
        linewidth=2,
    )
    ax.add_patch(trapezoid)

    # Add stage label and value
    y_mid = (y_top + y_bottom) / 2
    percentage = (values[i] / max_value) * 100
    label_text = f"{stages[i]}\n{values[i]:,} ({percentage:.0f}%)"
    ax.text(
        x_center,
        y_mid,
        label_text,
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="white" if i < 2 else "black",
    )

# Styling
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect("equal")
ax.axis("off")

ax.set_title("funnel-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
