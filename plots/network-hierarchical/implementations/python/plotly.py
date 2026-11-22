"""anyplot.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: plotly 7.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: one position per hierarchy level, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LEVEL_HEIGHT = 2.8  # vertical distance between levels
LEAF_SPACING = 1.6  # horizontal distance between neighbouring leaves

# Columns: set these to your table's column names
NODE = "Node"  # role: nodes
LABEL = "Label"  # role: extra
PARENT = "Parent"  # role: edges

# Data: replace this block with your own table, for example df = pd.read_csv("org_chart.csv")
# An organizational chart with 20 employees across 4 levels; the root has no parent.
df = pd.DataFrame(
    [
        ("CEO", "CEO", None),
        ("VP_Eng", "VP Engineering", "CEO"),
        ("VP_Sales", "VP Sales", "CEO"),
        ("VP_Ops", "VP Operations", "CEO"),
        ("Dir_FE", "Frontend", "VP_Eng"),
        ("Dir_BE", "Backend", "VP_Eng"),
        ("Dir_QA", "QA", "VP_Eng"),
        ("Dir_NA", "Americas", "VP_Sales"),
        ("Dir_EU", "EMEA", "VP_Sales"),
        ("Dir_HR", "HR", "VP_Ops"),
        ("Dir_Fin", "Finance", "VP_Ops"),
        ("Mgr_React", "React Lead", "Dir_FE"),
        ("Mgr_Vue", "Vue Lead", "Dir_FE"),
        ("Mgr_API", "API Lead", "Dir_BE"),
        ("Mgr_Test", "Test Lead", "Dir_QA"),
        ("Mgr_East", "East Sales", "Dir_NA"),
        ("Mgr_West", "West Sales", "Dir_NA"),
        ("Mgr_UK", "UK Sales", "Dir_EU"),
        ("Mgr_Recruit", "Recruiting", "Dir_HR"),
        ("Mgr_Acct", "Accounting", "Dir_Fin"),
    ],
    columns=[NODE, LABEL, PARENT],
)

# Plot: reads only df and the constants above
labels = dict(zip(df[NODE], df[LABEL], strict=True))
children = {node: [] for node in df[NODE]}
for node, parent in zip(df[NODE], df[PARENT], strict=True):
    if pd.notna(parent):
        children[parent].append(node)
root = df.loc[df[PARENT].isna(), NODE].iloc[0]

# Tidy tree layout: leaves take consecutive slots, each parent is centred over its children
level = {}
x_pos = {}
next_slot = [0]


def place(node, depth):
    level[node] = depth
    if children[node]:
        child_x = [place(child, depth + 1) for child in children[node]]
        x_pos[node] = sum(child_x) / len(child_x)
    else:
        x_pos[node] = next_slot[0] * LEAF_SPACING
        next_slot[0] += 1
    return x_pos[node]


place(root, 0)
positions = {node: (x_pos[node], -level[node] * LEVEL_HEIGHT) for node in df[NODE]}

# Orthogonal edges: down from the parent, across at mid-height, down into the child
edge_x, edge_y = [], []
for parent, kids in children.items():
    for kid in kids:
        x0, y0 = positions[parent]
        x1, y1 = positions[kid]
        mid_y = (y0 + y1) / 2
        edge_x += [x0, x0, x1, x1, None]
        edge_y += [y0, mid_y, mid_y, y1, None]

edge_trace = go.Scatter(
    x=edge_x, y=edge_y, mode="lines", line={"width": 1.5, "color": INK_SOFT}, hoverinfo="none", showlegend=False
)

nodes = list(df[NODE])
node_trace = go.Scatter(
    x=[positions[n][0] for n in nodes],
    y=[positions[n][1] for n in nodes],
    mode="markers+text",
    marker={"size": 24, "color": [IMPRINT_PALETTE[level[n]] for n in nodes], "line": {"width": 1.5, "color": PAGE_BG}},
    text=[labels[n] for n in nodes],
    textposition=["bottom center" if not children[n] else "middle right" for n in nodes],
    textfont={"size": 10, "color": INK},
    hoverinfo="text",
    hovertext=[f"{labels[n]}<br>Level {level[n]}" for n in nodes],
    showlegend=False,
)

fig = go.Figure(data=[edge_trace, node_trace])

xs = [p[0] for p in positions.values()]
ys = [p[1] for p in positions.values()]
fig.update_layout(
    autosize=False,
    title={
        "text": "network-hierarchical · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    showlegend=False,
    xaxis={
        "visible": False,
        "showgrid": False,
        "zeroline": False,
        "range": [min(xs) - LEAF_SPACING * 0.8, max(xs) + LEAF_SPACING * 0.8],
    },
    yaxis={
        "visible": False,
        "showgrid": False,
        "zeroline": False,
        "range": [min(ys) - LEVEL_HEIGHT * 0.6, max(ys) + LEVEL_HEIGHT * 0.3],
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 30, "r": 30, "t": 60, "b": 20},
    font={"color": INK},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
