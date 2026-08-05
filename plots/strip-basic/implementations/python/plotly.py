"""anyplot.ai
strip-basic: Basic Strip Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-08-05
"""

import os

import numpy as np
import pandas as pd
import plotly.express as px


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Commute time per trip, sampled across commonly used transport modes
np.random.seed(42)

modes = ["Car", "Bus", "Bike", "Train"]
n_per_mode = [55, 60, 45, 50]
mean_minutes = [28, 42, 35, 31]
std_minutes = [7, 9, 11, 5]

commute = pd.concat(
    [
        pd.DataFrame({"mode": mode, "commute_time": np.clip(np.random.normal(mean, std, n), 3, None)})
        for mode, n, mean, std in zip(modes, n_per_mode, mean_minutes, std_minutes, strict=True)
    ],
    ignore_index=True,
)

# Plot
fig = px.strip(
    commute,
    x="mode",
    y="commute_time",
    color="mode",
    category_orders={"mode": modes},
    color_discrete_sequence=IMPRINT_PALETTE,
)
fig.update_traces(jitter=0.3, marker={"size": 10, "opacity": 0.6, "line": {"width": 0}})

# Mean reference lines
for i, mode in enumerate(modes):
    mean_val = commute.loc[commute["mode"] == mode, "commute_time"].mean()
    fig.add_shape(type="line", x0=i - 0.3, x1=i + 0.3, y0=mean_val, y1=mean_val, line={"color": INK, "width": 2})

# Style
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    showlegend=False,
    title={
        "text": "strip-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Transportation Mode", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Commute Time (minutes)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
