""" anyplot.ai
radar-basic: Basic Radar Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-04-29
"""

import os

import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data - Employee performance comparison across competencies
categories = ["Communication", "Technical Skills", "Teamwork", "Problem Solving", "Leadership", "Creativity"]

senior_values = [85, 92, 78, 88, 72, 80]
junior_values = [70, 65, 82, 68, 55, 75]

# Close the polygon by repeating the first point
categories_closed = categories + [categories[0]]
senior_closed = senior_values + [senior_values[0]]
junior_closed = junior_values + [junior_values[0]]

fig = go.Figure()

fig.add_trace(
    go.Scatterpolar(
        r=senior_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(0, 158, 115, 0.25)",
        line={"color": OKABE_ITO[0], "width": 3},
        marker={"size": 12, "color": OKABE_ITO[0]},
        name="Senior Developer",
        hovertemplate="<b>Senior Developer</b><br>%{theta}: %{r}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatterpolar(
        r=junior_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(213, 94, 0, 0.25)",
        line={"color": OKABE_ITO[1], "width": 3},
        marker={"size": 12, "color": OKABE_ITO[1]},
        name="Junior Developer",
        hovertemplate="<b>Junior Developer</b><br>%{theta}: %{r}<extra></extra>",
    )
)

fig.update_layout(
    title={
        "text": "radar-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    polar={
        "bgcolor": PAGE_BG,
        "domain": {"x": [0.08, 0.92], "y": [0.08, 0.92]},
        "radialaxis": {
            "visible": True,
            "range": [0, 100],
            "tickvals": [20, 40, 60, 80, 100],
            "tickfont": {"size": 16, "color": INK_SOFT},
            "gridcolor": GRID,
            "linecolor": INK_SOFT,
        },
        "angularaxis": {"tickfont": {"size": 20, "color": INK}, "gridcolor": GRID, "linecolor": INK_SOFT},
    },
    paper_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=True,
    legend={
        "font": {"size": 18, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 0.95,
        "y": 0.95,
        "xanchor": "right",
    },
    margin={"l": 160, "r": 160, "t": 120, "b": 120},
)

# Square format — ideal for symmetric polar charts (3600×3600 px)
fig.write_image(f"plot-{THEME}.png", width=1200, height=1200, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
