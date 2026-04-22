""" pyplots.ai
ternary-basic: Basic Ternary Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Soil composition samples (sand, silt, clay)
np.random.seed(42)
n_points = 50

# Generate random compositional data that sums to 100
raw = np.random.dirichlet([2, 2, 2], size=n_points) * 100
sand = raw[:, 0]
silt = raw[:, 1]
clay = raw[:, 2]

# Ternary to Cartesian conversion
# In a standard ternary plot with equilateral triangle:
# - Bottom-left vertex (0,0): 100% Sand
# - Bottom-right vertex (1,0): 100% Silt
# - Top vertex (0.5, sqrt(3)/2): 100% Clay
height = np.sqrt(3) / 2
total = sand + silt + clay
x = silt / total + 0.5 * clay / total
y = clay / total * height

df = pd.DataFrame({"x": x, "y": y, "Sand (%)": sand.round(1), "Silt (%)": silt.round(1), "Clay (%)": clay.round(1)})

# Create triangle outline
triangle_vertices = pd.DataFrame(
    {"x": [0, 1, 0.5, 0], "y": [0, 0, height, 0], "order": [0, 1, 2, 3]}  # Close the triangle
)

# Create grid lines at 20% intervals
grid_lines = []

for pct in [20, 40, 60, 80]:
    # Lines parallel to bottom edge (constant clay)
    a1, b1, c1 = 100 - pct, 0, pct
    a2, b2, c2 = 0, 100 - pct, pct
    x1 = b1 / 100 + 0.5 * c1 / 100
    y1 = c1 / 100 * height
    x2 = b2 / 100 + 0.5 * c2 / 100
    y2 = c2 / 100 * height
    grid_lines.append({"x": x1, "y": y1, "x2": x2, "y2": y2})

    # Lines parallel to left edge (constant silt)
    a1, b1, c1 = 100 - pct, pct, 0
    a2, b2, c2 = 0, pct, 100 - pct
    x1 = b1 / 100 + 0.5 * c1 / 100
    y1 = c1 / 100 * height
    x2 = b2 / 100 + 0.5 * c2 / 100
    y2 = c2 / 100 * height
    grid_lines.append({"x": x1, "y": y1, "x2": x2, "y2": y2})

    # Lines parallel to right edge (constant sand)
    a1, b1, c1 = pct, 100 - pct, 0
    a2, b2, c2 = pct, 0, 100 - pct
    x1 = b1 / 100 + 0.5 * c1 / 100
    y1 = c1 / 100 * height
    x2 = b2 / 100 + 0.5 * c2 / 100
    y2 = c2 / 100 * height
    grid_lines.append({"x": x1, "y": y1, "x2": x2, "y2": y2})

grid_df = pd.DataFrame(grid_lines)

# Create tick marks along each edge (exclude 0 and 100 to avoid vertex overlap)
tick_data = []
tick_length = 0.03

for pct in [20, 40, 60, 80]:
    # Bottom edge ticks (sand axis) - from left (100%) to right (0%)
    tx = pct / 100
    tick_data.append(
        {"x": tx, "y": 0, "x2": tx, "y2": -tick_length, "label": str(100 - pct), "label_x": tx, "label_y": -0.06}
    )

    # Left edge ticks (clay axis) - from bottom (0%) to top (100%)
    cx = 0.5 * pct / 100
    cy = pct / 100 * height
    dx = -tick_length * np.cos(np.pi / 6)
    dy = -tick_length * np.sin(np.pi / 6)
    tick_data.append(
        {
            "x": cx,
            "y": cy,
            "x2": cx + dx,
            "y2": cy + dy,
            "label": str(pct),
            "label_x": cx + dx * 2.5,
            "label_y": cy + dy * 2.5,
        }
    )

    # Right edge ticks (silt axis) - from bottom (0%) to top (100%)
    sx = 1 - 0.5 * pct / 100
    sy = pct / 100 * height
    dx = tick_length * np.cos(np.pi / 6)
    dy = -tick_length * np.sin(np.pi / 6)
    tick_data.append(
        {
            "x": sx,
            "y": sy,
            "x2": sx + dx,
            "y2": sy + dy,
            "label": str(pct),
            "label_x": sx + dx * 2.5,
            "label_y": sy + dy * 2.5,
        }
    )

tick_df = pd.DataFrame(tick_data)

# Vertex labels
vertex_labels = pd.DataFrame(
    {"x": [0, 1, 0.5], "y": [-0.12, -0.12, height + 0.08], "label": ["Sand (100%)", "Silt (100%)", "Clay (100%)"]}
)

# Triangle outline
triangle = (
    alt.Chart(triangle_vertices)
    .mark_line(strokeWidth=3, color="#333333")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), order="order:O")
)

# Grid lines
grid = (
    alt.Chart(grid_df)
    .mark_rule(strokeWidth=1, opacity=0.3, color="#888888", strokeDash=[4, 4])
    .encode(x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q")
)

# Tick marks
ticks = alt.Chart(tick_df).mark_rule(strokeWidth=2, color="#333333").encode(x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q")

# Tick labels
tick_labels = (
    alt.Chart(tick_df).mark_text(fontSize=14, color="#555555").encode(x="label_x:Q", y="label_y:Q", text="label:N")
)

# Vertex labels
vertex_text = (
    alt.Chart(vertex_labels)
    .mark_text(fontSize=22, fontWeight="bold", color="#333333")
    .encode(x="x:Q", y="y:Q", text="label:N")
)

# Data points
points = (
    alt.Chart(df)
    .mark_point(filled=True, size=300, color="#306998", opacity=0.8)
    .encode(
        x="x:Q",
        y="y:Q",
        tooltip=[
            alt.Tooltip("Sand (%):Q", format=".1f"),
            alt.Tooltip("Silt (%):Q", format=".1f"),
            alt.Tooltip("Clay (%):Q", format=".1f"),
        ],
    )
)

# Combine all layers and hide default axes
chart = (
    alt.layer(grid, triangle, ticks, tick_labels, vertex_text, points)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(text="Soil Composition · ternary-basic · altair · pyplots.ai", fontSize=28),
    )
    .configure_axis(grid=False, domain=False, ticks=False, labels=False, title=None)
    .configure_view(strokeWidth=0)
)

# Save (1600 * 3 = 4800, 900 * 3 = 2700)
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
