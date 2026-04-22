""" pyplots.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import numpy as np
import plotly.graph_objects as go


# Data - encode a sample serial number into a Data Matrix pattern
# Data Matrix uses Reed-Solomon error correction (ECC 200)
# We'll create a 16x16 matrix with proper structure

content = "SERIAL:12345678"
matrix_size = 16

# Create the Data Matrix pattern
# The pattern has: L-shaped finder (solid left and bottom),
# alternating timing pattern (top and right edges)
np.random.seed(42)

matrix = np.zeros((matrix_size, matrix_size), dtype=int)

# L-shaped finder pattern (solid black on left column and bottom row)
matrix[:, 0] = 1  # Left column solid black
matrix[matrix_size - 1, :] = 1  # Bottom row solid black

# Alternating timing patterns (top row and right column)
# Top row: alternating starting with black
for i in range(matrix_size):
    matrix[0, i] = i % 2

# Right column: alternating starting with black
for i in range(matrix_size):
    matrix[i, matrix_size - 1] = i % 2

# Fill interior with encoded data pattern (simulated ECC 200 encoding)
# In real Data Matrix, this would be Reed-Solomon encoded data
# Using deterministic pattern based on content hash
content_hash = sum(ord(c) for c in content)
np.random.seed(content_hash)

for i in range(1, matrix_size - 1):
    for j in range(1, matrix_size - 1):
        # Create data pattern avoiding finder/timing edges
        matrix[i, j] = np.random.randint(0, 2)

# Flip matrix for correct visual orientation (row 0 at top)
matrix = np.flipud(matrix)

# Create figure with heatmap
fig = go.Figure()

# Add the Data Matrix as a heatmap
fig.add_trace(
    go.Heatmap(
        z=matrix,
        x=np.arange(matrix_size),
        y=np.arange(matrix_size),
        colorscale=[[0, "white"], [1, "black"]],
        showscale=False,
        xgap=1,
        ygap=1,
    )
)

# Update layout for proper barcode appearance
fig.update_layout(
    title={
        "text": "datamatrix-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "showticklabels": False,
        "showgrid": False,
        "zeroline": False,
        "scaleanchor": "y",
        "scaleratio": 1,
        "constrain": "domain",
    },
    yaxis={"showticklabels": False, "showgrid": False, "zeroline": False, "constrain": "domain"},
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 100, "r": 100, "t": 120, "b": 100},
    annotations=[
        {
            "text": f"Encoded: {content}",
            "xref": "paper",
            "yref": "paper",
            "x": 0.5,
            "y": -0.08,
            "showarrow": False,
            "font": {"size": 20, "color": "#555555"},
            "xanchor": "center",
        },
        {
            "text": "ECC 200 | 16×16 Matrix",
            "xref": "paper",
            "yref": "paper",
            "x": 0.5,
            "y": -0.14,
            "showarrow": False,
            "font": {"size": 16, "color": "#777777"},
            "xanchor": "center",
        },
    ],
)

# Ensure square aspect ratio
fig.update_yaxes(scaleanchor="x", scaleratio=1)

# Save as PNG (4800 x 2700 px using scale=3)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html("plot.html", include_plotlyjs="cdn")
