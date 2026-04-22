""" pyplots.ai
learning-curve-basic: Model Learning Curve
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go


# Data - Simulate learning curve data from cross-validation
np.random.seed(42)

# Training set sizes (10 different sizes)
train_sizes = np.array([50, 100, 200, 400, 600, 800, 1000, 1500, 2000, 3000])

# Simulate 5-fold cross-validation scores
n_folds = 5
n_sizes = len(train_sizes)

# Training scores: start high, stay high (slight decrease with more data due to harder fit)
train_scores = np.zeros((n_folds, n_sizes))
for i, size in enumerate(train_sizes):
    base_score = 0.98 - 0.03 * np.log10(size / 50)
    train_scores[:, i] = base_score + np.random.normal(0, 0.01, n_folds)

# Validation scores: start low, improve with more data, converge toward training
validation_scores = np.zeros((n_folds, n_sizes))
for i, size in enumerate(train_sizes):
    improvement = 0.15 * (1 - np.exp(-size / 800))
    base_score = 0.72 + improvement
    validation_scores[:, i] = base_score + np.random.normal(0, 0.02, n_folds)

# Calculate means and standard deviations
train_mean = train_scores.mean(axis=0)
train_std = train_scores.std(axis=0)
validation_mean = validation_scores.mean(axis=0)
validation_std = validation_scores.std(axis=0)

# Create figure
fig = go.Figure()

# Training score band (±1 std)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([train_sizes, train_sizes[::-1]]),
        y=np.concatenate([train_mean + train_std, (train_mean - train_std)[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.2)",
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
        line=dict(color="#306998", width=4),
        marker=dict(size=14, color="#306998"),
    )
)

# Validation score band (±1 std)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([train_sizes, train_sizes[::-1]]),
        y=np.concatenate([validation_mean + validation_std, (validation_mean - validation_std)[::-1]]),
        fill="toself",
        fillcolor="rgba(255, 212, 59, 0.3)",
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
        line=dict(color="#FFD43B", width=4),
        marker=dict(size=14, color="#FFD43B", line=dict(color="#B8960F", width=2)),
    )
)

# Layout
fig.update_layout(
    title=dict(
        text="learning-curve-basic · plotly · pyplots.ai", font=dict(size=32, color="#333333"), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Training Set Size", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        showgrid=True,
    ),
    yaxis=dict(
        title=dict(text="Accuracy Score", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        showgrid=True,
        range=[0.65, 1.02],
    ),
    legend=dict(
        font=dict(size=20),
        x=0.98,
        y=0.02,
        xanchor="right",
        yanchor="bottom",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="rgba(0,0,0,0.2)",
        borderwidth=1,
    ),
    template="plotly_white",
    margin=dict(l=100, r=80, t=100, b=100),
    plot_bgcolor="white",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
