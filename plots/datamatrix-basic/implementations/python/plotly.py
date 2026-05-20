""" anyplot.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: plotly 6.7.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-20
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Barcode cell colors — inverted per theme for contrast
CELL_ON = "#1A1A17" if THEME == "light" else "#F0EFE8"
CELL_OFF = PAGE_BG

# Data - encode a sample serial number into a 16×16 Data Matrix pattern
content = "SERIAL:12345678"
matrix_size = 16

matrix = np.zeros((matrix_size, matrix_size), dtype=int)

# L-shaped finder pattern (solid left column and bottom row)
matrix[:, 0] = 1
matrix[matrix_size - 1, :] = 1

# Alternating timing patterns (top row and right column)
for i in range(matrix_size):
    matrix[0, i] = i % 2
for i in range(matrix_size):
    matrix[i, matrix_size - 1] = i % 2

# Interior data cells — deterministic pattern based on content (simulated ECC 200)
content_hash = sum(ord(c) for c in content)
np.random.seed(content_hash)
for i in range(1, matrix_size - 1):
    for j in range(1, matrix_size - 1):
        matrix[i, j] = np.random.randint(0, 2)

# Flip for correct visual orientation (L-finder at left+bottom in display)
matrix = np.flipud(matrix)

# Cell type labels for interactive hover (post-flipud: row 0=bottom=finder, row 15=top=timing)
cell_type = np.empty((matrix_size, matrix_size), dtype=object)
for i in range(matrix_size):
    for j in range(matrix_size):
        if j == 0 or i == 0:
            cell_type[i, j] = "Finder"
        elif j == matrix_size - 1 or i == matrix_size - 1:
            cell_type[i, j] = "Timing"
        else:
            cell_type[i, j] = "Data"

# Plot
fig = go.Figure()

fig.add_trace(
    go.Heatmap(
        z=matrix,
        x=np.arange(matrix_size),
        y=np.arange(matrix_size),
        customdata=cell_type,
        hovertemplate="<b>%{customdata}</b><extra></extra>",
        colorscale=[[0, CELL_OFF], [1, CELL_ON]],
        showscale=False,
        xgap=1.5,
        ygap=1.5,
    )
)

# Quiet zone border — ISO/IEC 16022 requires at least 1 module of clear space
fig.add_shape(
    type="rect",
    x0=-0.5,
    y0=-0.5,
    x1=matrix_size - 0.5,
    y1=matrix_size - 0.5,
    xref="x",
    yref="y",
    line={"color": INK_MUTED, "width": 1, "dash": "dot"},
    fillcolor="rgba(0,0,0,0)",
)

fig.update_layout(
    title={
        "text": "datamatrix-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
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
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    margin={"l": 80, "r": 80, "t": 100, "b": 100},
    annotations=[
        {
            "text": f"Encoded: {content}",
            "xref": "paper",
            "yref": "paper",
            "x": 0.5,
            "y": -0.08,
            "showarrow": False,
            "font": {"size": 12, "color": INK_SOFT},
            "xanchor": "center",
        },
        {
            "text": "ECC 200 | 16×16 Matrix",
            "xref": "paper",
            "yref": "paper",
            "x": 0.5,
            "y": -0.13,
            "showarrow": False,
            "font": {"size": 10, "color": INK_MUTED},
            "xanchor": "center",
        },
        # L-Finder callout — arrow from margin into finder corner
        {
            "text": "L-Finder",
            "x": 0.5,
            "y": 0.5,
            "xref": "x",
            "yref": "y",
            "showarrow": True,
            "arrowhead": 2,
            "arrowwidth": 1.2,
            "arrowcolor": INK_SOFT,
            "ax": -50,
            "ay": 40,
            "font": {"size": 8, "color": INK_SOFT},
            "xanchor": "center",
        },
        # Timing callout — arrow from margin into timing corner
        {
            "text": "Timing",
            "x": 14.5,
            "y": 14.5,
            "xref": "x",
            "yref": "y",
            "showarrow": True,
            "arrowhead": 2,
            "arrowwidth": 1.2,
            "arrowcolor": INK_SOFT,
            "ax": 50,
            "ay": -40,
            "font": {"size": 8, "color": INK_SOFT},
            "xanchor": "center",
        },
    ],
)

fig.update_yaxes(scaleanchor="x", scaleratio=1)

# Save — square canvas (2400×2400 px) suits the symmetric barcode format
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
