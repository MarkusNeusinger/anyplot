""" pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: altair 6.0.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-15
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: 15 RCTs comparing drug vs placebo (log odds ratios)
np.random.seed(42)

studies = [
    "Adams 2016",
    "Baker 2017",
    "Chen 2017",
    "Davis 2018",
    "Evans 2018",
    "Foster 2019",
    "Garcia 2019",
    "Harris 2020",
    "Ibrahim 2020",
    "Jones 2021",
    "Klein 2021",
    "Lopez 2022",
    "Mitchell 2022",
    "Nelson 2023",
    "O'Brien 2023",
]

effect_sizes = np.array(
    [-0.52, -0.31, -0.78, -0.45, -0.19, -0.62, -0.38, -0.55, -0.41, -0.28, -0.70, -0.33, -0.48, -0.25, -0.90]
)

std_errors = np.array([0.18, 0.12, 0.28, 0.15, 0.10, 0.22, 0.14, 0.20, 0.16, 0.11, 0.25, 0.13, 0.17, 0.09, 0.32])

# Summary effect (inverse-variance weighted mean)
weights = 1.0 / std_errors**2
summary_effect = np.sum(weights * effect_sizes) / np.sum(weights)

df = pd.DataFrame({"study": studies, "effect_size": effect_sizes, "std_error": std_errors})

# Funnel confidence limits (pseudo 95% CI)
se_range = np.linspace(0, max(std_errors) + 0.05, 100)
funnel_df = pd.DataFrame(
    {"se": se_range, "lower": summary_effect - 1.96 * se_range, "upper": summary_effect + 1.96 * se_range}
)

# Study points
points = (
    alt.Chart(df)
    .mark_point(filled=True, size=250, color="#306998", stroke="white", strokeWidth=2)
    .encode(
        x=alt.X("effect_size:Q", title="Log Odds Ratio"),
        y=alt.Y("std_error:Q", title="Standard Error", scale=alt.Scale(reverse=True)),
        tooltip=[
            alt.Tooltip("study:N", title="Study"),
            alt.Tooltip("effect_size:Q", title="Log OR", format=".2f"),
            alt.Tooltip("std_error:Q", title="SE", format=".3f"),
        ],
    )
)

# Summary effect vertical line
summary_line = (
    alt.Chart(pd.DataFrame({"x": [summary_effect]}))
    .mark_rule(color="#306998", strokeWidth=3, opacity=0.8)
    .encode(x="x:Q")
)

# Null effect reference line (dashed at 0)
null_line = (
    alt.Chart(pd.DataFrame({"x": [0]}))
    .mark_rule(color="#888888", strokeDash=[8, 4], strokeWidth=2, opacity=0.6)
    .encode(x="x:Q")
)

# Funnel confidence bounds (left)
funnel_left = (
    alt.Chart(funnel_df)
    .mark_line(color="#306998", strokeDash=[6, 3], strokeWidth=2, opacity=0.5)
    .encode(x=alt.X("lower:Q"), y=alt.Y("se:Q", scale=alt.Scale(reverse=True)))
)

# Funnel confidence bounds (right)
funnel_right = (
    alt.Chart(funnel_df)
    .mark_line(color="#306998", strokeDash=[6, 3], strokeWidth=2, opacity=0.5)
    .encode(x=alt.X("upper:Q"), y=alt.Y("se:Q", scale=alt.Scale(reverse=True)))
)

# Combine layers
chart = (
    alt.layer(funnel_left, funnel_right, null_line, summary_line, points)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("funnel-meta-analysis · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22)
    .configure_axisX(grid=True, gridOpacity=0.2, gridDash=[4, 4])
    .configure_axisY(grid=False)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
