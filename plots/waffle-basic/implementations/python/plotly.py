""" anyplot.ai
waffle-basic: Basic Waffle Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-05
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette - first series ALWAYS #009E73
OKABE_ITO = [
    "#009E73",  # bluish green (brand)
    "#D55E00",  # vermillion
    "#0072B2",  # blue
    "#CC79A7",  # reddish purple
    "#E69F00",  # orange
]

# Data - Budget allocation across spending categories
categories = ["Operations", "Marketing", "R&D", "HR", "Other"]
values = [35, 25, 22, 12, 6]  # Percentages (sum to 100)

# Create 10x10 waffle grid (100 squares, each = 1%)
grid_size = 10
total_squares = grid_size * grid_size
waffle_data = np.zeros(total_squares, dtype=int)

# Fill grid with category indices (row by row from bottom-left)
square_idx = 0
for cat_idx, count in enumerate(values):
    for _ in range(count):
        if square_idx < total_squares:
            waffle_data[square_idx] = cat_idx
            square_idx += 1

# Reshape to 10x10 grid
waffle_matrix = waffle_data.reshape(grid_size, grid_size)

# Create figure
fig = go.Figure()

# Add squares using scatter plot with larger markers for visibility
for row in range(grid_size):
    for col in range(grid_size):
        cat_idx = waffle_matrix[row, col]
        fig.add_trace(
            go.Scatter(
                x=[col],
                y=[row],
                mode="markers",
                marker={
                    "size": 55,
                    "symbol": "square",
                    "color": OKABE_ITO[cat_idx],
                    "line": {"color": PAGE_BG, "width": 2},
                },
                showlegend=False,
                hoverinfo="skip",
            )
        )

# Add legend traces (one per category)
for cat_idx, (cat, val) in enumerate(zip(categories, values, strict=True)):
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={"size": 22, "symbol": "square", "color": OKABE_ITO[cat_idx]},
            name=f"{cat}: {val}%",
            showlegend=True,
        )
    )

# Layout
fig.update_layout(
    title={
        "text": "waffle-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "range": [-0.8, 9.8],
        "scaleanchor": "y",
        "scaleratio": 1,
    },
    yaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-0.8, 9.8]},
    legend={
        "font": {"size": 18, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "orientation": "h",
        "yanchor": "top",
        "y": -0.08,
        "xanchor": "center",
        "x": 0.5,
        "itemsizing": "constant",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 60, "r": 60, "t": 120, "b": 120},
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
