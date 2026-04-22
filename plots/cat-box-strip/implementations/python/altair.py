""" pyplots.ai
cat-box-strip: Box Plot with Strip Overlay
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Product quality scores across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Support"]
data = []

# Create varied distributions per department
for dept in departments:
    if dept == "Engineering":
        # Higher scores, tight distribution
        values = np.random.normal(85, 6, 40)
    elif dept == "Marketing":
        # Medium scores, wider spread
        values = np.random.normal(72, 12, 35)
        # Add some outliers
        values = np.append(values, [45, 48, 98])
    elif dept == "Sales":
        # Lower scores, moderate spread
        values = np.random.normal(65, 10, 45)
        # Add outliers
        values = np.append(values, [35, 92, 95])
    else:  # Support
        # Bimodal distribution
        values = np.concatenate([np.random.normal(60, 8, 20), np.random.normal(80, 5, 25)])

    for v in values:
        data.append({"Department": dept, "Quality Score": np.clip(v, 30, 100)})

df = pd.DataFrame(data)

# Box plot layer
boxplot = (
    alt.Chart(df)
    .mark_boxplot(size=60, color="#306998", median={"color": "#FFD43B", "strokeWidth": 3})
    .encode(
        x=alt.X("Department:N", title="Department", axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0)),
        y=alt.Y(
            "Quality Score:Q",
            title="Quality Score",
            scale=alt.Scale(domain=[25, 105]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
    )
)

# Strip plot layer with jitter
strip = (
    alt.Chart(df)
    .mark_circle(size=80, color="#306998", opacity=0.5)
    .encode(x=alt.X("Department:N"), y=alt.Y("Quality Score:Q"), xOffset="jitter:Q")
    .transform_calculate(jitter="sqrt(-2*log(random()))*cos(2*PI*random())*15")
)

# Combine layers
chart = (
    alt.layer(boxplot, strip)
    .properties(
        width=1600, height=900, title=alt.Title("cat-box-strip · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
