""" anyplot.ai
pie-basic: Basic Pie Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-28
"""

import os

import plotly.graph_objects as go


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Digital payment processor market share (2024)
processors = ["Visa", "Mastercard", "PayPal", "Amex", "Apple Pay", "Others"]
market_share = [38, 26, 18, 7, 5, 6]

# Colors - anyplot palette positions 1-6
colors = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Create donut chart
fig = go.Figure(
    data=[
        go.Pie(
            labels=processors,
            values=market_share,
            textinfo="label+percent",
            textposition="inside",
            insidetextorientation="horizontal",
            textfont={"size": 13, "color": "#FFFFFF"},
            hovertemplate="%{label}<br>%{value}% market share<extra></extra>",
            marker={"colors": colors, "line": {"color": PAGE_BG, "width": 3}},
            pull=[0.06, 0, 0, 0, 0, 0],
            sort=False,
            hole=0.35,
            direction="clockwise",
            rotation=90,
            domain={"x": [0.02, 0.72], "y": [0.05, 0.92]},
        )
    ]
)

# Center annotation inside the donut hole
fig.add_annotation(
    text="<b>Digital<br>Payments<br>2024</b>",
    x=0.37,
    y=0.485,
    xref="paper",
    yref="paper",
    showarrow=False,
    font={"size": 16, "color": colors[0], "family": "Arial Black, sans-serif"},
    xanchor="center",
    yanchor="middle",
)

# Layout
fig.update_layout(
    autosize=False,
    title={
        "text": "pie-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK, "family": "Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.98,
    },
    legend={
        "font": {"size": 12, "color": INK_SOFT},
        "orientation": "v",
        "yanchor": "middle",
        "y": 0.5,
        "xanchor": "left",
        "x": 0.76,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"t": 60, "b": 30, "l": 20, "r": 20},
    uniformtext={"minsize": 10, "mode": "hide"},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
