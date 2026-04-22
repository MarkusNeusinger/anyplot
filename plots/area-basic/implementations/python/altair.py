""" pyplots.ai
area-basic: Basic Area Chart
Library: altair 6.0.0 | Python 3.14.2
Quality: 93/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - daily website visitors over a month
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
# Simulate visitor pattern: weekday higher, weekend lower, with growth trend
base = 5000
trend = np.linspace(0, 2000, 30)
weekly_pattern = np.array([1.2, 1.1, 1.0, 1.05, 1.15, 0.8, 0.7] * 5)[:30]
noise = np.random.randn(30) * 300
visitors = (base + trend) * weekly_pattern + noise
# Add a traffic spike mid-month (e.g., marketing campaign on Jan 15)
visitors[14] *= 1.4
visitors = np.maximum(visitors, 1000).astype(int)

df = pd.DataFrame({"date": dates, "visitors": visitors})

# Spike annotation data
spike_row = df.iloc[14]

# Area chart with gradient fill
area = (
    alt.Chart(df)
    .mark_area(
        line={"color": "#306998", "strokeWidth": 2.5},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color="rgba(48, 105, 152, 0.05)", offset=0),
                alt.GradientStop(color="rgba(48, 105, 152, 0.45)", offset=1),
            ],
            x1=1,
            x2=1,
            y1=1,
            y2=0,
        ),
    )
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %d", labelAngle=-30)),
        y=alt.Y("visitors:Q", title="Daily Visitors", scale=alt.Scale(domain=[0, int(df["visitors"].max() * 1.15)])),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("visitors:Q", title="Visitors", format=","),
        ],
    )
)

# Spike annotation - vertical rule + point + text label
spike_df = pd.DataFrame(
    {"date": [spike_row["date"]], "visitors": [spike_row["visitors"]], "label": ["Marketing campaign spike"]}
)

spike_point = alt.Chart(spike_df).mark_circle(size=120, color="#c0392b", opacity=0.9).encode(x="date:T", y="visitors:Q")

spike_label = (
    alt.Chart(spike_df)
    .mark_text(align="left", dx=10, dy=-12, fontSize=16, fontWeight="bold", color="#c0392b")
    .encode(x="date:T", y="visitors:Q", text="label:N")
)

# Compose layered chart
chart = (
    alt.layer(area, spike_point, spike_label)
    .properties(width=1600, height=900, title=alt.Title("area-basic · altair · pyplots.ai", fontSize=28))
    .configure_axis(grid=True, gridOpacity=0.2, labelFontSize=18, titleFontSize=22)
    .configure_view(strokeWidth=0)
)

# Save as PNG (1600 x 900 at scale_factor=3 -> 4800 x 2700 px)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.interactive().save("plot.html")
