""" anyplot.ai
learning-curve-basic: Model Learning Curve
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-10
"""

# ruff: noqa: C408

import os
import sys


# Avoid import shadowing: remove current directory from path before importing plotly
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir in sys.path:
    sys.path.remove(_current_dir)
if "" in sys.path:
    sys.path.remove("")

import numpy as np  # noqa: E402
import plotly.graph_objects as go  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series always #009E73)
TRAIN_COLOR = "#009E73"  # bluish green
VAL_COLOR = "#C475FD"  # vermillion

# Data - Simulate learning curve data from cross-validation
np.random.seed(42)

# Training set sizes (10 different sizes)
train_sizes = np.array([50, 100, 200, 400, 600, 800, 1000, 1500, 2000, 3000])

# Simulate 5-fold cross-validation scores
n_folds = 5
n_sizes = len(train_sizes)

# Training scores: start high, decrease slightly with more data
train_scores = np.zeros((n_folds, n_sizes))
for i, size in enumerate(train_sizes):
    base_score = 0.96 - 0.04 * np.log10(size / 50)
    train_scores[:, i] = base_score + np.random.normal(0, 0.01, n_folds)

# Validation scores: start low, improve with more data, converge toward training
validation_scores = np.zeros((n_folds, n_sizes))
for i, size in enumerate(train_sizes):
    improvement = 0.20 * (1 - np.exp(-size / 800))
    base_score = 0.68 + improvement
    validation_scores[:, i] = base_score + np.random.normal(0, 0.02, n_folds)

# Calculate means and standard deviations
train_mean = train_scores.mean(axis=0)
train_std = train_scores.std(axis=0)
validation_mean = validation_scores.mean(axis=0)
validation_std = validation_scores.std(axis=0)

# Create figure
fig = go.Figure()

# Training score band (±1 std)
train_band_color = f"rgba({int(TRAIN_COLOR[1:3], 16)}, {int(TRAIN_COLOR[3:5], 16)}, {int(TRAIN_COLOR[5:7], 16)}, 0.2)"
fig.add_trace(
    go.Scatter(
        x=np.concatenate([train_sizes, train_sizes[::-1]]),
        y=np.concatenate([train_mean + train_std, (train_mean - train_std)[::-1]]),
        fill="toself",
        fillcolor=train_band_color,
        line=dict(color="rgba(255,255,255,0)"),
        showlegend=False,
        hoverinfo="skip",
        name="Training ±1 std",
    )
)

# Training score line
fig.add_trace(
    go.Scatter(
        x=train_sizes,
        y=train_mean,
        mode="lines+markers",
        name="Training Score",
        line=dict(color=TRAIN_COLOR, width=4),
        marker=dict(size=12, color=TRAIN_COLOR),
        hovertemplate="<b>Training Score</b><br>Size: %{x}<br>Score: %{y:.3f}<extra></extra>",
    )
)

# Validation score band (±1 std)
val_band_color = f"rgba({int(VAL_COLOR[1:3], 16)}, {int(VAL_COLOR[3:5], 16)}, {int(VAL_COLOR[5:7], 16)}, 0.2)"
fig.add_trace(
    go.Scatter(
        x=np.concatenate([train_sizes, train_sizes[::-1]]),
        y=np.concatenate([validation_mean + validation_std, (validation_mean - validation_std)[::-1]]),
        fill="toself",
        fillcolor=val_band_color,
        line=dict(color="rgba(255,255,255,0)"),
        showlegend=False,
        hoverinfo="skip",
        name="Validation ±1 std",
    )
)

# Validation score line
fig.add_trace(
    go.Scatter(
        x=train_sizes,
        y=validation_mean,
        mode="lines+markers",
        name="Validation Score",
        line=dict(color=VAL_COLOR, width=4),
        marker=dict(size=12, color=VAL_COLOR),
        hovertemplate="<b>Validation Score</b><br>Size: %{x}<br>Score: %{y:.3f}<extra></extra>",
    )
)

# Layout
fig.update_layout(
    title=dict(
        text="learning-curve-basic · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Training Set Size", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        showgrid=True,
        linecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Accuracy Score (0-1)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        showgrid=True,
        linecolor=INK_SOFT,
        range=[0.60, 1.02],
    ),
    legend=dict(
        font=dict(size=18, color=INK_SOFT),
        x=0.98,
        y=0.02,
        xanchor="right",
        yanchor="bottom",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=dict(l=100, r=80, t=100, b=100),
)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
