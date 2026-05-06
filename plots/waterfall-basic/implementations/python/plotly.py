"""pyplots.ai
waterfall-basic: Basic Waterfall Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 97/100 | Created: 2025-12-24
"""

import os
import sys


_orig_path = sys.path[:]
sys.path = [p for p in sys.path if p != os.path.dirname(__file__) and p != os.getcwd()]
import plotly.graph_objects as go  # noqa: E402


sys.path = _orig_path

# Theme colors
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
COLOR_POSITIVE = "#009E73"  # bluish green (first series)
COLOR_NEGATIVE = "#D55E00"  # vermillion
COLOR_TOTAL = "#0072B2"  # blue

# Data - Quarterly financial breakdown from revenue to net income
categories = ["Revenue", "Product Costs", "Operating Expenses", "Marketing", "Other Income", "Taxes", "Net Income"]

# Values: positive for increases, negative for decreases
# Revenue is the starting total, Net Income is the ending total
values = [500000, -180000, -95000, -45000, 25000, -51250, 153750]

# Define measure types: absolute for start, relative for changes, total for end
measures = ["absolute", "relative", "relative", "relative", "relative", "relative", "total"]

# Create waterfall chart using Plotly's native Waterfall trace
fig = go.Figure(
    go.Waterfall(
        name="Financial Breakdown",
        orientation="v",
        measure=measures,
        x=categories,
        y=values,
        textposition="outside",
        text=[f"${abs(v):,.0f}" for v in values],
        textfont={"size": 18, "color": INK},
        connector={"line": {"color": INK_SOFT, "width": 2, "dash": "dot"}},
        decreasing={"marker": {"color": COLOR_NEGATIVE}},
        increasing={"marker": {"color": COLOR_POSITIVE}},
        totals={"marker": {"color": COLOR_TOTAL}},
        showlegend=True,
        legendgroup="main",
    )
)

# Add dummy traces for legend (to explain colors)
fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker={"size": 14, "color": COLOR_POSITIVE},
        name="Increases",
        showlegend=True,
        legendgroup="colors",
        hoverinfo="skip",
    )
)

fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker={"size": 14, "color": COLOR_NEGATIVE},
        name="Decreases",
        showlegend=True,
        legendgroup="colors",
        hoverinfo="skip",
    )
)

fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker={"size": 14, "color": COLOR_TOTAL},
        name="Totals",
        showlegend=True,
        legendgroup="colors",
        hoverinfo="skip",
    )
)

# Update layout for 4800x2700 px canvas with theme colors
fig.update_layout(
    title={
        "text": "waterfall-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Category", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "linecolor": INK_SOFT,
        "gridcolor": GRID,
    },
    yaxis={
        "title": {"text": "Amount ($)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "tickformat": "$,.0f",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    template="plotly_white",
    showlegend=True,
    legend={
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": "rgba(0,0,0,0)" if THEME == "light" else "rgba(255,255,255,0)",
        "borderwidth": 0,
        "font": {"size": 16, "color": INK_SOFT},
    },
    margin={"t": 100, "b": 80, "l": 120, "r": 50},
)

# Save as PNG and HTML with theme-suffixed filenames
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
