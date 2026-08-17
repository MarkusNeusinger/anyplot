"""anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-08-17
"""

import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26, 26, 23, 0.15)" if THEME == "light" else "rgba(240, 239, 232, 0.15)"

# Imprint palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Product comparison across multiple attributes
categories = ["Performance", "Reliability", "Price Value", "Support", "Ease of Use", "Features"]

# Three products with different strengths
product_a = [85, 90, 70, 80, 75, 88]  # Strong overall, premium
product_b = [75, 65, 95, 70, 90, 60]  # Budget-friendly, easy to use
product_c = [95, 75, 60, 85, 65, 92]  # High-performance, feature-rich

# Close the polygon by repeating the first value
categories_closed = categories + [categories[0]]
product_a_closed = product_a + [product_a[0]]
product_b_closed = product_b + [product_b[0]]
product_c_closed = product_c + [product_c[0]]

# (name, closed r-values, line color, fill rgb, marker symbol) — symbol gives
# a redundant, colorblind-safe cue on top of hue for the three products
products = [
    ("Product A (Premium)", product_a_closed, IMPRINT[0], "0, 158, 115", "circle"),
    ("Product B (Budget)", product_b_closed, IMPRINT[1], "196, 117, 253", "diamond"),
    ("Product C (Pro)", product_c_closed, IMPRINT[2], "68, 103, 163", "square"),
]

# Create radar chart
fig = go.Figure()

for name, values, color, rgb, symbol in products:
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories_closed,
            fill="toself",
            fillcolor=f"rgba({rgb}, 0.25)",
            line={"color": color, "width": 3.5},
            marker={"size": 12, "symbol": symbol, "line": {"color": PAGE_BG, "width": 1.5}},
            name=name,
            hovertemplate=f"<b>%{{theta}}</b><br>{name}: %{{r}}<extra></extra>",
        )
    )

# Layout with theme-adaptive styling
fig.update_layout(
    autosize=False,
    title={
        "text": "radar-multi · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    polar={
        # Straight radial spokes between category ticks (classic "spider
        # web" look) instead of plotly's default concentric-circle grid —
        # reads more cleanly once three overlapping polygons are stacked.
        "gridshape": "linear",
        "radialaxis": {
            "visible": True,
            "range": [0, 100],
            "angle": 90,
            "tickangle": 0,
            "tickfont": {"size": 15, "color": INK_SOFT},
            "tickvals": [20, 40, 60, 80, 100],
            "gridcolor": GRID,
            "linecolor": INK_SOFT,
        },
        "angularaxis": {
            "rotation": 90,
            "direction": "clockwise",
            "tickfont": {"size": 16, "color": INK},
            "linecolor": INK_SOFT,
            "gridcolor": GRID,
        },
        "bgcolor": ELEVATED_BG,
    },
    legend={
        "orientation": "h",
        "font": {"size": 14, "color": INK_SOFT},
        "x": 0.5,
        "y": -0.08,
        "xanchor": "center",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 90, "r": 90, "t": 90, "b": 110},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
)

# Save as PNG (square — radar is a symmetric plot type) and HTML
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
