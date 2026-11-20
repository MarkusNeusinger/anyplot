"""anyplot.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: single series uses position 1
BRAND = "#009E73"

# Columns: set these to your table's column names
TEMPERATURE = "Temperature (°C)"  # role: x
HUMIDITY = "Relative Humidity (%)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
rng = np.random.default_rng(42)
n = 200
temperature = rng.normal(22, 3.5, n)
humidity = 0.65 * temperature + rng.normal(0, 6, n) + 35
df = pd.DataFrame({TEMPERATURE: temperature, HUMIDITY: humidity})

# Plot: reads only df and the constants above
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df[TEMPERATURE],
        y=df[HUMIDITY],
        mode="markers",
        marker={"size": 9, "color": BRAND, "opacity": 0.65, "line": {"width": 0.75, "color": PAGE_BG}},
        hovertemplate=f"{TEMPERATURE}: %{{x:.1f}}<br>{HUMIDITY}: %{{y:.1f}}<extra></extra>",
    )
)

# Top marginal: shares the scatter's x axis, counts on its own y axis
fig.add_trace(
    go.Histogram(
        x=df[TEMPERATURE],
        xaxis="x",
        yaxis="y2",
        marker={"color": BRAND, "opacity": 0.45},
        nbinsx=25,
        hovertemplate="%{x}: %{y} observations<extra></extra>",
    )
)

# Right marginal: shares the scatter's y axis, counts on its own x axis
fig.add_trace(
    go.Histogram(
        y=df[HUMIDITY],
        xaxis="x2",
        yaxis="y",
        marker={"color": BRAND, "opacity": 0.45},
        nbinsy=25,
        orientation="h",
        hovertemplate="%{y}: %{x} observations<extra></extra>",
    )
)

axis_style = {
    "tickfont": {"size": 10, "color": INK_SOFT},
    "gridcolor": GRID,
    "gridwidth": 0.5,
    "linecolor": INK_SOFT,
    "linewidth": 1,
    "showline": True,
    "zeroline": False,
}
marginal_style = {"showticklabels": False, "showgrid": False, "showline": False, "zeroline": False}

fig.update_layout(
    autosize=False,
    title={
        "text": "scatter-marginal · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={**axis_style, "domain": [0, 0.86], "title": {"text": TEMPERATURE, "font": {"size": 12, "color": INK}}},
    yaxis={**axis_style, "domain": [0, 0.84], "title": {"text": HUMIDITY, "font": {"size": 12, "color": INK}}},
    xaxis2={**marginal_style, "domain": [0.88, 1], "anchor": "y"},
    yaxis2={**marginal_style, "domain": [0.86, 1], "anchor": "x"},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    bargap=0.05,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    hovermode="closest",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
