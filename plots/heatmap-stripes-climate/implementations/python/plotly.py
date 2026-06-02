""" anyplot.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: plotly 6.7.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-06-02
"""

import sys


sys.path = sys.path[1:]  # Prevent self-import: script dir is removed so 'import plotly' finds the package

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data
np.random.seed(42)
years = np.arange(1850, 2025)
n_years = len(years)

trend = np.linspace(-0.35, 0.85, n_years)
noise = np.random.normal(0, 0.12, n_years)

volcanic_events = {1883: -0.25, 1912: -0.15, 1942: -0.20, 1991: -0.15}
volcanic_dips = np.zeros(n_years)
for year, dip in volcanic_events.items():
    volcanic_dips[year - years[0]] = dip

anomalies = trend + noise + volcanic_dips
vmax = max(abs(anomalies.min()), abs(anomalies.max()))

# Colorscale: classic warming stripes (deep blue → neutral → deep red)
# Midpoint is theme-adaptive so near-zero bars harmonise with the page surface
mid_color = "#E8E4D8" if THEME == "light" else "#3A3A35"
colorscale = [
    [0.0, "#08306b"],
    [0.25, "#2171b5"],
    [0.45, "#6baed6"],
    [0.5, mid_color],
    [0.55, "#fb6a4a"],
    [0.75, "#cb181d"],
    [1.0, "#67000d"],
]

# Hover labels per bar
labels = np.where(
    anomalies > 0.3,
    "Strong warming",
    np.where(anomalies > 0, "Warm", np.where(anomalies > -0.3, "Cool", "Strong cooling")),
)

# Plot — warming stripes heatmap
fig = go.Figure(
    data=go.Heatmap(
        z=[anomalies],
        x=years,
        y=[""],
        colorscale=colorscale,
        zmin=-vmax,
        zmax=vmax,
        showscale=False,
        xgap=0,
        ygap=0,
        customdata=[np.column_stack([labels])],
        hovertemplate="<b>%{x}</b><br>Anomaly: %{z:+.2f} °C<br>%{customdata[0]}<extra></extra>",
    )
)

# Subtle decade markers (semi-transparent, adapts to theme)
decade_color = "rgba(255,255,255,0.30)" if THEME == "light" else "rgba(0,0,0,0.40)"
for decade in [1900, 1950, 2000]:
    fig.add_shape(type="line", x0=decade, x1=decade, y0=-0.5, y1=0.5, line={"color": decade_color, "width": 1.5})

# Start / end year labels (theme-adaptive ink)
for x_pos, anchor, label in [(0.01, "left", "1850"), (0.99, "right", "2024")]:
    fig.add_annotation(
        x=x_pos,
        y=-0.04,
        text=label,
        showarrow=False,
        font={"size": 16, "color": INK_MUTED},
        xanchor=anchor,
        yanchor="top",
        xref="paper",
        yref="paper",
    )

title_text = "heatmap-stripes-climate · python · plotly · anyplot.ai"
fig.update_layout(
    autosize=False,
    title={"text": title_text, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={"showgrid": False, "showticklabels": False, "zeroline": False, "showline": False, "range": [1849.5, 2024.5]},
    yaxis={"showgrid": False, "showticklabels": False, "zeroline": False, "showline": False, "fixedrange": True},
    margin={"l": 20, "r": 20, "t": 70, "b": 40},
    showlegend=False,
)

# Save — landscape 3200×1800 canvas
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(
    f"plot-{THEME}.html",
    include_plotlyjs="cdn",
    config={"displayModeBar": False, "scrollZoom": False, "staticPlot": False},
)
