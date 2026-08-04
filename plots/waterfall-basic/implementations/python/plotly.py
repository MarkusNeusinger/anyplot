"""anyplot.ai
waterfall-basic: Basic Waterfall Chart
Library: plotly 6.9.0 | Python 3.13.14
Quality: 86/100 | Updated: 2026-08-04
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

# Imprint palette
COLOR_POSITIVE = "#009E73"  # brand green (first series) — increases
COLOR_NEGATIVE = "#AE3030"  # matte red — decreases (semantic loss anchor)
COLOR_TOTAL = "#4467A3"  # blue — start/end totals

# Data - Quarterly financial breakdown from revenue to net income
categories = ["Revenue", "Product Costs", "Operating Expenses", "Marketing", "Other Income", "Taxes", "Net Income"]

# Values: positive for increases, negative for decreases
# Revenue is the starting total, Net Income is the ending total
values = [500000, -180000, -95000, -45000, 25000, -51250, 153750]

# Define measure types: absolute for start, relative for changes, total for end
measures = ["absolute", "relative", "relative", "relative", "relative", "relative", "total"]

# Running/cumulative total after each step, so intermediate bars can display it
running_totals = []
cumulative = 0
for value, measure in zip(values, measures, strict=True):
    cumulative = value if measure != "relative" else cumulative + value
    running_totals.append(cumulative)

# Bar labels: delta amount for relative steps (with the running total below it),
# and the total itself for the absolute/total anchor bars
bar_labels = [
    f"${value:,.0f}"
    if measure != "relative"
    else f"{'+' if value >= 0 else '-'}${abs(value):,.0f}<br>(${running_total:,.0f})"
    for value, measure, running_total in zip(values, measures, running_totals, strict=True)
]

# Create waterfall chart using Plotly's native Waterfall trace
fig = go.Figure(
    go.Waterfall(
        name="Financial Breakdown",
        orientation="v",
        measure=measures,
        x=categories,
        y=values,
        textposition="outside",
        text=bar_labels,
        textfont={"size": 13, "color": INK},
        connector={"line": {"color": INK_SOFT, "width": 1.5, "dash": "dot"}},
        decreasing={"marker": {"color": COLOR_NEGATIVE}},
        increasing={"marker": {"color": COLOR_POSITIVE}},
        totals={"marker": {"color": COLOR_TOTAL}},
        showlegend=False,
    )
)

# Add dummy traces for legend (to explain colors)
fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker={"size": 10, "color": COLOR_POSITIVE},
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
        marker={"size": 10, "color": COLOR_NEGATIVE},
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
        marker={"size": 10, "color": COLOR_TOTAL},
        name="Totals",
        showlegend=True,
        legendgroup="colors",
        hoverinfo="skip",
    )
)

# Update layout for 3200x1800 px canvas with theme colors
fig.update_layout(
    autosize=False,
    title={
        "text": "waterfall-basic · python · plotly · anyplot.ai",
        "font": {"size": 19, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Category", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "linecolor": INK_SOFT,
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "Amount ($)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
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
        "font": {"size": 10, "color": INK_SOFT},
    },
    margin={"t": 90, "b": 70, "l": 100, "r": 40},
)

# Save as PNG and HTML with theme-suffixed filenames
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
