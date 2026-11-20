""" anyplot.ai
residual-plot: Residual Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-20
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
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"  # theme-adaptive zero line

# Constants
OUTLIER_SD = 2  # residuals beyond this many standard deviations are outliers
SMOOTH_WINDOW = 15  # moving-average window (observations) of the trend line

# Columns: set these to your table's column names
OBSERVED = "Observed value"  # role: y_true
PREDICTED = "Fitted value"  # role: y_pred

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
rng = np.random.default_rng(42)
n_samples = 150
x = np.linspace(0, 10, n_samples)
# Slightly curved truth that a straight-line model will miss
observed = 2 * x + 0.3 * x**1.5 + rng.normal(0, 2, n_samples)
slope, intercept = np.polyfit(x, observed, 1)
df = pd.DataFrame({OBSERVED: observed, PREDICTED: slope * x + intercept})

# Plot: reads only df and the constants above
RESIDUAL = "Residual (observed − fitted)"
df[RESIDUAL] = df[OBSERVED] - df[PREDICTED]
sd = df[RESIDUAL].std()
is_outlier = df[RESIDUAL].abs() > OUTLIER_SD * sd
normal, outliers = df[~is_outlier], df[is_outlier]
x_range = [df[PREDICTED].min(), df[PREDICTED].max()]

ordered = df.sort_values(PREDICTED)
trend = ordered[RESIDUAL].rolling(SMOOTH_WINDOW, center=True, min_periods=1).mean()

hover = "Fitted: %{x:.2f}<br>Residual: %{y:.2f}<extra></extra>"

fig = go.Figure()

for sign in (1, -1):
    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=[sign * OUTLIER_SD * sd] * 2,
            mode="lines",
            line=dict(color=IMPRINT_PALETTE[1], width=2.5, dash="dash"),
            name=f"{'+' if sign > 0 else '−'}{OUTLIER_SD} SD",
            hoverinfo="skip",
        )
    )

fig.add_trace(
    go.Scatter(
        x=x_range, y=[0, 0], mode="lines", line=dict(color=NEUTRAL, width=2.5), name="Zero residual", hoverinfo="skip"
    )
)

fig.add_trace(
    go.Scatter(
        x=normal[PREDICTED],
        y=normal[RESIDUAL],
        mode="markers",
        marker=dict(size=10, color=IMPRINT_PALETTE[0], opacity=0.7, line=dict(width=1, color=IMPRINT_PALETTE[0])),
        name="Residuals",
        hovertemplate=hover,
    )
)

if len(outliers):
    fig.add_trace(
        go.Scatter(
            x=outliers[PREDICTED],
            y=outliers[RESIDUAL],
            mode="markers",
            marker=dict(
                size=12,
                color=IMPRINT_PALETTE[1],
                opacity=0.9,
                line=dict(width=1.5, color=IMPRINT_PALETTE[1]),
                symbol="diamond",
            ),
            name=f"Outliers (>{OUTLIER_SD} SD)",
            hovertemplate=hover,
        )
    )

fig.add_trace(
    go.Scatter(
        x=ordered[PREDICTED],
        y=trend,
        mode="lines",
        line=dict(color=INK_SOFT, width=3),
        name="Trend (moving average)",
        hovertemplate="Fitted: %{x:.2f}<br>Smoothed residual: %{y:.2f}<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin=dict(l=80, r=170, t=70, b=60),
    title=dict(
        text="residual-plot · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text=PREDICTED, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text=RESIDUAL, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zeroline=False,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        font=dict(size=10, color=INK_SOFT),
        x=1.02,
        y=1,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
