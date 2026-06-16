""" anyplot.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-08
"""

import os

import pandas as pd
import plotly.graph_objects as go


# Theme configuration
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette - first color is always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data: Smartphone OS market share across world regions
categories = ["North America", "South America", "Europe", "Africa", "Asia"]
components = ["iOS", "Android", "Other"]

# Market share percentages by region
data = {
    "North America": [25, 72, 3],
    "South America": [18, 78, 4],
    "Europe": [22, 75, 3],
    "Africa": [8, 88, 4],
    "Asia": [15, 83, 2],
}

df = pd.DataFrame(data, index=components).T

# Create figure
fig = go.Figure()

for i, component in enumerate(components):
    fig.add_trace(
        go.Bar(
            name=component,
            x=categories,
            y=df[component].values,
            marker=dict(color=IMPRINT[i], line=dict(width=0)),
            text=[f"{v:.0f}%" for v in df[component].values],
            textposition="inside",
            textfont=dict(size=16, color="white"),
            hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y:.0f}%<extra></extra>",
        )
    )

# Layout for 4800x2700 px
fig.update_layout(
    barmode="stack",
    title=dict(
        text="bar-stacked-percent · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Region", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        linewidth=2,
        showline=True,
        showgrid=False,
    ),
    yaxis=dict(
        title=dict(text="Market Share (%)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        range=[0, 100],
        ticksuffix="%",
        gridcolor=GRID,
        linewidth=2,
        linecolor=INK_SOFT,
        showgrid=True,
        showline=True,
    ),
    legend=dict(
        font=dict(size=18, color=INK),
        bordercolor=INK_SOFT,
        borderwidth=2,
        orientation="h",
        yanchor="bottom",
        y=1.04,
        xanchor="center",
        x=0.5,
        bgcolor=PAGE_BG,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    margin=dict(l=100, r=40, t=140, b=100),
    bargap=0.2,
    hovermode="x unified",
)

fig.update_xaxes(showline=True, linewidth=2, linecolor=INK_SOFT, mirror=False)
fig.update_yaxes(showline=True, linewidth=2, linecolor=INK_SOFT, mirror=False, side="left")

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
