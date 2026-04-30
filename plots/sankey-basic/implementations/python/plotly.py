""" anyplot.ai
sankey-basic: Basic Sankey Diagram
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-04-30
"""

import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for source nodes (positions 1-4)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]
SOURCE_RGBA = ["rgba(0,158,115,0.4)", "rgba(213,94,0,0.4)", "rgba(0,114,178,0.4)", "rgba(204,121,167,0.4)"]

# Data - Energy flow from sources to sectors (TWh)
sources = ["Coal", "Natural Gas", "Nuclear", "Renewables"]
targets = ["Residential", "Commercial", "Industrial", "Transportation"]
labels = sources + targets

flows = [
    (0, 4, 5),
    (0, 5, 8),
    (0, 6, 25),
    (1, 4, 22),
    (1, 5, 18),
    (1, 6, 15),
    (1, 7, 3),
    (2, 4, 12),
    (2, 5, 10),
    (2, 6, 8),
    (3, 4, 8),
    (3, 5, 6),
    (3, 6, 5),
    (3, 7, 4),
]

source_indices = [f[0] for f in flows]
target_indices = [f[1] for f in flows]
values = [f[2] for f in flows]

# Source nodes use Okabe-Ito colors; target nodes use INK_SOFT
node_colors = OKABE_ITO + [INK_SOFT] * 4
link_colors = [SOURCE_RGBA[s] for s in source_indices]

# Plot
fig = go.Figure(
    data=[
        go.Sankey(
            node={
                "pad": 25,
                "thickness": 35,
                "line": {"color": PAGE_BG, "width": 1},
                "label": labels,
                "color": node_colors,
            },
            link={"source": source_indices, "target": target_indices, "value": values, "color": link_colors},
        )
    ]
)

fig.update_layout(
    title={
        "text": "Energy Distribution · sankey-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"size": 22, "color": INK},
    margin={"l": 80, "r": 80, "t": 120, "b": 60},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
