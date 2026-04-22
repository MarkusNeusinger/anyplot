""" pyplots.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Product quality measurements with asymmetric uncertainty (10th-90th percentile)
np.random.seed(42)
products = ["Product A", "Product B", "Product C", "Product D", "Product E", "Product F"]
central_values = np.array([85.2, 72.8, 91.5, 68.3, 78.9, 82.1])
# Asymmetric errors: lower bound extends less, upper bound extends more (skewed distribution)
error_lower = np.array([5.2, 8.1, 3.8, 9.5, 6.3, 4.9])
error_upper = np.array([8.7, 4.3, 6.2, 5.8, 10.1, 7.6])

df = pd.DataFrame(
    {
        "Product": products,
        "Quality Score": central_values,
        "Lower": central_values - error_lower,
        "Upper": central_values + error_upper,
    }
)

# Create error bar layer (vertical rules)
error_bars = (
    alt.Chart(df)
    .mark_rule(strokeWidth=3, color="#306998")
    .encode(
        x=alt.X("Product:N", title="Product", axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0)),
        y=alt.Y(
            "Lower:Q",
            title="Quality Score (10th–90th Percentile)",
            scale=alt.Scale(domain=[50, 105]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        y2=alt.Y2("Upper:Q"),
    )
)

# Create lower caps (horizontal tick marks at bottom of error bars)
lower_caps = (
    alt.Chart(df).mark_tick(size=30, thickness=3, color="#306998").encode(x=alt.X("Product:N"), y=alt.Y("Lower:Q"))
)

# Create upper caps (horizontal tick marks at top of error bars)
upper_caps = (
    alt.Chart(df).mark_tick(size=30, thickness=3, color="#306998").encode(x=alt.X("Product:N"), y=alt.Y("Upper:Q"))
)

# Create central points
points = (
    alt.Chart(df)
    .mark_point(size=300, filled=True, color="#FFD43B", stroke="#306998", strokeWidth=2)
    .encode(
        x=alt.X("Product:N"),
        y=alt.Y("Quality Score:Q"),
        tooltip=[
            alt.Tooltip("Product:N", title="Product"),
            alt.Tooltip("Quality Score:Q", title="Quality Score", format=".1f"),
            alt.Tooltip("Lower:Q", title="10th Percentile", format=".1f"),
            alt.Tooltip("Upper:Q", title="90th Percentile", format=".1f"),
        ],
    )
)

# Add annotation for what the error bars represent
annotation = (
    alt.Chart(pd.DataFrame({"x": ["Product F"], "y": [53], "text": ["Error bars show 10th–90th percentile range"]}))
    .mark_text(fontSize=16, fontStyle="italic", color="#555555", align="right")
    .encode(x=alt.X("x:N"), y=alt.Y("y:Q"), text="text:N")
)

# Combine all layers
chart = (
    alt.layer(error_bars, lower_caps, upper_caps, points, annotation)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("errorbar-asymmetric · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG (scale_factor=3 gives 4800x2700)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.save("plot.html")
