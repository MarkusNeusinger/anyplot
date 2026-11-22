"""anyplot.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: a single series uses position 1
BRAND = "#009E73"

# Constants
LAYOUT_SEED = 42  # fixes the start of the force-directed layout
LAYOUT_STEPS = 200  # iterations of the spring layout

# Columns: set these to your table's column names
SOURCE = "Exporter"  # role: edges
TARGET = "Importer"  # role: nodes
WEIGHT = "Trade volume (billion USD)"  # role: weight

# Data: replace this block with your own edge list, for example df = pd.read_csv("trade.csv")
df = pd.DataFrame(
    [
        ("USA", "China", 580),
        ("USA", "Canada", 620),
        ("USA", "Mexico", 550),
        ("China", "Japan", 320),
        ("China", "S. Korea", 280),
        ("China", "Germany", 190),
        ("Germany", "France", 180),
        ("Germany", "Netherlands", 210),
        ("Germany", "Italy", 140),
        ("UK", "Germany", 130),
        ("UK", "USA", 140),
        ("UK", "Netherlands", 90),
        ("Japan", "USA", 200),
        ("Japan", "S. Korea", 85),
        ("France", "Italy", 95),
        ("France", "Spain", 110),
        ("Spain", "Italy", 50),
        ("Canada", "Mexico", 40),
        ("Brazil", "USA", 75),
        ("Brazil", "China", 100),
        ("India", "USA", 90),
        ("India", "China", 115),
        ("India", "UK", 35),
        ("Australia", "China", 145),
        ("Australia", "Japan", 55),
        ("Australia", "S. Korea", 45),
        ("Netherlands", "UK", 65),
        ("S. Korea", "USA", 120),
        ("Mexico", "China", 70),
    ],
    columns=[SOURCE, TARGET, WEIGHT],
)

# Plot: reads only df and the constants above
nodes = list(pd.unique(df[[SOURCE, TARGET]].to_numpy().ravel()))
node_idx = {name: i for i, name in enumerate(nodes)}
src = df[SOURCE].map(node_idx).to_numpy()
dst = df[TARGET].map(node_idx).to_numpy()
weights = df[WEIGHT].to_numpy(dtype=float)
w_min, w_max = weights.min(), weights.max()
w_norm = (weights - w_min) / (w_max - w_min) if w_max > w_min else np.full(len(weights), 0.5)

# Weighted degree: sum of the weights of all edges at a node
degree = np.zeros(len(nodes))
np.add.at(degree, src, weights)
np.add.at(degree, dst, weights)

# Force-directed layout (Fruchterman-Reingold): heavier edges pull their nodes closer
rng = np.random.default_rng(LAYOUT_SEED)
pos = rng.random((len(nodes), 2)) * 2 - 1
k = 0.5
for step in range(LAYOUT_STEPS):
    disp = np.zeros_like(pos)
    for i in range(len(nodes)):
        diff = pos[i] - pos
        dist = np.maximum(np.sqrt((diff**2).sum(axis=1)), 0.01)
        rep = k**2 / dist
        rep[i] = 0
        disp[i] += (diff * rep[:, None]).sum(axis=0)
    for a, b, w in zip(src, dst, weights, strict=True):
        diff = pos[b] - pos[a]
        dist = np.sqrt((diff**2).sum())
        if dist > 0.01:
            pull = diff / dist * dist**2 / k * (1 + w / w_max)
            disp[a] += pull
            disp[b] -= pull
    length = np.maximum(np.sqrt((disp**2).sum(axis=1)), 0.01)
    pos += disp / length[:, None] * (0.1 * (1 - step / LAYOUT_STEPS) + 0.005)  # cooling

# Scale uniformly to fit the 16:9 canvas and centre
span = np.maximum(pos.max(axis=0) - pos.min(axis=0), 1e-9)
pos = (pos - pos.min(axis=0)) * min(3.2 / span[0], 1.8 / span[1])
pos -= (pos.max(axis=0) + pos.min(axis=0)) / 2

# Labels sit on the outer side of each node, away from its neighbours, where the edges are not
label_slots = [
    "middle right",
    "top right",
    "top center",
    "top left",
    "middle left",
    "bottom left",
    "bottom center",
    "bottom right",
]
neighbour_mean = np.array([pos[np.r_[dst[src == i], src[dst == i]]].mean(axis=0) for i in range(len(nodes))])
outward = pos - neighbour_mean
angle = np.degrees(np.arctan2(outward[:, 1], outward[:, 0])) % 360
label_pos = [label_slots[int(((a + 22.5) % 360) // 45)] for a in angle]

# Edge widths and node sizes follow the data
edge_width = 1.5 + w_norm * 9
edge_alpha = 0.4 + w_norm * 0.5
node_size = 9 + degree / degree.max() * 24

fig = go.Figure()
for a, b, w, lw, alpha in zip(src, dst, weights, edge_width, edge_alpha, strict=True):
    fig.add_trace(
        go.Scatter(
            x=[pos[a, 0], pos[b, 0]],
            y=[pos[a, 1], pos[b, 1]],
            mode="lines",
            line={"width": lw, "color": f"rgba(0, 158, 115, {alpha:.2f})"},
            hoverinfo="text",
            text=f"{nodes[a]} ↔ {nodes[b]}: {w:.0f}",
            showlegend=False,
        )
    )

fig.add_trace(
    go.Scatter(
        x=pos[:, 0],
        y=pos[:, 1],
        mode="markers+text",
        marker={"size": node_size, "color": BRAND, "line": {"width": 1, "color": INK_SOFT}},
        text=nodes,
        textposition=label_pos,
        textfont={"size": 10, "color": INK},
        hoverinfo="text",
        hovertext=[f"{n}<br>Weighted degree: {d:.0f}" for n, d in zip(nodes, degree, strict=True)],
        showlegend=False,
    )
)

# Weight scale: edge width and node size explained in one caption
fig.add_annotation(
    x=0.01,
    y=0.02,
    xref="paper",
    yref="paper",
    text=(
        f"<b>Edge width</b> = {WEIGHT}<br>thin: {w_min:.0f} · thick: {w_max:.0f}<br><b>Node size</b> = weighted degree"
    ),
    showarrow=False,
    font={"size": 10, "color": INK},
    align="left",
    xanchor="left",
    yanchor="bottom",
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=6,
)

axis = {"showgrid": False, "zeroline": False, "showticklabels": False, "title": "", "showline": False}
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={"text": "network-weighted · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}, "x": 0.5},
    xaxis={**axis, "range": [pos[:, 0].min() - 0.5, pos[:, 0].max() + 0.5]},
    yaxis={**axis, "range": [pos[:, 1].min() - 0.3, pos[:, 1].max() + 0.3]},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    margin={"l": 40, "r": 40, "t": 60, "b": 30},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
