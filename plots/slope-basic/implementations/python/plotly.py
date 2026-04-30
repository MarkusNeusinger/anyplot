""" anyplot.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: plotly 6.7.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-04-30
"""

import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito: increase = brand green, decrease = vermillion, flat = adaptive neutral
COLOR_UP = "#009E73"
COLOR_DOWN = "#D55E00"
COLOR_FLAT = INK_MUTED

# Data - Product sales Q1 vs Q4 comparison (10 products showing various patterns)
products = [
    "Laptop Pro",
    "Wireless Earbuds",
    "Smart Watch",
    "Tablet Ultra",
    "Gaming Mouse",
    "Mechanical Keyboard",
    "Webcam HD",
    "USB Hub",
    "Portable SSD",
    "Monitor Stand",
]

sales_q1 = [245, 180, 120, 195, 85, 110, 45, 30, 75, 55]
sales_q4 = [310, 220, 195, 160, 145, 130, 95, 85, 70, 40]

colors = []
for q1, q4 in zip(sales_q1, sales_q4, strict=True):
    if q4 > q1:
        colors.append(COLOR_UP)
    elif q4 < q1:
        colors.append(COLOR_DOWN)
    else:
        colors.append(COLOR_FLAT)

# Plot
fig = go.Figure()

for i, product in enumerate(products):
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[sales_q1[i], sales_q4[i]],
            mode="lines+markers",
            line={"color": colors[i], "width": 3},
            marker={"size": 14, "color": colors[i]},
            name=product,
            showlegend=False,
            hovertemplate=f"{product}<br>Q1: ${sales_q1[i]}K<br>Q4: ${sales_q4[i]}K<extra></extra>",
        )
    )

# Labels at Q1 (left side)
for i, product in enumerate(products):
    fig.add_annotation(
        x=-0.05,
        y=sales_q1[i],
        text=f"{product}: ${sales_q1[i]}K",
        showarrow=False,
        xanchor="right",
        font={"size": 16, "color": colors[i]},
    )

# Labels at Q4 (right side)
for i, product in enumerate(products):
    fig.add_annotation(
        x=1.05,
        y=sales_q4[i],
        text=f"${sales_q4[i]}K: {product}",
        showarrow=False,
        xanchor="left",
        font={"size": 16, "color": colors[i]},
    )

# Style
fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": "Product Sales Q1 vs Q4 · slope-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "tickmode": "array",
        "tickvals": [0, 1],
        "ticktext": ["Q1 2024", "Q4 2024"],
        "tickfont": {"size": 22, "color": INK_SOFT},
        "range": [-0.5, 1.5],
        "showgrid": False,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Sales ($K)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    margin={"l": 220, "r": 220, "t": 80, "b": 60},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
