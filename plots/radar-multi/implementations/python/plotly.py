""" anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: plotly 7.1.0 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-14
"""

import os

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26, 26, 23, 0.10)" if THEME == "light" else "rgba(240, 239, 232, 0.10)"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
FILL_ALPHA = 0.25  # translucent fill so overlapping polygons stay visible

# Columns: set these to your table's column names
ATTRIBUTE = "Attribute"  # role: category
SCORE = "Score (0-100)"  # role: value
PRODUCT = "Product"  # role: series

# Data: replace this block with your own table, for example df = pd.read_csv("products.csv")
attributes = ["Performance", "Reliability", "Price Value", "Support", "Ease of Use", "Features"]
scores = {
    "Product A (Premium)": [85, 90, 70, 80, 75, 88],
    "Product B (Budget)": [75, 65, 95, 70, 90, 60],
    "Product C (Pro)": [95, 75, 60, 85, 65, 92],
}
df = pd.DataFrame(
    {
        ATTRIBUTE: attributes * len(scores),
        PRODUCT: [name for name in scores for _ in attributes],
        SCORE: [value for values in scores.values() for value in values],
    }
)


# Plot
def to_rgba(hex_color, alpha):
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


fig = go.Figure()
for i, (product, rows) in enumerate(df.groupby(PRODUCT, sort=False)):
    # Close the polygon by repeating the first point
    theta = list(rows[ATTRIBUTE]) + [rows[ATTRIBUTE].iloc[0]]
    r = list(rows[SCORE]) + [rows[SCORE].iloc[0]]
    fig.add_trace(
        go.Scatterpolar(
            r=r,
            theta=theta,
            fill="toself",
            fillcolor=to_rgba(IMPRINT_PALETTE[i], FILL_ALPHA),
            line={"color": IMPRINT_PALETTE[i], "width": 2.5},
            marker={"size": 8, "color": IMPRINT_PALETTE[i]},
            name=str(product),
        )
    )

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "radar-multi · python · plotly · anyplot.ai",
        "font": {"size": 22, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    polar={
        "radialaxis": {
            "visible": True,
            "range": [0, 100],
            "tickfont": {"size": 13, "color": INK_SOFT},
            "tickvals": [20, 40, 60, 80, 100],
            "gridcolor": GRID,
            "linecolor": INK_SOFT,
        },
        "angularaxis": {"tickfont": {"size": 15, "color": INK}, "linecolor": INK_SOFT, "gridcolor": GRID},
        "bgcolor": PAGE_BG,
    },
    legend={
        "font": {"size": 14, "color": INK_SOFT},
        "orientation": "h",
        "x": 0.5,
        "y": -0.04,
        "xanchor": "center",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    template="plotly_white",
    margin={"l": 120, "r": 120, "t": 80, "b": 90},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
)

fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
