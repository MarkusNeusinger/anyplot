""" pyplots.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess


# Data - complex non-linear relationship
np.random.seed(42)
n = 200
x = np.linspace(0, 10, n)
# Non-linear pattern: sine wave with trend and noise
y = 2 * np.sin(x * 0.8) + 0.5 * x + np.random.normal(0, 0.8, n)

# Create DataFrame for scatter points
df = pd.DataFrame({"x": x, "y": y})

# Compute LOWESS smoothed values
lowess_result = lowess(y, x, frac=0.3, return_sorted=True)
df_lowess = pd.DataFrame({"x": lowess_result[:, 0], "y_lowess": lowess_result[:, 1]})

# Scatter points layer
scatter = (
    alt.Chart(df)
    .mark_point(size=100, opacity=0.6, color="#306998")
    .encode(x=alt.X("x:Q", title="Independent Variable (x)"), y=alt.Y("y:Q", title="Dependent Variable (y)"))
)

# LOWESS curve layer
lowess_line = (
    alt.Chart(df_lowess).mark_line(strokeWidth=4, color="#FFD43B").encode(x=alt.X("x:Q"), y=alt.Y("y_lowess:Q"))
)

# Combine layers
chart = (
    (scatter + lowess_line)
    .properties(width=1600, height=900, title=alt.Title("scatter-regression-lowess · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
