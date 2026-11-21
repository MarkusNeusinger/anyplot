""" anyplot.ai
contour-filled: Filled Contour Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
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
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint diverging scale: red below the midpoint, blue above, theme-adaptive neutral at zero
MIDPOINT = PAGE_BG
IMPRINT_DIV = [[0.0, IMPRINT_PALETTE[4]], [0.5, MIDPOINT], [1.0, IMPRINT_PALETTE[2]]]

# Constants
N_LEVELS = 16  # evenly stepped contour levels

# Columns: set these to your table's column names
X = "X position"  # role: x
Y = "Y position"  # role: y
Z = "Surface value"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("field.csv")
x_grid, y_grid = np.meshgrid(np.linspace(-3, 3, 100), np.linspace(-3, 3, 100))
z_grid = (
    2 * np.exp(-((x_grid - 1) ** 2 + (y_grid - 1) ** 2))
    + 1.5 * np.exp(-((x_grid + 1) ** 2 + (y_grid + 1) ** 2))
    - 1 * np.exp(-((x_grid - 1) ** 2 + (y_grid + 1) ** 2))
    + 0.5 * np.exp(-((x_grid + 1.5) ** 2 + (y_grid - 1.5) ** 2))
)
df = pd.DataFrame({X: x_grid.ravel(), Y: y_grid.ravel(), Z: z_grid.ravel()})

# Plot: reads only df and the constants above
field = df.pivot_table(index=Y, columns=X, values=Z)
level_step = (df[Z].max() - df[Z].min()) / N_LEVELS
bound = max(abs(df[Z].min()), abs(df[Z].max()))

fig = go.Figure(
    go.Contour(
        x=field.columns,
        y=field.index,
        z=field.to_numpy(),
        colorscale=IMPRINT_DIV,
        zmin=-bound,
        zmax=bound,
        contours={"coloring": "fill", "start": df[Z].min(), "end": df[Z].max(), "size": level_step},
        line={"width": 0.8, "color": INK_SOFT, "smoothing": 1.3},
        colorbar={
            "title": {"text": Z, "font": {"size": 12, "color": INK}},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "thickness": 16,
            "len": 0.9,
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
        },
        hovertemplate=f"{X}: %{{x:.2f}}<br>{Y}: %{{y:.2f}}<br>{Z}: %{{z:.3f}}<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "<b>contour-filled · python · plotly · anyplot.ai</b>",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": X, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": Y, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 70, "r": 40, "t": 60, "b": 55},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
