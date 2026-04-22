""" pyplots.ai
gain-curve: Cumulative Gains Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulated model predictions for customer response
np.random.seed(42)
n_samples = 1000

# Generate realistic customer response data
# Model with good discrimination - scores correlate with actual outcomes
base_score = np.random.beta(2, 5, n_samples)  # Skewed distribution of base scores
noise = np.random.normal(0, 0.15, n_samples)
y_score = np.clip(base_score + noise, 0, 1)

# Generate actual outcomes with correlation to scores
response_prob = 0.3 * y_score + 0.05  # Higher score = higher probability of positive
y_true = (np.random.random(n_samples) < response_prob).astype(int)

# Calculate cumulative gains curve
sorted_indices = np.argsort(y_score)[::-1]  # Sort by score descending
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative percentages
cumulative_positives = np.cumsum(y_true_sorted)
total_positives = y_true_sorted.sum()
pct_population = np.arange(1, n_samples + 1) / n_samples * 100
pct_gain = cumulative_positives / total_positives * 100

# Add origin point for complete curve
pct_population = np.insert(pct_population, 0, 0)
pct_gain = np.insert(pct_gain, 0, 0)

# Subsample for smoother visual (keep every 10th point plus endpoints)
sample_idx = np.concatenate([[0], np.arange(10, len(pct_population) - 1, 10), [len(pct_population) - 1]])
pct_population_smooth = pct_population[sample_idx]
pct_gain_smooth = pct_gain[sample_idx]

# Create DataFrame for gains curve
df_gains = pd.DataFrame({"population": pct_population_smooth, "gain": pct_gain_smooth, "Type": "Model"})

# Create diagonal reference line (random selection baseline)
df_baseline = pd.DataFrame({"population": [0, 100], "gain": [0, 100], "Type": "Random (Baseline)"})

# Combine data
df_combined = pd.concat([df_gains, df_baseline], ignore_index=True)

# Create gain curve chart with proper styling
model_curve = (
    alt.Chart(df_combined[df_combined["Type"] == "Model"])
    .mark_line(
        strokeWidth=4,
        color="#306998",
        interpolate="monotone",  # Smooth interpolation
    )
    .encode(
        x=alt.X(
            "population:Q",
            title="Population Targeted (%)",
            scale=alt.Scale(domain=[0, 100]),
            axis=alt.Axis(titleFontSize=22, labelFontSize=18, tickCount=10),
        ),
        y=alt.Y(
            "gain:Q",
            title="Positive Cases Captured (%)",
            scale=alt.Scale(domain=[0, 100]),
            axis=alt.Axis(titleFontSize=22, labelFontSize=18, tickCount=10),
        ),
    )
)

# Add shaded area under model curve
area_model = (
    alt.Chart(df_combined[df_combined["Type"] == "Model"])
    .mark_area(opacity=0.15, color="#306998", interpolate="monotone")
    .encode(x="population:Q", y="gain:Q")
)

# Baseline diagonal line
baseline_line = (
    alt.Chart(df_combined[df_combined["Type"] == "Random (Baseline)"])
    .mark_line(strokeWidth=3, strokeDash=[8, 4], color="#888888")
    .encode(x="population:Q", y="gain:Q")
)

# Custom legend using text and lines
legend_model_line = (
    alt.Chart(pd.DataFrame({"x": [8, 18], "y": [94, 94]}))
    .mark_line(strokeWidth=4, color="#306998")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"))
)

legend_model_text = (
    alt.Chart(pd.DataFrame({"x": [20], "y": [94], "text": ["Model"]}))
    .mark_text(align="left", fontSize=18, color="#333333")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

legend_baseline_line = (
    alt.Chart(pd.DataFrame({"x": [8, 18], "y": [88, 88]}))
    .mark_line(strokeWidth=3, strokeDash=[8, 4], color="#888888")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"))
)

legend_baseline_text = (
    alt.Chart(pd.DataFrame({"x": [20], "y": [88], "text": ["Random (Baseline)"]}))
    .mark_text(align="left", fontSize=18, color="#333333")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Combine all layers
chart = (
    alt.layer(
        area_model,
        baseline_line,
        model_curve,
        legend_model_line,
        legend_model_text,
        legend_baseline_line,
        legend_baseline_text,
    )
    .properties(
        width=1600, height=900, title=alt.Title("gain-curve · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[2, 2])
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
