""" pyplots.ai
bar-error: Bar Chart with Error Bars
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import altair as alt
import pandas as pd


# Data - Treatment comparison with measurement variability (±1 SD)
treatment_order = ["Control", "Drug A", "Drug B", "Drug C", "Combination"]
data = pd.DataFrame(
    {"treatment": treatment_order, "response": [45.2, 62.8, 58.3, 71.5, 82.1], "error": [8.5, 12.3, 9.8, 15.2, 11.7]}
)

# Calculate error bar bounds
data["lower"] = data["response"] - data["error"]
data["upper"] = data["response"] + data["error"]

# Create bars
bars = (
    alt.Chart(data)
    .mark_bar(size=60, color="#306998")
    .encode(
        x=alt.X(
            "treatment:N",
            title="Treatment Group",
            sort=treatment_order,
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0),
        ),
        y=alt.Y(
            "response:Q",
            title="Response Rate (%)",
            scale=alt.Scale(domain=[0, 100]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
    )
)

# Create error bars with caps using rule marks
error_bars = (
    alt.Chart(data)
    .mark_rule(strokeWidth=3, color="#333333")
    .encode(x=alt.X("treatment:N", sort=treatment_order), y="lower:Q", y2="upper:Q")
)

# Error bar caps (top)
caps_top = (
    alt.Chart(data)
    .mark_tick(size=30, thickness=3, color="#333333")
    .encode(x=alt.X("treatment:N", sort=treatment_order), y="upper:Q")
)

# Error bar caps (bottom)
caps_bottom = (
    alt.Chart(data)
    .mark_tick(size=30, thickness=3, color="#333333")
    .encode(x=alt.X("treatment:N", sort=treatment_order), y="lower:Q")
)

# Annotation for error bar meaning
annotation = (
    alt.Chart(pd.DataFrame({"text": ["Error bars: ±1 SD"]}))
    .mark_text(align="right", baseline="top", fontSize=16, color="#555555")
    .encode(x=alt.value(1550), y=alt.value(30), text="text:N")
)

# Combine all layers
chart = (
    alt.layer(bars, error_bars, caps_top, caps_bottom, annotation)
    .properties(
        width=1600, height=900, title=alt.Title("bar-error · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG (1600 × 900 × 3 = 4800 × 2700)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
