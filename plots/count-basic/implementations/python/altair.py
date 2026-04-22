""" pyplots.ai
count-basic: Basic Count Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Survey responses with varying frequencies
np.random.seed(42)
responses = np.random.choice(
    ["Excellent", "Good", "Average", "Poor", "Very Poor"],
    size=200,
    p=[0.25, 0.35, 0.20, 0.12, 0.08],  # Realistic distribution
)
df = pd.DataFrame({"Response": responses})

# Count and sort by frequency for better visualization
counts = df["Response"].value_counts().reset_index()
counts.columns = ["Response", "Count"]

# Create chart with automatic counting
chart = (
    alt.Chart(counts)
    .mark_bar(
        color="#306998",  # Python Blue
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4,
    )
    .encode(
        x=alt.X(
            "Response:N",
            sort="-y",  # Sort by count descending
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0),
            title="Survey Response",
        ),
        y=alt.Y("Count:Q", axis=alt.Axis(labelFontSize=18, titleFontSize=22), title="Number of Responses"),
    )
)

# Add count labels on top of bars
text = chart.mark_text(align="center", baseline="bottom", dy=-5, fontSize=18, fontWeight="bold").encode(text="Count:Q")

# Combine bar and text
final_chart = (
    (chart + text)
    .properties(
        width=1600, height=900, title=alt.Title("count-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save as PNG (1600 × 900 × 3 = 4800 × 2700)
final_chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
final_chart.save("plot.html")
