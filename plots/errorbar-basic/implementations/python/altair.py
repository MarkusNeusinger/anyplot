""" pyplots.ai
errorbar-basic: Basic Error Bar Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - experimental measurements with associated uncertainties
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
y_values = [25.3, 38.7, 42.1, 35.8, 48.2, 31.5]

# Asymmetric errors: Treatment C and D have notably different lower/upper bounds
asymmetric_lower = [2.1, 3.5, 2.8, 6.5, 4.8, 2.5]
asymmetric_upper = [2.1, 3.5, 2.8, 2.8, 2.2, 2.5]

# Create DataFrame with error bounds
df = pd.DataFrame(
    {
        "category": categories,
        "value": y_values,
        "error_lower": [y - el for y, el in zip(y_values, asymmetric_lower, strict=True)],
        "error_upper": [y + eu for y, eu in zip(y_values, asymmetric_upper, strict=True)],
    }
)

# Base chart with shared properties
base = alt.Chart(df).encode(
    x=alt.X(
        "category:N",
        title="Experimental Group",
        sort=categories,
        axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0),
    )
)

# Points for the central values
points = base.mark_circle(size=300, color="#306998").encode(
    y=alt.Y(
        "value:Q",
        title="Response Value (units)",
        scale=alt.Scale(domain=[0, 55]),
        axis=alt.Axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.3, gridDash=[4, 4]),
    )
)

# Error bars using mark_rule with y and y2
error_bars = base.mark_rule(strokeWidth=3, color="#306998").encode(y=alt.Y("error_lower:Q"), y2="error_upper:Q")

# Error bar caps (top)
caps_top = base.mark_tick(thickness=3, size=20, color="#306998").encode(y="error_upper:Q")

# Error bar caps (bottom)
caps_bottom = base.mark_tick(thickness=3, size=20, color="#306998").encode(y="error_lower:Q")

# Layer all elements
chart = (
    alt.layer(error_bars, caps_bottom, caps_top, points)
    .properties(width=1600, height=900, title=alt.Title("errorbar-basic · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
