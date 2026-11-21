"""anyplot.ai
network-directed: Directed Network Graph
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NODE_PX = 28  # node marker diameter in pixels on the 600 px canvas
CANVAS = 600  # square canvas, the circular layout has no preferred axis
ARROW_LEN = 0.4  # tail distance of the arrow annotation (data units)
CURVE = 0.55  # sideways bow of an edge whose reverse edge also exists (data units)

# Columns: set these to your table's column names
SOURCE = "Source module"  # role: edges
TARGET = "Target module"  # role: edges
MODULE = "Module"  # role: nodes
GROUP = "Module group"  # role: nodes

# Data: replace this block with your own edge list (df) and node table (nodes),
# for example df = pd.read_csv("edges.csv")
nodes = pd.DataFrame(
    {
        MODULE: [
            "main",
            "api",
            "auth",
            "database",
            "models",
            "utils",
            "config",
            "logging",
            "cache",
            "router",
            "middleware",
            "validators",
            "schemas",
        ],
        GROUP: [
            "Entry",
            "Core",
            "Core",
            "Core",
            "Data",
            "Helpers",
            "Helpers",
            "Helpers",
            "Core",
            "Core",
            "Core",
            "Data",
            "Data",
        ],
    }
)
edge_pairs = [
    ("main", "api"),
    ("main", "config"),
    ("main", "logging"),
    ("api", "auth"),
    ("api", "router"),
    ("api", "middleware"),
    ("auth", "database"),
    ("auth", "utils"),
    ("database", "models"),
    ("database", "cache"),
    ("models", "schemas"),
    ("utils", "logging"),
    ("config", "logging"),
    ("cache", "logging"),
    ("router", "middleware"),
    ("router", "validators"),
    ("middleware", "auth"),
    ("validators", "schemas"),
    ("schemas", "utils"),
    ("utils", "schemas"),
]
df = pd.DataFrame(edge_pairs, columns=[SOURCE, TARGET])

# Plot: reads only df, nodes and the constants above
# Circular layout: nodes evenly spaced in the order of the node table
n_nodes = len(nodes)
angles = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)
radius = 3.0
pos = {m: (radius * np.cos(a), radius * np.sin(a)) for m, a in zip(nodes[MODULE], angles, strict=True)}

# Scale: labels sit outside the ring, so the view extends past it by label width
view = radius * 1.55
px_per_unit = (CANVAS - 40) / (2 * view)
trim = (NODE_PX / 2 + 1) / px_per_unit  # edges stop at the node border

# Pairs linked in both directions get two curved edges, all others stay straight
edge_set = set(zip(df[SOURCE], df[TARGET], strict=True))

fig = go.Figure()
t = np.linspace(0, 1, 60)
for src, dst in zip(df[SOURCE], df[TARGET], strict=True):
    p0, p2 = np.array(pos[src]), np.array(pos[dst])
    direction = (p2 - p0) / np.hypot(*(p2 - p0))
    bow = CURVE if (dst, src) in edge_set else 0.0
    ctrl = (p0 + p2) / 2 + bow * np.array([-direction[1], direction[0]]) * 2
    # Quadratic Bezier from node centre to node centre
    path = ((1 - t) ** 2)[:, None] * p0 + (2 * (1 - t) * t)[:, None] * ctrl + (t**2)[:, None] * p2
    keep = (np.hypot(*(path - p0).T) > trim) & (np.hypot(*(path - p2).T) > trim)
    path = path[keep]
    fig.add_trace(
        go.Scatter(
            x=path[:, 0],
            y=path[:, 1],
            mode="lines",
            line=dict(width=1.5, color=INK_SOFT),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    # Arrowhead at the target border, pointing along the end of the path; the tail is
    # a fixed distance back so short edges keep a visible head
    back = np.nonzero(np.hypot(*(path - path[-1]).T) >= ARROW_LEN)[0]
    tail = path[back[-1]] if len(back) else path[0]
    fig.add_annotation(
        x=path[-1, 0],
        y=path[-1, 1],
        ax=tail[0],
        ay=tail[1],
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.3,
        arrowwidth=1.5,
        arrowcolor=INK_SOFT,
    )

# Nodes by group, label pushed outward from the ring so edges stay out of the text
for i, (group, members) in enumerate(nodes.groupby(GROUP, sort=False)):
    xs = np.array([pos[m][0] for m in members[MODULE]])
    ys = np.array([pos[m][1] for m in members[MODULE]])
    side = np.where(xs > 0.5, "middle right", np.where(xs < -0.5, "middle left", "top center"))
    side = np.where((side == "top center") & (ys < 0), "bottom center", side)
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            marker=dict(size=NODE_PX, color=IMPRINT_PALETTE[i], line=dict(width=1.5, color=INK_SOFT)),
            text=members[MODULE],
            textposition=list(side),
            textfont=dict(size=11, color=INK, family="monospace"),
            name=str(group),
            hovertemplate="<b>%{text}</b><br>" + GROUP + ": " + str(group) + "<extra></extra>",
        )
    )

# Style
fig.update_layout(
    autosize=False,
    title=dict(text="network-directed · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title="", range=[-view, view]),
    yaxis=dict(
        showgrid=False,
        zeroline=False,
        showticklabels=False,
        title="",
        range=[-view, view],
        scaleanchor="x",
        scaleratio=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    showlegend=True,
    legend=dict(
        title=dict(text=GROUP, font=dict(size=11, color=INK)),
        font=dict(size=11, color=INK_SOFT),
        orientation="h",
        x=0.5,
        xanchor="center",
        y=0.0,
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=20, r=20, t=60, b=60),
    hovermode="closest",
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=CANVAS, height=CANVAS, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
