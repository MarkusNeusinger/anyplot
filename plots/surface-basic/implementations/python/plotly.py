"""anyplot.ai
surface-basic: Basic 3D Surface Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-05
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette and its sequential colormap (single polarity)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = [[0.0, IMPRINT_PALETTE[0]], [1.0, IMPRINT_PALETTE[2]]]

# Columns: set these to your table's column names
X = "X Axis"  # role: x
Y = "Y Axis"  # role: y
Z = "Z Value"  # role: z

# Data: replace this block with your own long table, for example df = pd.read_csv("surface.csv")
grid_x, grid_y = np.meshgrid(np.linspace(-5, 5, 40), np.linspace(-5, 5, 40))
df = pd.DataFrame(
    {
        X: grid_x.ravel(),
        Y: grid_y.ravel(),
        Z: (
            np.sin(np.sqrt(grid_x**2 + grid_y**2)) * np.cos(grid_x / 2) + 0.5 * np.exp(-0.1 * (grid_x**2 + grid_y**2))
        ).ravel(),
    }
)

# Plot
grid = df.pivot_table(index=Y, columns=X, values=Z, sort=True)
fig = go.Figure(
    data=[
        go.Surface(
            x=grid.columns,
            y=grid.index,
            z=grid.to_numpy(),
            colorscale=imprint_seq,
            colorbar={
                "title": {"text": Z, "font": {"size": 12, "color": INK}},
                "tickfont": {"size": 10, "color": INK_SOFT},
                "len": 0.7,
            },
        )
    ]
)


def axis(label):
    return {
        "title": {"text": label, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "showbackground": True,
        "backgroundcolor": PAGE_BG,
    }


# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "surface-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    scene={"xaxis": axis(X), "yaxis": axis(Y), "zaxis": axis(Z), "camera": {"eye": {"x": 1.5, "y": 1.5, "z": 1.2}}},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 20, "r": 20, "t": 60, "b": 20},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
