"""anyplot.ai
box-basic: Basic Box Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-28
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
LEGEND_BORDER = "rgba(74,74,68,0.3)" if THEME == "light" else "rgba(184,183,176,0.3)"

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data
np.random.seed(42)
categories = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
colors = ANYPLOT_PALETTE[:5]

data = {
    "Engineering": np.random.normal(95000, 15000, 100),
    "Marketing": np.random.normal(75000, 12000, 80),
    "Sales": np.random.normal(70000, 20000, 120),
    "HR": np.random.normal(65000, 10000, 60),
    "Finance": np.random.normal(85000, 14000, 90),
}
data = {k: np.clip(v, 25000, None) for k, v in data.items()}

medians = {k: float(np.median(v)) for k, v in data.items()}
highest_dept = max(medians, key=medians.get)
lowest_dept = min(medians, key=medians.get)

# Plot
fig = go.Figure()

# Market rate band — PNG-visible plotly shape highlighting target compensation range
fig.add_hrect(
    y0=75000,
    y1=90000,
    fillcolor=ANYPLOT_PALETTE[0],
    opacity=0.06,
    line_width=0,
    layer="below",
    annotation_text="Market rate band",
    annotation_position="top right",
    annotation_font_size=9,
    annotation_font_color=INK_SOFT,
)

for i, category in enumerate(categories):
    values = data[category]
    fig.add_trace(
        go.Box(
            y=values,
            name=category,
            marker_color=colors[i],
            fillcolor=colors[i],
            opacity=0.85,
            boxpoints="outliers",
            marker={"size": 10, "opacity": 0.8, "line": {"width": 1, "color": INK_SOFT}},
            line={"width": 2.5, "color": colors[i]},
            whiskerwidth=0.6,
            hovertemplate="<b>%{x}</b><br>Salary: $%{y:,.0f}<br><extra></extra>",
        )
    )

# Annotations
highest_color = colors[categories.index(highest_dept)]
lowest_color = colors[categories.index(lowest_dept)]

fig.add_annotation(
    x=highest_dept,
    y=medians[highest_dept],
    text=f"Highest median<br><b>${medians[highest_dept]:,.0f}</b>",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowwidth=2,
    arrowcolor=highest_color,
    ax=70,
    ay=-60,
    font={"size": 11, "color": highest_color},
    bordercolor=highest_color,
    borderwidth=1.5,
    borderpad=6,
    bgcolor=ELEVATED_BG,
)

fig.add_annotation(
    x=lowest_dept,
    y=medians[lowest_dept],
    text=f"Lowest median<br><b>${medians[lowest_dept]:,.0f}</b>",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowwidth=2,
    arrowcolor=lowest_color,
    ax=80,
    ay=-60,
    font={"size": 11, "color": lowest_color},
    bordercolor=lowest_color,
    borderwidth=1.5,
    borderpad=6,
    bgcolor=ELEVATED_BG,
)

gap = medians[highest_dept] - medians[lowest_dept]
fig.add_annotation(
    x=0.98,
    y=0.98,
    xref="paper",
    yref="paper",
    text=f"Median salary gap: <b>${gap:,.0f}</b>",
    showarrow=False,
    font={"size": 11, "color": INK_SOFT},
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=8,
    bgcolor=ELEVATED_BG,
    xanchor="right",
    yanchor="top",
)

title_text = "box-basic · python · plotly · anyplot.ai"

fig.update_layout(
    autosize=False,
    title={
        "text": f"<b>{title_text}</b><br><span style='font-size:11px;color:{INK_SOFT}'>Annual Salary Distribution Across Departments</span>",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "tickfont": {"size": 11, "color": INK_SOFT},
        "showline": True,
        "linewidth": 1.5,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "Annual Salary ($)", "font": {"size": 12, "color": INK}, "standoff": 10},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickformat": "$,.0f",
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linewidth": 1.5,
        "linecolor": INK_SOFT,
        "range": [20000, 155000],
        "dtick": 20000,
        "showgrid": True,
    },
    showlegend=True,
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": LEGEND_BORDER,
        "borderwidth": 1,
        "font": {"size": 10, "color": INK_SOFT},
        "orientation": "h",
        "yanchor": "bottom",
        "y": -0.25,
        "xanchor": "center",
        "x": 0.5,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 80, "r": 40, "t": 100, "b": 110},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
