""" anyplot.ai
range-interval: Range Interval Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
BRAND = "#009E73"  # Primary series
SECONDARY = "#D55E00"  # Secondary series

# Data: Monthly temperature ranges (°C) for a temperate climate city
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Realistic temperature ranges that follow seasonal pattern
base_temps = [-2, 0, 5, 12, 18, 22, 25, 24, 19, 12, 5, 0]
min_temps = [t - np.random.uniform(3, 6) for t in base_temps]
max_temps = [t + np.random.uniform(4, 8) for t in base_temps]

# Create figure
fig = go.Figure()

# Add range bars as vertical lines with markers at endpoints
for i, month in enumerate(months):
    # Range bar (vertical line)
    fig.add_trace(
        go.Scatter(
            x=[month, month],
            y=[min_temps[i], max_temps[i]],
            mode="lines",
            line={"color": BRAND, "width": 18},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Add markers at min points (bottom)
fig.add_trace(
    go.Scatter(
        x=months,
        y=min_temps,
        mode="markers",
        marker={"color": SECONDARY, "size": 18, "line": {"color": BRAND, "width": 3}},
        name="Min Temperature",
        hovertemplate="%{x}<br>Min: %{y:.1f}°C<extra></extra>",
    )
)

# Add markers at max points (top)
fig.add_trace(
    go.Scatter(
        x=months,
        y=max_temps,
        mode="markers",
        marker={"color": SECONDARY, "size": 18, "line": {"color": BRAND, "width": 3}},
        name="Max Temperature",
        hovertemplate="%{x}<br>Max: %{y:.1f}°C<extra></extra>",
    )
)

# Add midpoint markers
midpoints = [(min_temps[i] + max_temps[i]) / 2 for i in range(len(months))]
fig.add_trace(
    go.Scatter(
        x=months,
        y=midpoints,
        mode="markers",
        marker={"color": INK, "size": 10, "line": {"color": BRAND, "width": 2}},
        name="Midpoint",
        hovertemplate="%{x}<br>Mid: %{y:.1f}°C<extra></extra>",
    )
)

# Update layout with theme-adaptive styling
fig.update_layout(
    title={
        "text": "range-interval · python · plotly · anyplot.ai", "font": {"size": 28, "color": INK}, "x": 0.5, "xanchor": "center"
    },
    xaxis={
        "title": {"text": "Month", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "categoryorder": "array",
        "categoryarray": months,
        "showgrid": False,
        "linecolor": INK_SOFT,
        "linewidth": 2,
    },
    yaxis={
        "title": {"text": "Temperature (°C)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": INK_SOFT,
        "zerolinewidth": 2,
        "linecolor": INK_SOFT,
        "linewidth": 2,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "font": {"size": 16, "color": INK_SOFT}, "x": 0.02, "y": 0.98, "bgcolor": ELEVATED_BG, "bordercolor": INK_SOFT, "borderwidth": 1
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    hovermode="closest",
)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
