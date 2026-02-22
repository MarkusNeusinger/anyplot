"""pyplots.ai
bullet-basic: Basic Bullet Chart
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: /100 | Updated: 2026-02-22
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch


# Data - Quarterly KPI dashboard with percentage-based metrics for consistent comparison
metrics = [
    {"label": "Revenue", "actual": 92, "target": 85, "ranges": [40, 70, 100]},
    {"label": "Profit Margin", "actual": 38, "target": 45, "ranges": [20, 40, 60]},
    {"label": "Customer Growth", "actual": 71, "target": 80, "ranges": [30, 60, 100]},
    {"label": "Satisfaction", "actual": 84, "target": 90, "ranges": [50, 75, 100]},
    {"label": "On-Time Delivery", "actual": 96, "target": 95, "ranges": [60, 80, 100]},
]

# Qualitative band colors (grayscale: poor -> satisfactory -> good)
band_colors = ["#e0e0e0", "#c8c8c8", "#b0b0b0"]
actual_color = "#306998"
target_color = "#1a1a1a"

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9))

bar_height = 0.32
band_height = bar_height * 2.4
spacing = 1.2
y_positions = [i * spacing for i in range(len(metrics))]

for i, metric in enumerate(metrics):
    y = y_positions[i]
    ranges = metric["ranges"]

    # Draw qualitative range bands using FancyBboxPatch for rounded corners
    band_starts = [0] + ranges[:-1]
    for j, (start, end) in enumerate(zip(band_starts, ranges, strict=True)):
        width = end - start
        box = FancyBboxPatch(
            (start, y - band_height / 2),
            width,
            band_height,
            boxstyle="round,pad=0,rounding_size=0.08",
            facecolor=band_colors[j],
            edgecolor="none",
            zorder=1,
        )
        ax.add_patch(box)

    # Draw actual value bar
    actual_bar = FancyBboxPatch(
        (0, y - bar_height / 2),
        metric["actual"],
        bar_height,
        boxstyle="round,pad=0,rounding_size=0.06",
        facecolor=actual_color,
        edgecolor="none",
        zorder=2,
    )
    ax.add_patch(actual_bar)

    # Draw target marker (diamond with white outline for visibility)
    ax.plot(
        metric["target"],
        y,
        marker="D",
        markersize=11,
        color=target_color,
        zorder=3,
        path_effects=[pe.withStroke(linewidth=3, foreground="white")],
    )

    # Actual value label to the right of the max range
    ax.text(
        ranges[-1] + 2,
        y,
        f"{metric['actual']}%",
        va="center",
        ha="left",
        fontsize=16,
        fontweight="bold",
        color=actual_color,
        zorder=4,
    )

# Y-axis labels (metric names)
ax.set_yticks(y_positions)
ax.set_yticklabels([m["label"] for m in metrics], fontsize=18, fontweight="bold")

# X-axis label — all metrics share a percentage scale
ax.set_xlabel("Performance (%)", fontsize=20)
ax.tick_params(axis="x", labelsize=16)
ax.tick_params(axis="y", length=0)

# Title
ax.set_title("bullet-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20)

# Grid on x-axis only, subtle
ax.xaxis.grid(True, alpha=0.2, linewidth=0.8, linestyle="--", zorder=0)
ax.set_axisbelow(True)

# Remove spines for cleaner look
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

# Set axis limits
ax.set_xlim(left=0, right=112)
ax.set_ylim(-spacing * 0.5, y_positions[-1] + spacing * 0.5)

# Invert y-axis so first metric is at top
ax.invert_yaxis()

# Legend
legend_elements = [
    Patch(facecolor=actual_color, edgecolor="none", label="Actual"),
    Line2D([0], [0], marker="D", color="w", markerfacecolor=target_color, markersize=8, label="Target"),
    Patch(facecolor=band_colors[2], edgecolor="none", label="Good"),
    Patch(facecolor=band_colors[1], edgecolor="none", label="Satisfactory"),
    Patch(facecolor=band_colors[0], edgecolor="none", label="Poor"),
]
ax.legend(handles=legend_elements, loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=5, fontsize=14, frameon=False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
