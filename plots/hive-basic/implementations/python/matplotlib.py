"""anyplot.ai
hive-basic: Basic Hive Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-07
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per axis group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
INNER_RADIUS = 0.15  # where the axes start, as a share of the outer ring
OUTER_RADIUS = 0.85  # where the axes end

# Columns: set these to your table's column names
EDGE_ENDS = ["Source module", "Target module"]  # role: edges
MODULE = "Module"  # role: nodes
GROUP = "Module type"  # role: axis_attribute
POSITION = "Position on axis"  # role: extra

# Data: replace this block with your own edge list (df) and node table (nodes),
# for example df = pd.read_csv("edges.csv")
# Software module dependency network: nodes sit on one axis per module type
nodes = pd.DataFrame(
    {
        MODULE: [
            *["Engine", "Config", "Logger", "Cache"],
            *["Parser", "Validator", "Formatter", "Converter", "Helper"],
            *["API", "Web", "CLI", "SDK"],
        ],
        GROUP: ["Core"] * 4 + ["Utility"] * 5 + ["Interface"] * 4,
        POSITION: [0.9, 0.7, 0.5, 0.3, 0.85, 0.65, 0.45, 0.25, 0.15, 0.95, 0.75, 0.55, 0.35],
    }
)
df = pd.DataFrame(
    [
        ("Engine", "Parser"),
        ("Engine", "Validator"),
        ("Config", "Parser"),
        ("Logger", "Formatter"),
        ("Cache", "Helper"),
        ("Parser", "API"),
        ("Validator", "API"),
        ("Formatter", "Web"),
        ("Converter", "SDK"),
        ("Helper", "CLI"),
        ("Engine", "API"),
        ("Config", "CLI"),
        ("Logger", "Web"),
        ("Engine", "Config"),
        ("Engine", "Logger"),
        ("Parser", "Validator"),
        ("API", "SDK"),
    ],
    columns=EDGE_ENDS,
)

# Plot: axes by group in order of appearance, radius from the position property
groups = list(nodes[GROUP].unique())
n_axes = len(groups)
axis_angles = np.pi / 2 + np.arange(n_axes) * 2 * np.pi / n_axes

nodes["axis"] = nodes[GROUP].map({g: i for i, g in enumerate(groups)})
nodes["angle"] = axis_angles[nodes["axis"].to_numpy()]
nodes["radius"] = INNER_RADIUS + nodes[POSITION] * (OUTER_RADIUS - INNER_RADIUS)
nodes["x"] = nodes["radius"] * np.cos(nodes["angle"])
nodes["y"] = nodes["radius"] * np.sin(nodes["angle"])
lookup = nodes.set_index(MODULE)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Radial axes with their group labels
for i, group in enumerate(groups):
    angle = axis_angles[i]
    ax.plot(
        [INNER_RADIUS * np.cos(angle), OUTER_RADIUS * np.cos(angle)],
        [INNER_RADIUS * np.sin(angle), OUTER_RADIUS * np.sin(angle)],
        color=IMPRINT_PALETTE[i],
        linewidth=3,
        solid_capstyle="round",
        zorder=1,
    )
    label_r = OUTER_RADIUS + 0.08
    ax.text(
        label_r * np.cos(angle),
        label_r * np.sin(angle),
        group,
        fontsize=12,
        fontweight="bold",
        ha="center",
        va="center",
        color=IMPRINT_PALETTE[i],
    )

# Edges as quadratic bezier curves pulled through the center
t = np.linspace(0, 1, 50)[:, None]
edge_lines = []
edge_colors = []
for source_id, target_id in zip(df[EDGE_ENDS[0]], df[EDGE_ENDS[1]], strict=True):
    p1 = lookup.loc[source_id, ["x", "y"]].to_numpy(dtype=float)
    p2 = lookup.loc[target_id, ["x", "y"]].to_numpy(dtype=float)
    points = (1 - t) ** 2 * p1 + t**2 * p2
    edge_lines.extend(np.stack([points[:-1], points[1:]], axis=1))
    edge_colors.extend([IMPRINT_PALETTE[int(lookup.loc[source_id, "axis"])]] * (len(t) - 1))

ax.add_collection(LineCollection(edge_lines, colors=edge_colors, linewidths=1.3, alpha=0.55, zorder=2))

# Nodes and their labels
for name, row in lookup.iterrows():
    ax.scatter(row.x, row.y, s=100, c=IMPRINT_PALETTE[int(row.axis)], edgecolors=PAGE_BG, linewidths=1, zorder=3)
    if row.axis == 0:
        label_x, label_y, ha = row.x + 0.08, row.y, "left"
    elif row.axis == 1:
        label_x, label_y, ha = row.x - 0.04, row.y + 0.024, "right"
    else:
        label_x, label_y, ha = row.x + 0.04, row.y + 0.024, "left"
    ax.text(label_x, label_y, name, fontsize=9, ha=ha, va="center", color=INK)

# Center point
ax.scatter(0, 0, s=50, c=PAGE_BG, edgecolors=INK_SOFT, linewidths=1, zorder=4)

# Style
ax.set_xlim(-1.1, 1.1)
ax.set_ylim(-1.1, 1.1)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("hive-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)

legend_elements = [
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="none",
        markerfacecolor=IMPRINT_PALETTE[i],
        markersize=9,
        markeredgecolor=PAGE_BG,
        markeredgewidth=1,
        label=group,
    )
    for i, group in enumerate(groups)
]
leg = ax.legend(
    handles=legend_elements, title=GROUP, loc="lower center", fontsize=9, ncol=n_axes, bbox_to_anchor=(0.5, 0.0)
)
leg.get_frame().set_facecolor(PAGE_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_title().set_color(INK_SOFT)
leg.get_title().set_fontsize(9)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.02)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
