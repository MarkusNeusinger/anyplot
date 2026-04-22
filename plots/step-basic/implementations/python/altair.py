""" pyplots.ai
step-basic: Basic Step Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

# Workaround for altair.py file shadowing the altair module
import os
import sys


_cwd = os.getcwd()
if _cwd in sys.path:
    sys.path.remove(_cwd)
if "" in sys.path:
    sys.path.remove("")

import altair as alt  # noqa: E402, I001

sys.path.insert(0, _cwd)

import pandas as pd  # noqa: E402, I001


# Data - Monthly cumulative sales (shows clear step pattern)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
cumulative_sales = [12, 25, 31, 48, 52, 67, 89, 95, 108, 124, 145, 168]

df = pd.DataFrame({"Month": months, "Cumulative Sales": cumulative_sales})

# Create step chart
chart = (
    alt.Chart(df)
    .mark_line(interpolate="step-after", strokeWidth=4, color="#306998")
    .encode(
        x=alt.X("Month:N", title="Month", sort=months, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Cumulative Sales:Q", title="Cumulative Sales (thousands $)"),
    )
    .properties(width=1600, height=900, title=alt.Title("step-basic · altair · pyplots.ai", fontSize=28))
)

# Add markers at data points to highlight where changes occur
points = (
    alt.Chart(df)
    .mark_point(size=200, color="#306998", filled=True)
    .encode(x=alt.X("Month:N", sort=months), y="Cumulative Sales:Q")
)

# Combine line and points
final_chart = (
    (chart + points)
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save as PNG (1600 × 900 @ scale 3 = 4800 × 2700)
final_chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
final_chart.save("plot.html")
