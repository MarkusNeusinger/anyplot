""" pyplots.ai
funnel-basic: Basic Funnel Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import pandas as pd


# Data - Sales funnel example
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]

# Create DataFrame with centered positioning for funnel shape
df = pd.DataFrame({"stage": stages, "value": values, "order": range(len(stages))})

# Calculate percentage of initial value for display
df["percentage"] = (df["value"] / df["value"].iloc[0] * 100).round(1)
df["label"] = df["value"].astype(str) + " (" + df["percentage"].astype(str) + "%)"

# For centered funnel: calculate x start and end positions
df["x_start"] = -df["value"] / 2
df["x_end"] = df["value"] / 2

# Colors for each stage (Python Blue gradient to Yellow)
colors = ["#306998", "#3D7AAF", "#4A8BC6", "#579CDD", "#FFD43B"]

# Create centered horizontal bars to form funnel shape
bars = (
    alt.Chart(df)
    .mark_bar(cornerRadius=4, height=70)
    .encode(
        x=alt.X("x_start:Q", axis=None, scale=alt.Scale(domain=[-600, 600])),
        x2="x_end:Q",
        y=alt.Y(
            "stage:N", sort=stages, axis=alt.Axis(labelFontSize=20, labelFontWeight="bold", title=None, labelPadding=15)
        ),
        color=alt.Color("stage:N", scale=alt.Scale(domain=stages, range=colors), legend=None),
    )
)

# Add value labels to the right of bars
text = (
    alt.Chart(df)
    .mark_text(align="left", baseline="middle", dx=15, fontSize=18, fontWeight="bold")
    .encode(x=alt.X("x_end:Q"), y=alt.Y("stage:N", sort=stages), text=alt.Text("label:N"), color=alt.value("#333333"))
)

# Combine bars and text
chart = (
    (bars + text)
    .properties(
        width=1600, height=900, title=alt.Title(text="funnel-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False)
)

# Save as PNG (target 4800x2700) and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
