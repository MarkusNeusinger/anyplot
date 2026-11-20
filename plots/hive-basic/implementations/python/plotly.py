"""anyplot.ai
hive-basic: Basic Hive Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
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

# Imprint palette: one position per axis group, in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MODULE = "Module"  # role: nodes
MODULE_TYPE = "Module type"  # role: axis_attribute
DEGREE = "Degree"  # role: extra
SOURCE = "Depends on"  # role: edges
TARGET = "Used by"  # role: extra

# Data: replace this block with your own edge list (df) and node table (nodes),
# for example df = pd.read_csv("edges.csv"); nodes = pd.read_csv("nodes.csv")
nodes = pd.DataFrame(
    {
        MODULE: [
            "engine", "runtime", "compiler", "memory", "scheduler",
            "logger", "parser", "config", "cache", "validator", "formatter",
            "api", "web", "cli", "rest", "grpc",
        ],
        MODULE_TYPE: ["core"] * 5 + ["utility"] * 6 + ["interface"] * 5,
        DEGREE: [8, 6, 5, 4, 3, 7, 6, 5, 4, 3, 2, 9, 6, 5, 4, 3],
    }
)  # fmt: skip
df = pd.DataFrame(
    [
        ("api", "engine"), ("api", "logger"), ("api", "config"), ("api", "cache"),
        ("cli", "engine"), ("cli", "parser"), ("cli", "formatter"),
        ("web", "runtime"), ("web", "logger"), ("web", "cache"),
        ("rest", "engine"), ("rest", "validator"),
        ("grpc", "runtime"), ("grpc", "config"),
        ("engine", "memory"), ("engine", "scheduler"), ("engine", "logger"),
        ("runtime", "memory"), ("runtime", "cache"),
        ("compiler", "parser"), ("compiler", "memory"),
        ("logger", "config"), ("cache", "memory"), ("parser", "validator"),
    ],
    columns=[SOURCE, TARGET],
)  # fmt: skip

# Plot
INNER_RADIUS = 0.25
OUTER_RADIUS = 0.90

groups = list(nodes[MODULE_TYPE].unique())
group_color = {g: IMPRINT_PALETTE[i] for i, g in enumerate(groups)}
group_angle = {g: np.radians(90 + 360 / len(groups) * i) for i, g in enumerate(groups)}
module_group = dict(zip(nodes[MODULE], nodes[MODULE_TYPE], strict=True))

# Position along each axis: highest degree innermost, evenly ranked outward
positions = {}
for g in groups:
    members = nodes[nodes[MODULE_TYPE] == g].sort_values(DEGREE, ascending=False, kind="stable")
    n = len(members)
    for rank, module in enumerate(members[MODULE]):
        t = rank / (n - 1) if n > 1 else 0.5
        r = INNER_RADIUS + t * (OUTER_RADIUS - INNER_RADIUS)
        positions[module] = (r * np.cos(group_angle[g]), r * np.sin(group_angle[g]))

fig = go.Figure()

# Radial axes
for g in groups:
    a = group_angle[g]
    fig.add_trace(
        go.Scatter(
            x=[INNER_RADIUS * 0.7 * np.cos(a), OUTER_RADIUS * 1.05 * np.cos(a)],
            y=[INNER_RADIUS * 0.7 * np.sin(a), OUTER_RADIUS * 1.05 * np.sin(a)],
            mode="lines",
            line={"color": group_color[g], "width": 3},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Edges: quadratic bezier curves pulled toward the center, translucent
t_vals = np.linspace(0, 1, 40)
for source, target in df[[SOURCE, TARGET]].itertuples(index=False):
    x0, y0 = positions[source]
    x1, y1 = positions[target]
    cx, cy = (x0 + x1) / 2 * 0.25, (y0 + y1) / 2 * 0.25
    fig.add_trace(
        go.Scatter(
            x=(1 - t_vals) ** 2 * x0 + 2 * (1 - t_vals) * t_vals * cx + t_vals**2 * x1,
            y=(1 - t_vals) ** 2 * y0 + 2 * (1 - t_vals) * t_vals * cy + t_vals**2 * y1,
            mode="lines",
            line={"color": group_color[module_group[source]], "width": 1.5},
            opacity=0.35,
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Nodes, one trace per group; labels sit beside the axis, away from it
label_side = {0: "middle right", 1: "top left", 2: "top right"}
for i, g in enumerate(groups):
    members = nodes[nodes[MODULE_TYPE] == g].sort_values(DEGREE, ascending=False, kind="stable")
    fig.add_trace(
        go.Scatter(
            x=[positions[m][0] for m in members[MODULE]],
            y=[positions[m][1] for m in members[MODULE]],
            mode="markers+text",
            marker={"size": members[DEGREE] * 2 + 8, "color": group_color[g], "line": {"color": PAGE_BG, "width": 1.5}},
            text=members[MODULE],
            textposition=label_side.get(i, "top center"),
            textfont={"size": 11, "color": INK_SOFT},
            name=str(g).capitalize(),
            hovertemplate="<b>%{text}</b><br>" + DEGREE + ": %{customdata}<extra></extra>",
            customdata=members[DEGREE],
        )
    )

# Axis labels beyond the outermost nodes
for g in groups:
    a = group_angle[g]
    fig.add_annotation(
        x=OUTER_RADIUS * 1.22 * np.cos(a),
        y=OUTER_RADIUS * 1.22 * np.sin(a),
        text=f"<b>{str(g).upper()}</b>",
        showarrow=False,
        font={"size": 14, "color": group_color[g]},
    )

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": (
            "hive-basic · python · plotly · anyplot.ai"
            f"<br><sup>Software dependency network: axis by module type, distance from center by {DEGREE.lower()}</sup>"
        ),
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    showlegend=True,
    legend={
        "title": {"text": MODULE_TYPE, "font": {"size": 12, "color": INK}},
        "font": {"size": 11, "color": INK_SOFT},
        "x": 0.01,
        "y": 0.86,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    xaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-1.15, 1.15]},
    yaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "range": [-0.8, 1.3],
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 30, "r": 30, "t": 70, "b": 30},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
