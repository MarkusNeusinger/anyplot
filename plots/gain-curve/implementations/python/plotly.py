"""anyplot.ai
gain-curve: Cumulative Gains Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-11
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BASELINE = "#888888"  # neutral for the random-selection reference

# Columns: set these to your table's column names
Y_TRUE = "Actual outcome (0 or 1)"  # role: y_true
Y_SCORE = "Predicted probability"  # role: y_score

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
n_samples = 1000
positive_rate = 0.20
y_true = np.random.binomial(1, positive_rate, n_samples)
y_score = np.where(
    y_true == 1,
    np.random.beta(5, 2, n_samples),  # positives skew toward higher scores
    np.random.beta(2, 5, n_samples),  # negatives skew toward lower scores
)
y_score = np.clip(y_score + np.random.normal(0, 0.1, n_samples), 0, 1)
df = pd.DataFrame({Y_TRUE: y_true, Y_SCORE: y_score})

# Plot: reads only df and the constants above
ranked = df.sort_values(Y_SCORE, ascending=False)[Y_TRUE].to_numpy()
n_rows = len(ranked)
pct_population = np.insert(np.arange(1, n_rows + 1) / n_rows * 100, 0, 0)
pct_captured = np.insert(np.cumsum(ranked) / ranked.sum() * 100, 0, 0)

# Perfect model: full capture at the positive class rate, flat afterwards
perfect_rate = ranked.mean() * 100
perfect_x = [0, perfect_rate, 100]
perfect_y = [0, 100, 100]

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=[0, 100],
        y=[0, 100],
        mode="lines",
        name="Random (Baseline)",
        line=dict(color=BASELINE, width=2.5, dash="dash"),
        hovertemplate="Baseline<br>Population: %{x:.1f}%<br>Positives: %{y:.1f}%<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=perfect_x,
        y=perfect_y,
        mode="lines",
        name="Perfect Model",
        line=dict(color=IMPRINT_PALETTE[2], width=2.5, dash="dot"),
        hovertemplate="Perfect<br>Population: %{x:.1f}%<br>Positives: %{y:.1f}%<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=pct_population,
        y=pct_captured,
        mode="lines",
        name="Model",
        line=dict(color=IMPRINT_PALETTE[0], width=3.5),
        fill="tozeroy",
        fillcolor="rgba(0, 158, 115, 0.15)",
        hovertemplate="Model<br>Population: %{x:.1f}%<br>Positives: %{y:.1f}%<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin=dict(l=80, r=40, t=70, b=60),
    title=dict(
        text="gain-curve · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Percentage of population targeted (%)", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        range=[0, 100],
        dtick=20,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Percentage of positives captured (%)", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        range=[0, 100],
        dtick=20,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        x=0.98,
        y=0.04,
        xanchor="right",
        yanchor="bottom",
        font=dict(size=10, color=INK_SOFT),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
