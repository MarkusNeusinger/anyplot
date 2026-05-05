""" anyplot.ai
streamgraph-basic: Basic Stream Graph
Library: plotly 6.7.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-05
"""

import sys


sys.path.pop(0)

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette — first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9"]

# Data - Monthly streaming hours by music genre over 2 years
np.random.seed(42)
months = pd.date_range(start="2022-01-01", periods=24, freq="ME")
genres = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz", "Classical"]

base_values = {"Pop": 45, "Rock": 35, "Hip-Hop": 40, "Electronic": 25, "Jazz": 15, "Classical": 12}
data = {}
for genre in genres:
    trend = np.cumsum(np.random.randn(24) * 2)
    seasonal = 5 * np.sin(np.linspace(0, 4 * np.pi, 24))
    noise = np.random.randn(24) * 3
    values = base_values[genre] + trend + seasonal + noise
    values = np.maximum(values, 5)
    data[genre] = values

df = pd.DataFrame(data, index=months)
month_labels = months.strftime("%Y-%m").tolist()

# Calculate streamgraph layout (centered baseline)
values_array = df.values.T  # Shape: (n_genres, n_time_points)
n_genres, n_time = values_array.shape

cumsum = np.vstack([np.zeros(n_time), np.cumsum(values_array, axis=0)])
total = cumsum[-1]
offset = total / 2

# Plot
fig = go.Figure()

for i, genre in enumerate(genres):
    y_lower = cumsum[i] - offset
    y_upper = cumsum[i + 1] - offset

    x_fill = month_labels + month_labels[::-1]
    y_fill = list(y_upper) + list(y_lower)[::-1]

    # Dominant stream (Pop) at full opacity; others slightly dimmed for visual hierarchy
    opacity = 1.0 if i == 0 else 0.80

    fig.add_trace(
        go.Scatter(
            x=x_fill,
            y=y_fill,
            fill="toself",
            fillcolor=OKABE_ITO[i],
            opacity=opacity,
            line={"color": OKABE_ITO[i], "width": 0.5, "shape": "spline", "smoothing": 1.0},
            name=genre,
            mode="none",
            hoverinfo="name+x",
            hoveron="fills",
        )
    )

subtitle = f"<span style='font-size:18px;color:{INK_SOFT}'>Monthly streaming hours by music genre, 2022–2023</span>"

fig.update_layout(
    title={
        "text": f"streamgraph-basic · plotly · anyplot.ai<br>{subtitle}",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Month", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "mirror": False,  # bottom spine only — no top spine
        "zeroline": False,
    },
    yaxis={
        "showticklabels": False,  # hide confusing negative offset values
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": INK_SOFT,
        "zerolinewidth": 1,
        "showline": False,  # no left spine (y labels hidden anyway)
        "mirror": False,
    },
    legend={
        "font": {"size": 18, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "orientation": "h",
        "yanchor": "top",
        "y": -0.12,
        "xanchor": "center",
        "x": 0.5,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    hovermode="x unified",
    margin={"l": 60, "r": 50, "t": 140, "b": 120},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
