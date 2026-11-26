"""anyplot.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-28
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BIAS_COLOR = IMPRINT_PALETTE[0]  # position 1 — first series (brand green)
VARIANCE_COLOR = IMPRINT_PALETTE[1]  # position 2 — lavender
IRRED_COLOR = INK_MUTED  # semantic muted — baseline noise floor
TOTAL_COLOR = IMPRINT_PALETTE[4]  # semantic red — total error (bad/loss)

# Constants
IRREDUCIBLE_NOISE = 0.1  # noise floor of the theoretical model (epsilon)

# Column constants
COMPLEXITY = "Model Complexity"  # role: model_complexity
BIAS = "Bias²"  # role: bias_squared
VARIANCE = "Variance"  # role: variance
IRREDUCIBLE = "Irreducible Error"  # role: irreducible_error
TOTAL = "Total Error"  # role: total_error

# Data: replace this block with your own table, one row per complexity level
x = np.linspace(0.5, 10, 100)
df = pd.DataFrame(
    {
        COMPLEXITY: x,
        BIAS: 0.8 / (1 + 0.5 * x) ** 2,
        VARIANCE: 0.02 * x**1.5,
        IRREDUCIBLE: np.full_like(x, IRREDUCIBLE_NOISE),
    }
)
df[TOTAL] = df[BIAS] + df[VARIANCE] + df[IRREDUCIBLE]

# Plot
x_min, x_max = df[COMPLEXITY].min(), df[COMPLEXITY].max()
x_span = x_max - x_min
y_top = df[TOTAL].max() * 1.4
optimal_idx = df[TOTAL].idxmin()
optimal_complexity = df.loc[optimal_idx, COMPLEXITY]
optimal_error = df.loc[optimal_idx, TOTAL]
last = df.iloc[-1]

fig = go.Figure()

# Shaded underfitting / overfitting zones
fig.add_vrect(x0=x_min, x1=optimal_complexity, fillcolor="rgba(0,158,115,0.08)", layer="below", line_width=0)
fig.add_vrect(x0=optimal_complexity, x1=x_max, fillcolor="rgba(196,117,253,0.08)", layer="below", line_width=0)

# Curves
curve_styles = [
    (BIAS, BIAS_COLOR, 4, "dash"),
    (VARIANCE, VARIANCE_COLOR, 4, "dash"),
    (IRREDUCIBLE, IRRED_COLOR, 3, "dot"),
    (TOTAL, TOTAL_COLOR, 5, "solid"),
]
for column, color, width, dash in curve_styles:
    fig.add_trace(
        go.Scatter(
            x=df[COMPLEXITY], y=df[column], mode="lines", name=column, line=dict(color=color, width=width, dash=dash)
        )
    )

# Optimal complexity marker
fig.add_trace(
    go.Scatter(
        x=[optimal_complexity],
        y=[optimal_error],
        mode="markers",
        name="Optimal Complexity",
        marker=dict(color=TOTAL_COLOR, size=16, symbol="star", line=dict(color=PAGE_BG, width=2)),
    )
)

# Vertical line at optimal point, labelled in the clear area above the curves
fig.add_vline(
    x=optimal_complexity,
    line=dict(color=TOTAL_COLOR, width=2, dash="dash"),
    annotation_text="Optimal<br>Complexity",
    annotation_position="top right",
    annotation_font=dict(size=12, color=TOTAL_COLOR),
)

# Zone labels: the underfitting label sits below the legend, the overfitting label above the curves
fig.add_annotation(
    x=x_min + 0.17 * x_span,
    y=y_top * 0.46,
    text="<b>Underfitting</b><br>(High Bias)",
    showarrow=False,
    font=dict(size=12, color=BIAS_COLOR),
)
fig.add_annotation(
    x=x_min + 0.81 * x_span,
    y=y_top * 0.8,
    text="<b>Overfitting</b><br>(High Variance)",
    showarrow=False,
    font=dict(size=12, color=VARIANCE_COLOR),
)

# Formula annotation: in the clear area between the zone labels
fig.add_annotation(
    x=x_min + 0.5 * x_span,
    y=y_top * 0.58,
    text=f"<b>{TOTAL} = {BIAS} + {VARIANCE} + ε</b>",
    showarrow=False,
    font=dict(size=13, color=INK),
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=6,
)

# Direct curve labels at the right edge of each curve
for column, color, _, _ in curve_styles:
    fig.add_annotation(
        x=1.02,
        xref="paper",
        y=float(last[column]),
        yref="y",
        text="Irred. Error" if column == IRREDUCIBLE else column,
        showarrow=False,
        xanchor="left",
        font=dict(size=11, color=color),
    )

title = "curve-bias-variance-tradeoff · python · plotly · anyplot.ai"

axis_style = dict(
    tickfont=dict(size=10, color=INK_SOFT),
    showgrid=True,
    gridcolor=GRID,
    gridwidth=1,
    linecolor=INK_SOFT,
    zerolinecolor=INK_SOFT,
    showline=False,
    mirror=False,
)

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    title=dict(text=title, font=dict(size=16, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text=COMPLEXITY, font=dict(size=12, color=INK)),
        tickvals=[x_min + f * x_span for f in (0.1, 0.3, 0.5, 0.7, 0.9)],
        ticktext=["Low", "", "Medium", "", "High"],
        range=[x_min - 0.05 * x_span, x_max + 0.05 * x_span],
        **axis_style,
    ),
    yaxis=dict(title=dict(text="Prediction Error", font=dict(size=12, color=INK)), range=[0, y_top], **axis_style),
    legend=dict(
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        font=dict(size=10, color=INK_SOFT),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=80, r=120, t=60, b=60),
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
