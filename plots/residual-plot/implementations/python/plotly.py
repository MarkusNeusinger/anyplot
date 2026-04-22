""" pyplots.ai
residual-plot: Residual Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go


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
        line=dict(color="rgba(255, 212, 59, 0.7)", width=3, dash="dash"),
        name="+2 SD",
        showlegend=True,
    )
)

fig.add_trace(
    go.Scatter(
        x=[y_pred.min(), y_pred.max()],
        y=[-2 * std_residuals, -2 * std_residuals],
        mode="lines",
        line=dict(color="rgba(255, 212, 59, 0.7)", width=3, dash="dash"),
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
        line=dict(color="#333333", width=3),
        name="Zero Line",
        showlegend=False,
    )
)

# Add normal residuals
fig.add_trace(
    go.Scatter(
        x=y_pred[normal_mask],
        y=residuals[normal_mask],
        mode="markers",
        marker=dict(size=14, color="#306998", opacity=0.7, line=dict(width=1, color="#1e4263")),
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
            marker=dict(size=16, color="#FFD43B", opacity=0.9, line=dict(width=2, color="#cc9900"), symbol="diamond"),
            name="Outliers (>2 SD)",
            hovertemplate="Fitted: %{x:.2f}<br>Residual: %{y:.2f}<extra></extra>",
        )
    )

# Add smoothing line to detect patterns (moving average with numpy)
sorted_indices = np.argsort(y_pred)
window_size = 15
kernel = np.ones(window_size) / window_size
smoothed_residuals = np.convolve(residuals[sorted_indices], kernel, mode="same")

fig.add_trace(
    go.Scatter(
        x=y_pred[sorted_indices],
        y=smoothed_residuals,
        mode="lines",
        line=dict(color="#cc4444", width=4),
        name="Trend Line",
        hovertemplate="Fitted: %{x:.2f}<br>Smoothed Residual: %{y:.2f}<extra></extra>",
    )
)

# Update layout
fig.update_layout(
    title=dict(
        text="residual-plot · plotly · pyplots.ai", font=dict(size=32, color="#333333"), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Fitted Values", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.1)",
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Residuals (y_true - y_pred)", font=dict(size=24)),
        tickfont=dict(size=18),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.1)",
        zeroline=False,
    ),
    template="plotly_white",
    legend=dict(
        font=dict(size=18),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="rgba(0,0,0,0.2)",
        borderwidth=1,
    ),
    margin=dict(l=100, r=50, t=100, b=80),
    plot_bgcolor="white",
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
