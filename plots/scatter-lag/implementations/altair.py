""" pyplots.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-04-12
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

y_t = values[:-lag]
y_t_lag = values[lag:]
r_value = np.corrcoef(y_t, y_t_lag)[0, 1]

df = pd.DataFrame({"y_t": y_t, "y_t_lag": y_t_lag, "time_index": np.arange(n_points - lag)})

# Reference line (y = x diagonal)
margin = 0.5
axis_min = min(df["y_t"].min(), df["y_t_lag"].min()) - margin
axis_max = max(df["y_t"].max(), df["y_t_lag"].max()) + margin
ref_df = pd.DataFrame({"x": [axis_min, axis_max], "y": [axis_min, axis_max]})

# Annotation for correlation coefficient
annot_df = pd.DataFrame({"x": [axis_max - 0.3], "y": [axis_min + 0.5], "label": [f"r = {r_value:.3f}"]})

# Reference line
reference_line = (
    alt.Chart(ref_df).mark_line(strokeDash=[8, 6], strokeWidth=1.5, color="#aaaaaa").encode(x="x:Q", y="y:Q")
)

# Scatter points with reduced size/opacity to prevent overplotting
points = (
    alt.Chart(df)
    .mark_point(size=45, filled=True, strokeWidth=0.5, stroke="white", opacity=0.45)
    .encode(
        x=alt.X("y_t:Q", title="y(t)", scale=alt.Scale(domain=[axis_min, axis_max]), axis=alt.Axis(tickCount=10)),
        y=alt.Y(
            "y_t_lag:Q", title="y(t + 1)", scale=alt.Scale(domain=[axis_min, axis_max]), axis=alt.Axis(tickCount=10)
        ),
        color=alt.Color(
            "time_index:Q",
            scale=alt.Scale(scheme="viridis"),
            legend=alt.Legend(
                title="Time Index",
                titleFontSize=16,
                labelFontSize=16,
                gradientLength=280,
                gradientThickness=14,
                orient="right",
                offset=10,
            ),
        ),
        tooltip=[
            alt.Tooltip("y_t:Q", title="y(t)", format=".2f"),
            alt.Tooltip("y_t_lag:Q", title="y(t+1)", format=".2f"),
            alt.Tooltip("time_index:Q", title="Time Index"),
        ],
    )
)

# Correlation annotation
annotation = (
    alt.Chart(annot_df)
    .mark_text(align="right", baseline="bottom", fontSize=20, fontWeight="bold", color="#333333")
    .encode(x="x:Q", y="y:Q", text="label:N")
)

chart = (
    (reference_line + points + annotation)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "scatter-lag · altair · pyplots.ai",
            fontSize=28,
            subtitle=f"AR(1) process (φ = {phi}) | lag = {lag}",
            subtitleFontSize=18,
            subtitleColor="#666666",
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        grid=True,
        gridOpacity=0.15,
        gridWidth=0.5,
        domainWidth=0,
        tickSize=6,
        tickWidth=0.8,
        tickColor="#999999",
        labelColor="#444444",
        titleColor="#333333",
    )
    .configure_view(strokeWidth=0)
    .configure_title(anchor="start", offset=10)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
