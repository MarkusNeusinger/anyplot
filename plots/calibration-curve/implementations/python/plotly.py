""" anyplot.ai
calibration-curve: Calibration Curve
Library: plotly 6.7.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-10
"""

import os

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"
SECONDARY = "#C475FD"
NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"

# Data - simulate predictions from two classifiers
np.random.seed(42)
n_samples = 2000

# Generate ground truth with varying base rates
base_prob = np.random.uniform(0.1, 0.9, n_samples)
y_true = (np.random.random(n_samples) < base_prob).astype(int)

# Well-calibrated model: predictions close to true probabilities
y_prob_calibrated = base_prob + np.random.normal(0, 0.1, n_samples)
y_prob_calibrated = np.clip(y_prob_calibrated, 0.01, 0.99)

# Overconfident model: pushes predictions toward 0 and 1
y_prob_overconfident = np.where(
    base_prob > 0.5,
    0.5 + (base_prob - 0.5) * 1.8 + np.random.normal(0, 0.05, n_samples),
    0.5 - (0.5 - base_prob) * 1.8 + np.random.normal(0, 0.05, n_samples),
)
y_prob_overconfident = np.clip(y_prob_overconfident, 0.01, 0.99)

# Compute calibration curves manually (10 uniform bins)
n_bins = 10
bin_edges = np.linspace(0, 1, n_bins + 1)

# Calibrated model calibration curve
prob_true_cal = []
prob_pred_cal = []
for i in range(n_bins):
    if i == n_bins - 1:
        mask = (y_prob_calibrated >= bin_edges[i]) & (y_prob_calibrated <= bin_edges[i + 1])
    else:
        mask = (y_prob_calibrated >= bin_edges[i]) & (y_prob_calibrated < bin_edges[i + 1])
    if np.sum(mask) > 0:
        prob_true_cal.append(np.mean(y_true[mask]))
        prob_pred_cal.append(np.mean(y_prob_calibrated[mask]))

# Overconfident model calibration curve
prob_true_over = []
prob_pred_over = []
for i in range(n_bins):
    if i == n_bins - 1:
        mask = (y_prob_overconfident >= bin_edges[i]) & (y_prob_overconfident <= bin_edges[i + 1])
    else:
        mask = (y_prob_overconfident >= bin_edges[i]) & (y_prob_overconfident < bin_edges[i + 1])
    if np.sum(mask) > 0:
        prob_true_over.append(np.mean(y_true[mask]))
        prob_pred_over.append(np.mean(y_prob_overconfident[mask]))

# Calculate Brier scores (mean squared error of predictions)
brier_cal = np.mean((y_prob_calibrated - y_true) ** 2)
brier_over = np.mean((y_prob_overconfident - y_true) ** 2)

# Create subplots: calibration curve on top, histogram below
fig = make_subplots(
    rows=2, cols=1, row_heights=[0.7, 0.3], vertical_spacing=0.12, subplot_titles=("", "Prediction Distribution")
)

# Diagonal reference line (perfect calibration)
fig.add_trace(
    go.Scatter(
        x=[0, 1],
        y=[0, 1],
        mode="lines",
        name="Perfect Calibration",
        line=dict(color=NEUTRAL, width=3, dash="dash"),
        showlegend=True,
    ),
    row=1,
    col=1,
)

# Well-calibrated model
fig.add_trace(
    go.Scatter(
        x=prob_pred_cal,
        y=prob_true_cal,
        mode="lines+markers",
        name=f"Calibrated Model (Brier: {brier_cal:.3f})",
        line=dict(color=BRAND, width=4),
        marker=dict(size=14, symbol="circle"),
    ),
    row=1,
    col=1,
)

# Overconfident model
fig.add_trace(
    go.Scatter(
        x=prob_pred_over,
        y=prob_true_over,
        mode="lines+markers",
        name=f"Overconfident Model (Brier: {brier_over:.3f})",
        line=dict(color=SECONDARY, width=4),
        marker=dict(size=14, symbol="diamond"),
    ),
    row=1,
    col=1,
)

# Histogram for calibrated model predictions
fig.add_trace(
    go.Histogram(
        x=y_prob_calibrated,
        name="Calibrated",
        marker=dict(color=BRAND, line=dict(color=INK_SOFT, width=1)),
        opacity=0.7,
        nbinsx=20,
        showlegend=False,
    ),
    row=2,
    col=1,
)

# Histogram for overconfident model predictions
fig.add_trace(
    go.Histogram(
        x=y_prob_overconfident,
        name="Overconfident",
        marker=dict(color=SECONDARY, line=dict(color=INK_SOFT, width=1)),
        opacity=0.7,
        nbinsx=20,
        showlegend=False,
    ),
    row=2,
    col=1,
)

# Update layout
fig.update_layout(
    title=dict(text="calibration-curve · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        font=dict(size=16, color=INK_SOFT),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    barmode="overlay",
    margin=dict(l=100, r=80, t=120, b=80),
)

# Update axes for calibration curve (row 1)
fig.update_xaxes(
    title=dict(text="Mean Predicted Probability", font=dict(size=22, color=INK)),
    tickfont=dict(size=18, color=INK_SOFT),
    range=[0, 1],
    dtick=0.1,
    gridcolor=GRID,
    gridwidth=1,
    linecolor=INK_SOFT,
    row=1,
    col=1,
)
fig.update_yaxes(
    title=dict(text="Fraction of Positives", font=dict(size=22, color=INK)),
    tickfont=dict(size=18, color=INK_SOFT),
    range=[0, 1],
    dtick=0.1,
    gridcolor=GRID,
    gridwidth=1,
    linecolor=INK_SOFT,
    row=1,
    col=1,
)

# Update axes for histogram (row 2)
fig.update_xaxes(
    title=dict(text="Predicted Probability", font=dict(size=20, color=INK)),
    tickfont=dict(size=16, color=INK_SOFT),
    range=[0, 1],
    dtick=0.1,
    gridcolor=GRID,
    gridwidth=1,
    linecolor=INK_SOFT,
    row=2,
    col=1,
)
fig.update_yaxes(
    title=dict(text="Count", font=dict(size=20, color=INK)),
    tickfont=dict(size=16, color=INK_SOFT),
    linecolor=INK_SOFT,
    row=2,
    col=1,
)

# Update subplot title font
fig.update_annotations(font=dict(size=22, color=INK))

# Save as PNG and HTML with theme-suffixed filenames
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
