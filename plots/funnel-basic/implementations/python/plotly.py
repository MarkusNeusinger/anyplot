"""anyplot.ai
funnel-basic: Basic Funnel Chart
Library: plotly 6.7.0 | Python 3.14.4
Quality: 87/100 | Updated: 2026-04-26
"""

import os

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per stage in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
STAGE = "Stage"  # role: stage
VALUE = "Count"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("funnel.csv")
df = pd.DataFrame(
    {STAGE: ["Awareness", "Interest", "Consideration", "Intent", "Purchase"], VALUE: [1000, 600, 400, 200, 100]}
)

# Plot: reads only df and the constants above
fig = go.Figure(
    go.Funnel(
        y=df[STAGE],
        x=df[VALUE],
        textposition="inside",
        textinfo="value+percent initial",
        textfont={"size": 12, "color": "#FAF8F1"},
        marker={"color": IMPRINT_PALETTE[: len(df)], "line": {"width": 1, "color": PAGE_BG}},
        connector={"line": {"color": INK_SOFT, "width": 1, "dash": "dot"}},
    )
)

# Style
fig.update_layout(
    title={
        "text": "funnel-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    yaxis={
        "title": {"text": STAGE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    xaxis={
        "title": {"text": VALUE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    autosize=False,
    margin={"l": 100, "r": 40, "t": 60, "b": 50},
    showlegend=False,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
