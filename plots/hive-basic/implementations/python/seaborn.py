""" pyplots.ai
hive-basic: Basic Hive Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seaborn theme for consistent styling
sns.set_theme(style="white", context="talk", font_scale=1.2)

# Data: Software module dependency network
np.random.seed(42)

# Define nodes with module types (3 categories for 3 axes)
node_data = {
    "id": [f"M{i}" for i in range(30)],
    "type": ["core"] * 10 + ["utility"] * 10 + ["interface"] * 10,
    "degree": np.random.randint(1, 15, 30),
}
nodes_df = pd.DataFrame(node_data)

# Define edges between modules
edges = [
    # Core to utility connections
    ("M0", "M10"),
    ("M0", "M11"),
    ("M1", "M12"),
    ("M2", "M13"),
    ("M3", "M14"),
    ("M4", "M15"),
    ("M5", "M16"),
    ("M6", "M17"),
    ("M7", "M18"),
    ("M8", "M19"),
    # Utility to interface connections
    ("M10", "M20"),
    ("M11", "M21"),
    ("M12", "M22"),
    ("M13", "M23"),
    ("M14", "M24"),
    ("M15", "M25"),
    ("M16", "M26"),
    ("M17", "M27"),
    ("M18", "M28"),
    ("M19", "M29"),
    # Core to interface connections (direct)
    ("M0", "M20"),
    ("M1", "M23"),
    ("M3", "M25"),
    ("M5", "M27"),
    ("M9", "M29"),
    # Internal connections
    ("M0", "M1"),
    ("M2", "M3"),
    ("M10", "M11"),
    ("M20", "M21"),
]

# Hive plot configuration: 3 axes at 120 degrees apart
axis_angles = {"core": np.pi / 2, "utility": np.pi / 2 + 2 * np.pi / 3, "interface": np.pi / 2 + 4 * np.pi / 3}
axis_colors = {"core": "#306998", "utility": "#FFD43B", "interface": "#4ECDC4"}

# Calculate node positions on radial axes (normalized by degree within each type)
nodes_df["angle"] = nodes_df["type"].map(axis_angles)
for node_type in ["core", "utility", "interface"]:
    mask = nodes_df["type"] == node_type
    degrees = nodes_df.loc[mask, "degree"]
    min_deg, max_deg = degrees.min(), degrees.max()
    if max_deg > min_deg:
        nodes_df.loc[mask, "radius"] = 0.3 + 0.7 * (degrees - min_deg) / (max_deg - min_deg)
    else:
        nodes_df.loc[mask, "radius"] = 0.65

# Convert to cartesian coordinates
nodes_df["x"] = nodes_df["radius"] * np.cos(nodes_df["angle"])
nodes_df["y"] = nodes_df["radius"] * np.sin(nodes_df["angle"])

# Create figure
fig, ax = plt.subplots(figsize=(12, 12))

# Draw axis lines (radial spokes)
for axis_name, angle in axis_angles.items():
    ax.plot([0, 1.1 * np.cos(angle)], [0, 1.1 * np.sin(angle)], color="#666666", linewidth=2, alpha=0.5, zorder=1)
    ax.text(
        1.2 * np.cos(angle),
        1.2 * np.sin(angle),
        axis_name.upper(),
        fontsize=18,
        fontweight="bold",
        ha="center",
        va="center",
        color=axis_colors[axis_name],
    )

# Build edge curves as DataFrame for seaborn lineplot
node_pos = nodes_df.set_index("id")[["x", "y"]]
edge_curves = []
for edge_id, (source, target) in enumerate(edges):
    src_x, src_y = node_pos.loc[source]
    tgt_x, tgt_y = node_pos.loc[target]
    t = np.linspace(0, 1, 50)
    ctrl_x, ctrl_y = 0.1 * (src_x + tgt_x), 0.1 * (src_y + tgt_y)
    curve_x = (1 - t) ** 2 * src_x + 2 * (1 - t) * t * ctrl_x + t**2 * tgt_x
    curve_y = (1 - t) ** 2 * src_y + 2 * (1 - t) * t * ctrl_y + t**2 * tgt_y
    for i in range(len(t)):
        edge_curves.append({"edge_id": edge_id, "x": curve_x[i], "y": curve_y[i]})
edges_df = pd.DataFrame(edge_curves)

# Draw edges using seaborn lineplot with lower alpha for better bundling
sns.lineplot(
    data=edges_df,
    x="x",
    y="y",
    hue="edge_id",
    palette=["#888888"] * len(edges),
    alpha=0.25,
    linewidth=1.5,
    legend=False,
    units="edge_id",
    estimator=None,
    ax=ax,
    zorder=2,
)

# Draw nodes using seaborn scatterplot
sns.scatterplot(
    data=nodes_df,
    x="x",
    y="y",
    hue="type",
    palette=axis_colors,
    s=400,
    alpha=0.9,
    edgecolor="white",
    linewidth=2,
    ax=ax,
    legend=False,
    zorder=3,
)

# Create legend
legend_handles = [
    mpatches.Patch(color=axis_colors["core"], label="Core Modules"),
    mpatches.Patch(color=axis_colors["utility"], label="Utility Modules"),
    mpatches.Patch(color=axis_colors["interface"], label="Interface Modules"),
]
ax.legend(handles=legend_handles, loc="upper right", fontsize=16, framealpha=0.9)

# Styling
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.5, 1.5)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("hive-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
