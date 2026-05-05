""" anyplot.ai
swarm-basic: Basic Swarm Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-05
"""

import sys


# Remove the script directory from sys.path so this file (plotly.py) does not
# shadow the installed plotly package.
sys.path.pop(0)

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

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]
FILL_COLORS = ["rgba(0,158,115,0.18)", "rgba(213,94,0,0.18)", "rgba(0,114,178,0.18)", "rgba(204,121,167,0.18)"]

# Data - student test scores across 4 classrooms with varied distributions
np.random.seed(42)
classrooms = ["Room A", "Room B", "Room C", "Room D"]

scores_a = np.concatenate([np.random.normal(75, 8, 35), np.random.normal(90, 5, 10)])
scores_b = np.random.normal(68, 12, 50)
scores_c = np.concatenate([np.random.normal(60, 6, 20), np.random.normal(82, 6, 25)])
scores_d = np.random.normal(78, 6, 40)

all_scores = [scores_a, scores_b, scores_c, scores_d]

# Plot — use Plotly's native go.Box with boxpoints='all' for a beeswarm effect:
# individual jittered points, box/whisker statistics, and mean line overlay.
fig = go.Figure()

for i, (classroom, scores) in enumerate(zip(classrooms, all_scores, strict=False)):
    color = OKABE_ITO[i]
    fig.add_trace(
        go.Box(
            y=scores,
            name=classroom,
            boxpoints="all",
            jitter=0.5,
            pointpos=0,
            marker={"color": color, "size": 10, "opacity": 0.8, "line": {"width": 1.5, "color": PAGE_BG}},
            line={"color": color, "width": 2},
            fillcolor=FILL_COLORS[i],
            whiskerwidth=0.5,
            boxmean=True,
            hovertemplate=f"{classroom}<br>Score: %{{y:.1f}}<extra></extra>",
        )
    )

# Layout
fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={"text": "swarm-basic · plotly · anyplot.ai", "font": {"size": 28, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Classroom", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": GRID,
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "Test Score (points)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": GRID,
        "range": [30, 110],
    },
    legend={"bgcolor": ELEVATED_BG, "bordercolor": INK_SOFT, "borderwidth": 1, "font": {"size": 16, "color": INK_SOFT}},
    showlegend=True,
    margin={"l": 100, "r": 120, "t": 100, "b": 80},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
