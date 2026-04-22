""" pyplots.ai
point-basic: Point Estimate Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Treatment effect estimates with 95% confidence intervals
np.random.seed(42)
groups = ["Treatment A", "Treatment B", "Treatment C", "Treatment D", "Control", "Placebo"]
estimates = [2.4, 1.8, 3.1, -0.5, 0.2, 0.8]
# Calculate realistic confidence intervals (varying precision)
ci_widths = [0.8, 1.2, 0.6, 1.0, 0.9, 1.1]
lower = [e - w for e, w in zip(estimates, ci_widths, strict=True)]
upper = [e + w for e, w in zip(estimates, ci_widths, strict=True)]

df = pd.DataFrame({"Group": groups, "Estimate": estimates, "Lower": lower, "Upper": upper})

# Base chart for points
points = (
    alt.Chart(df)
    .mark_point(size=400, filled=True, color="#306998")
    .encode(
        x=alt.X("Estimate:Q", title="Effect Size", scale=alt.Scale(domain=[-3, 5])),
        y=alt.Y("Group:N", title=None, sort=None),
        tooltip=["Group:N", "Estimate:Q", "Lower:Q", "Upper:Q"],
    )
)

# Error bars (confidence intervals)
error_bars = (
    alt.Chart(df)
    .mark_rule(strokeWidth=3, color="#306998")
    .encode(x=alt.X("Lower:Q"), x2=alt.X2("Upper:Q"), y=alt.Y("Group:N", sort=None))
)

# Error bar caps (left)
caps_left = (
    alt.Chart(df)
    .mark_tick(thickness=3, size=20, color="#306998")
    .encode(x=alt.X("Lower:Q"), y=alt.Y("Group:N", sort=None))
)

# Error bar caps (right)
caps_right = (
    alt.Chart(df)
    .mark_tick(thickness=3, size=20, color="#306998")
    .encode(x=alt.X("Upper:Q"), y=alt.Y("Group:N", sort=None))
)

# Reference line at zero (null hypothesis)
reference_line = (
    alt.Chart(pd.DataFrame({"x": [0]}))
    .mark_rule(strokeDash=[8, 4], strokeWidth=2, color="#888888")
    .encode(x=alt.X("x:Q"))
)

# Combine layers
chart = (
    alt.layer(reference_line, error_bars, caps_left, caps_right, points)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("point-basic \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, labelColor="#333333", titleColor="#333333")
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
