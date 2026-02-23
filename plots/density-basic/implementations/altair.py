""" pyplots.ai
density-basic: Basic Density Plot
Library: altair 6.0.0 | Python 3.14.3
Quality: 87/100 | Updated: 2026-02-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - bimodal distribution showing two student groups with distinct performance
np.random.seed(42)
values = np.concatenate(
    [
        np.random.normal(loc=38, scale=7, size=200),  # Group A — foundational course
        np.random.normal(loc=72, scale=8, size=150),  # Group B — advanced course
    ]
)
values = np.clip(values, 5, 100)  # Keep within realistic test score range

df = pd.DataFrame({"Test Score": values})


# Density curve with filled area
density = (
    alt.Chart(df)
    .transform_density("Test Score", as_=["Test Score", "density"], bandwidth=4)
    .mark_area(opacity=0.5, color="#306998", line={"color": "#1e4d6e", "strokeWidth": 2.5})
    .encode(
        x=alt.X(
            "Test Score:Q",
            title="Test Score (points)",
            scale=alt.Scale(domain=[10, 100]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, tickCount=10),
        ),
        y=alt.Y("density:Q", title="Probability Density", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        tooltip=[
            alt.Tooltip("Test Score:Q", title="Score", format=".1f"),
            alt.Tooltip("density:Q", title="Density", format=".4f"),
        ],
    )
)

# Rug plot — small tick marks showing individual observations along x-axis
rug = (
    alt.Chart(df)
    .mark_tick(color="#306998", opacity=0.4, thickness=1.5, size=18)
    .encode(x=alt.X("Test Score:Q"), y=alt.value(880))
)

# Combine layers
chart = (
    alt.layer(density, rug)
    .properties(width=1600, height=900, title=alt.Title(text="density-basic · altair · pyplots.ai", fontSize=28))
    .configure_view(strokeWidth=0)
    .configure_axis(gridColor="#e0e0e0", gridOpacity=0.2, gridDash=[4, 4], domainColor="#888888")
)

# Save as PNG (1600 * 3 = 4800, 900 * 3 = 2700)
chart.save("plot.png", scale_factor=3.0)

# Save as interactive HTML
chart.interactive().save("plot.html")
