""" pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-15
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
    [-0.52, -0.31, -0.85, -0.45, -0.08, -0.62, -0.38, -0.55, -0.41, -0.28, -0.78, -0.33, -0.48, -0.25, -1.05]
)

std_errors = np.array([0.18, 0.12, 0.24, 0.15, 0.10, 0.22, 0.14, 0.20, 0.16, 0.11, 0.21, 0.13, 0.17, 0.09, 0.28])

# Summary effect (inverse-variance weighted mean)
weights = 1.0 / std_errors**2
summary_effect = np.sum(weights * effect_sizes) / np.sum(weights)

# Classify studies as inside or outside the funnel (pseudo 95% CI)
lower_bound = summary_effect - 1.96 * std_errors
upper_bound = summary_effect + 1.96 * std_errors
inside_funnel = (effect_sizes >= lower_bound) & (effect_sizes <= upper_bound)

df = pd.DataFrame(
    {
        "study": studies,
        "effect_size": effect_sizes,
        "std_error": std_errors,
        "weight": weights / weights.max(),
        "region": np.where(inside_funnel, "Within funnel", "Outside funnel"),
    }
)

# Funnel confidence limits (pseudo 95% CI)
se_max = max(std_errors) + 0.02
se_range = np.linspace(0, se_max, 100)
funnel_df = pd.DataFrame(
    {"se": se_range, "lower": summary_effect - 1.96 * se_range, "upper": summary_effect + 1.96 * se_range}
)

# Funnel area fill
funnel_area = (
    alt.Chart(funnel_df)
    .transform_fold(["lower", "upper"], as_=["bound", "value"])
    .mark_area(opacity=0.06, color="#306998")
    .encode(x=alt.X("value:Q"), y=alt.Y("se:Q", scale=alt.Scale(reverse=True, domain=[se_max, 0])), detail="bound:N")
)

# Funnel confidence bounds (left and right as separate lines)
funnel_left = (
    alt.Chart(funnel_df)
    .mark_line(color="#306998", strokeDash=[6, 3], strokeWidth=1.5, opacity=0.4)
    .encode(x=alt.X("lower:Q"), y=alt.Y("se:Q", scale=alt.Scale(reverse=True, domain=[se_max, 0])))
)

funnel_right = (
    alt.Chart(funnel_df)
    .mark_line(color="#306998", strokeDash=[6, 3], strokeWidth=1.5, opacity=0.4)
    .encode(x=alt.X("upper:Q"), y=alt.Y("se:Q", scale=alt.Scale(reverse=True, domain=[se_max, 0])))
)

# Summary effect vertical line
summary_line = (
    alt.Chart(pd.DataFrame({"x": [summary_effect]}))
    .mark_rule(color="#306998", strokeWidth=2.5, opacity=0.7)
    .encode(x="x:Q")
)

# Null effect reference line (dashed at 0)
null_line = (
    alt.Chart(pd.DataFrame({"x": [0]}))
    .mark_rule(color="#999999", strokeDash=[8, 4], strokeWidth=1.5, opacity=0.5)
    .encode(x="x:Q")
)

# Color-coded study points sized by weight (storytelling: inside vs outside funnel)
region_color = alt.Color(
    "region:N",
    scale=alt.Scale(domain=["Within funnel", "Outside funnel"], range=["#306998", "#D4652F"]),
    legend=alt.Legend(title=None, orient="bottom-right", labelFontSize=16, symbolSize=200),
)

points = (
    alt.Chart(df)
    .mark_point(filled=True, stroke="white", strokeWidth=1.5, opacity=0.9)
    .encode(
        x=alt.X("effect_size:Q", title="Log Odds Ratio", scale=alt.Scale(domain=[-1.15, 0.35])),
        y=alt.Y("std_error:Q", title="Standard Error", scale=alt.Scale(reverse=True, domain=[se_max, 0])),
        color=region_color,
        size=alt.Size("weight:Q", scale=alt.Scale(range=[120, 450]), legend=None),
        tooltip=[
            alt.Tooltip("study:N", title="Study"),
            alt.Tooltip("effect_size:Q", title="Log OR", format=".2f"),
            alt.Tooltip("std_error:Q", title="SE", format=".3f"),
            alt.Tooltip("region:N", title="Region"),
        ],
    )
)

# Combine layers
chart = (
    alt.layer(funnel_area, funnel_left, funnel_right, null_line, summary_line, points)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "funnel-meta-analysis · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            subtitle="Asymmetry suggests possible publication bias — orange points fall outside the 95% pseudo-confidence funnel",
            subtitleFontSize=16,
            subtitleColor="#666666",
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, titleColor="#333333", labelColor="#555555")
    .configure_axisX(grid=True, gridOpacity=0.15, gridDash=[4, 4])
    .configure_axisY(grid=False)
    .configure_view(strokeWidth=0)
    .configure_legend(padding=10, cornerRadius=4, strokeColor="#dddddd")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
