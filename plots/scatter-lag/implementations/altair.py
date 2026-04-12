""" pyplots.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: altair 6.0.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-04-12
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - synthetic AR(1) process with moderate autocorrelation
np.random.seed(42)
n_points = 500
lag = 1
phi = 0.85
noise = np.random.normal(0, 1, n_points)
values = np.zeros(n_points)
values[0] = noise[0]
for i in range(1, n_points):
    values[i] = phi * values[i - 1] + noise[i]

df = pd.DataFrame({"y_t": values[:-lag], "y_t_lag": values[lag:], "time_index": np.arange(n_points - lag)})

# Reference line (y = x diagonal)
margin = 0.5
axis_min = min(df["y_t"].min(), df["y_t_lag"].min()) - margin
axis_max = max(df["y_t"].max(), df["y_t_lag"].max()) + margin
ref_df = pd.DataFrame({"x": [axis_min, axis_max], "y": [axis_min, axis_max]})

# Plot
reference_line = alt.Chart(ref_df).mark_line(strokeDash=[8, 6], strokeWidth=2, color="#999999").encode(x="x:Q", y="y:Q")

points = (
    alt.Chart(df)
    .mark_point(size=120, filled=True, strokeWidth=0.8, stroke="white", opacity=0.7)
    .encode(
        x=alt.X("y_t:Q", title="y(t)", scale=alt.Scale(domain=[axis_min, axis_max])),
        y=alt.Y("y_t_lag:Q", title="y(t + 1)", scale=alt.Scale(domain=[axis_min, axis_max])),
        color=alt.Color(
            "time_index:Q",
            scale=alt.Scale(scheme="viridis"),
            legend=alt.Legend(
                title="Time Index", titleFontSize=16, labelFontSize=14, gradientLength=300, gradientThickness=16
            ),
        ),
        tooltip=["y_t:Q", "y_t_lag:Q", "time_index:Q"],
    )
)

chart = (
    (reference_line + points)
    .properties(width=1600, height=900, title=alt.Title("scatter-lag · altair · pyplots.ai", fontSize=28))
    .configure_axis(
        labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.2, gridWidth=0.8, domainColor="#333333"
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
