""" anyplot.ai
learning-curve-basic: Model Learning Curve
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-10
"""

import os
import sys


saved_path = sys.path[:]
sys.path = [p for p in sys.path if p not in ("", ".", os.getcwd())]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


sys.path = saved_path

# Theme setup
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BRAND = "#009E73"  # Training (first series)
ACCENT = "#C475FD"  # Validation (second series)

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
    base_score = 0.98 - 0.02 * (size / 1000)
    noise = np.random.normal(0, 0.01, n_folds)
    train_scores[:, i] = np.clip(base_score + noise, 0.85, 1.0)

# Validation scores: start lower, improve with more data (learning curve shape)
val_scores = np.zeros((n_folds, n_sizes))
for i, size in enumerate(train_sizes):
    base_score = 0.70 + 0.18 * (1 - np.exp(-size / 400))
    noise = np.random.normal(0, 0.025 * np.exp(-size / 500), n_folds)
    val_scores[:, i] = np.clip(base_score + noise, 0.6, 0.95)

# Compute means and standard deviations
train_mean = train_scores.mean(axis=0)
train_std = train_scores.std(axis=0)
val_mean = val_scores.mean(axis=0)
val_std = val_scores.std(axis=0)

# Create DataFrame for Altair with enhanced tooltips
data = []
for i, size in enumerate(train_sizes):
    data.append(
        {
            "Training Set Size": size,
            "Score": train_mean[i],
            "Score_lower": train_mean[i] - train_std[i],
            "Score_upper": train_mean[i] + train_std[i],
            "Type": "Training",
            "Score_display": f"{train_mean[i]:.3f}",
            "Std": f"±{train_std[i]:.3f}",
        }
    )
    data.append(
        {
            "Training Set Size": size,
            "Score": val_mean[i],
            "Score_lower": val_mean[i] - val_std[i],
            "Score_upper": val_mean[i] + val_std[i],
            "Type": "Validation",
            "Score_display": f"{val_mean[i]:.3f}",
            "Std": f"±{val_std[i]:.3f}",
        }
    )

df = pd.DataFrame(data)

# Define color scale using Okabe-Ito palette
color_scale = alt.Scale(domain=["Training", "Validation"], range=[BRAND, ACCENT])

# Tighter Y-axis scale showing only relevant data range
y_scale = alt.Scale(domain=[0.65, 1.0])

# Create the confidence bands
band = (
    alt.Chart(df)
    .mark_area(opacity=0.2, interpolate="monotone")
    .encode(
        x=alt.X("Training Set Size:Q", title="Training Set Size (samples)"),
        y=alt.Y("Score_lower:Q", scale=y_scale),
        y2="Score_upper:Q",
        color=alt.Color("Type:N", scale=color_scale, legend=None),
    )
)

# Create the lines with enhanced tooltips
line = (
    alt.Chart(df)
    .mark_line(size=3, point=True, tension=0.3)
    .encode(
        x=alt.X("Training Set Size:Q", title="Training Set Size (samples)"),
        y=alt.Y("Score:Q", title="Accuracy Score", scale=y_scale),
        color=alt.Color("Type:N", scale=color_scale),
        tooltip=[
            alt.Tooltip("Training Set Size:Q", format=","),
            alt.Tooltip("Score:Q", format=".3f", title="Score"),
            alt.Tooltip("Std", title="Std Dev"),
            alt.Tooltip("Type:N", title="Curve Type"),
        ],
    )
)

# Points for better interactivity
points = (
    alt.Chart(df)
    .mark_point(size=100)
    .encode(
        x=alt.X("Training Set Size:Q"),
        y=alt.Y("Score:Q", scale=y_scale),
        color=alt.Color("Type:N", scale=color_scale, legend=None),
        tooltip=[
            alt.Tooltip("Training Set Size:Q", format=",", title="Size"),
            alt.Tooltip("Score:Q", format=".3f", title="Score"),
            alt.Tooltip("Std", title="Std Dev"),
            alt.Tooltip("Type:N", title="Type"),
        ],
    )
)

# Combine layers
chart = (
    alt.layer(band, line, points)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("learning-curve-basic · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, continuousWidth=1600, continuousHeight=900)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.1,
        labelColor=INK_SOFT,
        labelFontSize=18,
        titleColor=INK,
        titleFontSize=22,
    )
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        labelFontSize=16,
        titleColor=INK,
        titleFontSize=18,
        padding=10,
        cornerRadius=5,
    )
    .interactive()
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
