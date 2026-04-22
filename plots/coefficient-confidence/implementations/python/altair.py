""" pyplots.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: altair 6.0.0 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-09
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - regression coefficients for housing price prediction
np.random.seed(42)

variables = [
    "Living Area (sqft)",
    "Number of Bedrooms",
    "Number of Bathrooms",
    "Lot Size (acres)",
    "Year Built",
    "Garage Capacity",
    "Distance to Downtown (mi)",
    "School Rating",
    "Property Tax Rate (%)",
    "Basement Area (sqft)",
    "Pool",
    "Central Air",
]

# Coefficients with varying effect sizes and significance
coefficients = [45.2, 12.5, 28.7, 8.3, 0.85, 15.4, -22.1, 18.9, -5.2, 12.1, 35.6, 8.7]
std_errors = [3.2, 5.8, 4.1, 3.9, 0.42, 4.2, 3.8, 2.9, 4.1, 2.8, 6.2, 3.1]

# Calculate 95% confidence intervals
ci_lower = [c - 1.96 * se for c, se in zip(coefficients, std_errors, strict=True)]
ci_upper = [c + 1.96 * se for c, se in zip(coefficients, std_errors, strict=True)]

# Determine significance (CI doesn't cross zero)
significant = [(lo > 0 or hi < 0) for lo, hi in zip(ci_lower, ci_upper, strict=True)]

df = pd.DataFrame(
    {
        "variable": variables,
        "coefficient": coefficients,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "significant": significant,
    }
)

# Sort by coefficient magnitude for better visualization
df = df.sort_values("coefficient", ascending=True).reset_index(drop=True)
df["variable"] = pd.Categorical(df["variable"], categories=df["variable"].tolist(), ordered=True)

# Create the coefficient plot
# Error bars (confidence intervals)
error_bars = (
    alt.Chart(df)
    .mark_rule(strokeWidth=3)
    .encode(
        x=alt.X("ci_lower:Q", title="Coefficient Estimate (Effect on Price in $1000s)"),
        x2="ci_upper:Q",
        y=alt.Y("variable:N", title="Predictor Variable", sort=None),
        color=alt.condition(
            alt.datum.significant,
            alt.value("#306998"),  # Python Blue for significant
            alt.value("#999999"),  # Gray for non-significant
        ),
    )
)

# Points (coefficient estimates)
points = (
    alt.Chart(df)
    .mark_point(size=300, filled=True)
    .encode(
        x="coefficient:Q",
        y=alt.Y("variable:N", sort=None),
        color=alt.condition(
            alt.datum.significant,
            alt.value("#306998"),  # Python Blue for significant
            alt.value("#999999"),  # Gray for non-significant
        ),
        tooltip=[
            alt.Tooltip("variable:N", title="Variable"),
            alt.Tooltip("coefficient:Q", title="Coefficient", format=".2f"),
            alt.Tooltip("ci_lower:Q", title="CI Lower", format=".2f"),
            alt.Tooltip("ci_upper:Q", title="CI Upper", format=".2f"),
            alt.Tooltip("significant:N", title="Significant"),
        ],
    )
)

# Vertical reference line at zero
zero_line = (
    alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(strokeDash=[8, 6], strokeWidth=2, color="#333333").encode(x="x:Q")
)

# Combine layers
chart = (
    (zero_line + error_bars + points)
    .properties(
        width=1400,
        height=800,
        title=alt.Title("coefficient-confidence · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, labelLimit=400)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
