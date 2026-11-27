"""anyplot.ai
box-basic: Basic Box Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: category
SALARY = "Annual salary ($)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("salaries.csv")
np.random.seed(42)
spec = [("Engineering", 95000, 15000, 100), ("Marketing", 75000, 12000, 80), ("Sales", 70000, 20000, 120)]
spec += [("HR", 65000, 10000, 60), ("Finance", 85000, 14000, 90)]
df = pd.DataFrame(
    {
        DEPARTMENT: np.repeat([name for name, _, _, _ in spec], [n for _, _, _, n in spec]),
        SALARY: np.concatenate([np.random.normal(mu, sd, n) for _, mu, sd, n in spec]),
    }
)
df[SALARY] = df[SALARY].clip(lower=25000)

# Plot
fig = go.Figure()
for i, (department, rows) in enumerate(df.groupby(DEPARTMENT, sort=False)):
    fig.add_trace(
        go.Box(
            y=rows[SALARY],
            name=str(department),
            fillcolor=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
            line={"width": 2.5, "color": INK},
            marker={
                "size": 10,
                "color": IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
                "opacity": 0.85,
                "line": {"width": 1.5, "color": INK},
            },
            boxpoints="outliers",
            whiskerwidth=0.6,
            hovertemplate="<b>%{x}</b><br>Salary: $%{y:,.0f}<extra></extra>",
        )
    )

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "<b>box-basic · python · plotly · anyplot.ai</b>",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": DEPARTMENT, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 11, "color": INK_SOFT},
        "showline": True,
        "linewidth": 1.5,
        "linecolor": INK_SOFT,
        "mirror": False,
        "zeroline": False,
        "showgrid": False,
    },
    yaxis={
        "title": {"text": SALARY, "font": {"size": 12, "color": INK}, "standoff": 10},
        "tickfont": {"size": 11, "color": INK_SOFT},
        "tickformat": "$,.0f",
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linewidth": 1.5,
        "linecolor": INK_SOFT,
        "mirror": False,
        "showgrid": True,
    },
    showlegend=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 90, "r": 40, "t": 60, "b": 70},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
