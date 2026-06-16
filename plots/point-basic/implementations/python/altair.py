""" anyplot.ai
point-basic: Point Estimate Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-11
"""

import os
from pathlib import Path


# Change to script directory to ensure files save in the right place
os.chdir(Path(__file__).parent)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series is always #009E73 (brand green)
BRAND = "#009E73"
SECONDARY = "#C475FD"
REFERENCE_LINE = "#888888"

# Data - Treatment effect estimates with 95% confidence intervals
np.random.seed(42)
groups = ["Treatment A", "Treatment B", "Treatment C", "Treatment D", "Control", "Placebo"]
estimates = [2.4, 1.8, 3.1, -0.5, 0.2, 0.8]
ci_widths = [0.8, 1.2, 0.6, 1.0, 0.9, 1.1]
lower = [e - w for e, w in zip(estimates, ci_widths, strict=True)]
upper = [e + w for e, w in zip(estimates, ci_widths, strict=True)]

df = pd.DataFrame({"Group": groups, "Estimate": estimates, "Lower": lower, "Upper": upper})

# Base chart for points
points = (
    alt.Chart(df)
    .mark_point(size=400, filled=True, color=BRAND)
    .encode(
        x=alt.X("Estimate:Q", title="Effect Size", scale=alt.Scale(domain=[-3, 5])),
        y=alt.Y("Group:N", title=None, sort=None),
        tooltip=["Group:N", "Estimate:Q", "Lower:Q", "Upper:Q"],
    )
)

# Error bars (confidence intervals)
error_bars = (
    alt.Chart(df)
    .mark_rule(strokeWidth=3, color=BRAND)
    .encode(x=alt.X("Lower:Q"), x2=alt.X2("Upper:Q"), y=alt.Y("Group:N", sort=None))
)

# Error bar caps (left)
caps_left = (
    alt.Chart(df).mark_tick(thickness=3, size=20, color=BRAND).encode(x=alt.X("Lower:Q"), y=alt.Y("Group:N", sort=None))
)

# Error bar caps (right)
caps_right = (
    alt.Chart(df).mark_tick(thickness=3, size=20, color=BRAND).encode(x=alt.X("Upper:Q"), y=alt.Y("Group:N", sort=None))
)

# Reference line at zero (null hypothesis)
reference_line = (
    alt.Chart(pd.DataFrame({"x": [0]}))
    .mark_rule(strokeDash=[8, 4], strokeWidth=2, color=REFERENCE_LINE)
    .encode(x=alt.X("x:Q"))
)

# Combine layers
chart = (
    alt.layer(reference_line, error_bars, caps_left, caps_right, points)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("point-basic · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=1)
    .configure_title(color=INK)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
