""" pyplots.ai
calibration-curve: Calibration Curve
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate synthetic classification predictions
np.random.seed(42)
n_samples = 2000

# Simulate predictions from a slightly overconfident classifier
y_true = np.random.binomial(1, 0.4, n_samples)
# Create predictions correlated with true labels but with some noise
base_prob = y_true * 0.6 + (1 - y_true) * 0.3
noise = np.random.normal(0, 0.15, n_samples)
y_prob = np.clip(base_prob + noise, 0.01, 0.99)

# Calculate calibration curve manually (10 bins)
n_bins = 10
bin_edges = np.linspace(0, 1, n_bins + 1)
prob_true = []
prob_pred = []

for i in range(n_bins):
    mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
    if mask.sum() > 0:
        prob_pred.append(y_prob[mask].mean())
        prob_true.append(y_true[mask].mean())

# Create calibration data
calibration_df = pd.DataFrame({"Mean Predicted Probability": prob_pred, "Fraction of Positives": prob_true})

# Calculate Brier score
brier_score = np.mean((y_prob - y_true) ** 2)

# Create histogram data for predicted probabilities
hist, bin_edges_hist = np.histogram(y_prob, bins=20)
hist_df = pd.DataFrame({"Probability": (bin_edges_hist[:-1] + bin_edges_hist[1:]) / 2, "Count": hist})

# Perfect calibration line
perfect_df = pd.DataFrame({"x": [0, 1], "y": [0, 1]})

# Calibration curve chart
calibration_line = (
    alt.Chart(calibration_df)
    .mark_line(color="#306998", strokeWidth=4)
    .encode(
        x=alt.X("Mean Predicted Probability:Q", scale=alt.Scale(domain=[0, 1]), title="Mean Predicted Probability"),
        y=alt.Y("Fraction of Positives:Q", scale=alt.Scale(domain=[0, 1]), title="Fraction of Positives"),
    )
)

calibration_points = (
    alt.Chart(calibration_df)
    .mark_point(color="#306998", size=300, filled=True)
    .encode(
        x=alt.X("Mean Predicted Probability:Q"),
        y=alt.Y("Fraction of Positives:Q"),
        tooltip=["Mean Predicted Probability:Q", "Fraction of Positives:Q"],
    )
)

# Perfect calibration diagonal line
perfect_line = (
    alt.Chart(perfect_df)
    .mark_line(color="#FFD43B", strokeWidth=3, strokeDash=[8, 4])
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"))
)

# Main calibration chart
calibration_chart = alt.layer(perfect_line, calibration_line, calibration_points).properties(
    width=1400,
    height=600,
    title=alt.Title(
        "calibration-curve · altair · pyplots.ai",
        subtitle=f"Brier Score: {brier_score:.4f}",
        fontSize=28,
        subtitleFontSize=20,
    ),
)

# Histogram chart (below)
histogram_chart = (
    alt.Chart(hist_df)
    .mark_bar(color="#306998", opacity=0.7)
    .encode(
        x=alt.X("Probability:Q", scale=alt.Scale(domain=[0, 1]), title="Predicted Probability"),
        y=alt.Y("Count:Q", title="Count"),
    )
    .properties(width=1400, height=200, title=alt.Title("Distribution of Predicted Probabilities", fontSize=20))
)

# Combine charts vertically
combined_chart = (
    alt.vconcat(calibration_chart, histogram_chart)
    .configure_axis(labelFontSize=16, titleFontSize=18)
    .configure_title(anchor="middle")
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
combined_chart.save("plot.png", scale_factor=3.0)
combined_chart.save("plot.html")
