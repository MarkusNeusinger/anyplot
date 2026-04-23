""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: plotly 6.7.0 | Python 3.14.4
Quality: 89/100 | Updated: 2026-04-23
"""

import os

import numpy as np
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1 — always first series

# Data: study hours vs exam scores, moderate positive correlation
np.random.seed(42)
n_students = 180
study_hours = np.random.uniform(1, 10, n_students)
exam_scores = 45 + study_hours * 5 + np.random.randn(n_students) * 8
exam_scores = np.clip(exam_scores, 0, 100)

# Per-point local density → subtle alpha variation so sparse outliers gain
# presence while dense clusters reveal overlap through transparency.
density = gaussian_kde(np.vstack([study_hours, exam_scores]))(np.vstack([study_hours, exam_scores]))
density_rank = (density - density.min()) / (density.max() - density.min())
point_alpha = 0.90 - 0.35 * density_rank  # sparse: 0.90, dense: 0.55

# Percentile rank for richer hover context
score_percentile = np.argsort(np.argsort(exam_scores)) / (n_students - 1) * 100

# Plot
fig = go.Figure(
    go.Scatter(
        x=study_hours,
        y=exam_scores,
        mode="markers",
        marker={"size": 14, "color": BRAND, "opacity": point_alpha, "line": {"width": 1.2, "color": PAGE_BG}},
        customdata=np.stack([score_percentile], axis=-1),
        hovertemplate=(
            "<b>Study Hours</b>: %{x:.1f} h/day<br>"
            "<b>Exam Score</b>: %{y:.1f}%<br>"
            "<b>Percentile</b>: %{customdata[0]:.0f}<extra></extra>"
        ),
        showlegend=False,
    )
)

# Style
fig.update_layout(
    title={
        "text": "scatter-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
    },
    xaxis={
        "title": {"text": "Study Hours per Day", "font": {"size": 22, "color": INK}, "standoff": 12},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "showline": True,
        "mirror": False,
        "range": [0, 11],
        "dtick": 2,
        "ticksuffix": " h",
    },
    yaxis={
        "title": {"text": "Exam Score (%)", "font": {"size": 22, "color": INK}, "standoff": 12},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "showline": True,
        "mirror": False,
        "range": [35, 105],
        "dtick": 10,
        "ticksuffix": "%",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK, "family": "Inter, Helvetica Neue, Arial, sans-serif"},
    margin={"l": 100, "r": 70, "t": 110, "b": 90},
    hovermode="closest",
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
        "toImageButtonOptions": {"format": "png", "filename": "scatter-basic-plotly"},
    },
)
