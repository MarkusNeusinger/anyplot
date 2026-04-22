""" pyplots.ai
chessboard-basic: Chess Board Grid Visualization
Library: plotly 6.5.1 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-08
"""

import numpy as np
import plotly.graph_objects as go


# Data - 8x8 chess board
rows = 8
cols = 8
row_labels = ["1", "2", "3", "4", "5", "6", "7", "8"]
col_labels = ["a", "b", "c", "d", "e", "f", "g", "h"]

# Create chess board pattern (0 = light, 1 = dark)
# h1 should be light (white), so pattern starts with light at (0,7)
board = np.zeros((rows, cols))
for row in range(rows):
    for col in range(cols):
        # Light square when row+col is odd (to have h1 light)
        board[row, col] = 0 if (row + col) % 2 == 1 else 1

# Colors - classic cream and brown
light_color = "#F0D9B5"  # Cream
dark_color = "#B58863"  # Brown

# Create figure
fig = go.Figure()

# Add squares as shapes
for row in range(rows):
    for col in range(cols):
        color = light_color if board[row, col] == 0 else dark_color
        fig.add_shape(
            type="rect", x0=col, y0=row, x1=col + 1, y1=row + 1, fillcolor=color, line=dict(color="#8B7355", width=1)
        )

# Configure layout
fig.update_layout(
    title=dict(
        text="chessboard-basic · plotly · pyplots.ai", font=dict(size=32, color="#333333"), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        tickmode="array",
        tickvals=[i + 0.5 for i in range(cols)],
        ticktext=col_labels,
        tickfont=dict(size=24, color="#333333"),
        range=[0, 8],
        showgrid=False,
        zeroline=False,
        side="bottom",
        constrain="domain",
    ),
    yaxis=dict(
        tickmode="array",
        tickvals=[i + 0.5 for i in range(rows)],
        ticktext=row_labels,
        tickfont=dict(size=24, color="#333333"),
        range=[0, 8],
        showgrid=False,
        zeroline=False,
        scaleanchor="x",
        scaleratio=1,
    ),
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=80, r=80, t=120, b=80),
)

# Save as PNG (3600x3600 for square aspect ratio)
fig.write_image("plot.png", width=1200, height=1200, scale=3)

# Save interactive HTML
fig.write_html("plot.html")
