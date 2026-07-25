""" anyplot.ai
sankey-basic: Basic Sankey Diagram
Library: plotly 6.9.0 | Python 3.13.14
Quality: 83/100 | Updated: 2026-07-25
"""

import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette for source nodes (positions 1-4)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]
SOURCE_RGBA = [
    "rgba(0, 158, 115, 0.4)",
    "rgba(196, 117, 253, 0.4)",
    "rgba(68, 103, 163, 0.4)",
    "rgba(189, 130, 51, 0.4)",
]

# Data - Energy flow from sources to sectors (TWh)
sources = ["Coal", "Natural Gas", "Nuclear", "Renewables"]
targets = ["Residential", "Commercial", "Industrial", "Transportation"]
labels = sources + targets

flows = [
    (0, 4, 2),
    (0, 5, 8),
    (0, 6, 25),
    (1, 4, 22),
    (1, 5, 18),
    (1, 6, 15),
    (1, 7, 3),
    (2, 4, 12),
    (2, 5, 10),
    (2, 6, 8),
    (3, 4, 18),
    (3, 5, 4),
    (3, 6, 2),
    (3, 7, 10),
]

source_indices = [f[0] for f in flows]
target_indices = [f[1] for f in flows]
values = [f[2] for f in flows]

# Source nodes use Imprint colors; target nodes use INK_SOFT
node_colors = IMPRINT + [INK_SOFT] * 4
link_colors = [SOURCE_RGBA[s] for s in source_indices]

# Plot
fig = go.Figure(
    data=[
        go.Sankey(
            node={
                "pad": 20,
                "thickness": 28,
                "line": {"color": PAGE_BG, "width": 1},
                "label": labels,
                "color": node_colors,
            },
            link={"source": source_indices, "target": target_indices, "value": values, "color": link_colors},
        )
    ]
)

fig.update_layout(
    autosize=False,
    title={
        "text": "Energy Distribution · sankey-basic · python · plotly · anyplot.ai",
        "font": {"size": 20, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"size": 16, "color": INK},
    margin={"l": 60, "r": 60, "t": 90, "b": 45},
    annotations=[
        {
            "text": "Flow values in TWh",
            "font": {"size": 11, "color": INK_SOFT},
            "x": 0.99,
            "y": -0.06,
            "xref": "paper",
            "yref": "paper",
            "xanchor": "right",
            "yanchor": "top",
            "showarrow": False,
        }
    ],
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
