""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: plotly 6.7.0 | Python 3.14.4
Quality: 86/100 | Created: 2026-04-23
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1 — always first series

# Data: study hours vs exam scores, moderate positive correlation
np.random.seed(42)
n_students = 160
study_hours = np.random.uniform(1, 10, n_students)
exam_scores = 45 + study_hours * 5 + np.random.randn(n_students) * 8
exam_scores = np.clip(exam_scores, 0, 100)

# Plot
fig = go.Figure(
    go.Scatter(
        x=study_hours,
        y=exam_scores,
        mode="markers",
        marker={"size": 13, "color": BRAND, "opacity": 0.7, "line": {"width": 1.2, "color": PAGE_BG}},
        hovertemplate="Study: %{x:.1f} h<br>Score: %{y:.1f}%<extra></extra>",
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
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 90, "r": 60, "t": 100, "b": 80},
    hoverlabel={"bgcolor": ELEVATED_BG, "bordercolor": INK_SOFT, "font": {"color": INK}},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
