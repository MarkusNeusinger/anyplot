""" anyplot.ai
residual-plot: Residual Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-10
"""

import os
import sys

import numpy as np

# Avoid module shadowing by removing current directory from path during import
cwd = sys.path[0]
if cwd in sys.path:
    sys.path.remove(cwd)
import plotly.graph_objects as go  # noqa: E402

sys.path.insert(0, cwd)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
BRAND = "#009E73"
ACCENT = "#C475FD"
NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"

# Data - Generate realistic regression scenario with varying residual patterns
np.random.seed(42)
n_samples = 150

# Create features with some non-linearity to show interesting residual patterns
X = np.linspace(0, 10, n_samples)
# True relationship with slight curvature (linear model will miss this)
y_true = 2 * X + 0.3 * X**1.5 + np.random.randn(n_samples) * 2

# Simple linear regression (manual fit)
X_mean = np.mean(X)
y_mean = np.mean(y_true)
slope = np.sum((X - X_mean) * (y_true - y_mean)) / np.sum((X - X_mean) ** 2)
intercept = y_mean - slope * X_mean
y_pred = slope * X + intercept

# Calculate residuals
residuals = y_true - y_pred
std_residuals = np.std(residuals)

# Identify outliers (beyond ±2 standard deviations)
outlier_mask = np.abs(residuals) > 2 * std_residuals
normal_mask = ~outlier_mask

# Create figure
fig = go.Figure()

# Add ±2 standard deviation bands (dashed lines)
fig.add_trace(
    go.Scatter(
        x=[y_pred.min(), y_pred.max()],
        y=[2 * std_residuals, 2 * std_residuals],
        mode="lines",
        line=dict(color=ACCENT, width=3, dash="dash"),
        name="+2 SD",
        showlegend=True,
    )
)

fig.add_trace(
    go.Scatter(
        x=[y_pred.min(), y_pred.max()],
        y=[-2 * std_residuals, -2 * std_residuals],
        mode="lines",
        line=dict(color=ACCENT, width=3, dash="dash"),
        name="-2 SD",
        showlegend=True,
    )
)

# Add horizontal reference line at y=0
fig.add_trace(
    go.Scatter(
        x=[y_pred.min(), y_pred.max()],
        y=[0, 0],
        mode="lines",
        line=dict(color=NEUTRAL, width=3),
        name="Zero Line",
        showlegend=False,
    )
)

# Add normal residuals (using brand green for first series)
fig.add_trace(
    go.Scatter(
        x=y_pred[normal_mask],
        y=residuals[normal_mask],
        mode="markers",
        marker=dict(size=14, color=BRAND, opacity=0.7, line=dict(width=1, color=BRAND)),
        name="Residuals",
        hovertemplate="Fitted: %{x:.2f}<br>Residual: %{y:.2f}<extra></extra>",
    )
)

# Add outlier residuals
if np.any(outlier_mask):
    fig.add_trace(
        go.Scatter(
            x=y_pred[outlier_mask],
            y=residuals[outlier_mask],
            mode="markers",
            marker=dict(size=16, color=ACCENT, opacity=0.9, line=dict(width=2, color=ACCENT), symbol="diamond"),
            name="Outliers (>2 SD)",
            hovertemplate="Fitted: %{x:.2f}<br>Residual: %{y:.2f}<extra></extra>",
        )
    )

# Add smoothing line to detect patterns
sorted_indices = np.argsort(y_pred)
window_size = 15
kernel = np.ones(window_size) / window_size
smoothed_residuals = np.convolve(residuals[sorted_indices], kernel, mode="same")

fig.add_trace(
    go.Scatter(
        x=y_pred[sorted_indices],
        y=smoothed_residuals,
        mode="lines",
        line=dict(color=INK_SOFT, width=4),
        name="Trend Line",
        hovertemplate="Fitted: %{x:.2f}<br>Smoothed Residual: %{y:.2f}<extra></extra>",
    )
)

# Update layout with theme-adaptive styling
fig.update_layout(
    title=dict(text="residual-plot · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Fitted Values", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Residuals (y_true - y_pred)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zeroline=False,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        font=dict(size=18, color=INK_SOFT),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=100, r=50, t=100, b=80),
)

# Save as PNG and HTML with theme-suffixed filenames
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
