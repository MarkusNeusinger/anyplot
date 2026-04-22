""" pyplots.ai
line-stepwise: Step Line Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Daily temperature readings that change discretely
np.random.seed(42)
days = np.arange(0, 20)
# Temperature values that step discretely (simulating daily high temperature readings)
base_temp = 22
temps = base_temp + np.cumsum(np.random.choice([-2, -1, 0, 1, 2], size=20))

df = pd.DataFrame({"Day": days, "Temperature (°C)": temps})

# Create step line chart using interpolate='step-after'
chart = (
    alt.Chart(df)
    .mark_line(interpolate="step-after", strokeWidth=4, color="#306998")
    .encode(
        x=alt.X("Day:Q", title="Day", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y(
            "Temperature (°C):Q",
            title="Temperature (°C)",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        tooltip=["Day", "Temperature (°C)"],
    )
    .properties(
        width=1600, height=900, title=alt.Title("line-stepwise · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save as PNG (1600 × 900 * 3 = 4800 × 2700 px)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
