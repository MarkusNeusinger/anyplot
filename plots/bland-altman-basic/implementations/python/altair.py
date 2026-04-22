""" pyplots.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Simulated blood pressure measurements from two sphygmomanometers
np.random.seed(42)
n = 80

# Method 1 (reference): systolic blood pressure readings
method1 = np.random.normal(loc=125, scale=15, size=n)

# Method 2 (new device): has slight positive bias and proportional error
method2 = method1 + np.random.normal(loc=2.5, scale=5, size=n)

# Calculate Bland-Altman statistics
mean_values = (method1 + method2) / 2
diff_values = method1 - method2
mean_diff = np.mean(diff_values)
std_diff = np.std(diff_values, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# Create DataFrame
df = pd.DataFrame({"Mean": mean_values, "Difference": diff_values})

# Axis ranges
x_min = df["Mean"].min() - 5
x_max = df["Mean"].max() + 5
y_min = min(df["Difference"].min(), lower_loa) - 2
y_max = max(df["Difference"].max(), upper_loa) + 2

# Create scatter points
scatter = (
    alt.Chart(df)
    .mark_point(size=200, filled=True, opacity=0.7, color="#306998")
    .encode(
        x=alt.X("Mean:Q", title="Mean of Two Methods (mmHg)", scale=alt.Scale(domain=[x_min, x_max])),
        y=alt.Y(
            "Difference:Q", title="Difference (Method 1 - Method 2) (mmHg)", scale=alt.Scale(domain=[y_min, y_max])
        ),
        tooltip=[
            alt.Tooltip("Mean:Q", format=".1f", title="Mean"),
            alt.Tooltip("Difference:Q", format=".1f", title="Difference"),
        ],
    )
)

# Create DataFrames for horizontal lines
lines_df = pd.DataFrame(
    {
        "y": [mean_diff, upper_loa, lower_loa],
        "label": [f"Mean: {mean_diff:.2f}", f"+1.96 SD: {upper_loa:.2f}", f"-1.96 SD: {lower_loa:.2f}"],
        "line_type": ["mean", "loa", "loa"],
    }
)

# Mean bias line (solid)
mean_line = alt.Chart(pd.DataFrame({"y": [mean_diff]})).mark_rule(strokeWidth=3, color="#306998").encode(y="y:Q")

# Limits of agreement lines (dashed)
loa_lines = (
    alt.Chart(pd.DataFrame({"y": [upper_loa, lower_loa]}))
    .mark_rule(strokeWidth=2, strokeDash=[8, 4], color="#FFD43B")
    .encode(y="y:Q")
)

# Annotations for the lines
annotation_df = pd.DataFrame(
    {
        "x": [x_max - 2, x_max - 2, x_max - 2],
        "y": [mean_diff + 0.8, upper_loa + 0.8, lower_loa - 1.2],
        "text": [f"Mean Bias: {mean_diff:.2f}", f"+1.96 SD: {upper_loa:.2f}", f"-1.96 SD: {lower_loa:.2f}"],
    }
)

annotations = (
    alt.Chart(annotation_df)
    .mark_text(align="right", fontSize=16, fontWeight="bold", color="#333333")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Combine all layers
chart = (
    (scatter + mean_line + loa_lines + annotations)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("bland-altman-basic · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridColor="#cccccc", gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
