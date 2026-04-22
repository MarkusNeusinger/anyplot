""" pyplots.ai
forest-basic: Meta-Analysis Forest Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-27
"""

import altair as alt
import pandas as pd


# Data: Meta-analysis of RCTs comparing treatment efficacy (standardized mean difference)
studies = [
    "Johnson 2018",
    "Smith 2019",
    "Garcia 2020",
    "Williams 2020",
    "Brown 2021",
    "Davis 2021",
    "Miller 2022",
    "Wilson 2022",
    "Anderson 2023",
    "Taylor 2023",
]

effect_sizes = [-0.45, -0.32, -0.58, -0.21, -0.67, -0.38, -0.52, -0.29, -0.41, -0.55]
ci_lower = [-0.78, -0.61, -0.95, -0.48, -1.02, -0.69, -0.88, -0.56, -0.72, -0.91]
ci_upper = [-0.12, -0.03, -0.21, 0.06, -0.32, -0.07, -0.16, -0.02, -0.10, -0.19]
weights = [8.5, 10.2, 7.8, 11.5, 6.9, 9.3, 8.1, 10.8, 9.7, 7.2]

# Pooled estimate
pooled_effect = -0.42
pooled_ci_lower = -0.53
pooled_ci_upper = -0.31

# Order labels for y-axis (studies at top, pooled estimate at bottom)
y_labels = list(reversed(studies)) + ["Pooled Estimate"]

# Create DataFrame for studies
df_studies = pd.DataFrame(
    {"study": studies, "effect_size": effect_sizes, "ci_lower": ci_lower, "ci_upper": ci_upper, "weight": weights}
)

# Normalize weights for marker sizing (scale between 150 and 500 for visibility)
weight_min = min(weights)
weight_max = max(weights)
df_studies["marker_size"] = 150 + (df_studies["weight"] - weight_min) / (weight_max - weight_min) * 350

# Create DataFrame for pooled estimate (CI line and diamond point)
df_pooled = pd.DataFrame(
    {
        "study": ["Pooled Estimate"],
        "effect_size": [pooled_effect],
        "ci_lower": [pooled_ci_lower],
        "ci_upper": [pooled_ci_upper],
    }
)

# Vertical reference line at null effect (0)
reference_line = (
    alt.Chart(pd.DataFrame({"x": [0]}))
    .mark_rule(color="#888888", strokeDash=[8, 4], strokeWidth=2, opacity=0.7)
    .encode(x="x:Q")
)

# Confidence interval lines for studies
ci_lines = (
    alt.Chart(df_studies)
    .mark_rule(color="#306998", strokeWidth=4)
    .encode(
        x=alt.X("ci_lower:Q", scale=alt.Scale(domain=[-1.15, 0.15])), x2="ci_upper:Q", y=alt.Y("study:N", sort=y_labels)
    )
)

# Effect size points for studies
points = (
    alt.Chart(df_studies)
    .mark_point(filled=True, color="#306998", stroke="white", strokeWidth=2)
    .encode(
        x=alt.X("effect_size:Q", scale=alt.Scale(domain=[-1.15, 0.15])),
        y=alt.Y("study:N", sort=y_labels),
        size=alt.Size("marker_size:Q", legend=None, scale=alt.Scale(range=[150, 500])),
        tooltip=[
            alt.Tooltip("study:N", title="Study"),
            alt.Tooltip("effect_size:Q", title="Effect Size", format=".2f"),
            alt.Tooltip("ci_lower:Q", title="CI Lower", format=".2f"),
            alt.Tooltip("ci_upper:Q", title="CI Upper", format=".2f"),
        ],
    )
)

# Pooled estimate confidence interval line
pooled_ci = (
    alt.Chart(df_pooled)
    .mark_rule(color="#306998", strokeWidth=4)
    .encode(
        x=alt.X("ci_lower:Q", scale=alt.Scale(domain=[-1.15, 0.15])), x2="ci_upper:Q", y=alt.Y("study:N", sort=y_labels)
    )
)

# Diamond marker for pooled estimate using mark_point with shape
pooled_diamond = (
    alt.Chart(df_pooled)
    .mark_point(shape="diamond", filled=True, size=1500, color="#FFD43B", stroke="#306998", strokeWidth=3)
    .encode(
        x=alt.X("effect_size:Q", scale=alt.Scale(domain=[-1.15, 0.15])),
        y=alt.Y("study:N", sort=y_labels),
        tooltip=[
            alt.Tooltip("study:N", title="Estimate"),
            alt.Tooltip("effect_size:Q", title="Effect Size", format=".2f"),
            alt.Tooltip("ci_lower:Q", title="CI Lower", format=".2f"),
            alt.Tooltip("ci_upper:Q", title="CI Upper", format=".2f"),
        ],
    )
)

# Text annotations for "Favors Treatment" and "Favors Control"
annotation_left = (
    alt.Chart(pd.DataFrame({"x": [-1.05], "study": ["Pooled Estimate"], "text": ["← Favors Treatment"]}))
    .mark_text(fontSize=16, color="#555555", align="left", dy=35)
    .encode(x=alt.X("x:Q", scale=alt.Scale(domain=[-1.15, 0.15])), y=alt.Y("study:N", sort=y_labels), text="text:N")
)

annotation_right = (
    alt.Chart(pd.DataFrame({"x": [0.05], "study": ["Pooled Estimate"], "text": ["Favors Control →"]}))
    .mark_text(fontSize=16, color="#555555", align="right", dy=35)
    .encode(x=alt.X("x:Q", scale=alt.Scale(domain=[-1.15, 0.15])), y=alt.Y("study:N", sort=y_labels), text="text:N")
)

# Combine all layers
chart = (
    alt.layer(reference_line, ci_lines, points, pooled_ci, pooled_diamond, annotation_left, annotation_right)
    .properties(
        width=1600, height=900, title=alt.Title("forest-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22)
    .configure_axisX(title="Standardized Mean Difference (95% CI)", grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_axisY(title=None, grid=False, ticks=False, domain=False)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
