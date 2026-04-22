""" pyplots.ai
lift-curve: Model Lift Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulate customer churn prediction model results
np.random.seed(42)
n_samples = 1000

# Create realistic churn prediction scenario
# True positives have higher scores, some overlap for realism
y_true = np.concatenate([np.ones(200), np.zeros(800)])  # 20% churn rate
y_score = np.where(
    y_true == 1,
    np.clip(np.random.beta(5, 2, len(y_true)), 0, 1),  # Churners: higher scores
    np.clip(np.random.beta(2, 5, len(y_true)), 0, 1),  # Non-churners: lower scores
)

# Calculate lift curve
sorted_indices = np.argsort(y_score)[::-1]  # Sort by score descending
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative lift at each percentage
percentages = np.arange(1, 101)
n_total = len(y_true)
n_positives = y_true.sum()
baseline_rate = n_positives / n_total

lift_values = []
for pct in percentages:
    n_selected = int(np.ceil(n_total * pct / 100))
    n_captured = y_true_sorted[:n_selected].sum()
    model_rate = n_captured / n_selected
    lift = model_rate / baseline_rate
    lift_values.append(lift)

# Create DataFrame for Altair
df = pd.DataFrame({"Population (%)": percentages, "Cumulative Lift": lift_values})

# Reference line at y=1 (random selection)
df_reference = pd.DataFrame({"Population (%)": [0, 100], "Reference": [1.0, 1.0]})

# Create lift curve chart
lift_line = (
    alt.Chart(df)
    .mark_line(strokeWidth=4, color="#306998")
    .encode(
        x=alt.X("Population (%):Q", scale=alt.Scale(domain=[0, 100]), title="Population Targeted (%)"),
        y=alt.Y("Cumulative Lift:Q", scale=alt.Scale(domain=[0, 5]), title="Cumulative Lift"),
        tooltip=[alt.Tooltip("Population (%):Q", format=".0f"), alt.Tooltip("Cumulative Lift:Q", format=".2f")],
    )
)

# Reference line at lift = 1
reference_line = (
    alt.Chart(df_reference)
    .mark_line(strokeWidth=2, strokeDash=[8, 4], color="#999999")
    .encode(x="Population (%):Q", y="Reference:Q")
)

# Add decile markers
decile_df = df[df["Population (%)"].isin([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])]
decile_points = (
    alt.Chart(decile_df)
    .mark_point(size=200, color="#306998", filled=True)
    .encode(
        x="Population (%):Q",
        y="Cumulative Lift:Q",
        tooltip=[
            alt.Tooltip("Population (%):Q", format=".0f", title="Decile %"),
            alt.Tooltip("Cumulative Lift:Q", format=".2f", title="Lift"),
        ],
    )
)

# Add annotation for reference line
annotation = (
    alt.Chart(pd.DataFrame({"x": [75], "y": [1.25], "text": ["Random Selection (Lift = 1)"]}))
    .mark_text(fontSize=18, color="#555555", fontWeight="bold", align="center")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Combine all layers
chart = (
    alt.layer(reference_line, lift_line, decile_points, annotation)
    .properties(
        width=1600, height=900, title=alt.Title(text="lift-curve · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridColor="#dddddd", gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
