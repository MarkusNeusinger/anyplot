""" pyplots.ai
waffle-basic: Basic Waffle Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import numpy as np
import plotly.graph_objects as go


# Data - Budget allocation across spending categories
categories = ["Operations", "Marketing", "R&D", "HR", "Other"]
values = [35, 25, 22, 12, 6]  # Percentages (sum to 100)

# Colors (Python Blue first, then complementary colorblind-safe colors)
colors = ["#306998", "#FFD43B", "#4ECDC4", "#E76F51", "#9B59B6"]

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
                    "color": colors[cat_idx],
                    "line": {"color": "white", "width": 2},
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
            marker={"size": 22, "symbol": "square", "color": colors[cat_idx]},
            name=f"{cat}: {val}%",
            showlegend=True,
        )
    )

# Layout
fig.update_layout(
    title={
        "text": "Budget Allocation · waffle-basic · plotly · pyplots.ai",
        "font": {"size": 32},
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
        "font": {"size": 20},
        "orientation": "h",
        "yanchor": "top",
        "y": -0.05,
        "xanchor": "center",
        "x": 0.5,
        "itemsizing": "constant",
    },
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 60, "r": 60, "t": 120, "b": 120},
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
