""" pyplots.ai
sankey-basic: Basic Sankey Diagram
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 78/100 | Created: 2025-12-23
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seed for reproducibility
np.random.seed(42)

# Apply seaborn styling
sns.set_theme(style="white", context="talk", font_scale=1.2)

# Data - Energy flow from sources to sectors (in TWh)
flows_data = {
    "source": ["Coal", "Coal", "Coal", "Gas", "Gas", "Gas", "Nuclear", "Nuclear", "Nuclear"],
    "target": [
        "Residential",
        "Commercial",
        "Industrial",
        "Residential",
        "Commercial",
        "Industrial",
        "Residential",
        "Commercial",
        "Industrial",
    ],
    "value": [15, 12, 33, 20, 18, 22, 15, 15, 15],
}
df = pd.DataFrame(flows_data)

# Create figure with seaborn styling
fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn color palettes - distinct colors for sources and targets
source_names = df["source"].unique()
target_names = df["target"].unique()
source_palette = sns.color_palette("husl", n_colors=len(source_names))
target_palette = sns.color_palette("Set2", n_colors=len(target_names))
source_colors = dict(zip(source_names, source_palette, strict=True))
target_colors = dict(zip(target_names, target_palette, strict=True))

# Calculate node totals
sources = df.groupby("source")["value"].sum().sort_values(ascending=False)
targets = df.groupby("target")["value"].sum().sort_values(ascending=False)

# Node dimensions and positions
node_width = 0.06
x_source = 0.12
x_target = 0.88
gap = 0.025
total_height = 0.60  # Reduced to leave room for legends at bottom

# Calculate source node positions (left side)
total_source = sources.sum()
source_positions = {}
y_pos = 0.92
for source, value in sources.items():
    height = (value / total_source) * total_height
    source_positions[source] = {"y": y_pos - height, "height": height}
    y_pos -= height + gap

# Calculate target node positions (right side)
total_target = targets.sum()
target_positions = {}
y_pos = 0.92
for target, value in targets.items():
    height = (value / total_target) * total_height
    target_positions[target] = {"y": y_pos - height, "height": height}
    y_pos -= height + gap

# Track current position for stacking flows at each node
source_current_y = {s: source_positions[s]["y"] + source_positions[s]["height"] for s in sources.index}
target_current_y = {t: target_positions[t]["y"] + target_positions[t]["height"] for t in targets.index}

# Bezier curve parameters
n_points = 100
t = np.linspace(0, 1, n_points)

# Sort flows by source then by value for consistent stacking
df_sorted = df.sort_values(["source", "value"], ascending=[True, False])

# Draw flows with widths proportional to values
for _, row in df_sorted.iterrows():
    source = row["source"]
    target = row["target"]
    value = row["value"]
    color = source_colors[source]

    # Calculate band height proportional to flow value
    source_band_height = (value / sources[source]) * source_positions[source]["height"]
    target_band_height = (value / targets[target]) * target_positions[target]["height"]

    # Source side coordinates
    y0_top = source_current_y[source]
    y0_bot = y0_top - source_band_height
    source_current_y[source] = y0_bot

    # Target side coordinates
    y1_top = target_current_y[target]
    y1_bot = y1_top - target_band_height
    target_current_y[target] = y1_bot

    # Draw the flow band using cubic bezier curves
    x0 = x_source + node_width
    x1 = x_target
    cx0 = x0 + (x1 - x0) * 0.35
    cx1 = x0 + (x1 - x0) * 0.65

    # Generate bezier curve points for top and bottom edges
    top_x = (1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * cx0 + 3 * (1 - t) * t**2 * cx1 + t**3 * x1
    top_y = (1 - t) ** 3 * y0_top + 3 * (1 - t) ** 2 * t * y0_top + 3 * (1 - t) * t**2 * y1_top + t**3 * y1_top
    bot_y = (1 - t) ** 3 * y0_bot + 3 * (1 - t) ** 2 * t * y0_bot + 3 * (1 - t) * t**2 * y1_bot + t**3 * y1_bot

    # Draw flow band
    ax.fill_between(top_x, bot_y, top_y, color=color, alpha=0.65, linewidth=0, edgecolor="none")

# Draw source nodes (left) with seaborn colors
for source in sources.index:
    pos = source_positions[source]
    rect = patches.FancyBboxPatch(
        (x_source, pos["y"]),
        node_width,
        pos["height"],
        boxstyle="round,pad=0.005,rounding_size=0.015",
        facecolor=source_colors[source],
        edgecolor="white",
        linewidth=2.5,
    )
    ax.add_patch(rect)
    ax.text(
        x_source - 0.015,
        pos["y"] + pos["height"] / 2,
        f"{source}\n{sources[source]:.0f} TWh",
        ha="right",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="#2d2d2d",
    )

# Draw target nodes (right) with distinct colors from Set2 palette
for target in targets.index:
    pos = target_positions[target]
    rect = patches.FancyBboxPatch(
        (x_target, pos["y"]),
        node_width,
        pos["height"],
        boxstyle="round,pad=0.005,rounding_size=0.015",
        facecolor=target_colors[target],
        edgecolor="white",
        linewidth=2.5,
    )
    ax.add_patch(rect)
    ax.text(
        x_target + node_width + 0.015,
        pos["y"] + pos["height"] / 2,
        f"{target}\n{targets[target]:.0f} TWh",
        ha="left",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="#2d2d2d",
    )

# Create legend using simple patches for sources and targets
source_handles = [
    patches.Patch(facecolor=source_colors[s], edgecolor="white", linewidth=1.5, label=s) for s in source_names
]
target_handles = [
    patches.Patch(facecolor=target_colors[t], edgecolor="white", linewidth=1.5, label=t) for t in target_names
]

# Add source legend on the left
source_legend = ax.legend(
    handles=source_handles,
    title="Energy Sources",
    loc="lower left",
    bbox_to_anchor=(0.02, 0.02),
    fontsize=14,
    title_fontsize=16,
    frameon=True,
    fancybox=True,
    edgecolor="#cccccc",
)

# Add target legend on the right
ax.add_artist(source_legend)
ax.legend(
    handles=target_handles,
    title="Sectors",
    loc="lower right",
    bbox_to_anchor=(0.98, 0.02),
    fontsize=14,
    title_fontsize=16,
    frameon=True,
    fancybox=True,
    edgecolor="#cccccc",
)

# Set title using the required format
ax.set_title("sankey-basic · seaborn · pyplots.ai", fontsize=26, fontweight="bold", pad=25)

# Set axis limits and remove decorations
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
