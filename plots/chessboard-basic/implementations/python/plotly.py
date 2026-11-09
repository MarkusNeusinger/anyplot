"""anyplot.ai
chessboard-basic: Chess Board Grid Visualization
Library: plotly | Python 3.14
Quality: pending | Updated: 2026-11-09
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: brand green carries the dark squares, as on a tournament board
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
DARK_SQUARE = IMPRINT_PALETTE[0]
LIGHT_SQUARE = "#F0EFE8"  # warm paper cream, the same in both themes so the board keeps its identity

# Data: a generated board, set by its named parameters
files = list("abcdefgh")  # columns, left to right
ranks = [str(r) for r in range(1, 9)]  # rows, bottom to top

# Plot
n_files, n_ranks = len(files), len(ranks)
# a1 is dark; a square is light when file index + rank index is odd, which puts light squares on h1 and a8
is_dark = (np.add.outer(np.arange(n_ranks), np.arange(n_files)) % 2 == 0).astype(int)
square_names = [[f"{f}{r}" for f in files] for r in ranks]

fig = go.Figure(
    go.Heatmap(
        z=is_dark,
        x=files,
        y=ranks,
        text=square_names,
        colorscale=[[0.0, LIGHT_SQUARE], [0.5, LIGHT_SQUARE], [0.5, DARK_SQUARE], [1.0, DARK_SQUARE]],
        zmin=0,
        zmax=1,
        showscale=False,
        xgap=2,
        ygap=2,
        hovertemplate="Square %{text}<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    width=600,
    height=600,
    margin={"l": 70, "r": 50, "t": 80, "b": 60},
    title={
        "text": "chessboard-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=INK_SOFT,  # shows through the 2 px square gaps as the board's grid lines
    font={"color": INK},
    xaxis={
        "side": "bottom",
        "tickfont": {"size": 14, "color": INK_SOFT},
        "ticks": "",
        "showgrid": False,
        "zeroline": False,
        "showline": False,
        "constrain": "domain",
        "fixedrange": True,
    },
    yaxis={
        "tickfont": {"size": 14, "color": INK_SOFT},
        "ticks": "",
        "ticklabelstandoff": 8,
        "showgrid": False,
        "zeroline": False,
        "showline": False,
        "scaleanchor": "x",
        "scaleratio": 1,
        "constrain": "domain",
        "fixedrange": True,
    },
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
