""" anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: plotly 7.1.0 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
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

# Imprint palette: all eight positions, one per energy source in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
YEAR = "Year"  # role: time
SOURCE = "Energy source"  # role: category
GENERATION = "Electricity generation (TWh)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("generation.csv")
np.random.seed(42)
years = np.arange(2015, 2025)
trends = {
    "Coal": np.clip(np.linspace(40, 22, len(years)) + np.random.randn(len(years)) * 2, 5, 50),
    "Natural Gas": np.clip(np.linspace(30, 32, len(years)) + np.random.randn(len(years)) * 1, 20, 40),
    "Wind": np.clip(np.linspace(12, 20, len(years)) + np.random.randn(len(years)) * 1, 5, 25),
    "Solar": np.clip(np.linspace(8, 18, len(years)) + np.random.randn(len(years)) * 1, 3, 25),
    "Hydro": np.clip(np.linspace(10, 8, len(years)) + np.random.randn(len(years)) * 0.5, 5, 15),
}
df = pd.DataFrame(
    {
        YEAR: np.tile(years, len(trends)),
        SOURCE: np.repeat(list(trends), len(years)),
        GENERATION: np.round(np.concatenate(list(trends.values())) * 40, 1),
    }
)

# Plot: reads only df and the constants above; groupnorm turns each year's values into shares of 100 %
fig = go.Figure()
for i, (source, rows) in enumerate(df.groupby(SOURCE, sort=False)):
    fig.add_trace(
        go.Scatter(
            x=rows[YEAR],
            y=rows[GENERATION],
            name=str(source),
            mode="lines",
            stackgroup="share",
            groupnorm="percent",
            fillcolor=IMPRINT_PALETTE[i],
            line=dict(width=1.5, color=PAGE_BG),
        )
    )

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin=dict(l=80, r=150, t=70, b=60),
    title=dict(
        text="area-stacked-percent · python · plotly · anyplot.ai",
        font=dict(size=16, color=INK),
        x=0.5,
        xanchor="center",
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    xaxis=dict(
        title=dict(text=YEAR, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor=INK_SOFT,
        ticks="",
    ),
    yaxis=dict(
        title=dict(text="Share of total (%)", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        range=[0, 100],
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor=INK_SOFT,
        ticks="",
    ),
    legend=dict(
        title=dict(text=SOURCE, font=dict(size=11, color=INK)),
        font=dict(size=10, color=INK_SOFT),
        traceorder="reversed",
        x=1.02,
        xanchor="left",
        y=1,
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    hovermode="x unified",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
