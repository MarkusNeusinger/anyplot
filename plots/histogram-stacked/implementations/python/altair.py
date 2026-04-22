""" pyplots.ai
histogram-stacked: Stacked Histogram
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Test scores from three different study methods
np.random.seed(42)

# Generate realistic test score distributions for three study methods
method_a = np.random.normal(loc=72, scale=10, size=150)  # Traditional study
method_b = np.random.normal(loc=78, scale=8, size=120)  # Active recall
method_c = np.random.normal(loc=68, scale=12, size=100)  # Passive reading

# Clip to valid score range (0-100)
method_a = np.clip(method_a, 0, 100)
method_b = np.clip(method_b, 0, 100)
method_c = np.clip(method_c, 0, 100)

# Create DataFrame
df = pd.DataFrame(
    {
        "Score": np.concatenate([method_a, method_b, method_c]),
        "Study Method": (
            ["Traditional Study"] * len(method_a)
            + ["Active Recall"] * len(method_b)
            + ["Passive Reading"] * len(method_c)
        ),
    }
)

# Create stacked histogram using binned bar chart
chart = (
    alt.Chart(df)
    .mark_bar(opacity=0.85, stroke="white", strokeWidth=0.5)
    .encode(
        x=alt.X(
            "Score:Q",
            bin=alt.Bin(maxbins=20),
            title="Test Score (points)",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        y=alt.Y(
            "count():Q", title="Number of Students", stack="zero", axis=alt.Axis(labelFontSize=18, titleFontSize=22)
        ),
        color=alt.Color(
            "Study Method:N",
            scale=alt.Scale(
                domain=["Traditional Study", "Active Recall", "Passive Reading"],
                range=["#306998", "#FFD43B", "#E67E22"],
            ),
            legend=alt.Legend(title="Study Method", titleFontSize=18, labelFontSize=16, orient="right"),
        ),
        order=alt.Order("Study Method:N", sort="ascending"),
    )
    .properties(
        width=1600, height=900, title=alt.Title("histogram-stacked · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[2, 2])
    .configure_view(strokeWidth=0)
)

# Save as PNG (scale_factor=3 gives 4800x2700)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.save("plot.html")
