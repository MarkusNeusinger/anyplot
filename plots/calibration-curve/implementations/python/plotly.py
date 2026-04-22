""" pyplots.ai
calibration-curve: Calibration Curve
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


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
        line=dict(color="#888888", width=3, dash="dash"),
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
        line=dict(color="#306998", width=4),
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
        line=dict(color="#FFD43B", width=4),
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
        marker=dict(color="#306998", line=dict(color="#1a3d5c", width=1)),
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
        marker=dict(color="#FFD43B", line=dict(color="#b39500", width=1)),
        opacity=0.7,
        nbinsx=20,
        showlegend=False,
    ),
    row=2,
    col=1,
)

# Update layout
fig.update_layout(
    title=dict(text="calibration-curve · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    template="plotly_white",
    legend=dict(
        font=dict(size=18),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="#cccccc",
        borderwidth=1,
    ),
    barmode="overlay",
    margin=dict(l=100, r=80, t=120, b=80),
)

# Update axes for calibration curve (row 1)
fig.update_xaxes(
    title=dict(text="Mean Predicted Probability", font=dict(size=22)),
    tickfont=dict(size=18),
    range=[0, 1],
    dtick=0.1,
    gridcolor="rgba(0,0,0,0.1)",
    gridwidth=1,
    row=1,
    col=1,
)
fig.update_yaxes(
    title=dict(text="Fraction of Positives", font=dict(size=22)),
    tickfont=dict(size=18),
    range=[0, 1],
    dtick=0.1,
    gridcolor="rgba(0,0,0,0.1)",
    gridwidth=1,
    row=1,
    col=1,
)

# Update axes for histogram (row 2)
fig.update_xaxes(
    title=dict(text="Predicted Probability", font=dict(size=20)),
    tickfont=dict(size=16),
    range=[0, 1],
    dtick=0.1,
    row=2,
    col=1,
)
fig.update_yaxes(title=dict(text="Count", font=dict(size=20)), tickfont=dict(size=16), row=2, col=1)

# Update subplot title font
fig.update_annotations(font=dict(size=22))

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
