"""anyplot.ai
network-directed: Directed Network Graph
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Circle, FancyArrowPatch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SOURCE = "Source"  # role: edges
TARGET = "Target"  # role: extra
NODE = "Module"  # role: nodes
GROUP = "Module type"  # role: extra
X = "x"  # role: extra
Y = "y"  # role: extra

# Data: replace df with your own edge list, for example df = pd.read_csv("edges.csv");
# nodes holds one row per entity with its group and layout position
# Software package dependencies (an arrow points from the importing module to the one it imports)
nodes = pd.DataFrame(
    {
        NODE: [
            "main",
            "config",
            "database",
            "auth",
            "routes",
            "handlers",
            "validators",
            "helpers",
            "logger",
            "cache",
            "test_auth",
            "test_routes",
            "test_db",
        ],
        GROUP: ["Core"] * 3 + ["Api"] * 3 + ["Utils"] * 4 + ["Tests"] * 3,
        X: [0.45, 0.18, 0.45, 0.72, 0.88, 0.68, 0.32, 0.48, 0.12, 0.05, 0.92, 0.95, 0.25],
        Y: [0.88, 0.68, 0.55, 0.73, 0.52, 0.32, 0.38, 0.15, 0.38, 0.58, 0.88, 0.32, 0.12],
    }
)
edge_pairs = [
    ("main", "config"),
    ("main", "database"),
    ("main", "routes"),
    ("main", "logger"),
    ("config", "validators"),
    ("database", "logger"),
    ("database", "config"),
    ("auth", "database"),
    ("auth", "validators"),
    ("auth", "logger"),
    ("routes", "auth"),
    ("routes", "handlers"),
    ("routes", "validators"),
    ("handlers", "database"),
    ("handlers", "helpers"),
    ("handlers", "logger"),
    ("validators", "helpers"),
    ("cache", "logger"),
    ("cache", "config"),
    ("test_auth", "auth"),
    ("test_routes", "routes"),
    ("test_db", "database"),
]
df = pd.DataFrame(edge_pairs, columns=[SOURCE, TARGET])

# Plot: reads only df, nodes and the constants above
positions = {row[NODE]: (row[X], row[Y]) for _, row in nodes.iterrows()}
groups = list(dict.fromkeys(nodes[GROUP]))
group_colors = {group: IMPRINT_PALETTE[i] for i, group in enumerate(groups)}
node_radius = 0.065

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Nodes first, so each arrow can stop exactly at the border of its target circle
circles = {}
for _, row in nodes.iterrows():
    circle = Circle(
        positions[row[NODE]],
        radius=node_radius,
        facecolor=group_colors[row[GROUP]],
        edgecolor=INK_SOFT,
        linewidth=1.2,
        alpha=0.9,
        zorder=10,
    )
    ax.add_patch(circle)
    circles[row[NODE]] = circle
    ax.text(
        *positions[row[NODE]],
        row[NODE],
        ha="center",
        va="center",
        fontsize=6.5,
        fontweight="bold",
        color=INK,
        zorder=11,
    )

# Edges: one arrow style throughout, clipped to the node borders
for source, target in zip(df[SOURCE], df[TARGET], strict=True):
    arrow = FancyArrowPatch(
        positions[source],
        positions[target],
        arrowstyle="-|>",
        mutation_scale=11,
        color=INK_SOFT,
        linewidth=1.0,
        alpha=0.75,
        connectionstyle="arc3,rad=0.12",
        patchA=circles[source],
        patchB=circles[target],
        shrinkA=0,
        shrinkB=0,
        zorder=5,
    )
    ax.add_patch(arrow)

# Legend
legend_handles = [mpatches.Patch(color=color, label=group, alpha=0.9) for group, color in group_colors.items()]
leg = ax.legend(handles=legend_handles, loc="upper left", fontsize=8, framealpha=0.95, title=GROUP, title_fontsize=9)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
for text in leg.get_texts():
    text.set_color(INK_SOFT)
leg.get_title().set_color(INK)

# Style
ax.set_title("network-directed · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlim(nodes[X].min() - 0.1, nodes[X].max() + 0.1)
ax.set_ylim(nodes[Y].min() - 0.1, nodes[Y].max() + 0.1)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
