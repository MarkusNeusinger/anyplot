"""anyplot.ai
network-directed: Directed Network Graph
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per node group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
SOURCE = "Source module"  # role: edges
TARGET = "Target module"  # role: extra
WEIGHT = "Import weight"  # role: weight
MODULE = "Module"  # role: nodes
GROUP = "Module type"  # role: extra
X = "x"  # role: extra
Y = "y"  # role: extra

# Data: replace this block with your own edge list (df) and node table (nodes), for example
# df = pd.read_csv("edges.csv"); nodes = pd.read_csv("nodes.csv")
# Software module dependencies, arranged top-down in a hierarchical layout
nodes = pd.DataFrame(
    {
        MODULE: ["app", "config", "api", "auth", "db", "cache", "log", "valid", "router", "model", "mware"],
        GROUP: [
            "core",
            "core",
            "services",
            "services",
            "data",
            "data",
            "utils",
            "utils",
            "services",
            "data",
            "services",
        ],
        X: [0.50, 0.18, 0.50, 0.82, 0.28, 0.72, 0.15, 0.50, 0.85, 0.32, 0.68],
        Y: [0.88, 0.70, 0.68, 0.70, 0.45, 0.45, 0.22, 0.22, 0.22, 0.05, 0.05],
    }
)
df = pd.DataFrame(
    [
        ("app", "config", 3),
        ("app", "db", 5),
        ("app", "api", 5),
        ("app", "auth", 4),
        ("api", "valid", 4),
        ("api", "router", 3),
        ("api", "log", 2),
        ("auth", "cache", 4),
        ("auth", "db", 3),
        ("auth", "log", 2),
        ("db", "config", 3),
        ("db", "log", 1),
        ("cache", "config", 2),
        ("router", "valid", 3),
        ("router", "mware", 2),
        ("model", "db", 4),
        ("model", "valid", 3),
        ("mware", "auth", 3),
        ("mware", "log", 1),
    ],
    columns=[SOURCE, TARGET, WEIGHT],
)

# Plot: reads only df, nodes and the constants above
groups = sorted(nodes[GROUP].unique())
group_colors = {g: IMPRINT_PALETTE[i] for i, g in enumerate(groups)}
pos = nodes.set_index(MODULE)[[X, Y]]

NODE_AREA = 1400  # marker area in points^2
node_radius_pt = np.sqrt(NODE_AREA / np.pi)
w_min, w_max = df[WEIGHT].min(), df[WEIGHT].max()


def edge_width(weight):
    """One rule for every edge: line width grows linearly with the weight."""
    return 0.7 + 0.35 * weight


def label_color(fill):
    """Pick the node label color (dark or light) with the higher contrast on the fill."""

    def luminance(color):
        r, g, b = (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in to_rgb(color))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    lum = luminance(fill)
    dark, light = "#1A1A17", "#FAF8F1"
    return dark if (lum + 0.05) / (luminance(dark) + 0.05) > (luminance(light) + 0.05) / (lum + 0.05) else light


fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Edges: filled arrowheads stop at the border of the target node
for source, target, weight in df.itertuples(index=False):
    arrow = FancyArrowPatch(
        tuple(pos.loc[source]),
        tuple(pos.loc[target]),
        connectionstyle="arc3,rad=0.1",
        arrowstyle="-|>",
        mutation_scale=9,
        shrinkA=node_radius_pt + 1,
        shrinkB=node_radius_pt + 2,
        color=INK_SOFT,
        alpha=0.7,
        linewidth=edge_width(weight),
        zorder=1,
    )
    ax.add_patch(arrow)

# Nodes
sns.scatterplot(
    data=nodes,
    x=X,
    y=Y,
    hue=GROUP,
    palette=group_colors,
    s=NODE_AREA,
    edgecolor=PAGE_BG,
    linewidth=1.5,
    legend=False,
    ax=ax,
    zorder=2,
)

for module, group, x, y in nodes[[MODULE, GROUP, X, Y]].itertuples(index=False):
    ax.text(
        x,
        y,
        module,
        ha="center",
        va="center",
        fontsize=7.5,
        fontweight="bold",
        color=label_color(group_colors[group]),
        zorder=3,
    )

# Legend: node groups, then the weakest and strongest edge
legend_handles = [
    Line2D(
        [0],
        [0],
        marker="o",
        linestyle="",
        markersize=8,
        markerfacecolor=group_colors[g],
        markeredgecolor=PAGE_BG,
        label=g.capitalize(),
    )
    for g in groups
]
legend_handles += [
    Line2D([0], [0], color=INK_SOFT, alpha=0.7, linewidth=edge_width(w), label=f"{WEIGHT} {w}") for w in (w_min, w_max)
]
ax.legend(
    handles=legend_handles,
    loc="upper left",
    fontsize=8,
    title=f"{GROUP} / {WEIGHT.lower()}",
    title_fontsize=9,
    framealpha=0.95,
    borderpad=0.8,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    labelcolor=INK,
)

# Style
ax.set_title("network-directed · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)
ax.set_xlim(nodes[X].min() - 0.5, nodes[X].max() + 0.17)
ax.set_ylim(nodes[Y].min() - 0.13, nodes[Y].max() + 0.1)
ax.axis("off")

fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.92)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
