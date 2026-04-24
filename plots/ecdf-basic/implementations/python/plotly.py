""" anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: plotly 6.7.0 | Python 3.14.4
Quality: 88/100 | Updated: 2026-04-24
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
BRAND = "#009E73"  # Okabe-Ito position 1 — always first series

# Data: marathon finishing times (minutes) for 300 runners
np.random.seed(42)
n_runners = 300
finish_times = np.random.normal(loc=240, scale=32, size=n_runners)

# ECDF
sorted_times = np.sort(finish_times)
cumulative_proportion = np.arange(1, n_runners + 1) / n_runners

# Plot
fig = go.Figure(
    go.Scatter(
        x=sorted_times,
        y=cumulative_proportion,
        mode="lines",
        line={"color": BRAND, "width": 3.5, "shape": "hv"},
        hovertemplate=("<b>Finish Time</b>: %{x:.1f} min<br><b>Cumulative</b>: %{y:.1%}<br><extra></extra>"),
        showlegend=False,
    )
)

# Style
fig.update_layout(
    title={
        "text": "Marathon Finishing Times · ecdf-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
    },
    xaxis={
        "title": {"text": "Finishing Time (minutes)", "font": {"size": 22, "color": INK}, "standoff": 12},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "showline": True,
        "mirror": False,
        "ticksuffix": " min",
    },
    yaxis={
        "title": {"text": "Cumulative Proportion of Runners", "font": {"size": 22, "color": INK}, "standoff": 12},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "showline": True,
        "mirror": False,
        "range": [0, 1.02],
        "tickformat": ".0%",
        "dtick": 0.1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK, "family": "Inter, Helvetica Neue, Arial, sans-serif"},
    margin={"l": 110, "r": 70, "t": 110, "b": 90},
    hovermode="x unified",
    hoverlabel={"bgcolor": ELEVATED_BG, "bordercolor": INK_SOFT, "font": {"color": INK, "size": 15}, "align": "left"},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(
    f"plot-{THEME}.html",
    include_plotlyjs="cdn",
    config={
        "displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
        "toImageButtonOptions": {"format": "png", "filename": "ecdf-basic-plotly"},
    },
)
