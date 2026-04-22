""" pyplots.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: plotly 6.5.2 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-26
"""

import numpy as np
import plotly.graph_objects as go


# Data - Theoretical bias-variance decomposition curves
complexity = np.linspace(0.5, 10, 100)

# Bias squared: decreases with complexity (high bias = underfitting)
bias_squared = 0.8 / (1 + 0.5 * complexity) ** 2

# Variance: increases with complexity (high variance = overfitting)
variance = 0.02 * complexity**1.5

# Irreducible error: constant noise floor
irreducible_error = np.full_like(complexity, 0.1)

# Total error: sum of all components
total_error = bias_squared + variance + irreducible_error

# Find optimal complexity (minimum total error)
optimal_idx = np.argmin(total_error)
optimal_complexity = complexity[optimal_idx]
optimal_error = total_error[optimal_idx]

# Create figure
fig = go.Figure()

# Add shaded regions for underfitting and overfitting zones
fig.add_vrect(x0=0.5, x1=optimal_complexity, fillcolor="rgba(48, 105, 152, 0.1)", layer="below", line_width=0)

# Add zone labels as separate annotations to avoid overlap with legend
fig.add_annotation(
    x=1.5, y=0.85, text="<b>Underfitting</b><br>(High Bias)", showarrow=False, font=dict(size=16, color="#306998")
)
fig.add_annotation(
    x=8.5, y=0.85, text="<b>Overfitting</b><br>(High Variance)", showarrow=False, font=dict(size=16, color="#C49B00")
)
fig.add_vrect(x0=optimal_complexity, x1=10, fillcolor="rgba(255, 212, 59, 0.1)", layer="below", line_width=0)

# Bias squared curve
fig.add_trace(
    go.Scatter(
        x=complexity, y=bias_squared, mode="lines", name="Bias²", line=dict(color="#306998", width=4, dash="dash")
    )
)

# Variance curve
fig.add_trace(
    go.Scatter(
        x=complexity, y=variance, mode="lines", name="Variance", line=dict(color="#FFD43B", width=4, dash="dash")
    )
)

# Irreducible error curve
fig.add_trace(
    go.Scatter(
        x=complexity,
        y=irreducible_error,
        mode="lines",
        name="Irreducible Error",
        line=dict(color="#888888", width=3, dash="dot"),
    )
)

# Total error curve
fig.add_trace(
    go.Scatter(x=complexity, y=total_error, mode="lines", name="Total Error", line=dict(color="#E74C3C", width=5))
)

# Mark optimal complexity point
fig.add_trace(
    go.Scatter(
        x=[optimal_complexity],
        y=[optimal_error],
        mode="markers",
        name="Optimal Complexity",
        marker=dict(color="#E74C3C", size=18, symbol="star", line=dict(color="white", width=2)),
        showlegend=True,
    )
)

# Add vertical line at optimal point
fig.add_vline(
    x=optimal_complexity,
    line=dict(color="#E74C3C", width=2, dash="dash"),
    annotation_text="Optimal<br>Complexity",
    annotation_position="bottom",
    annotation_font=dict(size=14, color="#E74C3C"),
)

# Add formula annotation
fig.add_annotation(
    x=7.5,
    y=0.7,
    text="<b>Total Error = Bias² + Variance + ε</b>",
    showarrow=False,
    font=dict(size=18, color="#333333"),
    bgcolor="rgba(255, 255, 255, 0.8)",
    bordercolor="#333333",
    borderwidth=1,
    borderpad=8,
)

# Update layout
fig.update_layout(
    title=dict(text="curve-bias-variance-tradeoff · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Model Complexity", font=dict(size=22)),
        tickfont=dict(size=18),
        tickvals=[1, 3, 5, 7, 9],
        ticktext=["Low", "", "Medium", "", "High"],
        range=[0, 10.5],
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0, 0, 0, 0.1)",
    ),
    yaxis=dict(
        title=dict(text="Prediction Error", font=dict(size=22)),
        tickfont=dict(size=18),
        range=[0, 0.9],
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0, 0, 0, 0.1)",
    ),
    template="plotly_white",
    legend=dict(
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        font=dict(size=16),
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="rgba(0, 0, 0, 0.3)",
        borderwidth=1,
    ),
    margin=dict(l=80, r=40, t=80, b=80),
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html("plot.html", include_plotlyjs="cdn")
