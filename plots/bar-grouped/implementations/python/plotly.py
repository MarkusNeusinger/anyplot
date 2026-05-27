""" anyplot.ai
bar-grouped: Grouped Bar Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-06
"""

import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.20)" if THEME == "light" else "rgba(240,239,232,0.20)"

# Okabe-Ito palette
COLORS = ["#009E73", "#C475FD", "#4467A3"]

# Data: Quarterly revenue by product line
categories = ["Q1", "Q2", "Q3", "Q4"]
products = {"Electronics": [245, 312, 287, 398], "Clothing": [189, 156, 201, 234], "Home & Garden": [98, 145, 178, 156]}

# Create figure
fig = go.Figure()

# Add bars for each product group with hover templates
for i, (product, values) in enumerate(products.items()):
    fig.add_trace(
        go.Bar(
            name=product,
            x=categories,
            y=values,
            marker={"color": COLORS[i]},
            text=values,
            textposition="outside",
            textfont={"size": 16, "color": INK},
            hovertemplate=(f"<b>{product}</b><br>Quarter: %{{x}}<br>Revenue: $%{{y}}K<br><extra></extra>"),
        )
    )

# Layout
fig.update_layout(
    title={"text": "bar-grouped · plotly · anyplot.ai", "font": {"size": 28, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Quarter", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Revenue ($ thousands)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    barmode="group",
    bargap=0.2,
    bargroupgap=0.1,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend={
        "font": {"size": 18, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
    },
    margin={"l": 100, "r": 40, "t": 140, "b": 80},
    hovermode="x unified",
)

# Save outputs
script_dir = os.path.dirname(os.path.abspath(__file__))
fig.write_image(os.path.join(script_dir, f"plot-{THEME}.png"), width=1600, height=900, scale=3)
fig.write_html(os.path.join(script_dir, f"plot-{THEME}.html"), include_plotlyjs="cdn")
