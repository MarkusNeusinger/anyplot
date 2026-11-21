""" anyplot.ai
network-bipartite: Bipartite Network Graph
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="ticks",
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
SPECIES = "Species"  # role: source
HABITAT = "Habitat"  # role: target

# Data: replace this block with your own edge list, for example df = pd.read_csv("occurrences.csv")
rng = np.random.default_rng(7)
species_names = [
    "Snow leopard",
    "Red fox",
    "Golden eagle",
    "Brown bear",
    "Grey wolf",
    "Otter",
    "Beaver",
    "Lynx",
    "Moose",
    "Capercaillie",
    "Black stork",
    "Natterjack toad",
]
habitat_names = [
    "Alpine meadow",
    "Boreal forest",
    "Wetland",
    "River bank",
    "Rocky scree",
    "Mixed woodland",
    "Peat bog",
    "Open steppe",
]
rows = []
for name in species_names:
    n_habitats = rng.integers(1, 5)
    for h in rng.choice(len(habitat_names), size=n_habitats, replace=False):
        rows.append((name, habitat_names[h]))
df = pd.DataFrame(rows, columns=[SPECIES, HABITAT])

# Plot: reads only df and the constants above
degree = pd.concat([df[SPECIES].value_counts(), df[HABITAT].value_counts()])
species_order = list(dict.fromkeys(df[SPECIES]))
habitat_order = list(dict.fromkeys(df[HABITAT]))


def column_positions(order, x):
    """Spread the nodes of one set evenly down a vertical line at position x."""
    y = np.linspace(1, 0, len(order)) if len(order) > 1 else np.array([0.5])
    return {name: (x, yi) for name, yi in zip(order, y, strict=True)}


pos = {**column_positions(species_order, 0.0), **column_positions(habitat_order, 1.0)}
nodes = pd.DataFrame(
    {
        "node": list(pos),
        "x": [p[0] for p in pos.values()],
        "y": [p[1] for p in pos.values()],
        "set": [SPECIES] * len(species_order) + [HABITAT] * len(habitat_order),
    }
)
nodes["degree"] = nodes["node"].map(degree)
set_colors = {SPECIES: IMPRINT_PALETTE[0], HABITAT: IMPRINT_PALETTE[1]}

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Edges first, thin and light, beneath the nodes
segments = [[pos[s], pos[h]] for s, h in zip(df[SPECIES], df[HABITAT], strict=True)]
ax.add_collection(LineCollection(segments, colors=INK_SOFT, alpha=0.35, linewidths=0.7, zorder=1))

# Nodes: hue = set membership, size = degree
sns.scatterplot(
    data=nodes,
    x="x",
    y="y",
    hue="set",
    size="degree",
    sizes=(90, 420),
    palette=set_colors,
    edgecolor=PAGE_BG,
    linewidth=1.0,
    legend=False,
    zorder=3,
    ax=ax,
)

# Labels on the outer side of each column
for _, node in nodes.iterrows():
    left = node["set"] == SPECIES
    ax.annotate(
        node["node"],
        xy=(node["x"], node["y"]),
        xytext=(-12 if left else 12, 0),
        textcoords="offset points",
        ha="right" if left else "left",
        va="center",
        fontsize=8,
        color=INK_SOFT,
    )

# Column headings above each column
top = nodes["y"].max()
for name in (SPECIES, HABITAT):
    ax.annotate(
        name,
        xy=(nodes.loc[nodes["set"] == name, "x"].iloc[0], top),
        xytext=(0, 16),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color=set_colors[name],
    )

# Legend
legend_elements = [
    Line2D(
        [0],
        [0],
        marker="o",
        linestyle="",
        markersize=7,
        markerfacecolor=set_colors[name],
        markeredgecolor=PAGE_BG,
        label=name,
    )
    for name in (SPECIES, HABITAT)
] + [Line2D([0], [0], color=INK_SOFT, alpha=0.6, linewidth=1.5, label="Occurs in")]
legend = ax.legend(
    handles=legend_elements, loc="lower center", bbox_to_anchor=(0.5, -0.02), ncol=3, fontsize=8, framealpha=0.9
)
for text in legend.get_texts():
    text.set_color(INK)

ax.set_xlim(-0.55, 1.55)
ax.set_ylim(-0.12, 1.14)
ax.axis("off")

ax.set_title(
    "Species–Habitat Occurrence · network-bipartite · python · seaborn · anyplot.ai",
    fontsize=11,
    fontweight="medium",
    color=INK,
    pad=6,
)

fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.02)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
