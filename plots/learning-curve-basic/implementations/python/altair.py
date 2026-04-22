""" pyplots.ai
learning-curve-basic: Model Learning Curve
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - simulate learning curve for a classification model
np.random.seed(42)

# Training set sizes (10 points from 100 to 1000 samples)
train_sizes = np.linspace(100, 1000, 10).astype(int)

# Simulate 5-fold cross-validation scores
n_folds = 5
n_sizes = len(train_sizes)

# Training scores: start high, remain high (slight decrease variance with more data)
train_scores = np.zeros((n_folds, n_sizes))
for i, size in enumerate(train_sizes):
    base_score = 0.98 - 0.02 * (size / 1000)  # Slight decrease as model generalizes
    noise = np.random.normal(0, 0.01, n_folds)
    train_scores[:, i] = np.clip(base_score + noise, 0.85, 1.0)

# Validation scores: start lower, improve with more data (learning curve shape)
val_scores = np.zeros((n_folds, n_sizes))
for i, size in enumerate(train_sizes):
    # Validation improves with data, converging toward training
    base_score = 0.70 + 0.18 * (1 - np.exp(-size / 400))
    noise = np.random.normal(0, 0.025 * np.exp(-size / 500), n_folds)
    val_scores[:, i] = np.clip(base_score + noise, 0.6, 0.95)

# Compute means and standard deviations
train_mean = train_scores.mean(axis=0)
train_std = train_scores.std(axis=0)
val_mean = val_scores.mean(axis=0)
val_std = val_scores.std(axis=0)

# Create DataFrame for Altair
data = []
for i, size in enumerate(train_sizes):
    data.append(
        {
            "Training Set Size": size,
            "Score": train_mean[i],
            "Score_lower": train_mean[i] - train_std[i],
            "Score_upper": train_mean[i] + train_std[i],
            "Type": "Training Score",
        }
    )
    data.append(
        {
            "Training Set Size": size,
            "Score": val_mean[i],
            "Score_lower": val_mean[i] - val_std[i],
            "Score_upper": val_mean[i] + val_std[i],
            "Type": "Validation Score",
        }
    )

df = pd.DataFrame(data)

# Define shared encodings
y_scale = alt.Scale(domain=[0.65, 1.02])
color_scale = alt.Scale(domain=["Training Score", "Validation Score"], range=["#306998", "#FFD43B"])

# Create the confidence bands
band = (
    alt.Chart(df)
    .mark_area(opacity=0.3)
    .encode(
        x=alt.X("Training Set Size:Q", title="Training Set Size (samples)"),
        y=alt.Y("Score_lower:Q", scale=y_scale, title="Accuracy Score"),
        y2="Score_upper:Q",
        color=alt.Color("Type:N", scale=color_scale, legend=None),
    )
)

# Create the lines with legend
line = (
    alt.Chart(df)
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("Training Set Size:Q", title="Training Set Size (samples)"),
        y=alt.Y("Score:Q", title="Accuracy Score", scale=y_scale),
        color=alt.Color("Type:N", scale=color_scale, legend=alt.Legend(title="Curve Type", symbolStrokeWidth=4)),
    )
)

# Combine layers with independent legends resolved to shared
chart = (
    alt.layer(band, line)
    .resolve_legend(color="independent")
    .properties(
        width=1600,
        height=900,
        title=alt.Title("learning-curve-basic · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_legend(
        strokeColor="gray", fillColor="white", padding=10, cornerRadius=5, labelFontSize=18, titleFontSize=20
    )
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
