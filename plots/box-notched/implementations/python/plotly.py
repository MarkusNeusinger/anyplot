""" anyplot.ai
box-notched: Notched Box Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-07
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

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data - Employee salary distributions across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
salary_data = {
    "Engineering": np.random.normal(95000, 15000, 80),
    "Marketing": np.random.normal(72000, 12000, 65),
    "Sales": np.random.normal(68000, 18000, 90),
    "HR": np.random.normal(65000, 10000, 50),
    "Finance": np.random.normal(85000, 14000, 70),
}

# Add outliers
salary_data["Engineering"] = np.append(salary_data["Engineering"], [145000, 150000, 42000])
salary_data["Sales"] = np.append(salary_data["Sales"], [135000, 28000, 25000])
salary_data["Finance"] = np.append(salary_data["Finance"], [140000, 45000])

# Plot
fig = go.Figure()

for i, (dept, values) in enumerate(salary_data.items()):
    fig.add_trace(
        go.Box(
            y=values,
            name=dept,
            boxpoints="outliers",
            notched=True,
            marker={"color": IMPRINT[i], "size": 10, "opacity": 0.7},
            line={"width": 2},
            fillcolor=IMPRINT[i],
            opacity=0.7,
        )
    )

# Style
fig.update_layout(
    title={"text": "box-notched · plotly · anyplot.ai", "font": {"size": 28, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Department", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Annual Salary (USD)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "tickformat": "$,.0f",
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    showlegend=False,
    margin={"l": 100, "r": 60, "t": 100, "b": 80},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
