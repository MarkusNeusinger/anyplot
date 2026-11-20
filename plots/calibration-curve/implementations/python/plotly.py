"""anyplot.ai
calibration-curve: Calibration Curve
Library: plotly 7.1.0 | Python 3.14.9
Quality: pending | Updated: 2026-11-20
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per model in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 10  # equal-width probability bins, as the spec asks
MARKERS = ["circle", "diamond", "square", "triangle-up", "cross", "x", "star", "hexagon"]

# Columns: set these to your table's column names
Y_TRUE = "Actual outcome"  # role: y_true
Y_PROB = ["Calibrated model", "Overconfident model"]  # role: y_prob

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
rng = np.random.default_rng(42)
n_samples = 2000
true_risk = rng.uniform(0.1, 0.9, n_samples)
outcome = (rng.random(n_samples) < true_risk).astype(int)
calibrated = np.clip(true_risk + rng.normal(0, 0.1, n_samples), 0.01, 0.99)
overconfident = np.clip(0.5 + (true_risk - 0.5) * 1.8 + rng.normal(0, 0.05, n_samples), 0.01, 0.99)
df = pd.DataFrame(dict(zip([Y_TRUE, *Y_PROB], [outcome, calibrated, overconfident], strict=True)))

# Plot: reads only df and the constants above
edges = np.linspace(0, 1, N_BINS + 1)

fig = make_subplots(rows=2, cols=1, row_heights=[0.72, 0.28], vertical_spacing=0.13)

fig.add_trace(
    go.Scatter(
        x=[0, 1],
        y=[0, 1],
        mode="lines",
        name="Perfect calibration",
        line=dict(color=INK_SOFT, width=2, dash="dash"),
        hoverinfo="skip",
    ),
    row=1,
    col=1,
)

for i, model in enumerate(Y_PROB):
    prob = df[model].to_numpy()
    truth = df[Y_TRUE].to_numpy()
    bin_idx = np.clip(np.digitize(prob, edges[1:-1]), 0, N_BINS - 1)
    filled = [b for b in range(N_BINS) if (bin_idx == b).any()]
    mean_pred = [prob[bin_idx == b].mean() for b in filled]
    frac_pos = [truth[bin_idx == b].mean() for b in filled]
    brier = np.mean((prob - truth) ** 2)

    fig.add_trace(
        go.Scatter(
            x=mean_pred,
            y=frac_pos,
            mode="lines+markers",
            name=f"{model} (Brier {brier:.3f})",
            line=dict(color=IMPRINT_PALETTE[i], width=2.5),
            marker=dict(size=9, symbol=MARKERS[i], line=dict(color=PAGE_BG, width=1)),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Histogram(
            x=prob,
            name=model,
            xbins=dict(start=0, end=1, size=1 / (2 * N_BINS)),
            marker=dict(color=IMPRINT_PALETTE[i], line=dict(color=PAGE_BG, width=0.5)),
            opacity=0.7,
            showlegend=False,
        ),
        row=2,
        col=1,
    )

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin=dict(l=70, r=30, t=60, b=50),
    title=dict(text="calibration-curve · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    barmode="overlay",
    legend=dict(
        font=dict(size=10, color=INK_SOFT),
        x=0.98,
        y=0.42,
        xanchor="right",
        yanchor="bottom",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
)
axis_style = dict(gridcolor=GRID, linecolor=INK_SOFT, zerolinecolor=INK_SOFT, tickfont=dict(size=10, color=INK_SOFT))
fig.update_xaxes(range=[0, 1], dtick=0.1, **axis_style)
fig.update_yaxes(**axis_style)
fig.update_xaxes(title=dict(text="Mean predicted probability", font=dict(size=12, color=INK)), row=1, col=1)
fig.update_xaxes(title=dict(text="Predicted probability (all samples)", font=dict(size=12, color=INK)), row=2, col=1)
fig.update_yaxes(
    title=dict(text="Fraction of positives", font=dict(size=12, color=INK)), range=[0, 1], dtick=0.1, row=1, col=1
)
fig.update_yaxes(title=dict(text="Count", font=dict(size=12, color=INK)), row=2, col=1)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
