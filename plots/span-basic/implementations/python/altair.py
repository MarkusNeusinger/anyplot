""" pyplots.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Stock price over time with recession period highlight
np.random.seed(42)
dates = pd.date_range(start="2007-01-01", periods=36, freq="MS")

# Simulate stock price with a dip during 2008-2009 recession period
base_price = 100
prices = [base_price]
for i in range(1, 36):
    # Add recession dip in months 12-24 (2008-2009)
    if 12 <= i < 24:
        drift = -0.01
    else:
        drift = 0.008
    change = drift + np.random.randn() * 0.03
    prices.append(prices[-1] * (1 + change))

df = pd.DataFrame({"Date": dates, "Price": prices})

# Span data - highlight recession period (vertical span) and threshold zone (horizontal span)
recession_start = pd.Timestamp("2008-01-01")
recession_end = pd.Timestamp("2009-12-01")

# Threshold zone for warning level
threshold_low = 85
threshold_high = 95

# Create base line chart
line = (
    alt.Chart(df)
    .mark_line(strokeWidth=4, color="#306998")
    .encode(
        x=alt.X("Date:T", title="Date", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y(
            "Price:Q",
            title="Stock Price ($)",
            scale=alt.Scale(domain=[60, 130]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
    )
)

# Add points for visibility
points = alt.Chart(df).mark_point(size=150, color="#306998", filled=True).encode(x="Date:T", y="Price:Q")

# Vertical span - Recession period highlight
recession_span_data = pd.DataFrame({"start": [recession_start], "end": [recession_end], "label": ["Recession Period"]})

vertical_span = (
    alt.Chart(recession_span_data)
    .mark_rect(opacity=0.25, color="#FFD43B")
    .encode(x=alt.X("start:T"), x2=alt.X2("end:T"))
)

# Vertical span edge lines
left_edge = (
    alt.Chart(pd.DataFrame({"x": [recession_start]}))
    .mark_rule(strokeWidth=2, strokeDash=[6, 4], color="#D4A000")
    .encode(x="x:T")
)

right_edge = (
    alt.Chart(pd.DataFrame({"x": [recession_end]}))
    .mark_rule(strokeWidth=2, strokeDash=[6, 4], color="#D4A000")
    .encode(x="x:T")
)

# Horizontal span - Warning threshold zone
threshold_span_data = pd.DataFrame({"y": [threshold_low], "y2": [threshold_high]})

horizontal_span = (
    alt.Chart(threshold_span_data).mark_rect(opacity=0.2, color="#E74C3C").encode(y=alt.Y("y:Q"), y2=alt.Y2("y2:Q"))
)

# Horizontal span edge lines
bottom_edge = (
    alt.Chart(pd.DataFrame({"y": [threshold_low]}))
    .mark_rule(strokeWidth=2, strokeDash=[6, 4], color="#C0392B")
    .encode(y="y:Q")
)

top_edge = (
    alt.Chart(pd.DataFrame({"y": [threshold_high]}))
    .mark_rule(strokeWidth=2, strokeDash=[6, 4], color="#C0392B")
    .encode(y="y:Q")
)

# Text labels for spans
recession_label = (
    alt.Chart(pd.DataFrame({"x": [pd.Timestamp("2008-07-01")], "y": [125], "text": ["Recession Period"]}))
    .mark_text(fontSize=18, fontWeight="bold", color="#7D6608")
    .encode(x="x:T", y="y:Q", text="text:N")
)

threshold_label = (
    alt.Chart(pd.DataFrame({"x": [pd.Timestamp("2009-10-01")], "y": [90], "text": ["Warning Zone"]}))
    .mark_text(fontSize=16, fontWeight="bold", color="#922B21")
    .encode(x="x:T", y="y:Q", text="text:N")
)

# Combine all layers
chart = (
    alt.layer(
        horizontal_span,
        bottom_edge,
        top_edge,
        vertical_span,
        left_edge,
        right_edge,
        line,
        points,
        recession_label,
        threshold_label,
    )
    .properties(width=1600, height=900, title=alt.Title("span-basic · altair · pyplots.ai", fontSize=28))
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save as PNG (1600 x 900 x 3 = 4800 x 2700 px)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.save("plot.html")
