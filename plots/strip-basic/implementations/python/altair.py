""" pyplots.ai
strip-basic: Basic Strip Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Survey response scores by department
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Support"]
data = []

# Create varying distributions for each department to show diversity
distributions = {
    "Engineering": (75, 10),  # Higher mean, moderate spread
    "Marketing": (68, 15),  # Medium mean, wider spread
    "Sales": (72, 12),  # Medium-high mean, moderate spread
    "Support": (65, 18),  # Lower mean, widest spread (shows more outliers)
}

for dept in departments:
    mean, std = distributions[dept]
    n_points = np.random.randint(35, 50)  # 35-50 points per category
    scores = np.clip(np.random.normal(mean, std, n_points), 20, 100)
    for score in scores:
        data.append({"Department": dept, "Response Score": score})

df = pd.DataFrame(data)

# Calculate group means for reference lines
means = df.groupby("Department")["Response Score"].mean().reset_index()
means.columns = ["Department", "Mean"]

# Base strip chart
strip = (
    alt.Chart(df)
    .mark_circle(size=200, opacity=0.6)
    .encode(
        x=alt.X("Department:N", title="Department", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y(
            "Response Score:Q",
            title="Response Score",
            scale=alt.Scale(domain=[15, 105]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        xOffset="jitter:Q",
        color=alt.value("#306998"),
    )
    .transform_calculate(jitter="sqrt(-2*log(random()))*cos(2*PI*random())*0.2")
)

# Mean reference lines per group
mean_lines = (
    alt.Chart(means).mark_tick(thickness=3, size=40, color="#FFD43B").encode(x=alt.X("Department:N"), y=alt.Y("Mean:Q"))
)

# Combine layers
chart = (
    alt.layer(strip, mean_lines)
    .properties(width=1600, height=900, title=alt.Title("strip-basic · altair · pyplots.ai", fontSize=28))
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
