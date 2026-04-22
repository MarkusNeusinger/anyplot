""" pyplots.ai
precision-recall: Precision-Recall Curve
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulate precision-recall curves for two classifiers
np.random.seed(42)

# Generate recall values (from 1 to 0, as thresholds increase)
n_points = 100
recall_vals = np.linspace(1, 0, n_points)

# Simulate Logistic Regression PR curve
# Good classifier: precision increases as recall decreases
lr_precision = 0.3 + 0.65 * (1 - recall_vals) + np.random.normal(0, 0.02, n_points)
lr_precision = np.clip(lr_precision, 0, 1)
# Ensure monotonic-ish behavior with step-like pattern
lr_precision = np.maximum.accumulate(lr_precision)
lr_ap = np.trapezoid(lr_precision, recall_vals[::-1])  # Average Precision

# Simulate Random Forest PR curve (better classifier)
rf_precision = 0.4 + 0.58 * (1 - recall_vals) ** 0.7 + np.random.normal(0, 0.015, n_points)
rf_precision = np.clip(rf_precision, 0, 1)
rf_precision = np.maximum.accumulate(rf_precision)
rf_ap = np.trapezoid(rf_precision, recall_vals[::-1])

# Baseline (positive class ratio - simulating ~30% positive class)
baseline = 0.30

# Create DataFrames for Altair
lr_df = pd.DataFrame(
    {"Recall": recall_vals, "Precision": lr_precision, "Model": f"Logistic Regression (AP = {lr_ap:.3f})"}
)

rf_df = pd.DataFrame({"Recall": recall_vals, "Precision": rf_precision, "Model": f"Random Forest (AP = {rf_ap:.3f})"})

# Combine classifier data
curve_df = pd.concat([lr_df, rf_df], ignore_index=True)

# Baseline data for reference line
baseline_df = pd.DataFrame(
    {"Recall": [0.0, 1.0], "Precision": [baseline, baseline], "Model": f"Random Classifier (baseline = {baseline:.2f})"}
)

# Create precision-recall curves with stepped interpolation
pr_curves = (
    alt.Chart(curve_df)
    .mark_line(strokeWidth=4, interpolate="step-after")
    .encode(
        x=alt.X("Recall:Q", title="Recall", scale=alt.Scale(domain=[0, 1])),
        y=alt.Y("Precision:Q", title="Precision", scale=alt.Scale(domain=[0, 1])),
        color=alt.Color(
            "Model:N",
            scale=alt.Scale(
                domain=[
                    f"Logistic Regression (AP = {lr_ap:.3f})",
                    f"Random Forest (AP = {rf_ap:.3f})",
                    f"Random Classifier (baseline = {baseline:.2f})",
                ],
                range=["#306998", "#FFD43B", "#888888"],
            ),
            legend=alt.Legend(
                title="Model",
                titleFontSize=20,
                labelFontSize=16,
                labelLimit=400,
                orient="bottom-right",
                direction="vertical",
                offset=10,
                symbolStrokeWidth=4,
                symbolSize=300,
            ),
        ),
        strokeDash=alt.StrokeDash(
            "Model:N",
            scale=alt.Scale(
                domain=[
                    f"Logistic Regression (AP = {lr_ap:.3f})",
                    f"Random Forest (AP = {rf_ap:.3f})",
                    f"Random Classifier (baseline = {baseline:.2f})",
                ],
                range=[[0], [0], [8, 4]],  # Solid for models, dashed for baseline
            ),
            legend=None,
        ),
    )
)

# Baseline reference line
baseline_line = (
    alt.Chart(baseline_df)
    .mark_line(strokeWidth=3, strokeDash=[8, 4])
    .encode(x=alt.X("Recall:Q"), y=alt.Y("Precision:Q"), color=alt.Color("Model:N", legend=None))
)

# Combine layers
chart = (
    alt.layer(pr_curves, baseline_line)
    .properties(
        width=1600, height=900, title=alt.Title("precision-recall · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridColor="#CCCCCC", gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
