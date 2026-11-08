""" anyplot.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 70/100 | Updated: 2026-05-17
"""

import os

import matplotlib.patheffects as patheffects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens (prompts/default-style-guide.md "Background" and "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint position 1: the nodes are one series
EDGE_COLOR = INK_MUTED  # the muted anchor: edges sit behind the nodes and carry their weight in width alone

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "text.color": INK,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
LAYOUT_STEPS = 300  # Fruchterman-Reingold iterations
LAYOUT_ASPECT = 1.6  # width over height of the layout box, the shape of the free canvas left of the legends
EDGE_CLEARANCE = 0.2  # layout units (the box is 2 high) a node keeps from edges it does not belong to
EDGE_PUSH = 50  # strength of the push that keeps that clearance
EDGE_WIDTHS = (0.6, 6.0)  # line width in points of the lightest and the heaviest edge
NODE_AREA = 700  # marker area in points² of the node with the largest total; area grows with the total

# Columns: set these to your table's column names
COUNTRY_A = "Country A"  # role: extra
COUNTRY_B = "Country B"  # role: extra
TRADE = "Trade volume (billion USD)"  # role: weight

# Data: replace this block with your own edge list, for example df = pd.read_csv("trade.csv")
df = pd.DataFrame(
    [
        ("USA", "China", 580),
        ("USA", "Canada", 620),
        ("USA", "Mexico", 550),
        ("USA", "Japan", 210),
        ("USA", "Germany", 180),
        ("USA", "UK", 140),
        ("China", "Japan", 320),
        ("China", "S. Korea", 280),
        ("China", "Germany", 190),
        ("China", "Australia", 150),
        ("China", "India", 90),
        ("Germany", "France", 170),
        ("Germany", "Netherlands", 200),
        ("Germany", "UK", 130),
        ("Germany", "Italy", 140),
        ("Japan", "S. Korea", 85),
        ("Japan", "Australia", 70),
        ("UK", "France", 95),
        ("UK", "Netherlands", 80),
        ("France", "Italy", 85),
        ("France", "Spain", 100),
        ("India", "USA", 75),
        ("Brazil", "USA", 65),
        ("Brazil", "China", 100),
        ("Canada", "UK", 25),
        ("Mexico", "Canada", 20),
        ("Australia", "Japan", 60),
        ("S. Korea", "USA", 120),
        ("Netherlands", "UK", 70),
        ("Italy", "Spain", 50),
    ],
    columns=[COUNTRY_A, COUNTRY_B, TRADE],
)

# Plot: reads only df and the constants above
edges = df.dropna(subset=[TRADE])
weights = edges[TRADE].to_numpy(dtype=float)

# Weighted degree: the summed weight of every edge that touches a node
edge_ends = pd.concat([edges.set_index(COUNTRY_A)[TRADE], edges.set_index(COUNTRY_B)[TRADE]])
totals = edge_ends.groupby(level=0, sort=False).sum()
names = totals.index
source = names.get_indexer(edges[COUNTRY_A])
target = names.get_indexer(edges[COUNTRY_B])

# Fruchterman-Reingold spring layout: heavier edges pull their ends harder together
n_nodes = len(names)
ideal = np.sqrt(4 * LAYOUT_ASPECT / n_nodes)
pull_factor = 1 + 4 * weights / weights.max()
foreign = (np.arange(n_nodes)[:, None] != source) & (np.arange(n_nodes)[:, None] != target)
angles = 2 * np.pi * np.arange(n_nodes) / n_nodes
pos = np.column_stack([LAYOUT_ASPECT * np.cos(angles), np.sin(angles)])
for step in range(LAYOUT_STEPS):
    delta = pos[:, None, :] - pos[None, :, :]
    dist = np.maximum(np.linalg.norm(delta, axis=2), 0.01)
    disp = (delta * (ideal**2 / dist**2)[:, :, None]).sum(axis=1)
    edge_delta = pos[source] - pos[target]
    edge_dist = np.maximum(np.linalg.norm(edge_delta, axis=1), 0.01)
    pull = edge_delta * (edge_dist * pull_factor / ideal)[:, None]
    np.add.at(disp, source, -pull)
    np.add.at(disp, target, pull)
    if step >= 0.7 * LAYOUT_STEPS:
        # Once the springs have settled, push each node off the edges it does not belong to,
        # so no edge runs hidden beneath a node
        along = pos[:, None, :] - pos[source][None, :, :]
        share = np.clip((along * -edge_delta).sum(axis=2) / edge_dist**2, 0, 1)
        off_edge = along + share[:, :, None] * edge_delta
        off_dist = np.maximum(np.linalg.norm(off_edge, axis=2), 0.01)
        push = foreign * np.maximum(EDGE_CLEARANCE - off_dist, 0) * EDGE_PUSH / ideal
        disp += (off_edge / off_dist[:, :, None] * push[:, :, None]).sum(axis=1)
    length = np.maximum(np.linalg.norm(disp, axis=1), 0.01)
    pos += disp / length[:, None] * np.minimum(length, 0.1 * (1 - step / LAYOUT_STEPS))[:, None]
    pos = np.clip(pos, [-LAYOUT_ASPECT, -1], [LAYOUT_ASPECT, 1])

node_total = f"Total {TRADE[:1].lower()}{TRADE[1:]}"
nodes = pd.DataFrame({"x": pos[:, 0], "y": pos[:, 1], node_total: totals.to_numpy()})
ends = np.column_stack([source, target]).ravel()
segments = pd.DataFrame(
    {"edge": np.repeat(np.arange(len(edges)), 2), "x": pos[ends, 0], "y": pos[ends, 1], TRADE: np.repeat(weights, 2)}
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
fig.subplots_adjust(left=0.02, right=0.71, top=0.9, bottom=0.03)

# Edges: one line per edge, its width mapped from the weight by seaborn's size semantic
sns.lineplot(
    data=segments,
    x="x",
    y="y",
    units="edge",
    estimator=None,
    sort=False,
    size=TRADE,
    sizes=EDGE_WIDTHS,
    size_norm=(weights.min(), weights.max()),
    color=EDGE_COLOR,
    solid_capstyle="round",
    legend="brief",
    ax=ax,
)
edge_handles, edge_labels = ax.get_legend_handles_labels()

# Nodes: marker area proportional to the weighted degree, drawn above the edges
sns.scatterplot(
    data=nodes,
    x="x",
    y="y",
    size=node_total,
    sizes=(0, NODE_AREA),
    size_norm=(0, totals.max()),
    color=BRAND,
    edgecolor=PAGE_BG,
    linewidth=1.2,
    legend="brief",
    zorder=3,
    ax=ax,
)
handles, labels = ax.get_legend_handles_labels()
# Node areas: every second of seaborn's entries, counted down from the largest, so the circles stay apart
node_handles = handles[len(edge_handles) :][::-2][::-1]
node_labels = labels[len(edge_labels) :][::-2][::-1]

# Labels: each one just outside its node, in the widest angular gap between the node's edges,
# with a page-colored halo where an edge still passes behind it
halo = [patheffects.withStroke(linewidth=2.5, foreground=PAGE_BG)]
radii = np.sqrt(NODE_AREA * totals.to_numpy() / totals.max()) / 2
for i, name in enumerate(names):
    neighbors = np.concatenate([target[source == i], source[target == i]])
    offsets = pos[neighbors] - pos[i]
    edge_angles = np.sort(np.arctan2(offsets[:, 1], offsets[:, 0]))
    gaps = np.diff(np.append(edge_angles, edge_angles[0] + 2 * np.pi))
    widest = np.argmax(gaps)
    label_angle = edge_angles[widest] + gaps[widest] / 2
    dx, dy = np.cos(label_angle), np.sin(label_angle)
    ax.annotate(
        name,
        pos[i],
        xytext=((radii[i] + 2) * dx, (radii[i] + 2) * dy),
        textcoords="offset points",
        ha="left" if dx > 0.4 else "right" if dx < -0.4 else "center",
        va="bottom" if dy > 0.4 else "top" if dy < -0.4 else "center",
        fontsize=8,
        fontweight="bold",
        color=INK,
        path_effects=halo,
        zorder=4,
    )

# Legends: one for the edge widths, one for the node areas, each labeled with the values it stands for
legend_kws = {"fontsize": 7, "title_fontsize": 8, "frameon": True, "borderpad": 0.8}
edge_legend = ax.legend(
    edge_handles,
    edge_labels,
    title=TRADE,
    loc="lower left",
    bbox_to_anchor=(1.02, 0.0),
    handlelength=3.2,
    labelspacing=0.7,
    **legend_kws,
)
ax.add_artist(edge_legend)
largest = max(handle.get_markersize() for handle in node_handles)
ax.legend(
    node_handles,
    node_labels,
    title=node_total,
    loc="upper left",
    bbox_to_anchor=(1.02, 1.0),
    handleheight=largest / 7,
    handlelength=largest / 7,
    labelspacing=0.9,
    **legend_kws,
)
for legend in ax.get_legend(), edge_legend:
    legend.get_title().set_color(INK)
    for text in legend.get_texts():
        text.set_color(INK_SOFT)

# Style: positions come from the layout, not from data, so no axes are drawn
pad_x = 0.12 * np.ptp(pos[:, 0])
pad_y = 0.14 * np.ptp(pos[:, 1])
ax.set_xlim(pos[:, 0].min() - pad_x, pos[:, 0].max() + pad_x)
ax.set_ylim(pos[:, 1].min() - pad_y, pos[:, 1].max() + pad_y)
ax.set_aspect("equal", adjustable="datalim")
ax.set_axis_off()
fig.suptitle("network-weighted · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.97)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
