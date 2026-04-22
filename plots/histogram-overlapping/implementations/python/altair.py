""" pyplots.ai
histogram-overlapping: Overlapping Histograms
Library: altair 6.0.0 | Python 3.13.11
Quality: 97/100 | Created: 2025-12-25
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Employee response times (ms) by department
np.random.seed(42)

engineering = np.random.normal(loc=350, scale=80, size=150)
sales = np.random.normal(loc=420, scale=100, size=150)
support = np.random.normal(loc=280, scale=60, size=150)

df = pd.DataFrame(
    {
        "Response Time (ms)": np.concatenate([engineering, sales, support]),
        "Department": ["Engineering"] * 150 + ["Sales"] * 150 + ["Support"] * 150,
    }
)

# Plot - overlapping histograms with semi-transparent bars
chart = (
    alt.Chart(df)
    .mark_bar(opacity=0.5, binSpacing=0)
    .encode(
        x=alt.X(
            "Response Time (ms):Q",
            bin=alt.Bin(maxbins=25),
            title="Response Time (ms)",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        y=alt.Y("count():Q", title="Frequency", stack=None, axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        color=alt.Color(
            "Department:N",
            scale=alt.Scale(domain=["Engineering", "Sales", "Support"], range=["#306998", "#FFD43B", "#4CAF50"]),
            legend=alt.Legend(
                title="Department",
                titleFontSize=20,
                labelFontSize=18,
                orient="right",
                symbolSize=300,
                symbolStrokeWidth=0,
            ),
        ),
        tooltip=[alt.Tooltip("Department:N"), alt.Tooltip("count():Q", title="Count")],
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title("histogram-overlapping · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[3, 3])
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
