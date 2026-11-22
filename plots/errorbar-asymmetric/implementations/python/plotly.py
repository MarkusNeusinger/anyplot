"""anyplot.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-15
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: first categorical series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CONDITION = "Condition"  # role: x
RT = "Median reaction time (ms)"  # role: y
ERROR_LOWER = "Error below (ms)"  # role: error_lower
ERROR_UPPER = "Error above (ms)"  # role: error_upper

# Data: replace this block with your own table, for example df = pd.read_csv("reaction_times.csv")
df = pd.DataFrame(
    {
        CONDITION: ["Congruent", "Neutral", "Incongruent", "Dual task", "Low contrast", "Fatigued"],
        RT: [412, 448, 521, 586, 540, 633],
        ERROR_LOWER: [48, 52, 61, 70, 74, 66],
        ERROR_UPPER: [95, 118, 160, 205, 230, 285],
    }
)

# Plot: reads only df and the constants above
lower_bound = df[RT] - df[ERROR_LOWER]
upper_bound = df[RT] + df[ERROR_UPPER]
bounds = np.column_stack([lower_bound, upper_bound])

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[CONDITION],
        y=df[RT],
        mode="markers",
        marker=dict(size=10, color=IMPRINT_PALETTE[0], line=dict(width=1, color=PAGE_BG)),
        error_y=dict(
            type="data",
            symmetric=False,
            array=df[ERROR_UPPER],
            arrayminus=df[ERROR_LOWER],
            color=IMPRINT_PALETTE[0],
            thickness=1.5,
            width=6,
        ),
        name="Median (10th–90th percentile)",
        showlegend=True,
        customdata=bounds,
        hovertemplate=(
            "<b>%{x}</b><br>Median: %{y:.0f} ms<br>10th–90th: %{customdata[0]:.0f} – %{customdata[1]:.0f} ms<extra></extra>"
        ),
    )
)

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin=dict(l=80, r=40, t=60, b=60),
    title=dict(text="errorbar-asymmetric · python · plotly · anyplot.ai", font=dict(size=16, color=INK)),
    xaxis=dict(
        title=dict(text=CONDITION, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=False,
        showline=True,
        linecolor=INK_SOFT,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text=RT, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        showline=True,
        linecolor=INK_SOFT,
        zeroline=False,
        range=[0, upper_bound.max() * 1.1],
    ),
    template="none",
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        font=dict(size=10, color=INK_SOFT),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
)

fig.add_annotation(
    x=0.98,
    y=0.03,
    xref="paper",
    yref="paper",
    text="Error bars show the 10th–90th percentile range",
    showarrow=False,
    font=dict(size=9, color=INK_MUTED),
    xanchor="right",
    yanchor="bottom",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
