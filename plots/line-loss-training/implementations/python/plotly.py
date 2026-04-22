""" pyplots.ai
line-loss-training: Training Loss Curve
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
import plotly.graph_objects as go


# Data - Simulated neural network training history
np.random.seed(42)
epochs = np.arange(1, 101)

# Training loss: starts high, decreases with noise, eventually plateaus
train_loss = 2.5 * np.exp(-0.05 * epochs) + 0.15 + np.random.normal(0, 0.02, len(epochs))
train_loss = np.maximum(train_loss, 0.1)  # Ensure positive

# Validation loss: follows training initially, then diverges (overfitting after epoch ~60)
val_loss = 2.5 * np.exp(-0.045 * epochs) + 0.25 + np.random.normal(0, 0.03, len(epochs))
# Add overfitting effect: validation loss starts increasing after epoch 60
overfitting_effect = np.where(epochs > 60, 0.008 * (epochs - 60), 0)
val_loss = val_loss + overfitting_effect
val_loss = np.maximum(val_loss, 0.15)

# Find minimum validation loss epoch for annotation
min_val_epoch = epochs[np.argmin(val_loss)]
min_val_loss = np.min(val_loss)

# Create figure
fig = go.Figure()

# Training loss curve
fig.add_trace(
    go.Scatter(
        x=epochs,
        y=train_loss,
        mode="lines",
        name="Training Loss",
        line=dict(color="#306998", width=3),
        hovertemplate="Epoch %{x}<br>Training Loss: %{y:.4f}<extra></extra>",
    )
)

# Validation loss curve
fig.add_trace(
    go.Scatter(
        x=epochs,
        y=val_loss,
        mode="lines",
        name="Validation Loss",
        line=dict(color="#FFD43B", width=3),
        hovertemplate="Epoch %{x}<br>Validation Loss: %{y:.4f}<extra></extra>",
    )
)

# Mark minimum validation loss point
fig.add_trace(
    go.Scatter(
        x=[min_val_epoch],
        y=[min_val_loss],
        mode="markers+text",
        name="Best Epoch",
        marker=dict(color="#E74C3C", size=16, symbol="star"),
        text=[f"Best: Epoch {min_val_epoch}"],
        textposition="top center",
        textfont=dict(size=16, color="#E74C3C"),
        hovertemplate="Best Epoch: %{x}<br>Min Val Loss: %{y:.4f}<extra></extra>",
    )
)

# Update layout
fig.update_layout(
    title=dict(text="line-loss-training · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Epoch", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(128, 128, 128, 0.3)",
        gridwidth=1,
        showgrid=True,
        range=[0, 105],
    ),
    yaxis=dict(
        title=dict(text="Cross-Entropy Loss", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(128, 128, 128, 0.3)",
        gridwidth=1,
        showgrid=True,
    ),
    legend=dict(
        font=dict(size=18),
        x=0.75,
        y=0.95,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(128, 128, 128, 0.3)",
        borderwidth=1,
    ),
    template="plotly_white",
    margin=dict(l=100, r=80, t=100, b=100),
    plot_bgcolor="white",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
