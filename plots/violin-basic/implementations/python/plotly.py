"""anyplot.ai
violin-basic: Basic Violin Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-29
"""

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
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: category
SALARY = "Annual Salary ($)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("salaries.csv")
rng = np.random.RandomState(42)
samples = {
    "Engineering": np.concatenate([rng.normal(92000, 8000, 120), rng.normal(75000, 5000, 80)]),
    "Marketing": rng.normal(72000, 10000, 180),
    "Sales": rng.normal(78000, 18000, 220),
    "Support": rng.normal(55000, 8000, 190),
}
df = pd.DataFrame(
    {
        DEPARTMENT: np.repeat(list(samples), [len(v) for v in samples.values()]),
        SALARY: np.concatenate(list(samples.values())),
    }
)

# Plot: reads only df and the constants above
fig = go.Figure()
for i, (dept, rows) in enumerate(df.groupby(DEPARTMENT, sort=False)):
    fig.add_trace(
        go.Violin(
            y=rows[SALARY],
            name=str(dept),
            line=dict(color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)], width=2),
            fillcolor=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
            opacity=0.8,
            points=False,
            box=dict(visible=True, width=0.2, fillcolor=ELEVATED_BG, line=dict(color=INK, width=1.5)),
            meanline=dict(visible=True, color=INK, width=2),
            hoveron="violins+kde",
            hoverinfo="y+name",
            scalemode="width",
            spanmode="hard",
            width=0.7,
        )
    )

# Style
title = "violin-basic · python · plotly · anyplot.ai"
fig.update_layout(
    autosize=False,
    margin=dict(l=110, r=80, t=80, b=60),
    title=dict(text=title, font=dict(size=16, color=INK, weight="bold"), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text=DEPARTMENT, font=dict(size=12, color=INK), standoff=12),
        tickfont=dict(size=10, color=INK_SOFT),
        linecolor=INK_SOFT,
        showline=True,
        mirror=False,
        showgrid=False,
    ),
    yaxis=dict(
        title=dict(text=SALARY, font=dict(size=12, color=INK), standoff=12),
        tickfont=dict(size=10, color=INK_SOFT),
        tickformat=",.0f",
        tickprefix="$",
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        showline=True,
        mirror=False,
        zeroline=False,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    showlegend=False,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
