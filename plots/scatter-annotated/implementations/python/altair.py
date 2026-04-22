""" pyplots.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Selected tech companies showing range of revenue/profit metrics
np.random.seed(42)
companies = ["NVIDIA", "Apple", "Microsoft", "Amazon", "Google", "Meta", "Adobe", "Oracle", "Tesla", "Intel"]
# Revenue (billions USD) - realistic values
revenue = np.array([61, 385, 211, 574, 307, 135, 19, 50, 97, 63])
# Profit margin (%) - realistic values
profit_margin = np.array([55, 25, 35, 6, 22, 20, 34, 26, 11, 8])

df = pd.DataFrame({"company": companies, "revenue": revenue, "profit_margin": profit_margin})

# Points layer
points = (
    alt.Chart(df)
    .mark_point(size=250, filled=True, opacity=0.7, color="#306998")
    .encode(
        x=alt.X("revenue:Q", title="Revenue (Billions USD)", scale=alt.Scale(domain=[0, 620])),
        y=alt.Y("profit_margin:Q", title="Profit Margin (%)", scale=alt.Scale(domain=[0, 60])),
        tooltip=["company:N", "revenue:Q", "profit_margin:Q"],
    )
)

# Text labels layer
labels = (
    alt.Chart(df)
    .mark_text(align="left", dx=12, dy=-8, fontSize=18, fontWeight="bold", color="#333333")
    .encode(x=alt.X("revenue:Q"), y=alt.Y("profit_margin:Q"), text="company:N")
)

# Combine layers
chart = (
    (points + labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(text="scatter-annotated · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG (4800x2700 with scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
