""" pyplots.ai
line-loss-training: Training Loss Curve
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulating neural network training loss curves
np.random.seed(42)
epochs = np.arange(1, 51)

# Training loss: exponential decay with noise (continues decreasing)
train_loss = 2.5 * np.exp(-0.08 * epochs) + 0.15 + np.random.normal(0, 0.02, len(epochs))

# Validation loss: decay then overfitting (U-shape after minimum)
val_base = 2.5 * np.exp(-0.07 * epochs) + 0.35
val_loss = val_base + np.random.normal(0, 0.025, len(epochs))
# Add overfitting: loss increases after epoch 25
val_loss[25:] = val_loss[25:] + np.linspace(0, 0.35, 25)

# Find minimum validation loss epoch for annotation
min_val_epoch = epochs[np.argmin(val_loss)]
min_val_loss = np.min(val_loss)

# Create DataFrame in long format for Altair
df = pd.DataFrame(
    {
        "Epoch": np.tile(epochs, 2),
        "Loss": np.concatenate([train_loss, val_loss]),
        "Type": ["Training Loss"] * len(epochs) + ["Validation Loss"] * len(epochs),
    }
)

# Point for minimum validation loss annotation
min_point_df = pd.DataFrame({"Epoch": [min_val_epoch], "Loss": [min_val_loss], "Type": ["Optimal Stopping Point"]})

# Base line chart
lines = (
    alt.Chart(df)
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("Epoch:Q", title="Epoch", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y("Loss:Q", title="Cross-Entropy Loss", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        color=alt.Color(
            "Type:N",
            scale=alt.Scale(domain=["Training Loss", "Validation Loss"], range=["#306998", "#FFD43B"]),
            legend=alt.Legend(title="Curve Type", labelFontSize=16, titleFontSize=18),
        ),
    )
)

# Add points on lines for visibility
points = (
    alt.Chart(df)
    .mark_point(size=60, filled=True)
    .encode(
        x="Epoch:Q",
        y="Loss:Q",
        color=alt.Color(
            "Type:N",
            scale=alt.Scale(domain=["Training Loss", "Validation Loss"], range=["#306998", "#FFD43B"]),
            legend=None,
        ),
    )
)

# Annotation for minimum validation loss
min_marker = (
    alt.Chart(min_point_df)
    .mark_point(size=300, shape="diamond", filled=True, color="#E63946")
    .encode(x="Epoch:Q", y="Loss:Q")
)

# Text annotation for optimal stopping point
min_text = (
    alt.Chart(min_point_df)
    .mark_text(align="left", dx=12, dy=-10, fontSize=16, fontWeight="bold", color="#E63946")
    .encode(x="Epoch:Q", y="Loss:Q", text=alt.value(f"Min Val Loss (Epoch {min_val_epoch})"))
)

# Combine all layers
chart = (
    (lines + points + min_marker + min_text)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("line-loss-training · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_legend(labelFontSize=16, titleFontSize=18)
    .configure_view(strokeWidth=0)
)

# Save as PNG (4800 x 2700 with scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
